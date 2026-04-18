"""Feature engineering for customer behavioural segmentation."""

from datetime import date

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


TODAY = date(2026, 4, 17)
MIN_ORDERS = 3
BULK_KG_THRESHOLD = 5.0
N_CROPS = 10


def build_features(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    min_orders: int = MIN_ORDERS,
    bulk_kg_threshold: float = BULK_KG_THRESHOLD,
) -> pd.DataFrame:
    """Build per-customer behavioural feature vectors.

    Parameters
    ----------
    customers : pd.DataFrame
        Customer table from customers.csv.
    orders : pd.DataFrame
        Order table from orders.csv.
    min_orders : int
        Minimum orders needed to include a customer (default 3).
    bulk_kg_threshold : float
        Kg/order threshold for bulk buyer flag (default 5.0).

    Returns
    -------
    pd.DataFrame
        One row per customer with feature columns. Customers with < min_orders
        are excluded. The DataFrame includes customer_id + 5 scaled features
        suitable for K-Means input.

    Raises
    ------
    ValueError
        If required columns are missing from inputs.
    """
    _validate_inputs(customers, orders)

    # Parse dates and compute months_since_first_order
    orders = orders.copy()
    customers = customers.copy()
    orders["date"] = pd.to_datetime(orders["date"]).dt.date
    customers["first_order_date"] = pd.to_datetime(customers["first_order_date"]).dt.date
    today = pd.Timestamp(TODAY).date()

    # Count orders per customer
    order_counts = orders.groupby("customer_id").size().reset_index(name="n_orders")
    customers = customers.merge(order_counts, on="customer_id", how="left")
    customers["n_orders"] = customers["n_orders"].fillna(0).astype(int)

    # Filter to min_orders
    customers = customers[customers["n_orders"] >= min_orders].copy()

    if customers.empty:
        raise ValueError(
            f"No customers with >= {min_orders} orders. "
            "Cannot build behavioural features."
        )

    # Per-customer aggregations
    agg = (
        orders.groupby("customer_id")
        .agg(
            avg_basket_sgd=("sgd_total", "mean"),
            avg_kg=("kg", "mean"),
            bulk_count=("kg", lambda s: (s > bulk_kg_threshold).sum()),
            live_count=("is_live_commerce", "sum"),
            unique_crops=("crop_id", "nunique"),
            order_dates=("date", lambda s: (today - s.min()).days),
        )
        .reset_index()
    )
    agg["order_dates"] = agg["order_dates"].replace(0, 1)  # avoid div by zero
    agg["months_active"] = agg["order_dates"] / 30.0

    # Dominant crop per customer
    dominant_crop = (
        orders.groupby("customer_id")["crop_id"]
        .agg(lambda s: s.value_counts().idxmax())
        .reset_index()
    )
    dominant_crop.columns = ["customer_id", "crop_id"]

    # Merge features onto filtered customer list
    df = customers.merge(agg, on="customer_id", how="left")
    df = df.merge(dominant_crop, on="customer_id", how="left")

    # Feature 1: purchase_frequency — orders per month
    df["purchase_frequency"] = df["n_orders"] / df["months_active"]

    # Feature 2: avg_order_sgd — already computed

    # Feature 3: bulk_buyer — fraction of orders that are bulk
    df["bulk_buyer"] = df["bulk_count"] / df["n_orders"]

    # Feature 4: live_commerce_share — fraction of orders that are live
    df["live_commerce_share"] = df["live_count"] / df["n_orders"]

    # Feature 5: crop_diversity — normalised unique crops
    df["crop_diversity"] = df["unique_crops"] / N_CROPS

    # Select feature columns
    feature_cols = [
        "purchase_frequency",
        "avg_basket_sgd",
        "bulk_buyer",
        "live_commerce_share",
        "crop_diversity",
    ]

    # Scale features with StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[feature_cols])
    for i, col in enumerate(feature_cols):
        df[f"{col}_scaled"] = X_scaled[:, i]

    return df


def _validate_inputs(customers: pd.DataFrame, orders: pd.DataFrame) -> None:
    """Validate required columns exist."""
    cust_cols = {"customer_id", "customer_type", "first_order_date", "organic_certified", "primary_channel"}
    order_cols = {"order_id", "customer_id", "date", "crop_id", "kg", "sgd_total", "channel", "is_live_commerce"}
    missing_cust = cust_cols - set(customers.columns)
    missing_ord = order_cols - set(orders.columns)
    if missing_cust:
        raise ValueError(f"customers.csv missing columns: {missing_cust}")
    if missing_ord:
        raise ValueError(f"orders.csv missing columns: {missing_ord}")
