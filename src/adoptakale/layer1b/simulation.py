"""Simulation layer for Layer 1b demo.

Provides mock_diagnose() for when no real model/data is available.
All outputs are clearly labeled as is_simulated=True.

Rack IDs match the optimizer's tier_0..tier_9 naming convention
so diagnosis results can feed directly into Layer 2.
"""

from __future__ import annotations

import hashlib
import os
import random

import numpy as np

from adoptakale.layer1b.architecture import (
    GROWTH_LABELS,
    NUTRITION_LABELS,
    DiagnosisResult,
)

# ---------------------------------------------------------------------------
# Rack scenarios for demo — each tier shows a different diagnosis combo
# to make the dashboard visually interesting.
# ---------------------------------------------------------------------------

RACK_SCENARIOS: dict[str, dict] = {
    "tier_0": {
        "growth_stage": "harvest_ready",
        "nutrition": "normal",
        "growth_conf": 0.94,
        "nutrition_conf": 0.91,
    },
    "tier_1": {
        "growth_stage": "mid",
        "nutrition": "normal",
        "growth_conf": 0.88,
        "nutrition_conf": 0.93,
    },
    "tier_2": {
        "growth_stage": "early",
        "nutrition": "normal",
        "growth_conf": 0.87,
        "nutrition_conf": 0.95,
    },
    "tier_3": {
        "growth_stage": "harvest_ready",
        "nutrition": "nitrogen_low",
        "growth_conf": 0.92,
        "nutrition_conf": 0.68,  # Low confidence — borderline for model certainty
    },
    "tier_4": {
        "growth_stage": "mid",
        "nutrition": "water_stress",
        "growth_conf": 0.90,
        "nutrition_conf": 0.82,
    },
    "tier_5": {
        "growth_stage": "harvest_ready",
        "nutrition": "normal",
        "growth_conf": 0.96,
        "nutrition_conf": 0.94,
    },
    "tier_6": {
        "growth_stage": "mid",
        "nutrition": "nitrogen_low",
        "growth_conf": 0.85,
        "nutrition_conf": 0.76,
    },
    "tier_7": {
        "growth_stage": "early",
        "nutrition": "normal",
        "growth_conf": 0.91,
        "nutrition_conf": 0.97,
    },
    "tier_8": {
        "growth_stage": "harvest_ready",
        "nutrition": "normal",
        "growth_conf": 0.93,
        "nutrition_conf": 0.90,
    },
    "tier_9": {
        "growth_stage": "mid",
        "nutrition": "water_stress",
        "growth_conf": 0.89,
        "nutrition_conf": 0.81,
    },
}


def _make_noisy_probs(true_label: str, label_list: list[str], confidence: float) -> list[float]:
    """Generate a realistic softmax probability distribution around the true label."""
    probs = np.zeros(len(label_list))
    true_idx = label_list.index(true_label)
    probs[true_idx] = confidence
    remaining = 1.0 - confidence
    other_indices = [i for i in range(len(label_list)) if i != true_idx]
    dirichlet_weights = np.random.dirichlet([1.0, 0.5])
    probs[other_indices[0]] = remaining * dirichlet_weights[0]
    probs[other_indices[1]] = remaining * dirichlet_weights[1]
    return probs.tolist()


def mock_diagnose(rack_id: str) -> DiagnosisResult:
    """Generate a simulated diagnosis for a rack.

    Returns realistic-looking outputs from RACK_SCENARIOS lookup table
    with controlled noise added to confidence scores.

    Args:
        rack_id: Rack identifier (e.g. 'tier_3')

    Returns:
        DiagnosisResult with is_simulated=True
    """
    scenario = RACK_SCENARIOS.get(
        rack_id,
        {"growth_stage": "mid", "nutrition": "normal", "growth_conf": 0.80, "nutrition_conf": 0.85},
    )

    base_growth_conf = scenario.get("growth_conf", scenario.get("confidence", 0.80))
    base_nutrition_conf = scenario.get("nutrition_conf", base_growth_conf - 0.05)

    noisy_growth = float(np.clip(base_growth_conf + random.gauss(0, 0.02), 0.55, 0.98))
    noisy_nutrition = float(np.clip(base_nutrition_conf + random.gauss(0, 0.02), 0.55, 0.97))

    growth_probs = _make_noisy_probs(scenario["growth_stage"], GROWTH_LABELS, noisy_growth)
    nutrition_probs = _make_noisy_probs(scenario["nutrition"], NUTRITION_LABELS, noisy_nutrition)

    return DiagnosisResult(
        rack_id=rack_id,
        growth_stage=scenario["growth_stage"],
        growth_confidence=noisy_growth,
        growth_probs=growth_probs,
        nutrition_status=scenario["nutrition"],
        nutrition_confidence=noisy_nutrition,
        nutrition_probs=nutrition_probs,
        is_simulated=True,
    )


def mock_diagnose_from_image(image_bytes: bytes, rack_id: str) -> DiagnosisResult:
    """Generate a deterministic mock diagnosis from image content.

    Uses the image hash to pick a scenario so the same photo always
    produces the same result — important for demo consistency.
    """
    h = int(hashlib.sha256(image_bytes).hexdigest()[:8], 16)
    growth_idx = h % len(GROWTH_LABELS)
    nutrition_idx = (h >> 4) % len(NUTRITION_LABELS)
    growth_conf = 0.75 + (h % 25) / 100
    nutrition_conf = 0.70 + ((h >> 2) % 30) / 100

    return DiagnosisResult(
        rack_id=rack_id,
        growth_stage=GROWTH_LABELS[growth_idx],
        growth_confidence=round(growth_conf, 2),
        growth_probs=_make_noisy_probs(GROWTH_LABELS[growth_idx], GROWTH_LABELS, growth_conf),
        nutrition_status=NUTRITION_LABELS[nutrition_idx],
        nutrition_confidence=round(nutrition_conf, 2),
        nutrition_probs=_make_noisy_probs(
            NUTRITION_LABELS[nutrition_idx], NUTRITION_LABELS, nutrition_conf
        ),
        is_simulated=True,
    )


def diagnose_all_racks_simulated() -> dict[str, DiagnosisResult]:
    """Return simulated diagnoses for all 10 tiers."""
    return {rack_id: mock_diagnose(rack_id) for rack_id in RACK_SCENARIOS}


# ---------------------------------------------------------------------------
# Batch processing — multiple racks diagnosed at once
# ---------------------------------------------------------------------------


def diagnose_batch(
    images: dict[str, bytes],
) -> dict[str, DiagnosisResult]:
    """Diagnose multiple racks from uploaded images.

    Args:
        images: Dict mapping rack_id (e.g. 'tier_3') to image bytes.

    Returns:
        Dict mapping rack_id to DiagnosisResult. Unrecognised rack_ids
        default to 'tier_0' for the mock.
    """
    results: dict[str, DiagnosisResult] = {}
    for rack_id, image_bytes in images.items():
        # Default unknown racks to tier_0 for mock (real model would reject)
        effective_rack = rack_id if rack_id in RACK_SCENARIOS else "tier_0"
        results[rack_id] = mock_diagnose_from_image(image_bytes, effective_rack)
    return results


# ---------------------------------------------------------------------------
# Filename → rack_id parser
# ---------------------------------------------------------------------------

# Keywords that map demo images to crop_ids
_FILENAME_CROP_KEYWORDS = {
    "spinach": "baby_spinach",
    "nitrogen": "baby_spinach",
    "kailan": "kai_lan",
    "wilt": "lettuce_mambo",
    "water_stress": None,  # generic — don't auto-assign
    "healthy": None,  # generic
}


def parse_filename_to_crop(filename: str) -> str | None:
    """Return crop_id from a demo image filename, or None if no match."""
    lower = filename.lower()
    for keyword, crop_id in _FILENAME_CROP_KEYWORDS.items():
        if keyword in lower:
            return crop_id
    return None


# ---------------------------------------------------------------------------
# Rack-number pattern in filenames: rack_3.jpg, tier_5.png
_RACK_NUM_PATTERN = __import__("re").compile(r"(?:rack|tier)[_\s]*(\d+)", __import__("re").IGNORECASE)


def parse_rack_number(filename: str) -> int | None:
    """Return rack number (0-9) if filename matches rack_N pattern, else None."""
    m = _RACK_NUM_PATTERN.search(filename)
    if m:
        n = int(m.group(1))
        if 0 <= n <= 9:
            return n
    return None


def filename_to_rack_id(
    filename: str,
    rack_layout: dict[str, str],
) -> str | None:
    """Map an uploaded filename to a rack_id.

    Priority:
    1. Filename contains 'rack_N' / 'tier_N' → direct mapping to tier_N
    2. Filename contains crop keyword → find first rack with that crop today
    3. Otherwise None (manual selection required)

    Args:
        filename: Uploaded file name, e.g. 'demo_spinach_nitrogen.jpg'
        rack_layout: Today's MILP rack layout {rack_id: crop_id}

    Returns:
        rack_id string (e.g. 'tier_3') or None
    """
    # Priority 1: rack number in filename
    rack_num = parse_rack_number(filename)
    if rack_num is not None:
        return f"tier_{rack_num}"

    # Priority 2: crop keyword in filename
    crop_id = parse_filename_to_crop(filename)
    if crop_id:
        for rack_id, c in rack_layout.items():
            if c == crop_id:
                return rack_id

    return None


# ---------------------------------------------------------------------------
# Impact statements — what Layer 2 / Layer 3 should do with the diagnosis
# ---------------------------------------------------------------------------

GROWTH_BADGES = {
    "harvest_ready": ("Harvest Ready", "🟢"),
    "mid": ("Mid Stage", "🟡"),
    "early": ("Early Stage", "🔵"),
}

NUTRITION_BADGES = {
    "normal": ("Normal", "✅"),
    "nitrogen_low": ("Nitrogen Low", "⚠️"),
    "water_stress": ("Water Stress", "💧"),
}


def generate_impacts(diagnosis: DiagnosisResult, crop_name: str) -> list[str]:
    """Generate human-readable Layer 2 / Layer 3 impact statements."""
    impacts: list[str] = []
    rack_num = diagnosis.rack_id.replace("tier_", "")

    if diagnosis.growth_stage == "harvest_ready":
        impacts.append(f"**{crop_name}** added to this week's harvest schedule")
    elif diagnosis.growth_stage == "early":
        impacts.append(f"**{crop_name}** harvest estimate: ~14 days (early stage)")
    else:
        impacts.append(f"**{crop_name}** on track — mid growth, no schedule change")

    if diagnosis.nutrition_status == "nitrogen_low":
        impacts.append(f"Rack {rack_num} nitrogen delivery increased by 15%")
        impacts.append(f"Layer 3 nutrient dosing target for {crop_name} adjusted upward")
    elif diagnosis.nutrition_status == "water_stress":
        impacts.append(f"Rack {rack_num} irrigation frequency doubled")
        impacts.append(f"Layer 3 soil moisture target for {crop_name} adjusted to 80%")
    else:
        impacts.append("Nutrition normal — no adjustment needed")

    return impacts


# ---------------------------------------------------------------------------
# Demo mode flag
# ---------------------------------------------------------------------------

GREENLOOP_CV_MODE = os.environ.get("GREENLOOP_CV_MODE", "simulated")


def is_simulated_mode() -> bool:
    """Return True when running in demo/simulation mode."""
    return GREENLOOP_CV_MODE == "simulated"
