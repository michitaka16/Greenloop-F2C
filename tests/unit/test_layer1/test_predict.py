"""Unit tests for Layer 1 demand prediction."""

import numpy as np
import pandas as pd
import pytest

from adoptakale.layer1.features import build_features
from adoptakale.layer1.model import train_models
from adoptakale.layer1.predict import predict_demand


@pytest.fixture
def trained_setup(tmp_path):
    """Build features, train models, return (models, features_df)."""
    dates = pd.date_range("2025-10-01", periods=90, freq="D")
    crops = ["kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim", "arugula"]
    rows = []
    rng = np.random.default_rng(42)
    for d in dates:
        for c in crops:
            rows.append({
                "date": d,
                "crop_id": c,
                "kg_shipped": rng.uniform(10, 60),
                "price_sgd_per_kg": rng.uniform(3, 8),
            })
    shipments = pd.DataFrame(rows)
    features_df = build_features(shipments)
    models_dir = tmp_path / "models"
    models = train_models(features_df, models_dir=models_dir)
    return models, features_df


class TestPredictDemand:
    """Verify prediction output structure and values."""

    def test_returns_dict(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        assert isinstance(result, dict)

    def test_all_crops_present(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        expected_crops = {"kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim", "arugula"}
        assert set(result.keys()) == expected_crops

    def test_prediction_keys(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        for crop_id, pred in result.items():
            assert "predicted_kg" in pred, f"Missing predicted_kg for {crop_id}"
            assert "lower_ci" in pred, f"Missing lower_ci for {crop_id}"
            assert "upper_ci" in pred, f"Missing upper_ci for {crop_id}"
            assert "interval_width" in pred, f"Missing interval_width for {crop_id}"

    def test_quantile_ordering(self, trained_setup):
        """lower_ci <= predicted_kg <= upper_ci must hold after crossing fix."""
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        for crop_id, pred in result.items():
            assert pred["lower_ci"] <= pred["predicted_kg"], (
                f"{crop_id}: lower_ci ({pred['lower_ci']}) > predicted_kg ({pred['predicted_kg']})"
            )
            assert pred["predicted_kg"] <= pred["upper_ci"], (
                f"{crop_id}: predicted_kg ({pred['predicted_kg']}) > upper_ci ({pred['upper_ci']})"
            )

    def test_interval_width_is_positive(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        for crop_id, pred in result.items():
            assert pred["interval_width"] >= 0, (
                f"{crop_id}: negative interval_width: {pred['interval_width']}"
            )

    def test_interval_width_equals_upper_minus_lower(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        for crop_id, pred in result.items():
            expected_width = pred["upper_ci"] - pred["lower_ci"]
            assert pred["interval_width"] == pytest.approx(expected_width, abs=0.02)

    def test_predictions_are_positive(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        for crop_id, pred in result.items():
            assert pred["predicted_kg"] > 0, f"{crop_id}: non-positive prediction"


class TestPredictSingleCrop:
    """Verify filtering by crop_id."""

    def test_single_crop_returns_one_entry(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df, crop_id="kai_lan")
        assert set(result.keys()) == {"kai_lan"}

    def test_single_crop_has_all_fields(self, trained_setup):
        models, features_df = trained_setup
        result = predict_demand(models, features_df, crop_id="arugula")
        pred = result["arugula"]
        assert "predicted_kg" in pred
        assert "lower_ci" in pred
        assert "upper_ci" in pred
        assert "interval_width" in pred

    def test_invalid_crop_raises(self, trained_setup):
        models, features_df = trained_setup
        with pytest.raises(ValueError, match="crop_id"):
            predict_demand(models, features_df, crop_id="nonexistent_crop")


class TestQuantileCrossingFix:
    """Verify that quantile crossing is handled correctly."""

    def test_crossing_fix_sorts_values(self, trained_setup):
        """Even if raw quantile predictions cross, the output must be sorted."""
        models, features_df = trained_setup
        result = predict_demand(models, features_df)
        for crop_id, pred in result.items():
            values = [pred["lower_ci"], pred["predicted_kg"], pred["upper_ci"]]
            assert values == sorted(values), (
                f"{crop_id}: values not sorted after crossing fix: {values}"
            )
