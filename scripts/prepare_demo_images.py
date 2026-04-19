#!/usr/bin/env python3
"""Prepare 3 demo images from existing CV training data.

Selects representative images from data/cv_training/, resizes to 600x600,
and saves to data/demo_images/ for use in the Streamlit uploader demo.
"""

from pathlib import Path

from PIL import Image

SRC = Path("data/cv_training")
DST = Path("data/demo_images")
DST.mkdir(parents=True, exist_ok=True)

SELECTIONS = [
    {
        "src": SRC / "kale/early/normal/kale_early_normal_000.jpg",
        "dst": DST / "demo_kailan_healthy.jpg",
        "label": "Healthy kale (early stage)",
    },
    {
        "src": SRC / "kale/early/nitrogen_low/kale_early_nitrogen_low_000.jpg",
        "dst": DST / "demo_spinach_nitrogen.jpg",
        "label": "Kale showing nitrogen deficiency (yellowing)",
    },
    {
        "src": SRC / "kale/early/water_stress/kale_early_water_stress_000.jpg",
        "dst": DST / "demo_lettuce_wilt.jpg",
        "label": "Kale showing water stress / wilting",
    },
]


def resize_keep_aspect(src: Path, dst: Path, target_size: int = 600) -> None:
    """Resize image to target_size x target_size, centre-crop to square."""
    img = Image.open(src).convert("RGB")
    # Resize so smallest dimension = target_size, maintaining aspect ratio
    img.thumbnail((target_size, target_size), Image.LANCZOS)
    # Centre-crop to square
    w, h = img.size
    left = (w - target_size) // 2
    top = (h - target_size) // 2
    right = left + target_size
    bottom = top + target_size
    # If image is smaller than target, pad with white
    if w < target_size or h < target_size:
        new_img = Image.new("RGB", (target_size, target_size), (255, 255, 255))
        paste_x = (target_size - w) // 2
        paste_y = (target_size - h) // 2
        new_img.paste(img, (paste_x, paste_y))
        img = new_img
    else:
        img = img.crop((left, top, right, bottom))
    img.save(dst, "JPEG", quality=95)
    print(f"  {src.name} ({img.width}x{img.height}) -> {dst.name}")


def main() -> None:
    print(f"Preparing demo images in {DST}/\n")
    for sel in SELECTIONS:
        src = sel["src"]
        dst = sel["dst"]
        if not src.exists():
            print(f"  [SKIP] {src} — not found")
            continue
        print(f"  [{sel['label']}]")
        resize_keep_aspect(src, dst)
        print(f"  ✓ {dst}\n")

    print("Done. Demo images ready:")
    for sel in SELECTIONS:
        dst = sel["dst"]
        if dst.exists():
            size_kb = dst.stat().st_size // 1024
            print(f"  {dst.name} ({size_kb} KB)")


if __name__ == "__main__":
    main()
