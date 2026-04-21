"""Select demo images from cv_training data and resize to 600x600 center-crop.

Images are sourced from data/cv_training/{crop}/{stage}/{condition}/ directories.
Kale is used as a proxy for kailan, spinach, and lettuce since those crops
are not present in the training data but share similar visual signatures:
  - kale/harvest_ready/normal      → demo_kailan_healthy.jpg
  - kale/early/nitrogen_low        → demo_spinach_nitrogen.jpg
  - kale/early/water_stress        → demo_lettuce_wilt.jpg
"""

from pathlib import Path

from PIL import Image
import numpy as np

BASE = Path(__file__).resolve().parent.parent / "data" / "cv_training"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "demo_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_SIZE = (600, 600)

# (output_filename, source_dir_subpath, selection_strategy)
DEMOS = [
    ("demo_kailan_healthy.jpg", "kale/harvest_ready/normal", "brightest_green"),
    ("demo_spinach_nitrogen.jpg", "kale/early/nitrogen_low", "most_yellow"),
    ("demo_lettuce_wilt.jpg", "kale/early/water_stress", "most_desaturated"),
]


def center_crop(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Crop to target size from center."""
    w, h = img.size
    tw, th = size
    left = (w - tw) // 2
    top = (h - th) // 2
    return img.crop((left, top, left + tw, top + th))


def avg_hsv(img: Image.Image) -> np.ndarray:
    """Return mean HSV values for the image (H in [0,360], S/V in [0,1])."""
    rgb = np.array(img.convert("RGB")) / 255.0
    rgb = np.clip(rgb, 0.001, 0.999)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    maxc = np.maximum(r, np.maximum(g, b))
    minc = np.minimum(r, np.minimum(g, b))
    v = maxc
    s = np.where(maxc > 0, (maxc - minc) / maxc, 0)

    delta = maxc - minc
    delta = np.where(delta == 0, np.ones_like(delta), delta)  # avoid div-by-zero
    h = np.zeros_like(delta)
    mask_r = (maxc == r) & (delta > 0)
    mask_g = (maxc == g) & (delta > 0)
    mask_b = (maxc == b) & (delta > 0)
    h[mask_r] = 60 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
    h[mask_g] = 60 * ((b[mask_g] - r[mask_g]) / delta[mask_g] + 2)
    h[mask_b] = 60 * ((r[mask_b] - g[mask_b]) / delta[mask_b] + 4)
    return np.array([h.mean(), s.mean(), v.mean()])


def score_brightest_green(hsv: np.ndarray) -> float:
    """Higher score = most green-ish (lowest H away from blue background).

    Images have blue-dominant background (H~195-235). Healthy plant pixels
    have lower H. Score = (max_H - H) * S  so lower H + higher S wins.
    """
    h, s, v = hsv
    max_h = 235.0
    return (max_h - h) * s


def score_most_yellow(hsv: np.ndarray) -> float:
    """Higher score = most yellow-green (nitrogen deficiency chlorosis).

    Nitrogen-deficient kale shows yellowing (lower H than healthy) but
    very low saturation. Score: prioritise lower H over high S since
    all images have low S anyway.
    """
    h, s, v = hsv
    # Penalise blue background (high H), reward yellow-green (low H)
    # Baseline H offset: average background ~235, green ~120, yellow-green ~60
    # Lower H = more chlorosis
    h_penalty = max(0, h - 180) / 60.0  # 0 at H=180, grows as H→blue
    return (1 - h_penalty) * max(s, 0.005)


def score_most_desaturated(hsv: np.ndarray) -> float:
    """Higher score = most desaturated/dark (water stress/wilting).

    Water-stressed images have lower saturation and value.
    Score = (1 - S) + (1 - V)  so darkest, most washed-out wins.
    """
    h, s, v = hsv
    return (1 - s) * 0.6 + (1 - v) * 0.4


def select_best_image(source_dir: Path, strategy: str) -> Path | None:
    """Return the best image path for the given selection strategy."""
    images = sorted(source_dir.glob("*.jpg")) + sorted(source_dir.glob("*.png"))
    if not images:
        return None

    scorer = {
        "brightest_green": score_brightest_green,
        "most_yellow": score_most_yellow,
        "most_desaturated": score_most_desaturated,
    }[strategy]

    best_path, best_score = None, -1.0
    for path in images:
        try:
            img = Image.open(path)
            hsv = avg_hsv(img)
            score = scorer(hsv)
            if score > best_score:
                best_score = score
                best_path = path
        except Exception as e:
            print(f"  Warning: could not process {path.name}: {e}")
            continue

    return best_path


def main():
    for output_name, source_subdir, strategy in DEMOS:
        source_dir = BASE / source_subdir
        print(f"\n[{output_name}]")
        print(f"  Source: {source_dir}")
        print(f"  Strategy: {strategy}")

        best = select_best_image(source_dir, strategy)
        if best is None:
            print(f"  ERROR: no images found in {source_dir}")
            continue

        print(f"  Selected: {best.name} (score={score_for_print(best, strategy)})")

        img = Image.open(best)
        cropped = center_crop(img, TARGET_SIZE)
        out_path = OUT_DIR / output_name
        cropped.save(out_path, "JPEG", quality=90)
        print(f"  Saved: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


def score_for_print(path: Path, strategy: str) -> str:
    try:
        img = Image.open(path)
        hsv = avg_hsv(img)
        scorer = {
            "brightest_green": score_brightest_green,
            "most_yellow": score_most_yellow,
            "most_desaturated": score_most_desaturated,
        }[strategy]
        return f"{scorer(hsv):.4f}"
    except Exception:
        return "N/A"


if __name__ == "__main__":
    main()
