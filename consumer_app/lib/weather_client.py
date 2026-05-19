"""Weather client — fetches Singapore NEA weather for delivery schedule corrections."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root/src for greenloop imports
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SRC_DIR = str(_PROJECT_ROOT / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from greenloop.data.nea import fetch_nea_weather

logger = logging.getLogger(__name__)

# Cache weather for 30 minutes
_cached_weather: Optional[dict] = None
_cache_timestamp: float = 0.0
_CACHE_TTL_SECONDS = 30 * 60


def _get_weather() -> dict:
    """Return cached or fresh weather data from NEA."""
    import time as _time

    global _cached_weather, _cache_timestamp
    now = _time.time()
    if _cached_weather is None or (now - _cache_timestamp) > _CACHE_TTL_SECONDS:
        nea_data = fetch_nea_weather()
        if nea_data:
            _cached_weather = {
                "condition": nea_data.condition,
                "temperature": nea_data.temperature,
                "humidity": nea_data.humidity,
                "rainfall": nea_data.rainfall,
                "forecast": nea_data.forecast,
            }
        else:
            _cached_weather = {"condition": "Unknown", "temperature": None, "humidity": None, "rainfall": None, "forecast": ""}
        _cache_timestamp = now
    return _cached_weather


def get_weather_condition() -> str:
    """Return current weather condition string."""
    return _get_weather().get("condition", "Unknown")


def get_weather_delivery_warning() -> Optional[str]:
    """Return a delivery warning string if weather is adverse, else None."""
    condition = get_weather_condition().lower()
    if "rain" in condition or "thunder" in condition:
        return "Rain advisory — delivery may be delayed by up to 30 minutes"
    if "haze" in condition:
        return "Haze advisory — delivery routes may be adjusted"
    return None


def get_weather_note() -> str:
    """Return a short human-readable weather note for display."""
    data = _get_weather()
    cond = data.get("condition", "Unknown")
    temp = data.get("temperature")
    if temp is not None:
        return f"{cond}, {temp:.0f}°C"
    return cond
