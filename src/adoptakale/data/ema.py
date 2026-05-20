"""Layer 0: EMA Energy API integration for live electricity tariff data.

Fetches Singapore half-hourly wholesale electricity prices (USE — Uniform Singapore Energy)
from the Energy Market Authority via data.gov.sg public API.

Public API — no key required for basic access.
Docs: https://data.gov.sg/developer/api/half-hourly-wholesale-electricity-price
"""

from __future__ import annotations

import os
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from adoptakale.utils.config import DATA_DIR

logger = logging.getLogger(__name__)

# data.gov.sg Half-Hourly Wholesale Electricity Price API
_EMA_API_URL = "https://data.gov.sg/api/action/datastore_search"
_EMA_RESOURCE_ID = "9b0529c6-4f17-47c7-9f2e-7eb3ac5c6382"  # confirmed public resource
_EMA_TIMEOUT_SECONDS = 10


def _fetch_ema_api(target_date: date) -> pd.DataFrame | None:
    """Fetch half-hourly USE prices from data.gov.sg for a single date.

    Returns None if the API is unavailable or returns an error.
    """
    try:
        params = {
            "resource_id": _EMA_RESOURCE_ID,
            "filters": f'{{"end_period": "{target_date.isoformat()}"}}',
            "limit": 100,  # enough for 48 half-hourly readings
        }
        response = requests.get(
            _EMA_API_URL,
            params=params,
            timeout=_EMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        records = data.get("result", {}).get("records", [])
        if not records:
            return None

        rows = []
        for r in records:
            # API returns: end_period (ISO datetime), uos ($/MWh)
            end_period_str = r.get("end_period", "")
            uos = float(r.get("uos", 0))  # $/MWh
            if not end_period_str or uos <= 0:
                continue
            dt = datetime.fromisoformat(end_period_str.replace("Z", "+00:00"))
            # Convert $/MWh to $/kWh (divide by 1000)
            tariff = round(uos / 1000, 5)
            rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "hour": dt.hour,
                "tariff_rate_sgd_per_kwh": tariff,
            })

        if not rows:
            return None

        return pd.DataFrame(rows)

    except Exception as exc:
        logger.warning(f"EMA API fetch failed: {exc}")
        return None


def load_live_electricity(
    days: int = 7,
    data_dir: Path | None = None,
) -> pd.DataFrame:
    """Load recent electricity tariff data, preferring live EMA API.

    Strategy:
    1. Try to backfill the last `days` days from the EMA API (most recent first).
    2. For any missing days, fall back to electricity.csv.
    3. Return combined DataFrame with most-recent data from EMA.

    Returns a DataFrame with columns: date, hour, tariff_rate_sgd_per_kwh.
    """
    fallback_df = _load_csv_fallback(data_dir)

    today = date.today()
    live_records: dict[str, dict[int, float]] = {}  # date_str -> {hour: tariff}

    # Try fetching up to `days` days, newest first
    for days_ago in range(0, days):
        d = today - timedelta(days=days_ago)
        d_str = d.isoformat()

        df_live = _fetch_ema_api(d)
        if df_live is not None and len(df_live) > 0:
            live_records[d_str] = {
                int(row["hour"]): row["tariff_rate_sgd_per_kwh"]
                for row in df_live.to_dict("records")
            }
            logger.info(f"EMA live data loaded for {d_str} ({len(df_live)} readings)")
        else:
            # No live data for this day — use CSV fallback
            if d_str in fallback_df["date"].values:
                csv_day = fallback_df[fallback_df["date"] == d_str]
                live_records[d_str] = {
                    int(row["hour"]): row["tariff_rate_sgd_per_kwh"]
                    for row in csv_day.to_dict("records")
                }

    # Build combined DataFrame (live overrides CSV for the same hour)
    fallback_by_date_hour: dict[str, dict[int, float]] = {}
    for _, row in fallback_df.iterrows():
        d = str(row["date"])
        h = int(row["hour"])
        if d not in fallback_by_date_hour:
            fallback_by_date_hour[d] = {}
        fallback_by_date_hour[d][h] = row["tariff_rate_sgd_per_kwh"]

    # Merge: CSV as base, live as overlay
    merged_rows = []
    all_dates = sorted(set(list(live_records.keys()) + list(fallback_by_date_hour.keys())), reverse=True)

    for d_str in all_dates:
        csv_hours = fallback_by_date_hour.get(d_str, {})
        live_hours = live_records.get(d_str, {})
        all_hours = set(csv_hours.keys()) | set(live_hours.keys())

        for hour in sorted(all_hours):
            # Live data wins; fall back to CSV
            tariff = live_hours.get(hour) or csv_hours.get(hour)
            if tariff is not None:
                merged_rows.append({
                    "date": d_str,
                    "hour": hour,
                    "tariff_rate_sgd_per_kwh": tariff,
                })

    if not merged_rows:
        logger.warning("No live or CSV electricity data available — using fallback")
        return fallback_df

    df = pd.DataFrame(merged_rows, columns=["date", "hour", "tariff_rate_sgd_per_kwh"])

    # Save merged data back to CSV so next run has recent data cached
    try:
        save_path = (data_dir or DATA_DIR) / "electricity.csv"
        df.to_csv(save_path, index=False)
        logger.info(f"Saved merged electricity data to {save_path}")
    except Exception as exc:
        logger.warning(f"Could not save merged electricity data: {exc}")

    return df


def _load_csv_fallback(data_dir: Path | None = None) -> pd.DataFrame:
    """Load electricity data from CSV (fallback when API unavailable)."""
    try:
        path = (data_dir or DATA_DIR) / "electricity.csv"
        df = pd.read_csv(path)
        if "date" not in df.columns:
            return pd.DataFrame(columns=["date", "hour", "tariff_rate_sgd_per_kwh"])
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "hour", "tariff_rate_sgd_per_kwh"])
