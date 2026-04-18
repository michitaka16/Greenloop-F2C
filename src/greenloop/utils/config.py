"""Configuration loader — reads from .env, no hardcoded secrets."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _find_project_root() -> Path:
    """Locate the project root by walking up until we find a ``src/`` directory.

    This handles both regular installs (where ``__file__`` is in
    ``site-packages/greenloop/``) and editable installs (where a ``.pth``
    file points to the ``src/`` checkout).  In both cases the ``src/`` marker
    is the reliable anchor for the actual repository root.
    """
    candidate = Path(__file__).resolve().parent
    while candidate != candidate.parent:
        if (candidate / "src").is_dir():
            return candidate
        candidate = candidate.parent
    # Fallback: original 4-parent heuristic
    return Path(__file__).resolve().parent.parent.parent.parent


PROJECT_ROOT = _find_project_root()
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data"))
MODELS_DIR = Path(os.environ.get("MODELS_DIR", PROJECT_ROOT / "models"))

# Singapore-specific constants
SGD_CURRENCY = "SGD"
SG_TIMEZONE = "Asia/Singapore"

# Crops — order must match generate_seed_data.generate_crops() row order
# so the optimizer's integer indices align with CSV row indices.
CROP_IDS = [
    # 5 staple leafy greens
    "kai_lan",
    "baby_spinach",
    "lettuce_mambo",
    "chye_sim",
    "arugula",
    # 2 more leafy (1 staple + 1 premium)
    "pak_choi",
    "kale",
    # 3 high-margin herbs
    "basil_thai",
    "coriander",
    "mint",
]

# Shifts
SHIFTS = {
    "morning": (6, 14),    # 6am-2pm
    "afternoon": (14, 22), # 2pm-10pm
    "night": (22, 6),      # 10pm-6am
}

# SP Group tariff
PEAK_HOURS = range(8, 22)        # 8am-10pm
PEAK_RATE_SGD = 0.28             # SGD/kWh
OFF_PEAK_RATE_SGD = 0.18         # SGD/kWh

# MOM regulations
MAX_SHIFT_HOURS = 8
MAX_WEEKLY_HOURS = 44

# Safety limits
TEMP_SAFETY_MIN = 10.0   # °C
TEMP_SAFETY_MAX = 35.0   # °C
HUMIDITY_SAFETY_MIN = 40.0  # %
HUMIDITY_SAFETY_MAX = 90.0  # %
CO2_SAFETY_MIN = 300.0   # ppm
CO2_SAFETY_MAX = 1500.0  # ppm
MOISTURE_SAFETY_MIN = 0.1
MOISTURE_SAFETY_MAX = 0.95
