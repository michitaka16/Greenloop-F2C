"""Feature engineering for demand forecasting.

Transforms raw shipments data into ML-ready features with lags, rolling
statistics, cyclical time encodings, and holiday flags for Singapore.
"""

import numpy as np
import pandas as pd

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


def build_features(shipments: pd.DataFrame) -> pd.DataFrame:
    """Transform shipments data into ML-ready features.

    Args:
        shipments: DataFrame with columns [date, crop_id, kg_shipped, price_sgd_per_kg].

    Returns:
        DataFrame with feature columns plus target 'kg_shipped'.
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

    # Drop rows where lag/rolling features are NaN (warmup period)
    feature_cols = [
        "lag_7d", "lag_14d", "lag_28d",
        "rolling_mean_28d", "rolling_std_28d",
    ]
    result = result.dropna(subset=feature_cols).reset_index(drop=True)

    return result
