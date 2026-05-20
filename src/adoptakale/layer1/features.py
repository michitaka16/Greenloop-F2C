"""Feature engineering for demand forecasting.

Transforms raw shipments data into ML-ready features with lags, rolling
statistics, cyclical time encodings, and holiday flags for Singapore.

New features added:
- school_holiday_flag: Singapore school vacation indicator (June, Dec)
- rainy_day_flag / rainy_day_lag_1d: simulated monsoon rain signal
- avg_tariff / peak_tariff: daily electricity tariff aggregates
- indoor_temp_mean_7d / indoor_humidity_mean_7d / co2_deviation_from_optimal_mean_7d:
  7-day rolling mean of indoor climate sensor readings
- market_order_density_prev_week: market-wide order volume from prior week
"""

import numpy as np
import pandas as pd

from adoptakale.data.loader import load_electricity, load_sensors

# Singapore public holidays (approximate fixed dates and known ranges).
# For holidays that move year-to-year (CNY, Hari Raya, Deepavali),
# we use representative dates covering the simulation period (2025-2026).
_SG_HOLIDAYS = {
    # 2025
    "2025-01-29",  # CNY Day 1
    "2025-01-30",  # CNY Day 2
    "2025-03-31",  # Hari Raya Puasa
    "2025-05-01",  # Labour Day
    "2025-05-12",  # Vesak Day
    "2025-06-07",  # Hari Raya Haji
    "2025-08-09",  # National Day
    "2025-10-20",  # Deepavali
    "2025-12-25",  # Christmas
    # 2026
    "2026-02-17",  # CNY Day 1
    "2026-02-18",  # CNY Day 2
    "2026-03-20",  # Hari Raya Puasa
    "2026-05-01",  # Labour Day
    "2026-05-31",  # Vesak Day
    "2026-05-27",  # Hari Raya Haji
    "2026-08-09",  # National Day
    "2026-11-08",  # Deepavali
    "2026-12-25",  # Christmas
}
_SG_HOLIDAY_SET = {pd.Timestamp(d) for d in _SG_HOLIDAYS}

# Singapore school holidays (vacation periods).
_SG_SCHOOL_HOLIDAYS = {
    pd.Timestamp("2026-06-01"): pd.Timestamp("2026-06-30"),  # June vacation
    pd.Timestamp("2026-12-01"): pd.Timestamp("2026-12-31"),  # Christmas vacation
}


def _simulate_rainy_day(date: pd.Timestamp, rng: np.random.Generator) -> int:
    """Simulate rainy day based on Singapore monsoon patterns.

    Northeast monsoon: Oct-Dec (40% rain chance)
    Rest of year: May-Sep (15% rain chance)
    Other months: Jan-Apr, Mar (25% rain chance)
    """
    month = date.month
    if month in (10, 11, 12):
        prob = 0.40
    elif month in (5, 6, 7, 8, 9):
        prob = 0.15
    else:
        prob = 0.25  # Jan-Apr
    return 1 if rng.random() < prob else 0


def _load_daily_tariff(electricity_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly electricity tariff data to daily averages and peaks."""
    daily = electricity_df.copy()
    daily["date"] = pd.to_datetime(daily["date"])
    agg = daily.groupby("date").agg(
        avg_tariff=("tariff_rate_sgd_per_kwh", "mean"),
        peak_tariff=("tariff_rate_sgd_per_kwh", "max"),
    ).reset_index()
    return agg


def _load_daily_indoor_climate(sensors_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate minute-level sensor readings to daily and compute 7-day rolling means."""
    sensors_df = sensors_df.copy()
    sensors_df["timestamp"] = pd.to_datetime(sensors_df["timestamp"])
    daily = sensors_df.resample("D", on="timestamp").agg(
        temp_c=("temp_c", "mean"),
        humidity_pct=("humidity_pct", "mean"),
        co2_ppm=("co2_ppm", "mean"),
    ).reset_index()
    daily["co2_deviation_from_optimal"] = abs(daily["co2_ppm"] - 800)
    # 7-day rolling mean (shift by 1 to avoid lookahead)
    for col in ["temp_c", "humidity_pct", "co2_deviation_from_optimal"]:
        daily[f"{col}_mean_7d"] = daily[col].shift(1).rolling(7, min_periods=1).mean()
    # Rename to final output names
    daily = daily.rename(columns={
        "temp_c_mean_7d": "indoor_temp_mean_7d",
        "humidity_pct_mean_7d": "indoor_humidity_mean_7d",
    })
    return daily[["timestamp", "indoor_temp_mean_7d", "indoor_humidity_mean_7d", "co2_deviation_from_optimal_mean_7d"]]


def build_features(shipments: pd.DataFrame) -> pd.DataFrame:
    """Transform shipments data into ML-ready features.

    Adds the following feature groups:

    Lag features:
        lag_7d, lag_14d, lag_28d: shipment volume N days prior (same crop).
        rolling_mean_28d, rolling_std_28d: 28-day rolling stats per crop.

    Cyclical / temporal:
        week_sin, week_cos: sine/cosine encoding of week-of-year.
        day_of_week: integer day-of-week (0=Monday).

    Calendar:
        is_holiday: 1 if date is a Singapore public holiday, else 0.
        school_holiday_flag: 1 if date falls in a school vacation period
            (June or December), else 0.

    Weather (simulated):
        rainy_day_flag: 1 if rainy day simulated via monsoon probability
            (Oct-Dec 40%, May-Sep 15%, rest 25%).
        rainy_day_lag_1d: rainy_day_flag shifted by 1 day.

    Electricity tariff:
        avg_tariff: mean hourly tariff (SGD/kWh) for the date.
        peak_tariff: max hourly tariff (SGD/kWh) for the date.

    Indoor climate (7-day rolling means of sensor aggregates):
        indoor_temp_mean_7d: rolling mean of daily average temperature (°C).
        indoor_humidity_mean_7d: rolling mean of daily average humidity (%).
        co2_deviation_from_optimal_mean_7d: absolute deviation of daily average CO2
            from 800 ppm optimal.

    Market signal:
        market_order_density_prev_week: total market-wide kg_shipped
            from 7 days prior.

    Args:
        shipments: DataFrame with columns [date, crop_id, kg_shipped, price_sgd_per_kg].

    Returns:
        DataFrame with all feature columns plus target 'kg_shipped'.
        Rows without sufficient lag history are dropped (no NaN in output).

    Raises:
        ValueError: If shipments is empty or missing required columns.
    """
    required_cols = {"date", "crop_id", "kg_shipped", "price_sgd_per_kg"}
    missing = required_cols - set(shipments.columns)
    if missing:
        raise ValueError(
            f"shipments DataFrame missing required columns: {missing}"
        )
    if len(shipments) == 0:
        raise ValueError("shipments DataFrame is empty — cannot build features")

    df = shipments.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["crop_id", "date"]).reset_index(drop=True)

    result_frames = []
    for _crop_id, crop_df in df.groupby("crop_id"):
        crop_df = crop_df.sort_values("date").reset_index(drop=True)

        # Lag features (shift by N days; since data is daily per crop, shift by N rows)
        crop_df["lag_7d"] = crop_df["kg_shipped"].shift(7)
        crop_df["lag_14d"] = crop_df["kg_shipped"].shift(14)
        crop_df["lag_28d"] = crop_df["kg_shipped"].shift(28)

        # Rolling stats: 28-day (4-week) window
        crop_df["rolling_mean_28d"] = (
            crop_df["kg_shipped"].rolling(window=28, min_periods=28).mean()
        )
        crop_df["rolling_std_28d"] = (
            crop_df["kg_shipped"].rolling(window=28, min_periods=28).std()
        )

        result_frames.append(crop_df)

    result = pd.concat(result_frames, ignore_index=True)

    # Cyclical encoding of week-of-year
    week_of_year = result["date"].dt.isocalendar().week.astype(float)
    result["week_sin"] = np.sin(2 * np.pi * week_of_year / 52.0)
    result["week_cos"] = np.cos(2 * np.pi * week_of_year / 52.0)

    # Day of week (0=Monday, 6=Sunday)
    result["day_of_week"] = result["date"].dt.dayofweek

    # Public holiday flag
    result["is_holiday"] = result["date"].apply(
        lambda d: 1 if d.normalize() in _SG_HOLIDAY_SET else 0
    )

    # SG school holiday flag
    def _in_school_holiday(date: pd.Timestamp) -> int:
        for start, end in _SG_SCHOOL_HOLIDAYS.items():
            if start <= date.normalize() <= end:
                return 1
        return 0

    result["school_holiday_flag"] = result["date"].apply(_in_school_holiday)

    # Rainy day signal (simulated, seeded for reproducibility)
    rng = np.random.default_rng(42)
    result["rainy_day_flag"] = result["date"].apply(lambda d: _simulate_rainy_day(d, rng))
    # Lag 1 day
    result["rainy_day_lag_1d"] = result["rainy_day_flag"].shift(1)

    # Electricity tariff features
    electricity_df = load_electricity()
    daily_tariff = _load_daily_tariff(electricity_df)
    result = result.merge(daily_tariff, on="date", how="left")

    # Indoor climate features
    sensors_df = load_sensors()
    daily_climate = _load_daily_indoor_climate(sensors_df)
    daily_climate = daily_climate.rename(columns={"timestamp": "date"})
    result = result.merge(daily_climate, on="date", how="left")

    # Cross-crop demand signal: market-wide order volume from prior week
    market_prev_week = (
        shipments.copy()
    )
    market_prev_week["date"] = pd.to_datetime(market_prev_week["date"])
    market_prev_week = market_prev_week.groupby("date")["kg_shipped"].sum().shift(7)
    result["market_order_density_prev_week"] = result["date"].map(market_prev_week)

    # Fill NaN for new columns that may have missing values:
    # - rainy_day_lag_1d: first row per crop has no prior day
    # - tariff/climate: may not cover all shipment dates (left merge)
    # - market_order_density_prev_week: first 7 days have no prior-week data
    result["rainy_day_lag_1d"] = result["rainy_day_lag_1d"].fillna(0)
    result["avg_tariff"] = result["avg_tariff"].fillna(0)
    result["peak_tariff"] = result["peak_tariff"].fillna(0)
    result["indoor_temp_mean_7d"] = result["indoor_temp_mean_7d"].fillna(0)
    result["indoor_humidity_mean_7d"] = result["indoor_humidity_mean_7d"].fillna(0)
    result["co2_deviation_from_optimal_mean_7d"] = (
        result["co2_deviation_from_optimal_mean_7d"].fillna(0)
    )
    result["market_order_density_prev_week"] = (
        result["market_order_density_prev_week"].fillna(0)
    )

    # Drop rows where lag/rolling features are NaN (warmup period)
    feature_cols = [
        "lag_7d", "lag_14d", "lag_28d",
        "rolling_mean_28d", "rolling_std_28d",
    ]
    result = result.dropna(subset=feature_cols).reset_index(drop=True)

    return result
