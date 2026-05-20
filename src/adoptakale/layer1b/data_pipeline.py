"""Layer 1b data pipeline — synthetic image generation for CV model training.

This module generates realistic-looking synthetic training images for the 2 MVP crops
(basil, kale) and provides data augmentation with LED-spectrum adaptation.

Real deployment: Replace this with a DataModule backed by PlantVillage/PlantDoc
datasets and farm-operator collected images.  See specs/layer1b_cv_diagnosis.md §3.1
for the full data-collection roadmap.

Directory structure produced:
    data/cv_training/
        basil/
            early/normal/           → basil_early_normal_*.jpg
            early/nitrogen_low/    → basil_early_nitrogen_low_*.jpg
            early/water_stress/    → basil_early_water_stress_*.jpg
            mid/normal/
            mid/nitrogen_low/
            mid/water_stress/
            harvest_ready/normal/
            harvest_ready/nitrogen_low/
            harvest_ready/water_stress/
        kale/
            [same 9 subdirectories]

Per spec §3.1 MVP: only basil and kale are trained. Other 8 crops show
"Data pending" in inference until field data is collected.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Iterator

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from adoptakale.layer1b.architecture import GROWTH_LABELS, NUTRITION_LABELS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Spec §3.1 MVP: only basil and kale have training data
TRAINED_CROPS = ["basil", "kale"]

GROWTH_STAGES = ["early", "mid", "harvest_ready"]
NUTRITION_STATUSES = ["normal", "nitrogen_low", "water_stress"]

# Images per (crop, growth_stage, nutrition_status) cell
IMAGES_PER_CELL = 20

# Image dimensions
IMG_HEIGHT = 224
IMG_WIDTH = 224
IMG_CHANNELS = 3

# LED-spectrum augmentation — spec §3.2 colour channel adjustments
# Singapore vertical farms use full-spectrum LED panels (~400–700nm).
# We approximate the LED colour shift relative to standard ImageNet photos.
LED_SPECTRUM_RGB = np.array([1.10, 1.05, 0.85], dtype=np.float32)  # B×, R×, G÷


# ---------------------------------------------------------------------------
# Colour palettes per crop × growth_stage × nutrition_status
# ---------------------------------------------------------------------------


def _colour_for(crop: str, growth_stage: str, nutrition: str) -> np.ndarray:
    """Return the base RGB colour (0-255 uint8) for a given combination.

    The colour encodes both growth stage (leaf colour deepening with maturity)
    and nutrition status (chlorosis for nitrogen_low, bronzing for water_stress).
    """
    # Base leaf colour per crop (normal nutrition)
    crop_colours = {
        "basil": np.array([45, 130, 60], dtype=np.uint8),    # deep green
        "kale":  np.array([50, 110, 45], dtype=np.uint8),     # very dark green
    }
    base = crop_colours.get(crop, np.array([50, 120, 50], dtype=np.uint8))

    # Growth stage modifiers (leaves darken / enlarge with maturity)
    if growth_stage == "early":
        base = (base * 0.70).astype(np.uint8)
    elif growth_stage == "mid":
        base = (base * 0.88).astype(np.uint8)
    # harvest_ready: full colour

    # Nutrition modifiers
    if nutrition == "nitrogen_low":
        # Chlorosis: shift toward yellow-green (paler, desaturated)
        base = np.array([
            min(255, int(base[0] * 1.60)),   # R — yellow shift
            min(255, int(base[1] * 1.10)),   # G
            min(255, int(base[2] * 0.65)),   # B — reduced
        ], dtype=np.uint8)
    elif nutrition == "water_stress":
        # Bronzing / slight wilt: warm shift toward brown-orange
        base = np.array([
            min(255, int(base[0] * 1.30)),   # R
            min(255, int(base[1] * 0.80)),   # G
            min(255, int(base[2] * 0.70)),   # B
        ], dtype=np.uint8)
    # normal: no change

    return base


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------


def _generate_synthetic_image(
    crop: str,
    growth_stage: str,
    nutrition: str,
    image_id: int,
    seed: int,
) -> np.ndarray:
    """Generate a single synthetic 224×224×3 image.

    Images are programmatically constructed using overlapping ellipses to
    simulate leaf canopies viewed from above under LED lighting.
    """
    rng = random.Random(
        hash(f"{crop}_{growth_stage}_{nutrition}_{image_id}_{seed}") & 0xFFFFFFFF,
    )

    img = np.full((IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS), 240, dtype=np.uint8)

    base_colour = _colour_for(crop, growth_stage, nutrition)

    # Number of leaf blobs scales with growth stage
    n_leaves = {"early": 5, "mid": 12, "harvest_ready": 22}[growth_stage]

    # Leaf size also scales with growth stage
    leaf_w_range = {"early": (8, 18), "mid": (14, 32), "harvest_ready": (20, 45)}[growth_stage]
    leaf_h_scale = {"early": 0.7, "mid": 0.65, "harvest_ready": 0.60}

    for _ in range(n_leaves):
        # Position — clustered toward centre with organic scatter
        cx = int(rng.gauss(IMG_WIDTH // 2, IMG_WIDTH * 0.28))
        cy = int(rng.gauss(IMG_HEIGHT // 2, IMG_HEIGHT * 0.28))
        cx = np.clip(cx, 0, IMG_WIDTH - 1)
        cy = np.clip(cy, 0, IMG_HEIGHT - 1)

        # Size
        w = rng.randint(leaf_w_range[0], leaf_w_range[1])
        h = int(w * leaf_h_scale[growth_stage])

        # Colour with per-leaf variation (±15%)
        variation = rng.uniform(0.85, 1.15)
        colour = np.clip(base_colour * variation, 0, 255).astype(np.uint8)

        # LED spectrum augmentation (applied per blob)
        colour = np.clip(colour * LED_SPECTRUM_RGB, 0, 255).astype(np.uint8)

        # Draw filled ellipse
        y1 = max(0, cy - h // 2)
        y2 = min(IMG_HEIGHT, cy + h // 2)
        x1 = max(0, cx - w // 2)
        x2 = min(IMG_WIDTH, cx + w // 2)
        if y2 > y1 and x2 > x1:
            img[y1:y2, x1:x2] = colour

    # Add slight noise to simulate texture
    noise = rng.randint(-12, 12)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img


# ---------------------------------------------------------------------------
# PyTorch Dataset
# ---------------------------------------------------------------------------


class SyntheticCVDataset(Dataset):
    """PyTorch dataset wrapping the synthetic basil/kale training images.

    Loads images from a manifest.json produced by generate_training_data().
    Performs ImageNet normalization and optional augmentation.

    Args:
        manifest: Dict loaded from data/cv_training/manifest.json
        split: "train" (80%) or "val" (20%) — deterministic split by seed=42
        augment: If True, applies RandomHorizontalFlip + ColorJitter
    """

    _IMAGENET_NORMALIZE = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.229, 0.224],
    )

    def __init__(
        self,
        manifest: dict,
        split: str = "train",
        augment: bool = True,
        train_fraction: float = 0.8,
    ):
        self.samples: list[tuple[str, int, int]] = []  # (filepath, growth_idx, nutrition_idx)

        for crop, stages in manifest.items():
            for stage, nutrition_map in stages.items():
                for nutrition, image_ids in nutrition_map.items():
                    growth_idx = GROWTH_LABELS.index(stage)
                    nutrition_idx = NUTRITION_LABELS.index(nutrition)
                    for img_id, filepath in image_ids.items():
                        self.samples.append((filepath, growth_idx, nutrition_idx))

        # Deterministic train/val split (seed=42)
        n = len(self.samples)
        n_train = int(n * train_fraction)
        indices = list(range(n))
        random.Random(42).shuffle(indices)
        chosen = indices[:n_train] if split == "train" else indices[n_train:]
        self.samples = [self.samples[i] for i in chosen]

        self.augment = augment
        self.base_transform = transforms.Compose([
            transforms.Resize((IMG_HEIGHT, IMG_WIDTH)),
            transforms.ToTensor(),
        ])
        self.aug_transform = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        ])

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int, int]:
        filepath, growth_idx, nutrition_idx = self.samples[idx]
        img = Image.open(filepath).convert("RGB")
        img = self.base_transform(img)
        if self.augment:
            img = self.aug_transform(img)
        img = self._IMAGENET_NORMALIZE(img)
        return img, growth_idx, nutrition_idx

    def iterate_batches(
        self, batch_size: int = 16
    ) -> Iterator[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        """Yield (images, growth_labels, nutrition_labels) batches."""
        for i in range(0, len(self), batch_size):
            end = min(i + batch_size, len(self))
            imgs, g_lbls, n_lbls = [], [], []
            for j in range(i, end):
                img, g_lbl, n_lbl = self[j]
                imgs.append(img)
                g_lbls.append(g_lbl)
                n_lbls.append(n_lbl)
            yield torch.stack(imgs), torch.tensor(g_lbls, dtype=torch.long), torch.tensor(n_lbls, dtype=torch.long)


# ---------------------------------------------------------------------------
# Main pipeline — generate training data on disk
# ---------------------------------------------------------------------------


def generate_training_data(output_dir: Path | str | None = None) -> dict:
    """Generate synthetic training images for basil and kale.

    Produces 2 crops × 9 (growth × nutrition) cells × 20 images = 360 images.
    Images are saved as JPEG at data/cv_training/{crop}/{growth_stage}/{nutrition}/.

    Returns a manifest dict:
        {crop: {growth_stage: {nutrition: {image_id: filepath}}}}

    Call this once before training:
        from adoptakale.layer1b.data_pipeline import generate_training_data
        manifest = generate_training_data()
    """
    if output_dir is None:
        from adoptakale.utils.config import DATA_DIR
        output_dir = DATA_DIR / "cv_training"
    else:
        output_dir = Path(output_dir)

    manifest: dict = {}
    total_written = 0

    for crop in TRAINED_CROPS:
        manifest[crop] = {}
        for stage in GROWTH_STAGES:
            manifest[crop][stage] = {}
            for nutrition in NUTRITION_STATUSES:
                cell_dir = output_dir / crop / stage / nutrition
                cell_dir.mkdir(parents=True, exist_ok=True)
                manifest[crop][stage][nutrition] = {}

                for img_idx in range(IMAGES_PER_CELL):
                    img_array = _generate_synthetic_image(
                        crop, stage, nutrition, image_id=img_idx, seed=img_idx
                    )

                    filename = f"{crop}_{stage}_{nutrition}_{img_idx:03d}.jpg"
                    filepath = cell_dir / filename
                    Image.fromarray(img_array).save(filepath, quality=85)
                    manifest[crop][stage][nutrition][img_idx] = str(filepath)
                    total_written += 1

                logger.info(
                    "data_pipeline.cell_complete",
                    extra={
                        "crop": crop,
                        "growth_stage": stage,
                        "nutrition": nutrition,
                        "count": IMAGES_PER_CELL,
                        "output_dir": str(cell_dir),
                    },
                )

    # Write manifest alongside images
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(
        "data_pipeline.complete",
        extra={"total_images": total_written, "output_dir": str(output_dir)},
    )
    print(f"[Layer 1b data pipeline] Generated {total_written} images in {output_dir}/")

    return manifest


def load_training_data(output_dir: Path | str | None = None) -> dict:
    """Load the training data manifest from disk.

    Raises FileNotFoundError if the data has not been generated yet.
    """
    if output_dir is None:
        from adoptakale.utils.config import DATA_DIR
        output_dir = DATA_DIR / "cv_training"
    else:
        output_dir = Path(output_dir)

    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Training data not found at {output_dir}/. "
            "Run generate_training_data() first."
        )
    return json.loads(manifest_path.read_text())
