"""Tests for Layer 4 segmentation pipeline."""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from greenloop.layer4.segmentation import (
    ClusteringResult,
    SegmentProfile,
    cluster_customers,
)

# Suppress sklearn numerical warnings during silhouette computation
# (sklearn emits these when clusters have near-zero variance — our data handling is correct)
warnings.filterwarnings("ignore", message="divide by zero", category=RuntimeWarning)
warnings.filterwarnings("ignore", message="overflow encountered", category=RuntimeWarning)
warnings.filterwarnings("ignore", message="invalid value encountered", category=RuntimeWarning)

DATA_DIR = Path(__file__).parents[3] / "data"


class TestClusteringPipeline:
    """Test K-Means clustering with spec-compliant segment naming."""

    @pytest.fixture
    def df(self):
        """Load pre-computed features for clustering."""
        path = DATA_DIR / "customers.csv"
        if not path.exists():
            pytest.skip("customers.csv not generated — run scripts/generate_retail_data.py")
        customers = pd.read_csv(path)
        # Apply StandardScaler to match what load_features() does
        feature_cols = [
            "purchase_frequency", "avg_order_sgd", "organic_preference",
            "bulk_buyer", "live_commerce_active",
        ]
        scaler = StandardScaler()
        X = scaler.fit_transform(customers[feature_cols].astype(float))
        X = np.where(np.isnan(X), 0.0, X)
        for i, col in enumerate(feature_cols):
            customers[f"{col}_scaled"] = X[:, i]
        return customers

    def test_k4_returns_4_clusters(self, df):
        result = cluster_customers(df, k=4)
        assert result.k == 4
        assert len(set(result.labels)) == 4

    def test_k4_silhouette_is_valid(self, df):
        result = cluster_customers(df, k=4)
        assert 0.0 <= result.silhouette <= 1.0

    def test_k4_profiles_count(self, df):
        result = cluster_customers(df, k=4)
        assert len(result.profiles) == 4

    def test_all_4_named_segments_present(self, df):
        """All 4 spec segment names must appear across clusters."""
        result = cluster_customers(df, k=4)
        names = {p.segment_name for p in result.profiles}
        expected = {"Organic Subscribers", "Bulk Buyers",
                     "Live Commerce Fans", "Casual Shoppers"}
        assert expected.issubset(names), \
            f"Missing segments: {expected - names}. Got: {names}"

    def test_labels_array_length_matches_df(self, df):
        result = cluster_customers(df, k=4)
        assert len(result.labels) == len(df)

    def test_invalid_k_raises(self, df):
        with pytest.raises(ValueError):
            cluster_customers(df, k=1)

    def test_silhouette_guided_selects_from_range(self, df):
        result = cluster_customers(df, k_range=range(3, 6))
        assert result.k in range(3, 6)
        assert 0.0 <= result.silhouette <= 1.0

    def test_profile_has_required_fields(self, df):
        result = cluster_customers(df, k=4)
        for p in result.profiles:
            assert isinstance(p, SegmentProfile)
            assert p.size > 0
            assert p.size_pct > 0
            assert 0 <= p.organic_pct <= 100
            assert 0 <= p.bulk_pct <= 100
            assert 0 <= p.live_pct <= 100
            assert p.segment_name != ""
            assert p.recommended_action != ""

    def test_clustering_result_is_dataclass(self, df):
        result = cluster_customers(df, k=4)
        assert isinstance(result, ClusteringResult)
        assert isinstance(result.labels, np.ndarray)
