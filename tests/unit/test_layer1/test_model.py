"""Unit tests for Layer 1 XGBoost model training and loading."""

import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch

from greenloop.layer1.features import build_features
from greenloop.layer1.model import train_models, load_models


@pytest.fixture
def features_df():
    """Build a features DataFrame from synthetic shipments data."""
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
    return build_features(shipments)


@pytest.fixture
def models_dir(tmp_path):
    """Provide a temporary directory for model storage."""
    return tmp_path / "models"


class TestTrainModels:
    """Verify model training produces expected outputs."""

    def test_returns_dict_with_three_quantiles(self, features_df, models_dir):
        models = train_models(features_df, models_dir=models_dir)
        assert isinstance(models, dict)
        assert "q05" in models
        assert "q50" in models
        assert "q95" in models

    def test_saves_three_model_files(self, features_df, models_dir):
        train_models(features_df, models_dir=models_dir)
        json_files = list(models_dir.glob("*.json"))
        assert len(json_files) == 3, f"Expected 3 .json files, got {len(json_files)}: {json_files}"

    def test_saved_files_are_valid_xgboost(self, features_df, models_dir):
        """Saved .json files should be loadable by XGBoost."""
        train_models(features_df, models_dir=models_dir)
        loaded = load_models(models_dir=models_dir)
        assert len(loaded) == 3

    def test_models_can_predict(self, features_df, models_dir):
        """Each trained model should produce predictions."""
        models = train_models(features_df, models_dir=models_dir)
        feature_cols = [c for c in features_df.columns if c not in ("crop_id", "kg_shipped", "date")]
        X = features_df[feature_cols].values
        for name, model in models.items():
            preds = model.predict(X)
            assert len(preds) == len(X), f"Model {name} prediction length mismatch"
            assert not np.isnan(preds).any(), f"Model {name} produced NaN predictions"


class TestLoadModels:
    """Verify model loading."""

    def test_load_after_save(self, features_df, models_dir):
        original_models = train_models(features_df, models_dir=models_dir)
        loaded_models = load_models(models_dir=models_dir)
        assert set(loaded_models.keys()) == set(original_models.keys())

    def test_load_from_nonexistent_dir_raises(self, tmp_path):
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            load_models(models_dir=nonexistent)

    def test_load_from_empty_dir_raises(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            load_models(models_dir=empty_dir)

    def test_loaded_models_predict_same_as_original(self, features_df, models_dir):
        """Loaded models should produce identical predictions to originals."""
        original = train_models(features_df, models_dir=models_dir)
        loaded = load_models(models_dir=models_dir)
        feature_cols = [c for c in features_df.columns if c not in ("crop_id", "kg_shipped", "date")]
        X = features_df[feature_cols].values[:5]
        for key in original:
            orig_pred = original[key].predict(X)
            load_pred = loaded[key].predict(X)
            np.testing.assert_array_almost_equal(orig_pred, load_pred)


class TestTrainModelsEdgeCases:
    """Edge cases for training."""

    def test_empty_features_raises(self, models_dir):
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError):
            train_models(empty_df, models_dir=models_dir)

    def test_models_dir_created_if_missing(self, features_df, tmp_path):
        new_dir = tmp_path / "new" / "nested" / "models"
        train_models(features_df, models_dir=new_dir)
        assert new_dir.exists()
