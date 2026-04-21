"""Tests for ObjectiveWeights dataclass and mode presets."""

import pytest

from greenloop.layer2.objective import MODE_LABELS, ObjectiveWeights


class TestObjectiveWeightsDefaults:
    def test_defaults_are_balanced(self):
        w = ObjectiveWeights()
        assert w.revenue == 1.0
        assert w.electricity == 1.0
        assert w.labour == 1.0
        assert w.waste == 1.0
        assert w.balance == 1.0
        assert w.sustainability == 0.0

    def test_crop_weights_auto_filled(self):
        w = ObjectiveWeights()
        assert len(w.crop_weights) > 0
        for v in w.crop_weights.values():
            assert v == 1.0


class TestObjectiveWeightsFromMode:
    @pytest.mark.parametrize("mode", ["profit", "sustainability", "balanced"])
    def test_from_mode_returns_correct_type(self, mode):
        w = ObjectiveWeights.from_mode(mode)
        assert isinstance(w, ObjectiveWeights)

    def test_profit_mode_high_revenue(self):
        w = ObjectiveWeights.from_mode("profit")
        assert w.revenue == 1.5
        assert w.electricity == 1.0
        assert w.waste == 0.8
        assert w.balance == 0.5

    def test_sustainability_mode_low_electricity(self):
        w = ObjectiveWeights.from_mode("sustainability")
        assert w.electricity == 0.5
        assert w.revenue == 1.0
        assert w.sustainability == 2.0
        assert w.balance == 1.5

    def test_balanced_mode_equal_weights(self):
        w = ObjectiveWeights.from_mode("balanced")
        assert w.revenue == 1.0
        assert w.electricity == 1.0
        assert w.labour == 1.0
        assert w.waste == 1.0
        assert w.balance == 1.0
        assert w.sustainability == 1.0

    def test_unknown_mode_returns_balanced(self):
        w = ObjectiveWeights.from_mode("unknown")
        assert w.revenue == 1.0


class TestObjectiveWeightsCustom:
    def test_custom_weights_override_defaults(self):
        w = ObjectiveWeights(revenue=2.0, electricity=0.5)
        assert w.revenue == 2.0
        assert w.electricity == 0.5
        # Others stay at defaults
        assert w.labour == 1.0

    def test_custom_crop_weights(self):
        w = ObjectiveWeights(crop_weights={"kai_lan": 2.0, "lettuce": 0.5})
        assert w.crop_weights["kai_lan"] == 2.0
        assert w.crop_weights["lettuce"] == 0.5


class TestModeLabels:
    def test_mode_labels_has_three_entries(self):
        assert len(MODE_LABELS) == 3

    def test_mode_labels_values_are_labels(self):
        for k, v in MODE_LABELS.items():
            assert v == v.capitalize() or v in ("Profit", "Sustainability", "Balanced")
