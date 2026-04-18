#!/usr/bin/env python3
"""Generate synthetic retail data for Layer 4 customer segmentation demo.

Produces data/customers.csv and data/orders.csv with realistic customer
behavioural patterns suitable for K-Means clustering and VC pitch demo.

Usage:
    python scripts/generate_retail_data.py
"""

import random
import uuid
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RNG = random.Random(42)
NP_RNG = np.random.default_rng(42)
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TODAY = date(2026, 4, 17)
N_B2B = 30
N_B2C = 470
N_CROPS = 10

CROPS = [
    "kale", "baby_spinach", "arugula", "butterhead_lettuce",
    "cherry_tomatoes", "bell_peppers", "strawberries", "basil",
    "mint", "cilantro",
]

CHANNELS = ["app", "delivery", "live"]
CROP_WEIGHTS = [0.15, 0.12, 0.10, 0.08, 0.12, 0.10, 0.08, 0.10, 0.08, 0.07]


# ---------------------------------------------------------------------------
# B2B generation
# ---------------------------------------------------------------------------
def generate_b2b_customers() -> pd.DataFrame:
    """Generate B2B customers (supermarkets, restaurants, platforms)."""
    business_types = ["supermarket", "restaurant", "platform", "catering", "hotel"]
    prefixes = [
        "Sunrise", "Metro", "Green", "Ocean", "Golden", "Silver", "Prime",
        "Fresh", "Blue", "Red", "Royal", "Crown", "Urban", "Classic", "Modern",
    ]
    suffixes = [
        "Supermarket", "Grocer", "Foods", "Dining", "Eats", "Mart",
        "Restaurant", "Cafe", "Kitchen", "Bistro", "Express", "Hub",
    ]
    b2b_types = RNG.choices(business_types, weights=[0.35, 0.25, 0.20, 0.12, 0.08], k=N_B2B)

    customers = []
    for i in range(N_B2B):
        cid = f"C{i+1:03d}"
        prefix = RNG.choice(prefixes)
        suffix = RNG.choice(suffixes)
        name = f"{prefix} {suffix}"
        first_order = TODAY - timedelta(days=RNG.randint(30, 540))
        customers.append({
            "customer_id": cid,
            "name": name,
            "customer_type": "B2B",
            "first_order_date": first_order.isoformat(),
            "organic_certified": RNG.random() < 0.3,
            "primary_channel": RNG.choices(["delivery", "app"], weights=[0.7, 0.3])[0],
        })
    return pd.DataFrame(customers)


def generate_b2b_orders(customers: pd.DataFrame) -> pd.DataFrame:
    """Generate orders for B2B customers — large, infrequent, price-sensitive."""
    orders = []
    order_counter = 1
    b2b_cids = customers[customers["customer_type"] == "B2B"]["customer_id"].tolist()

    for cid in b2b_cids:
        # 2-12 orders over the period
        n_orders = RNG.randint(2, 12)
        for _ in range(n_orders):
            order_date = TODAY - timedelta(days=RNG.randint(0, 540))
            crop = RNG.choices(CROPS, weights=CROP_WEIGHTS)[0]
            kg = RNG.uniform(5.0, 50.0)  # Large kg per order
            price_per_kg = 3.0 + RNG.uniform(-0.5, 1.5)
            sgd_total = round(kg * price_per_kg, 2)
            orders.append({
                "order_id": f"O{order_counter:05d}",
                "customer_id": cid,
                "date": order_date.isoformat(),
                "crop_id": crop,
                "kg": round(kg, 2),
                "sgd_total": sgd_total,
                "channel": "delivery",
                "is_live_commerce": False,
            })
            order_counter += 1
    return pd.DataFrame(orders)


# ---------------------------------------------------------------------------
# B2C generation
# ---------------------------------------------------------------------------
def _b2c_weighted_choice(options: list, weights: list) -> list:
    return RNG.choices(options, weights=weights, k=1)[0]


def _assign_b2c_segment(cid: str) -> str:
    """Assign a behavioural segment to a B2C customer for realistic clustering."""
    roll = RNG.random()
    if roll < 0.23:
        return "organic_subscriber"
    elif roll < 0.37:
        return "bulk_buyer"
    elif roll < 0.55:
        return "live_commerce"
    else:
        return "casual"


def _b2c_order_profile(segment: str) -> dict:
    """Return (n_orders_range, kg_range, price_per_kg_range, live_share) for segment."""
    if segment == "organic_subscriber":
        return {
            "n_orders": (8, 15), "kg": (0.5, 2.5), "ppkg": (5.0, 9.0), "live_share": 0.05,
        }
    elif segment == "bulk_buyer":
        return {
            "n_orders": (2, 5), "kg": (5.0, 15.0), "ppkg": (3.0, 6.0), "live_share": 0.1,
        }
    elif segment == "live_commerce":
        return {
            "n_orders": (5, 10), "kg": (0.8, 3.5), "ppkg": (4.0, 8.0), "live_share": 0.6,
        }
    else:  # casual
        return {
            "n_orders": (1, 4), "kg": (0.3, 1.5), "ppkg": (3.5, 7.0), "live_share": 0.15,
        }


def generate_b2c_customers() -> pd.DataFrame:
    """Generate B2C customers (synthetic app/delivery/live commerce)."""
    customers = []
    for i in range(N_B2B, N_B2B + N_B2C):
        cid = f"C{i+1:03d}"
        segment = _assign_b2c_segment(cid)
        organic = segment == "organic_subscriber"
        first_order = TODAY - timedelta(days=RNG.randint(14, 365))
        primary_channel = _b2c_weighted_choice(
            ["app", "delivery", "live"], [0.5, 0.3, 0.2]
        )
        customers.append({
            "customer_id": cid,
            "name": f"Consumer-{i-N_B2B+1:03d}",
            "customer_type": "B2C",
            "first_order_date": first_order.isoformat(),
            "organic_certified": organic,
            "primary_channel": primary_channel,
        })
    return pd.DataFrame(customers)


def generate_b2c_orders(b2c_customers: pd.DataFrame) -> pd.DataFrame:
    """Generate orders for B2C customers — small, varied frequency."""
    orders = []
    order_counter = N_B2B * 10  # start after B2B order counter would be
    b2c_cids = b2c_customers["customer_id"].tolist()

    for cid in b2c_cids:
        segment = _assign_b2c_segment(cid)
        profile = _b2c_order_profile(segment)
        n_orders_min, n_orders_max = profile["n_orders"]
        n_orders = RNG.randint(n_orders_min, n_orders_max)

        for _ in range(n_orders):
            order_date = TODAY - timedelta(days=RNG.randint(0, 365))
            crop = RNG.choices(CROPS, weights=CROP_WEIGHTS)[0]
            kg = RNG.uniform(profile["kg"][0], profile["kg"][1])
            ppkg = RNG.uniform(profile["ppkg"][0], profile["ppkg"][1])
            sgd_total = round(kg * ppkg, 2)
            is_live = RNG.random() < profile["live_share"]
            channel = "live" if is_live else RNG.choices(["app", "delivery"], [0.6, 0.4])[0]
            orders.append({
                "order_id": f"O{order_counter:05d}",
                "customer_id": cid,
                "date": order_date.isoformat(),
                "crop_id": crop,
                "kg": round(kg, 2),
                "sgd_total": sgd_total,
                "channel": channel,
                "is_live_commerce": is_live,
            })
            order_counter += 1
    return pd.DataFrame(orders)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("Generating B2B customers...")
    b2b_customers = generate_b2b_customers()
    print(f"  {len(b2b_customers)} B2B customers")

    print("Generating B2C customers...")
    b2c_customers = generate_b2c_customers()
    print(f"  {len(b2c_customers)} B2C customers")

    customers = pd.concat([b2b_customers, b2c_customers], ignore_index=True)

    print("Generating B2B orders...")
    b2b_orders = generate_b2b_orders(b2b_customers)
    print(f"  {len(b2b_orders)} B2B orders")

    print("Generating B2C orders...")
    b2c_orders = generate_b2c_orders(b2c_customers)
    print(f"  {len(b2c_orders)} B2C orders")

    orders = pd.concat([b2b_orders, b2c_orders], ignore_index=True)

    # Sort by customer_id then date
    customers = customers.sort_values("customer_id").reset_index(drop=True)
    orders = orders.sort_values(["customer_id", "date"]).reset_index(drop=True)

    customers_path = DATA_DIR / "customers.csv"
    orders_path = DATA_DIR / "orders.csv"
    customers.to_csv(customers_path, index=False)
    orders.to_csv(orders_path, index=False)

    print(f"\nWritten:")
    print(f"  {customers_path}  ({len(customers)} rows)")
    print(f"  {orders_path}  ({len(orders)} rows)")

    # Quick sanity check
    n_customers = len(customers)
    n_orders = len(orders)
    print(f"\nSanity check:")
    print(f"  Total customers: {n_customers}  (B2B={N_B2B}, B2C={N_B2C})")
    print(f"  Total orders: {n_orders}")
    print(f"  Avg orders/customer: {n_orders/n_customers:.2f}")
    print(f"  B2C segment sizes:")
    for seg in ["organic_subscriber", "bulk_buyer", "live_commerce", "casual"]:
        cnt = len([c for c in b2c_customers["customer_id"] if _assign_b2c_segment(c) == seg])
        print(f"    {seg}: {cnt} ({cnt/N_B2C*100:.1f}%)")


if __name__ == "__main__":
    main()
