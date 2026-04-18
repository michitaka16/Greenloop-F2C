"""Inference pipeline for Layer 1b crop diagnosis.

Provides:
- diagnose_rack(): main inference entry point (real model or simulation fallback)
- load_cv_model(): cached model loader
- _real_diagnose(): actual model inference path
- _simulate_diagnose(): demo fallback path
- _ood_check(): out-of-distribution detection for non-plant images
"""

from __future__ import annotations

import os
import time
import warnings
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch

from greenloop.layer1b.architecture import (
    DiagnosisResult,
    DualHeadClassifier,
    GROWTH_LABELS,
    NUTRITION_LABELS,
    is_ood_by_feature_norm,
)
from greenloop.layer1b.simulation import GREENLOOP_CV_MODE, mock_diagnose


# ---------------------------------------------------------------------------
# Constants (from spec)
# ---------------------------------------------------------------------------

IMAGE_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
CONFIDENCE_WARN_THRESHOLD = 0.70
CONFIDENCE_CRITICAL_THRESHOLD = 0.50
INFERENCE_TIMEOUT_SECONDS = 5.0


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------

def preprocess_image(img: np.ndarray) -> torch.Tensor:
    """Preprocess a numpy image for EfficientNet-B0 input.

    Args:
        img: BGR or RGB image as numpy array (H, W, C)

    Returns:
        Preprocessed tensor of shape (1, 3, 224, 224)
    """
    # Resize
    img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
    # Convert BGR → RGB if needed
    if img.shape[-1] == 3 and img.dtype == np.uint8:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Normalize to [0, 1]
    img = img.astype(np.float32) / 255.0
    # ImageNet normalization
    mean = np.array(IMAGENET_MEAN, dtype=np.float32)
    std = np.array(IMAGENET_STD, dtype=np.float32)
    img = (img - mean) / std
    # HWC → CHW
    img = img.transpose(2, 0, 1)
    # Add batch dim
    tensor = torch.from_numpy(img).unsqueeze(0)
    return tensor


# ---------------------------------------------------------------------------
# Model loading (cached)
# ---------------------------------------------------------------------------

_cached_model: Optional[DualHeadClassifier] = None
_model_load_attempted: bool = False


def load_cv_model() -> Optional[DualHeadClassifier]:
    """Load the trained DualHeadClassifier from disk.

    Returns None if model file is not found (demo mode).
    Raises if GREENLOOP_CV_MODE is 'real' but loading fails.
    """
    global _cached_model, _model_load_attempted

    if _model_load_attempted:
        return _cached_model
    _model_load_attempted = True

    model_path = Path(__file__).resolve().parent.parent.parent / "models" / "layer1b_efficientnet_b0.pt"

    if not model_path.exists():
        warnings.warn(f"Layer 1b model not found at {model_path}. Using simulation mode.")
        _cached_model = None
        return None

    try:
        model = DualHeadClassifier(pretrained=False)
        state = torch.load(model_path, map_location="cpu", weights_only=False)
        model.load_state_dict(state)
        model.eval()
        _cached_model = model
        return model
    except Exception as e:
        warnings.warn(f"Failed to load Layer 1b model: {e}. Using simulation mode.")
        _cached_model = None
        return None


# ---------------------------------------------------------------------------
# OOD detection
# ---------------------------------------------------------------------------

def check_ood(img_tensor: torch.Tensor) -> bool:
    """Detect if the image is likely out-of-distribution (non-plant).

    Uses feature norm heuristic. Real plant images under LED lights
    have different feature norms than random ImageNet images.
    """
    return is_ood_by_feature_norm(img_tensor)


# ---------------------------------------------------------------------------
# Real inference path
# ---------------------------------------------------------------------------

def _real_diagnose(rack_id: str, img: np.ndarray) -> DiagnosisResult:
    """Run real model inference on an image.

    Returns DiagnosisResult with is_ood=True if non-plant image detected.
    """
    img_tensor = preprocess_image(img)

    # OOD check before inference
    if check_ood(img_tensor):
        # Return unknown with low confidence — but don't crash
        return DiagnosisResult(
            rack_id=rack_id,
            growth_stage="mid",
            growth_confidence=0.0,
            growth_probs=[0.33, 0.34, 0.33],
            nutrition_status="normal",
            nutrition_confidence=0.0,
            nutrition_probs=[0.33, 0.33, 0.34],
            is_simulated=False,
            is_ood=True,
        )

    model = load_cv_model()
    if model is None:
        # Fall back to simulation
        result = mock_diagnose(rack_id)
        result.rack_id = rack_id
        return result

    img_tensor = preprocess_image(img)
    start = time.perf_counter()
    with torch.no_grad():
        growth_logits, nutrition_logits, growth_probs, nutrition_probs = model(img_tensor)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if elapsed_ms > INFERENCE_TIMEOUT_SECONDS * 1000:
        warnings.warn(f"Inference took {elapsed_ms:.0f}ms — exceeds {INFERENCE_TIMEOUT_SECONDS}s timeout")

    growth_idx = growth_probs.argmax(dim=-1).item()
    nutrition_idx = nutrition_probs.argmax(dim=-1).item()

    return DiagnosisResult(
        rack_id=rack_id,
        growth_stage=GROWTH_LABELS[growth_idx],
        growth_confidence=growth_probs[0, growth_idx].item(),
        growth_probs=growth_probs[0].tolist(),
        nutrition_status=NUTRITION_LABELS[nutrition_idx],
        nutrition_confidence=nutrition_probs[0, nutrition_idx].item(),
        nutrition_probs=nutrition_probs[0].tolist(),
        is_simulated=False,
        is_ood=False,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def diagnose_rack(
    rack_id: str,
    img: Optional[np.ndarray] = None,
    *,
    use_simulation: Optional[bool] = None,
) -> DiagnosisResult:
    """Diagnose a crop rack from an image.

    Args:
        rack_id: Identifier for the rack (e.g. 'basil_A')
        img: Numpy image array (H, W, C). Required for real mode.
        use_simulation: Override GREENLOOP_CV_MODE. If None, use env var.

    Returns:
        DiagnosisResult

    Behaviour:
        - use_simulation=True or GREENLOOP_CV_MODE=simulated → mock_diagnose()
        - use_simulation=False and img is None → raises ValueError
        - use_simulation=False and model not found → falls back to mock_diagnose()
        - use_simulation=False and non-plant image detected → returns is_ood=True result
    """
    if use_simulation is None:
        use_simulation = GREENLOOP_CV_MODE == "simulated"

    if use_simulation:
        result = mock_diagnose(rack_id)
        result.rack_id = rack_id
        return result

    if img is None:
        raise ValueError(
            f"diagnose_rack('{rack_id}'): real mode requires an image. "
            "Either pass img= or set GREENLOOP_CV_MODE=simulated"
        )

    return _real_diagnose(rack_id, img)


# ---------------------------------------------------------------------------
# All-racks batch diagnosis
# ---------------------------------------------------------------------------

def diagnose_all_racks(
    rack_ids: list[str],
    images: Optional[dict[str, np.ndarray]] = None,
) -> dict[str, DiagnosisResult]:
    """Diagnose all racks.

    Args:
        rack_ids: List of rack identifiers
        images: Optional dict mapping rack_id → numpy image. Required for real mode.

    Returns:
        Dict mapping rack_id → DiagnosisResult
    """
    use_sim = images is None or GREENLOOP_CV_MODE == "simulated"
    results = {}
    for rack_id in rack_ids:
        img = images.get(rack_id) if images else None
        results[rack_id] = diagnose_rack(rack_id, img, use_simulation=use_sim)
    return results
