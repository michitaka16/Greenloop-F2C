"""Feature importance explanation using SHAP TreeExplainer.

Provides interpretable feature importance rankings for demand
forecasting models.
"""

import logging

import numpy as np
import pandas as pd
import shap

logger = logging.getLogger(__name__)

# Columns excluded from feature matrix (must match model.py)
_NON_FEATURE_COLS = {"crop_id", "kg_shipped", "date"}


def get_feature_importance(model, features_df, crop_id):
    """Return top-10 feature importances for a given crop using SHAP.

    Args:
        model: Trained XGBRegressor model (typically the q50 median model).
        features_df: DataFrame from build_features() with feature columns.
        crop_id: The crop to explain.

    Returns:
        Dict with keys:
            - crop_id: The crop being explained.
            - feature_importances: List of dicts, each with 'feature' and
              'importance' (mean absolute SHAP value), sorted descending.
              Top 10 features only.

    Raises:
        ValueError: If crop_id is not found in features_df.
    """
    available_crops = features_df["crop_id"].unique()
    if crop_id not in available_crops:
        raise ValueError(
            f"crop_id '{crop_id}' not found in features_df. "
            f"Available crops: {sorted(available_crops)}"
        )

    feature_cols = sorted([c for c in features_df.columns if c not in _NON_FEATURE_COLS])

    crop_df = features_df[features_df["crop_id"] == crop_id].copy()
    X = crop_df[feature_cols].values

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Mean absolute SHAP value per feature
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    # Build feature importance ranking
    importance_pairs = list(zip(feature_cols, mean_abs_shap))
    importance_pairs.sort(key=lambda x: x[1], reverse=True)

    top_10 = importance_pairs[:10]

    logger.info(
        "explain.feature_importance",
        extra={
            "crop_id": crop_id,
            "top_feature": top_10[0][0] if top_10 else "none",
            "n_features": len(feature_cols),
        },
    )

    return {
        "crop_id": crop_id,
        "feature_importances": [
            {"feature": name, "importance": round(float(val), 6)}
            for name, val in top_10
        ],
    }
