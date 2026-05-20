"""Unit tests for Layer 1 feature engineering."""

import numpy as np
import pandas as pd
import pytest

from adoptakale.layer1.features import build_features


@pytest.fixture
def sample_shipments():
    """Create a minimal shipments DataFrame spanning enough days for lag features."""
    dates = pd.date_range("2025-10-01", periods=60, freq="D")
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
    return pd.DataFrame(rows)


@pytest.fixture
def real_shipments():
    """Load the actual shipments.csv from the data directory."""
    from adoptakale.data.loader import load_shipments
    return load_shipments()


class TestBuildFeaturesColumns:
    """Verify that build_features produces the expected feature columns."""

    def test_has_target_column(self, sample_shipments):
        result = build_features(sample_shipments)
        assert "kg_shipped" in result.columns

    def test_has_lag_features(self, sample_shipments):
        result = build_features(sample_shipments)
        for lag in ["lag_7d", "lag_14d", "lag_28d"]:
            assert lag in result.columns, f"Missing lag feature: {lag}"

    def test_has_rolling_features(self, sample_shipments):
        result = build_features(sample_shipments)
        assert "rolling_mean_28d" in result.columns
        assert "rolling_std_28d" in result.columns

    def test_has_cyclical_week_encoding(self, sample_shipments):
        result = build_features(sample_shipments)
        assert "week_sin" in result.columns
        assert "week_cos" in result.columns

    def test_has_day_of_week(self, sample_shipments):
        result = build_features(sample_shipments)
        assert "day_of_week" in result.columns

    def test_has_holiday_flag(self, sample_shipments):
        result = build_features(sample_shipments)
        assert "is_holiday" in result.columns

    def test_has_price_feature(self, sample_shipments):
        result = build_features(sample_shipments)
        assert "price_sgd_per_kg" in result.columns

    def test_has_crop_id(self, sample_shipments):
        result = build_features(sample_shipments)
        assert "crop_id" in result.columns


class TestBuildFeaturesValues:
    """Verify correctness of feature values."""

    def test_no_nan_after_build(self, sample_shipments):
        """After dropping initial rows that lack lag history, no NaN should remain."""
        result = build_features(sample_shipments)
        feature_cols = [c for c in result.columns if c != "crop_id"]
        assert not result[feature_cols].isna().any().any(), (
            f"NaN found in columns: {result[feature_cols].columns[result[feature_cols].isna().any()].tolist()}"
        )

    def test_day_of_week_range(self, sample_shipments):
        result = build_features(sample_shipments)
        assert result["day_of_week"].min() >= 0
        assert result["day_of_week"].max() <= 6

    def test_cyclical_encoding_bounded(self, sample_shipments):
        result = build_features(sample_shipments)
        assert result["week_sin"].between(-1, 1).all()
        assert result["week_cos"].between(-1, 1).all()

    def test_holiday_flag_is_binary(self, sample_shipments):
        result = build_features(sample_shipments)
        assert set(result["is_holiday"].unique()).issubset({0, 1})

    def test_lag_values_are_correct(self, sample_shipments):
        """Verify lag_7d is actually the value from 7 days prior for the same crop."""
        result = build_features(sample_shipments)
        crop_df = result[result["crop_id"] == "kai_lan"].sort_values("date").reset_index(drop=True)
        # Find a row that has lag_7d set and verify it matches the value from 7 rows prior
        # (since data is daily per crop, row i-7 is 7 days prior)
        if len(crop_df) > 7:
            for i in range(7, min(15, len(crop_df))):
                expected = crop_df.loc[i - 7, "kg_shipped"]
                actual = crop_df.loc[i, "lag_7d"]
                assert actual == pytest.approx(expected), (
                    f"lag_7d mismatch at row {i}: expected {expected}, got {actual}"
                )

    def test_rows_reduced_by_warmup(self, sample_shipments):
        """Building features should drop rows without enough lag history."""
        result = build_features(sample_shipments)
        # With 28-day lag, at least 28 days of warmup are needed per crop
        # Original: 60 days * 5 crops = 300 rows
        # After dropping warmup: should be fewer rows
        assert len(result) < len(sample_shipments)
        assert len(result) > 0


class TestBuildFeaturesWithRealData:
    """Verify build_features works with the actual shipments.csv."""

    def test_real_data_produces_valid_features(self, real_shipments):
        result = build_features(real_shipments)
        assert len(result) > 0
        feature_cols = [c for c in result.columns if c != "crop_id"]
        assert not result[feature_cols].isna().any().any()

    def test_real_data_all_crops_present(self, real_shipments):
        """Every crop in the live CROP_IDS list must survive feature engineering.

        Rows get dropped during warmup (first 28 days per crop), so a crop
        with <28 days of history would disappear. This test is the gate
        catching that class of regression.
        """
        from adoptakale.utils.config import CROP_IDS

        result = build_features(real_shipments)
        assert set(result["crop_id"].unique()) == set(CROP_IDS)


class TestBuildFeaturesEdgeCases:
    """Edge case handling."""

    def test_empty_dataframe_raises(self):
        empty = pd.DataFrame(columns=["date", "crop_id", "kg_shipped", "price_sgd_per_kg"])
        with pytest.raises(ValueError, match="shipments"):
            build_features(empty)

    def test_missing_column_raises(self):
        bad = pd.DataFrame({"date": [pd.Timestamp("2025-10-01")], "crop_id": ["kai_lan"]})
        with pytest.raises(ValueError, match="kg_shipped"):
            build_features(bad)
