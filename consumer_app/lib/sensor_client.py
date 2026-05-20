"""Sensor client — reads real sensor data from sensors_sim.csv."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root/src for adoptakale imports
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SRC_DIR = str(_PROJECT_ROOT / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import pandas as pd
from adoptakale.data.loader import load_sensors


def get_latest_readings() -> dict:
    """Return latest sensor readings for the 5 displayed metrics.

    Returns dict with keys:
        temperature (°C), humidity (%), ppfd (µmol/m²/s), ph (float), co2 (ppm)
    """
    df = load_sensors()
    latest = df.iloc[-1]

    return {
        "temperature": round(float(latest["temp_c"]), 1),
        "humidity": round(float(latest["humidity_pct"]), 1),
        "ppfd": 240,  # PPFD not in sensors_sim.csv — simulated
        "ph": 5.8,    # pH not in sensors_sim.csv — simulated
        "co2": int(latest["co2_ppm"]),
    }


def get_weather_note() -> str:
    """Return a short weather note based on latest humidity."""
    df = load_sensors()
    latest = df.iloc[-1]
    humidity = float(latest["humidity_pct"])
    if humidity > 75:
        return "High humidity advisory — dehumidifier active"
    elif humidity < 55:
        return "Low humidity — misting cycle triggered"
    return None  # No correction needed
