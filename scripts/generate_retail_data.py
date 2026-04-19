#!/usr/bin/env python3
"""Generate synthetic retail data for Layer 4 customer segmentation demo.

Produces data/customers.csv and data/orders.csv matching the spec schema.
customers.csv columns: customer_id, purchase_frequency, avg_order_sgd,
organic_preference, bulk_buyer, live_commerce_active, top_crop
orders.csv columns: order_id, customer_id, date, crop_id, kg, sgd_total

Usage:
    python scripts/generate_retail_data.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RNG = random.Random(42)
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TODAY = date(2026, 4, 17)
N_CUSTOMERS = 500

CROPS = ["kai_lan", "spinach", "lettuce", "chye_sim", "arugula"]
CROP_WEIGHTS = [0.22, 0.25, 0.20, 0.18, 0.15]
CROP_BASE_PRICE = {
    "kai_lan": 6.5, "spinach": 5.8, "lettuce": 4.9,
    "chye_sim": 5.5, "arugula": 7.2,
}

# ---------------------------------------------------------------------------
# Ground-truth segment parameters (used to generate realistic features)
# ---------------------------------------------------------------------------
_SEGMENT_DEFS = {
    "Organic Subscribers": dict(
        organic_range=(0.80, 1.0), bulk_range=(0.3, 1.5),
        freq_range=(7, 14), basket_range=(25, 55), live_range=(0.0, 0.1),
    ),
    "Bulk Buyers": dict(
        organic_range=(0.0, 0.2), bulk_range=(5.0, 15.0),
        freq_range=(1, 4), basket_range=(80, 200), live_range=(0.0, 0.1),
    ),
    "Live Commerce Fans": dict(
        organic_range=(0.2, 0.5), bulk_range=(0.5, 2.5),
        freq_range=(3, 8), basket_range=(20, 50), live_range=(0.5, 1.0),
    ),
    "Casual Shoppers": dict(
        organic_range=(0.0, 0.3), bulk_range=(0.3, 1.5),
        freq_range=(1, 4), basket_range=(10, 30), live_range=(0.0, 0.15),
    ),
}
_SEGMENT_WEIGHTS = [0.23, 0.14, 0.18, 0.45]  # Organic, Bulk, Live, Casual
_SEGMENT_NAMES = list(_SEGMENT_DEFS.keys())


# ---------------------------------------------------------------------------
# Customer generation
# ---------------------------------------------------------------------------
def generate_customers() -> pd.DataFrame:
    """Generate customers with behavioural features pre-computed.

    Each customer's features are drawn from segment-specific distributions
    so K-Means will naturally recover these segments.
    """
    rows = []

    for i in range(N_CUSTOMERS):
        cid = f"C{i+1:04d}"
        segment_name = RNG.choices(_SEGMENT_NAMES, weights=_SEGMENT_WEIGHTS)[0]
        seg = _SEGMENT_DEFS[segment_name]

        # Time baseline
        months_active = RNG.randint(2, 14)
        first_order_date = TODAY - timedelta(days=months_active * 30)

        # Feature draws from segment-specific ranges
        organic_pref = RNG.uniform(*seg["organic_range"])
        bulk_kg = RNG.uniform(*seg["bulk_range"])
        purchase_freq = RNG.randint(*seg["freq_range"])
        avg_basket = RNG.uniform(*seg["basket_range"])
        live_share = RNG.uniform(*seg["live_range"])

        # Derived flags
        bulk_buyer = bulk_kg > 3.5
        live_commerce_active = live_share > 0.3

        # Top crop weighted toward segment's preferred crops
        if segment_name == "Organic Subscribers":
            top_crop = RNG.choices(
                ["spinach", "kai_lan", "arugula"],
                weights=[0.45, 0.30, 0.25],
            )[0]
        elif segment_name == "Bulk Buyers":
            top_crop = RNG.choices(
                ["kai_lan", "chye_sim", "lettuce"],
                weights=[0.40, 0.35, 0.25],
            )[0]
        elif segment_name == "Live Commerce Fans":
            top_crop = RNG.choices(
                ["kai_lan", "spinach", "arugula"],
                weights=[0.35, 0.35, 0.30],
            )[0]
        else:  # Casual
            top_crop = RNG.choices(
                CROPS, weights=CROP_WEIGHTS,
            )[0]

        rows.append({
            "customer_id": cid,
            "purchase_frequency": round(purchase_freq, 2),
            "avg_order_sgd": round(avg_basket, 2),
            "organic_preference": round(organic_pref, 3),
            "bulk_buyer": bulk_buyer,
            "live_commerce_active": live_commerce_active,
            "top_crop": top_crop,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Orders generation
# ---------------------------------------------------------------------------
def generate_orders(customers: pd.DataFrame) -> pd.DataFrame:
    """Generate orders for each customer based on their behavioural features."""
    rows = []
    order_counter = 1

    for _, cust in customers.iterrows():
        cid = cust["customer_id"]
        months_active = RNG.randint(2, 14)
        first_order_date = TODAY - timedelta(days=months_active * 30)

        # Approximate number of orders from purchase_frequency
        # purchase_frequency is orders/month; months_active gives total
        n_orders = max(2, int(cust["purchase_frequency"] * months_active / 6))
        n_orders = min(n_orders, 60)  # cap at 60 orders

        for _ in range(n_orders):
            order_date = first_order_date + timedelta(
                days=RNG.randint(0, months_active * 30)
            )
            crop = cust["top_crop"] if RNG.random() < 0.7 else RNG.choices(CROPS, weights=CROP_WEIGHTS)[0]
            base_price = CROP_BASE_PRICE[crop]
            if cust["organic_preference"] > 0.6:
                base_price *= 1.3
            kg = RNG.uniform(0.3, 5.0) if not cust["bulk_buyer"] else RNG.uniform(5.0, 15.0)
            sgd = round(kg * base_price * RNG.uniform(0.88, 1.12), 2)

            rows.append({
                "order_id": f"O{order_counter:05d}",
                "customer_id": cid,
                "date": order_date.isoformat(),
                "crop_id": crop,
                "kg": round(kg, 2),
                "sgd_total": sgd,
            })
            order_counter += 1

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    customers = generate_customers()
    print(f"Generated {len(customers)} customers")

    orders = generate_orders(customers)
    print(f"Generated {len(orders)} orders")

    customers_path = DATA_DIR / "customers.csv"
    orders_path = DATA_DIR / "orders.csv"
    customers.to_csv(customers_path, index=False)
    orders.to_csv(orders_path, index=False)
    print(f"\nWritten:")
    print(f"  {customers_path}  ({len(customers)} rows)")
    print(f"  {orders_path}  ({len(orders)} rows)")

    # Schema validation
    exp_cust = ["customer_id", "purchase_frequency", "avg_order_sgd",
                 "organic_preference", "bulk_buyer", "live_commerce_active", "top_crop"]
    exp_ord = ["order_id", "customer_id", "date", "crop_id", "kg", "sgd_total"]
    assert list(customers.columns) == exp_cust, f"Customer cols: {list(customers.columns)}"
    assert list(orders.columns) == exp_ord, f"Order cols: {list(orders.columns)}"
    assert set(customers["top_crop"].unique()).issubset(set(CROPS))
    assert customers["bulk_buyer"].dtype == bool
    assert customers["live_commerce_active"].dtype == bool
    print("\nSchema validation PASSED")


if __name__ == "__main__":
    main()
