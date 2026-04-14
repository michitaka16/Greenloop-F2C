"""Demand prediction using trained quantile models.

Produces point forecasts (median) with prediction intervals (5th/95th
percentile) for each crop. Handles quantile crossing by sorting values.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Columns excluded from feature matrix (must match model.py)
_NON_FEATURE_COLS = {"crop_id", "kg_shipped", "date"}


def predict_demand(
    models,
    features_df,
    crop_id=None,
):
    """Predict demand for one or all crops.

    Uses the most recent row per crop from features_df to produce
    a next-period forecast.

    Args:
        models: Dict with keys 'q05', 'q50', 'q95' mapping to trained
            XGBRegressor models.
        features_df: DataFrame from build_features() with feature columns.
        crop_id: If provided, predict only for this crop. If None,
            predict for all crops in features_df.

    Returns:
        Dict mapping crop_id to prediction dict with keys:
            - predicted_kg: median forecast (q50)
            - lower_ci: 5th percentile (q05)
            - upper_ci: 95th percentile (q95)
            - interval_width: upper_ci - lower_ci

    Raises:
        ValueError: If crop_id is not found in features_df.
    """
    available_crops = features_df["crop_id"].unique()

    if crop_id is not None:
        if crop_id not in available_crops:
            raise ValueError(
                f"crop_id '{crop_id}' not found in features_df. "
                f"Available crops: {sorted(available_crops)}"
            )
        crops_to_predict = [crop_id]
    else:
        crops_to_predict = sorted(available_crops)

    feature_cols = sorted([c for c in features_df.columns if c not in _NON_FEATURE_COLS])

    results = {}
    for cid in crops_to_predict:
        crop_df = features_df[features_df["crop_id"] == cid].copy()
        # Use the most recent row for each crop as the prediction input
        crop_df = crop_df.sort_values("date")
        latest_row = crop_df.iloc[[-1]]
        X = latest_row[feature_cols].values

        raw_q05 = float(models["q05"].predict(X)[0])
        raw_q50 = float(models["q50"].predict(X)[0])
        raw_q95 = float(models["q95"].predict(X)[0])

        # Handle quantile crossing: sort the three values
        lower, median, upper = sorted([raw_q05, raw_q50, raw_q95])

        # Ensure non-negative predictions (demand cannot be negative)
        lower = max(0.0, lower)
        median = max(0.0, median)
        upper = max(0.0, upper)

        interval_width = upper - lower

        results[cid] = {
            "predicted_kg": round(median, 2),
            "lower_ci": round(lower, 2),
            "upper_ci": round(upper, 2),
            "interval_width": round(interval_width, 2),
        }

        logger.info(
            "predict.demand",
            extra={
                "crop_id": cid,
                "predicted_kg": results[cid]["predicted_kg"],
                "lower_ci": results[cid]["lower_ci"],
                "upper_ci": results[cid]["upper_ci"],
            },
        )

    return results
