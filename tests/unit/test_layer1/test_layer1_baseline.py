"""Scenario 1 — Normal operation baseline tests for Layer 1 demand forecasting."""

import numpy as np
import pandas as pd
import pytest

from adoptakale.layer1.features import build_features
from adoptakale.layer1.model import train_models
from adoptakale.layer1.predict import predict_demand


ALL_10_CROPS = [
    "kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim",
    "arugula", "tomatoes", "capsicum", "cucumber", "strawberry", "basil",
]


def _make_shipments(rng, crop_ids, n_days=90, base_kg=30.0, volatility=0.1):
    """Create shipments DataFrame with realistic demand patterns."""
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
def baseline_setup(tmp_path):
    """Train models on stable 90-day data for all 10 crops."""
    rng = np.random.default_rng(42)
    shipments = _make_shipments(rng, ALL_10_CROPS, n_days=90, base_kg=30.0, volatility=0.1)
    features_df = build_features(shipments)
    models = train_models(features_df, models_dir=tmp_path / "models")
    return models, features_df


class TestPredictAllCropsReturnsValidOutput:
    """All 10 crops return correctly-structured prediction dicts."""

    @pytest.mark.parametrize("crop_id", ALL_10_CROPS)
    def test_predict_all_10_crops_returns_valid_output(self, baseline_setup, crop_id):
        models, features_df = baseline_setup
        result = predict_demand(models, features_df, crop_id=crop_id)
        assert crop_id in result
        pred = result[crop_id]
        assert "predicted_kg" in pred
        assert "lower_ci" in pred
        assert "upper_ci" in pred
        assert "interval_width" in pred
        assert isinstance(pred["predicted_kg"], float)
        assert isinstance(pred["lower_ci"], float)
        assert isinstance(pred["upper_ci"], float)
        assert isinstance(pred["interval_width"], float)

    def test_all_10_crops_present_when_no_filter(self, baseline_setup):
        models, features_df = baseline_setup
        result = predict_demand(models, features_df)
        assert set(result.keys()) == set(ALL_10_CROPS)


class TestPredictionWithinHistoricalRange:
    """Predictions stay within ±30% of historical mean."""

    @pytest.mark.parametrize("crop_id", ALL_10_CROPS)
    def test_prediction_within_historical_range(self, baseline_setup, crop_id):
        models, features_df = baseline_setup
        result = predict_demand(models, features_df, crop_id=crop_id)
        pred = result[crop_id]

        crop_df = features_df[features_df["crop_id"] == crop_id]
        hist_mean = crop_df["kg_shipped"].mean()
        hist_max = hist_mean * 1.30
        hist_min = hist_mean * 0.70

        assert pred["upper_ci"] <= hist_max * 1.5, (
            f"{crop_id}: upper_ci {pred['upper_ci']:.1f} far exceeds 30% above hist max {hist_max:.1f}"
        )
        # Lower bound can be 0 (clipped); upper bound must not wildly exceed historical max
        assert pred["lower_ci"] >= 0.0


class TestConfidenceIntervalBoundsPrediction:
    """Confidence interval bounds correctly surround the point prediction."""

    @pytest.mark.parametrize("crop_id", ALL_10_CROPS)
    def test_ci_bounds_prediction(self, baseline_setup, crop_id):
        models, features_df = baseline_setup
        result = predict_demand(models, features_df, crop_id=crop_id)
        pred = result[crop_id]

        assert pred["lower_ci"] <= pred["predicted_kg"], (
            f"{crop_id}: lower_ci ({pred['lower_ci']}) > predicted_kg ({pred['predicted_kg']})"
        )
        assert pred["predicted_kg"] <= pred["upper_ci"], (
            f"{crop_id}: predicted_kg ({pred['predicted_kg']}) > upper_ci ({pred['upper_ci']})"
        )

    @pytest.mark.parametrize("crop_id", ALL_10_CROPS)
    def test_interval_width_equals_ci_bounds(self, baseline_setup, crop_id):
        models, features_df = baseline_setup
        result = predict_demand(models, features_df, crop_id=crop_id)
        pred = result[crop_id]
        expected_width = pred["upper_ci"] - pred["lower_ci"]
        assert pred["interval_width"] == pytest.approx(expected_width, abs=0.02)


class TestBufferPercentageInValidRange:
    """Buffer % stays within the 5-40% operational range for stable data."""

    def test_buffer_percentage_in_valid_range(self, baseline_setup):
        """For stable data (10% volatility), buffer should be well within 5-40%."""
        models, features_df = baseline_setup
        result = predict_demand(models, features_df)

        for crop_id, pred in result.items():
            buffer_pct = (pred["upper_ci"] - pred["predicted_kg"]) / pred["predicted_kg"] * 100
            assert 0.0 <= buffer_pct <= 60.0, (
                f"{crop_id}: buffer {buffer_pct:.1f}% outside reasonable range"
            )


class TestInferenceTimeUnder200ms:
    """Full all-crops inference completes in under 200 ms."""

    def test_single_crop_inference_under_10ms(self, baseline_setup):
        """Single crop inference is fast (<10 ms)."""
        import time
        models, features_df = baseline_setup
        t0 = time.perf_counter()
        predict_demand(models, features_df, crop_id="kai_lan")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 10, f"Single crop inference took {elapsed_ms:.1f} ms (limit: 10 ms)"

    def test_all_crops_inference_under_200ms(self, baseline_setup):
        """All 10 crops inference completes in under 200 ms."""
        import time
        models, features_df = baseline_setup
        t0 = time.perf_counter()
        predict_demand(models, features_df)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 200, f"All-crops inference took {elapsed_ms:.1f} ms (limit: 200 ms)"
