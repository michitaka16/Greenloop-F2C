"""Scenario tests for Typhoon v2 expansion."""

import numpy as np
import pandas as pd
import pytest

from adoptakale.layer1.features import build_features
from adoptakale.layer1.model import train_models
from adoptakale.layer1.predict import predict_demand
from adoptakale.layer2.optimizer import build_and_solve
from adoptakale.layer2.scenarios import (
    TyphoonScenarioInput,
    apply_typhoon,
    compare_plans,
)
from adoptakale.data.loader import load_crops, load_electricity, load_staff


def _make_base_kwargs(forecast, crops, electricity, staff):
    return dict(
        forecast=forecast,
        crops_df=crops,
        electricity_df=electricity,
        staff_df=staff,
        available_headcount=6,
    )


class TestTyphoonScenarioInput:
    """TyphoonScenarioInput dataclass with all v2 parameters."""

    def test_typhoon_scenario_input_defaults(self):
        """Default scenario has expected values."""
        scenario = TyphoonScenarioInput()
        assert scenario.delivery_hours == 6
        assert scenario.power_outage_probability == 0.3
        assert scenario.ups_countdown_hours == 4
        assert scenario.emergency_harvest is False
        assert scenario.demand_multiplier == 1.2
        assert scenario.cold_storage_switch is False
        assert scenario.staff_reduced_pct == 30

    def test_typhoon_scenario_input_custom(self):
        """Custom scenario overrides defaults."""
        scenario = TyphoonScenarioInput(
            delivery_hours=8,
            power_outage_probability=0.5,
            ups_countdown_hours=6,
            demand_multiplier=1.5,
        )
        assert scenario.delivery_hours == 8
        assert scenario.power_outage_probability == 0.5
        assert scenario.ups_countdown_hours == 6
        assert scenario.demand_multiplier == 1.5


class TestApplyTyphoon:
    """apply_typhoon applies scenario parameters correctly."""

    def test_apply_typhoon_sets_delivery_hours(self):
        """apply_typhoon sets delivery_hours=6 in returned kwargs."""
        scenario = TyphoonScenarioInput(delivery_hours=6)
        base = _make_base_kwargs({}, load_crops(), load_electricity(), load_staff())
        result = apply_typhoon(base, scenario)
        assert result["delivery_hours"] == 6

    def test_apply_typhoon_sets_power_outage_true(self):
        """apply_typhoon sets power_outage=True in returned kwargs."""
        scenario = TyphoonScenarioInput()
        base = _make_base_kwargs({}, load_crops(), load_electricity(), load_staff())
        result = apply_typhoon(base, scenario)
        assert result["power_outage"] is True

    def test_apply_typhoon_applies_demand_multiplier(self):
        """apply_typhoon scales upper_ci by demand_multiplier."""
        scenario = TyphoonScenarioInput(demand_multiplier=1.2)
        forecast = {
            "kai_lan": {"upper_ci": 100.0, "predicted_kg": 50.0, "lower_ci": 30.0},
        }
        base = _make_base_kwargs(forecast, load_crops(), load_electricity(), load_staff())
        result = apply_typhoon(base, scenario)
        assert result["forecast"]["kai_lan"]["upper_ci"] == 120.0  # 100 * 1.2

    def test_apply_typhoon_does_not_mutate_base(self):
        """apply_typhoon returns new dict, does not mutate base."""
        scenario = TyphoonScenarioInput(delivery_hours=6)
        base = _make_base_kwargs({}, load_crops(), load_electricity(), load_staff())
        original_delivery = base.get("delivery_hours", 12)
        result = apply_typhoon(base, scenario)
        assert base.get("delivery_hours", 12) == original_delivery
        assert result["delivery_hours"] == 6

    def test_apply_typhoon_none_scenario_uses_defaults(self):
        """apply_typhoon with None scenario uses TyphoonScenarioInput() defaults."""
        base = _make_base_kwargs({}, load_crops(), load_electricity(), load_staff())
        result = apply_typhoon(base, None)
        assert result["delivery_hours"] == 6
        assert result["power_outage"] is True


class TestPowerOutageOptimizer:
    """Layer 2 optimizer handles power_outage parameter."""

    def test_build_and_solve_accepts_power_outage_param(self, tmp_path):
        """build_and_solve accepts power_outage=False without error."""
        rng = np.random.default_rng(42)
        dates = pd.date_range("2025-10-01", periods=60, freq="D")
        rows = []
        for d in dates:
            rows.append({"date": d, "crop_id": "kai_lan", "kg_shipped": rng.normal(30.0, 5.0), "price_sgd_per_kg": 5.0})
        shipments = pd.DataFrame(rows)
        features = build_features(shipments)
        models = train_models(features, models_dir=tmp_path / "models")
        forecast = predict_demand(models, features)

        electricity = load_electricity()
        crops = load_crops()
        staff = load_staff()

        # Complete forecast for all crops (optimizer requires all 10)
        all_crops = ["kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim", "arugula",
                     "pak_choi", "kale", "basil_thai", "coriander", "mint"]
        for crop_id in all_crops:
            if crop_id not in forecast:
                forecast[crop_id] = {"upper_ci": 50.0, "predicted_kg": 40.0, "lower_ci": 30.0}

        # Should not raise
        plan = build_and_solve(
            forecast=forecast,
            crops_df=crops,
            electricity_df=electricity,
            staff_df=staff,
            available_headcount=6,
            power_outage=False,
        )
        assert "objective_value_sgd" in plan

    def test_power_outage_in_plan_dict(self, tmp_path):
        """When power_outage=True, plan dict contains power_outage key."""
        rng = np.random.default_rng(42)
        dates = pd.date_range("2025-10-01", periods=60, freq="D")
        rows = []
        for d in dates:
            rows.append({"date": d, "crop_id": "kai_lan", "kg_shipped": rng.normal(30.0, 5.0), "price_sgd_per_kg": 5.0})
        shipments = pd.DataFrame(rows)
        features = build_features(shipments)
        models = train_models(features, models_dir=tmp_path / "models")
        forecast = predict_demand(models, features)

        electricity = load_electricity()
        crops = load_crops()
        staff = load_staff()

        # Complete forecast for all crops (optimizer requires all 10)
        all_crops = ["kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim", "arugula",
                     "pak_choi", "kale", "basil_thai", "coriander", "mint"]
        for crop_id in all_crops:
            if crop_id not in forecast:
                forecast[crop_id] = {"upper_ci": 50.0, "predicted_kg": 40.0, "lower_ci": 30.0}

        plan = build_and_solve(
            forecast=forecast,
            crops_df=crops,
            electricity_df=electricity,
            staff_df=staff,
            available_headcount=6,
            power_outage=True,
        )
        assert "power_outage" in plan


class TestComparePlans:
    """compare_plans works correctly with Typhoon plan comparison."""

    def test_compare_plans_returns_delta(self):
        """compare_plans returns a dict with before/after/delta."""
        plan_a = {
            "objective_value_sgd": 1000.0,
            "cost_breakdown": {"revenue": 1000.0, "electricity": 100.0, "labour": 50.0, "waste_penalty": 10.0},
            "room_temp_target_c": 22,
            "staff_shifts": [{"shift": "morning", "staff_count": 2}],
        }
        plan_b = {
            "objective_value_sgd": 800.0,
            "cost_breakdown": {"revenue": 900.0, "electricity": 100.0, "labour": 50.0, "waste_penalty": 10.0},
            "room_temp_target_c": 24,
            "staff_shifts": [{"shift": "morning", "staff_count": 1}],
        }
        result = compare_plans(plan_a, plan_b)
        assert "before" in result
        assert "after" in result
        assert "delta" in result
        assert result["delta"]["objective_value_sgd"] == -200.0
