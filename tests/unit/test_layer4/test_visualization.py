"""Tests for Layer 4 UMAP and PCA visualization."""

from pathlib import Path

import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from greenloop.layer4.visualization import reduce_pca, reduce_umap

DATA_DIR = Path(__file__).parents[3] / "data"


def _make_df():
    """Load customers and add scaled columns."""
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    feature_cols = [
        "purchase_frequency", "avg_order_sgd", "organic_preference",
        "bulk_buyer", "live_commerce_active",
    ]
    scaler = StandardScaler()
    X = scaler.fit_transform(customers[feature_cols])
    for i, col in enumerate(feature_cols):
        customers[f"{col}_scaled"] = X[:, i]
    return customers


class TestPCA:
    def test_returns_correct_columns(self):
        df = _make_df()
        result = reduce_pca(df)
        assert list(result.columns) == ["customer_id", "pca_1", "pca_2"]

    def test_row_count_matches_input(self):
        df = _make_df()
        result = reduce_pca(df)
        assert len(result) == len(df)

    def test_is_deterministic(self):
        df = _make_df()
        r1 = reduce_pca(df)
        r2 = reduce_pca(df)
        pd.testing.assert_frame_equal(r1, r2)


class TestUMAP:
    def test_returns_correct_columns(self):
        df = _make_df()
        result = reduce_umap(df, random_state=42)
        assert list(result.columns) == ["customer_id", "umap_1", "umap_2"]

    def test_row_count_matches_input(self):
        df = _make_df()
        result = reduce_umap(df, random_state=42)
        assert len(result) == len(df)

    def test_random_state_deterministic(self):
        df = _make_df()
        r1 = reduce_umap(df, random_state=42)
        r2 = reduce_umap(df, random_state=42)
        pd.testing.assert_frame_equal(r1, r2)

    def test_different_seeds_different_output(self):
        df = _make_df()
        r1 = reduce_umap(df, random_state=42)
        r2 = reduce_umap(df, random_state=99)
        assert not r1[["umap_1", "umap_2"]].equals(r2[["umap_1", "umap_2"]])
