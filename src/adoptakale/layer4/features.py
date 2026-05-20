"""Feature loading and scaling for customer segmentation.

Since customers.csv contains pre-computed behavioural features per the spec schema,
this module loads those columns and applies StandardScaler for K-Means input.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from adoptakale.utils.config import DATA_DIR


# The 5 behavioural feature columns in customers.csv (per spec)
_FEATURE_COLS = [
    "purchase_frequency",
    "avg_order_sgd",
    "organic_preference",
    "bulk_buyer",
    "live_commerce_active",
]


def load_features(
    data_dir: Path | None = None,
    customers_path: str | None = None,
) -> pd.DataFrame:
    """Load customers.csv and return DataFrame with raw + scaled features.

    Returns
    -------
    pd.DataFrame
        customer_id, purchase_frequency, avg_order_sgd, organic_preference,
        bulk_buyer, live_commerce_active, top_crop,
        and 5 *_scaled columns for K-Means input.
    """
    path = customers_path or str((data_dir or DATA_DIR) / "customers.csv")
    df = pd.read_csv(path)

    expected = ["customer_id", "top_crop"] + _FEATURE_COLS
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"customers.csv missing columns: {missing}")

    # Scale features with StandardScaler
    # Convert bool columns to float; handle zero-variance cols to avoid NaN
    feature_data = df[_FEATURE_COLS].astype(float).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_data)
    # Replace any NaN (from zero-variance columns) with 0.0
    X_scaled = np.where(np.isnan(X_scaled), 0.0, X_scaled)
    for i, col in enumerate(_FEATURE_COLS):
        df[f"{col}_scaled"] = X_scaled[:, i]

    return df


def get_feature_cols() -> list[str]:
    """Return the list of raw feature column names."""
    return list(_FEATURE_COLS)


def get_scaled_cols() -> list[str]:
    """Return the list of scaled feature column names for K-Means input."""
    return [f"{c}_scaled" for c in _FEATURE_COLS]
