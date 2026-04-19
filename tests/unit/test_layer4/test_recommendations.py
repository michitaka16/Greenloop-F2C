"""Tests for Layer 4 recommendations module."""

from pathlib import Path

import pandas as pd
import pytest

from greenloop.layer4.recommendations import (
    CropRecommendation,
    get_segment_recommendations,
)
from greenloop.layer4.segmentation import cluster_customers
from greenloop.layer4.features import load_features

DATA_DIR = Path(__file__).parents[3] / "data"
ORDERS_PATH = DATA_DIR / "orders.csv"


class TestRecommendations:
    """Test per-segment crop recommendations."""

    @pytest.fixture
    def pipeline(self):
        df_features = load_features()
        orders = pd.read_csv(ORDERS_PATH, parse_dates=["date"])
        result = cluster_customers(df_features, k=4)
        # Attach cluster labels to df
        df_features = df_features.copy()
        df_features["_cluster"] = result.labels
        return df_features, orders, result

    def test_returns_one_per_segment(self, pipeline):
        df_features, orders, result = pipeline
        recs = get_segment_recommendations(df_features, orders, result)
        assert len(recs) == result.k

    def test_top_3_crops_are_valid(self, pipeline):
        df_features, orders, result = pipeline
        recs = get_segment_recommendations(df_features, orders, result)
        valid_crops = {"kai_lan", "spinach", "lettuce", "chye_sim", "arugula"}
        for rec in recs:
            assert len(rec.top_crops) == 3
            assert set(rec.top_crops).issubset(valid_crops)

    def test_bundle_name_non_empty(self, pipeline):
        df_features, orders, result = pipeline
        recs = get_segment_recommendations(df_features, orders, result)
        for rec in recs:
            assert rec.bundle_name != ""
            assert len(rec.bundle_name) > 5

    def test_segment_names_match_result(self, pipeline):
        df_features, orders, result = pipeline
        recs = get_segment_recommendations(df_features, orders, result)
        result_names = {p.segment_name for p in result.profiles}
        rec_names = {r.segment_name for r in recs}
        assert result_names == rec_names

    def test_recommended_action_populated(self, pipeline):
        df_features, orders, result = pipeline
        recs = get_segment_recommendations(df_features, orders, result)
        for rec in recs:
            assert rec.recommended_action != ""
            assert len(rec.recommended_action) > 5

    def test_returns_list_of_crop_recommendation(self, pipeline):
        df_features, orders, result = pipeline
        recs = get_segment_recommendations(df_features, orders, result)
        assert all(isinstance(r, CropRecommendation) for r in recs)
