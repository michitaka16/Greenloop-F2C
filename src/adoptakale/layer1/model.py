"""XGBoost quantile regression models for demand forecasting.

Trains three models (q=0.05, q=0.50, q=0.95) to produce prediction
intervals. Uses TimeSeriesSplit for cross-validation respecting
temporal ordering.
"""

import logging
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

from adoptakale.utils.config import MODELS_DIR

logger = logging.getLogger(__name__)

# Columns excluded from feature matrix
_NON_FEATURE_COLS = {"crop_id", "kg_shipped", "date"}

# Quantile configuration: label -> alpha
_QUANTILES = {
    "q05": 0.05,
    "q50": 0.50,
    "q95": 0.95,
}


def _get_feature_columns(df):
    """Return sorted list of feature column names."""
    return sorted([c for c in df.columns if c not in _NON_FEATURE_COLS])


def train_models(
    features_df, models_dir=None,
):
    """Train quantile regression models (q=0.05, 0.50, 0.95).

    Args:
        features_df: DataFrame from build_features() with feature columns
            and target 'kg_shipped'.
        models_dir: Directory to save trained models. Defaults to MODELS_DIR.

    Returns:
        Dict mapping quantile labels ('q05', 'q50', 'q95') to trained
        XGBRegressor instances.

    Raises:
        ValueError: If features_df is empty or missing required columns.
    """
    if features_df is None or len(features_df) == 0:
        raise ValueError("features_df is empty — cannot train models")

    if "kg_shipped" not in features_df.columns:
        raise ValueError("features_df missing target column 'kg_shipped'")

    save_dir = Path(models_dir) if models_dir is not None else MODELS_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    feature_cols = _get_feature_columns(features_df)
    if len(feature_cols) == 0:
        raise ValueError("features_df has no feature columns after excluding non-feature cols")

    X = features_df[feature_cols].values
    y = features_df["kg_shipped"].values

    models = {}
    tscv = TimeSeriesSplit(n_splits=3)

    for label, alpha in _QUANTILES.items():
        logger.info(
            "model.train.start",
            extra={"quantile_label": label, "quantile_alpha": alpha, "n_samples": len(X)},
        )

        model = xgb.XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=alpha,
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )

        # Use TimeSeriesSplit for final validation score logging,
        # then train on all data for the production model.
        cv_scores = []
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            cv_model = xgb.XGBRegressor(
                objective="reg:quantileerror",
                quantile_alpha=alpha,
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
            cv_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
            val_pred = cv_model.predict(X_val)
            mae = np.mean(np.abs(y_val - val_pred))
            cv_scores.append(mae)

        mean_cv_mae = np.mean(cv_scores)
        logger.info(
            "model.cv.complete",
            extra={"quantile_label": label, "mean_cv_mae": round(mean_cv_mae, 4)},
        )

        # Train final model on all data
        model.fit(X, y, verbose=False)

        # Save as XGBoost native JSON
        model_path = save_dir / f"demand_{label}.json"
        model.save_model(str(model_path))
        logger.info(
            "model.saved",
            extra={"quantile_label": label, "path": str(model_path)},
        )

        models[label] = model

    return models


def load_models(models_dir=None):
    """Load trained quantile models from disk.

    Args:
        models_dir: Directory containing saved model .json files.
            Defaults to MODELS_DIR.

    Returns:
        Dict mapping quantile labels ('q05', 'q50', 'q95') to loaded
        XGBRegressor instances.

    Raises:
        FileNotFoundError: If models_dir does not exist or contains
            no model files.
    """
    load_dir = Path(models_dir) if models_dir is not None else MODELS_DIR

    if not load_dir.exists():
        raise FileNotFoundError(
            f"Models directory does not exist: {load_dir}"
        )

    models = {}
    for label in _QUANTILES:
        model_path = load_dir / f"demand_{label}.json"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}"
            )
        model = xgb.XGBRegressor()
        model.load_model(str(model_path))
        models[label] = model
        logger.info(
            "model.loaded",
            extra={"quantile_label": label, "path": str(model_path)},
        )

    return models
