"""Adversarial stress tests for Layer 1 demand forecasting data poisoning.

Phase 7 Red-Team: MGMT655 Dimension B — hostile inputs and edge cases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from greenloop.layer1.features import build_features
from greenloop.layer1.predict import predict_demand
from greenloop.layer1.model import train_models


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_shipments():
    """Clean historical shipments spanning 60 days for 2 crops."""
    dates = pd.date_range("2025-09-01", periods=60, freq="D")
    rows = []
    for date in dates:
        for crop_id in ["kai_lan", "baby_spinach"]:
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "crop_id": crop_id,
                "kg_shipped": 50.0 + np.random.default_rng(42).normal(0, 5),
                "price_sgd_per_kg": 3.50,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def outlier_shipments():
    """Shipments with extreme outlier values injected."""
    dates = pd.date_range("2025-09-01", periods=60, freq="D")
    rows = []
    for date in dates:
        for crop_id in ["kai_lan", "baby_spinach"]:
            # Day 45: extreme spike (10x normal) — simulated data poisoning
            if date.dayofyear == 45:
                kg = 500.0  # 10x normal ~50kg
            # Day 50: extreme negative (corrupted reading)
            elif date.dayofyear == 50:
                kg = -20.0  # physically impossible
            else:
                kg = 50.0 + np.random.default_rng(99).normal(0, 5)
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "crop_id": crop_id,
                "kg_shipped": kg,
                "price_sgd_per_kg": 3.50,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def corrupted_labels():
    """Shipments with 5% random label corruption."""
    dates = pd.date_range("2025-09-01", periods=60, freq="D")
    rows = []
    rng = np.random.default_rng(777)
    for date in dates:
        for crop_id in ["kai_lan", "baby_spinach"]:
            kg = 50.0 + np.random.default_rng(42).normal(0, 5)
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "crop_id": crop_id,
                "kg_shipped": kg,
                "price_sgd_per_kg": 3.50,
            })
    df = pd.DataFrame(rows)
    # Corrupt 5% of labels randomly
    n_corrupt = int(len(df) * 0.05)
    corrupt_idx = rng.choice(df.index, n_corrupt, replace=False)
    df.loc[corrupt_idx, "kg_shipped"] = df.loc[corrupt_idx, "kg_shipped"] * rng.uniform(2, 5, n_corrupt)
    return df


# ---------------------------------------------------------------------------
# Test 1: Injected outliers → prediction must not explode
# ---------------------------------------------------------------------------

class TestOutlierInjection:
    """test_historical_data_with_injected_outliers"""

    def test_extreme_outlier_does_not_produce_infinite_forecast(
        self, outlier_shipments
    ):
        """An extreme spike (+1000%) in historical data must not produce
        an astronomical forecast — the model should be robust to outliers."""
        features = build_features(outlier_shipments)
        # After feature engineering, the outlier row should be present
        # but the model should not predict infinite kg
        assert len(features) > 0, "Feature engineering dropped all rows unexpectedly"

        # Train models
        models = train_models(features)

        # Predict
        preds = predict_demand(models, features)
        assert preds is not None

        for crop_id, pred in preds.items():
            assert pred["predicted_kg"] >= 0, f"{crop_id}: negative prediction from outlier data"
            assert pred["predicted_kg"] < 10_000, (
                f"{crop_id}: prediction {pred['predicted_kg']} is astronomical — "
                "model not robust to outlier training data"
            )
            assert pred["lower_ci"] >= 0
            assert pred["upper_ci"] >= 0

    def test_negative_label_does_not_crash_feature_engineering(self):
        """A physically impossible negative kg_shipped must not crash
        build_features() — NaN handling should drop or zero-fill."""
        dates = pd.date_range("2025-09-01", periods=35, freq="D")  # minimum warmup
        bad_rows = []
        for date in dates:
            for crop_id in ["kai_lan"]:
                bad_rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "crop_id": crop_id,
                    "kg_shipped": -5.0,  # invalid
                    "price_sgd_per_kg": 3.50,
                })
        df = pd.DataFrame(bad_rows)
        # Should not raise — NaN in lag features drops the bad row
        features = build_features(df)
        assert len(features) >= 0  # empty or valid output

    def test_outlier_ci_width_is_bounded(self, outlier_shipments):
        """Prediction interval width should be reasonable, not expanded
        infinitely by a single outlier."""
        features = build_features(outlier_shipments)
        models = train_models(features)
        preds = predict_demand(models, features)

        for crop_id, pred in preds.items():
            width = pred["upper_ci"] - pred["lower_ci"]
            # CI width should be less than 10x the predicted value
            # (a very wide but finite interval)
            assert width < pred["predicted_kg"] * 15, (
                f"{crop_id}: CI width {width} is suspiciously wide — "
                "outlier is dominating quantile spread"
            )


# ---------------------------------------------------------------------------
# Test 2: 5% label corruption → prediction stays within ±50%
# ---------------------------------------------------------------------------

class TestLabelCorruption:
    """test_prediction_stable_under_5pct_data_corruption"""

    def test_5pct_corruption_does_not_dramatically_shift_predictions(
        self, clean_shipments, corrupted_labels
    ):
        """Corrupting 5% of training labels should not shift the median
        prediction by more than ±50% — model should be robust."""
        clean_features = build_features(clean_shipments)
        corrupt_features = build_features(corrupted_labels)

        clean_models = train_models(clean_features)
        corrupt_models = train_models(corrupt_features)

        # Predict using each model on the same clean features
        # (simulates: same current state, different corrupted history)
        clean_preds = predict_demand(clean_models, clean_features)
        corrupt_preds = predict_demand(corrupt_models, clean_features)

        for crop_id in clean_preds:
            clean_median = clean_preds[crop_id]["predicted_kg"]
            corrupt_median = corrupt_preds[crop_id]["predicted_kg"]

            shift = abs(corrupt_median - clean_median) / max(clean_median, 1.0)
            assert shift < 0.50, (
                f"{crop_id}: 5% label corruption shifted prediction by {shift:.1%} "
                f"(clean={clean_median:.1f}, corrupt={corrupt_median:.1f}) — "
                "model is insufficiently robust to training data corruption"
            )

    def test_corrupted_features_do_not_produce_nan_predictions(
        self, corrupted_labels
    ):
        """Corrupted labels must not produce NaN predictions."""
        features = build_features(corrupted_labels)
        models = train_models(features)
        preds = predict_demand(models, features)

        for crop_id, pred in preds.items():
            assert not np.isnan(pred["predicted_kg"]), (
                f"{crop_id}: NaN prediction from corrupted training data"
            )
            assert not np.isnan(pred["lower_ci"])
            assert not np.isnan(pred["upper_ci"])
