"""NEA Singapore Weather API client — public, no API key required."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_NEA_API_BASE = "https://data.gov.sg/api/action/datastore_search"


@dataclass
class WeatherData:
    """Current weather from NEA two-hour nowcast."""

    condition: str        # e.g. "Light Rain", "Partly Cloudy"
    temperature: Optional[float]  # °C, if available
    humidity: Optional[float]      # %, if available
    rainfall: Optional[float]        # mm, if available
    forecast: str                    # 24h forecast text


def fetch_nea_weather() -> Optional[WeatherData]:
    """Fetch current weather from NEA Data API (no API key required).

    Falls back to None if the API is unavailable.
    """
    try:
        # 2-hour nowcast resource
        resp = requests.get(
            _NEA_API_BASE,
            params={"resource_id": "25c85d11-7f41-4ae3-933e-0d205c816d11", "limit": 1},
            timeout=5,
        )
        resp.raise_for_status()
        records = resp.json().get("result", {}).get("records", [])
        if not records:
            return None

        r = records[0]
        return WeatherData(
            condition=r.get("weather", "Unknown"),
            temperature=None,
            humidity=None,
            rainfall=None,
            forecast=r.get("forecast", ""),
        )
    except Exception as exc:
        logger.warning("nea.weather_fetch_failed: %s", str(exc))
        return None
