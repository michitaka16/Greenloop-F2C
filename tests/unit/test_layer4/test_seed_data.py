"""Tests for Layer 4 seed data generation and schema."""

from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).parents[3] / "data"

CROPS = ["kai_lan", "spinach", "lettuce", "chye_sim", "arugula"]


class TestCustomersSchema:
    """Test that customers.csv matches the spec schema."""

    @pytest.fixture
    def customers(self):
        path = DATA_DIR / "customers.csv"
        if not path.exists():
            pytest.skip("customers.csv not generated — run scripts/generate_retail_data.py")
        return pd.read_csv(path)

    def test_has_500_customers(self, customers):
        assert len(customers) == 500

    def test_has_required_columns(self, customers):
        expected = [
            "customer_id", "purchase_frequency", "avg_order_sgd",
            "organic_preference", "bulk_buyer", "live_commerce_active", "top_crop",
        ]
        assert list(customers.columns) == expected, f"Got: {list(customers.columns)}"

    def test_customer_id_format(self, customers):
        assert customers["customer_id"].str.match(r"^C\d{4}$").all()

    def test_top_crop_is_valid(self, customers):
        assert set(customers["top_crop"].unique()).issubset(set(CROPS))

    def test_bulk_buyer_is_boolean(self, customers):
        assert customers["bulk_buyer"].dtype == bool
        assert set(customers["bulk_buyer"].unique()).issubset({True, False})

    def test_live_commerce_active_is_boolean(self, customers):
        assert customers["live_commerce_active"].dtype == bool
        assert set(customers["live_commerce_active"].unique()).issubset({True, False})

    def test_purchase_frequency_positive(self, customers):
        assert (customers["purchase_frequency"] > 0).all()

    def test_avg_order_sgd_positive(self, customers):
        assert (customers["avg_order_sgd"] > 0).all()

    def test_organic_preference_in_0_1(self, customers):
        assert (customers["organic_preference"] >= 0).all()
        assert (customers["organic_preference"] <= 1).all()


class TestOrdersSchema:
    """Test that orders.csv matches the spec schema."""

    @pytest.fixture
    def orders(self):
        path = DATA_DIR / "orders.csv"
        if not path.exists():
            pytest.skip("orders.csv not generated — run scripts/generate_retail_data.py")
        return pd.read_csv(path, parse_dates=["date"])

    def test_has_required_columns(self, orders):
        expected = ["order_id", "customer_id", "date", "crop_id", "kg", "sgd_total"]
        assert list(orders.columns) == expected, f"Got: {list(orders.columns)}"

    def test_order_id_format(self, orders):
        assert orders["order_id"].str.match(r"^O\d{5}$").all()

    def test_kg_positive(self, orders):
        assert (orders["kg"] > 0).all()

    def test_sgd_total_positive(self, orders):
        assert (orders["sgd_total"] > 0).all()

    def test_crop_id_is_valid(self, orders):
        assert set(orders["crop_id"].unique()).issubset(set(CROPS))

    def test_customer_ids_match_customers(self, orders):
        customers = pd.read_csv(DATA_DIR / "customers.csv")
        order_cids = set(orders["customer_id"].unique())
        cust_cids = set(customers["customer_id"].unique())
        assert order_cids.issubset(cust_cids), \
            f"Orders reference unknown customers: {order_cids - cust_cids}"

    def test_at_least_2_orders_per_customer(self, orders):
        counts = orders.groupby("customer_id").size()
        assert (counts >= 2).all(), \
            f"Customers with <2 orders: {(counts < 2).sum()}"
