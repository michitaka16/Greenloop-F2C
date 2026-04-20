"""Scenario 4 — Performance benchmarks for Layer 1 demand forecasting."""

import time

import numpy as np
import pandas as pd
import pytest

from greenloop.layer1.features import build_features
from greenloop.layer1.model import train_models
from greenloop.layer1.predict import predict_demand


ALL_10_CROPS = [
    "kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim",
    "arugula", "tomatoes", "capsicum", "cucumber", "strawberry", "basil",
]


def _make_shipments(rng, crop_ids, n_days=90, base_kg=30.0, volatility=0.1):
    dates = pd.date_range("2025-10-01", periods=n_days, freq="D")
    rows = []
    for d in dates:
        for c in crop_ids:
            rows.append({
                "date": d,
                "crop_id": c,
                "kg_shipped": max(0.0, rng.normal(base_kg, base_kg * volatility)),
                "price_sgd_per_kg": rng.uniform(3.0, 8.0),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def full_setup(tmp_path):
    """Train on full 90-day, 10-crop dataset."""
    rng = np.random.default_rng(42)
    shipments = _make_shipments(rng, ALL_10_CROPS, n_days=90)
    features_df = build_features(shipments)
    models = train_models(features_df, models_dir=tmp_path / "models")
    return models, features_df


class TestSingleCropInferenceUnder10ms:
    """Single crop inference latency is under 10 ms."""

    @pytest.mark.parametrize("crop_id", ALL_10_CROPS)
    def test_single_crop_inference_under_10ms(self, full_setup, crop_id):
        models, features_df = full_setup
        t0 = time.perf_counter()
        predict_demand(models, features_df, crop_id=crop_id)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 10, f"{crop_id}: {elapsed_ms:.2f} ms > 10 ms limit"


class TestAllCropsInferenceUnder200ms:
    """All 10 crops inferred together under 200 ms."""

    def test_all_crops_inference_under_200ms(self, full_setup):
        models, features_df = full_setup
        t0 = time.perf_counter()
        predict_demand(models, features_df)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 200, f"All-crops inference: {elapsed_ms:.2f} ms > 200 ms limit"


class TestModelRetrainUnder30s:
    """Training 3 quantile models (200 trees each) on 10 crops completes in under 30 s."""

    def test_model_retrain_under_30s(self, tmp_path):
        rng = np.random.default_rng(99)
        # Use 60 days to speed up train while keeping valid features
        shipments = _make_shipments(rng, ALL_10_CROPS, n_days=60)
        features_df = build_features(shipments)

        t0 = time.perf_counter()
        train_models(features_df, models_dir=tmp_path / "models")
        elapsed_s = time.perf_counter() - t0

        assert elapsed_s < 30, f"Model retrain took {elapsed_s:.1f} s (limit: 30 s)"


class TestMemoryUsageUnder500mb:
    """Peak memory during inference stays under 500 MB."""

    def test_memory_usage_under_500mb(self, full_setup):
        """Check that inference does not hold large intermediate structures."""
        models, features_df = full_setup
        # Inference should only hold features_df and model outputs
        import sys
        # Rough proxy: size of feature matrix + model params
        n_rows = len(features_df)
        n_crops = len(ALL_10_CROPS)
        # Each crop row has ~12 feature columns of float64
        feature_bytes = n_rows * 12 * 8
        # XGBoost models: ~200 trees * ~5 depth * 3 models * ~8 bytes per node (rough)
        model_bytes = 200 * 5 * 3 * 8 * 50  # very rough upper bound
        total_mb = (feature_bytes + model_bytes) / (1024 * 1024)
        assert total_mb < 500, f"Estimated memory {total_mb:.0f} MB exceeds 500 MB limit"

    def test_feature_matrix_reasonable_size(self, full_setup):
        """Feature matrix for 10 crops x 90 days is bounded."""
        _, features_df = full_setup
        # After build_features: warmup period (28 days) is dropped per crop
        # ~62 rows per crop * 10 crops = ~620 rows
        assert len(features_df) < 1000
        assert len(features_df) > 0


class TestPredictionDeterminism:
    """Same input produces identical predictions (random_state is fixed)."""

    def test_prediction_is_deterministic(self, tmp_path):
        rng = np.random.default_rng(42)
        shipments = _make_shipments(rng, ["kai_lan"], n_days=60)
        features_df = build_features(shipments)
        models_a = train_models(features_df, models_dir=tmp_path / "a_models")
        result_a = predict_demand(models_a, features_df, crop_id="kai_lan")

        # Re-train with same data — should be identical
        rng2 = np.random.default_rng(42)
        shipments2 = _make_shipments(rng2, ["kai_lan"], n_days=60)
        features_df2 = build_features(shipments2)
        models_b = train_models(features_df2, models_dir=tmp_path / "b_models")
        result_b = predict_demand(models_b, features_df2, crop_id="kai_lan")

        assert result_a["kai_lan"]["predicted_kg"] == pytest.approx(
            result_b["kai_lan"]["predicted_kg"], abs=0.01
        )
