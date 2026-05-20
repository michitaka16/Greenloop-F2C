"""Unit tests for Layer 2 scenarios — Typhoon and plan comparison."""

import pandas as pd
import pytest

from adoptakale.layer2.optimizer import build_and_solve
from adoptakale.layer2.scenarios import apply_typhoon, compare_plans
from adoptakale.utils.config import CROP_IDS


@pytest.fixture
def crops_df():
    """Load the real crops.csv so the fixture stays in lockstep with CROP_IDS."""
    from adoptakale.data.loader import load_crops

    return load_crops()


@pytest.fixture
def electricity_df():
    rows = []
    for hour in range(24):
        rate = 0.28 if 8 <= hour < 22 else 0.18
        rows.append({"date": "2025-10-15", "hour": hour, "tariff_rate_sgd_per_kwh": rate})
    return pd.DataFrame(rows)


@pytest.fixture
def staff_df():
    return pd.DataFrame({
        "staff_id": ["S001", "S002", "S003", "S004", "S005", "S006", "S007", "S008"],
        "name": ["Ahmad", "Wei Lin", "Priya", "Jun Hao", "Siti", "Ravi", "Mei Ying", "Ismail"],
        "availability": [
            "morning,afternoon", "morning,afternoon", "morning",
            "afternoon,night", "morning,afternoon,night", "night",
            "morning,afternoon", "afternoon,night",
        ],
        "hourly_rate_sgd": [12.5, 13.0, 14.0, 12.0, 15.0, 16.0, 11.5, 13.5],
    })


@pytest.fixture
def forecast():
    """Synthetic forecast for every crop in CROP_IDS."""
    return {
        cid: {"predicted_kg": 80.0, "lower_ci": 65.0, "upper_ci": 100.0}
        for cid in CROP_IDS
    }


@pytest.fixture
def base_kwargs(forecast, crops_df, electricity_df, staff_df):
    return {
        "forecast": forecast,
        "crops_df": crops_df,
        "electricity_df": electricity_df,
        "staff_df": staff_df,
        "delivery_hours": 12,
        "available_headcount": 6,
    }


class TestApplyTyphoon:
    """Typhoon scenario must modify kwargs and produce a different plan."""

    def test_typhoon_sets_delivery_hours_to_6(self, base_kwargs):
        modified = apply_typhoon(base_kwargs)
        assert modified["delivery_hours"] == 6

    def test_typhoon_plan_solves(self, base_kwargs):
        modified = apply_typhoon(base_kwargs)
        result = build_and_solve(**modified)
        assert isinstance(result, dict)
        assert "objective_value_sgd" in result

    def test_typhoon_does_not_mutate_original(self, base_kwargs):
        original_hours = base_kwargs["delivery_hours"]
        apply_typhoon(base_kwargs)
        assert base_kwargs["delivery_hours"] == original_hours


class TestComparePlans:
    """compare_plans must return a structured before/after comparison."""

    def test_compare_returns_dict(self, base_kwargs):
        plan_normal = build_and_solve(**base_kwargs)
        typhoon_kwargs = apply_typhoon(base_kwargs)
        plan_typhoon = build_and_solve(**typhoon_kwargs)
        comparison = compare_plans(plan_normal, plan_typhoon)
        assert isinstance(comparison, dict)

    def test_compare_has_before_after(self, base_kwargs):
        plan_normal = build_and_solve(**base_kwargs)
        typhoon_kwargs = apply_typhoon(base_kwargs)
        plan_typhoon = build_and_solve(**typhoon_kwargs)
        comparison = compare_plans(plan_normal, plan_typhoon)
        assert "before" in comparison
        assert "after" in comparison

    def test_compare_has_delta(self, base_kwargs):
        plan_normal = build_and_solve(**base_kwargs)
        typhoon_kwargs = apply_typhoon(base_kwargs)
        plan_typhoon = build_and_solve(**typhoon_kwargs)
        comparison = compare_plans(plan_normal, plan_typhoon)
        assert "delta" in comparison

    def test_compare_delta_has_objective_diff(self, base_kwargs):
        plan_normal = build_and_solve(**base_kwargs)
        typhoon_kwargs = apply_typhoon(base_kwargs)
        plan_typhoon = build_and_solve(**typhoon_kwargs)
        comparison = compare_plans(plan_normal, plan_typhoon)
        assert "objective_value_sgd" in comparison["delta"]

    def test_compare_identical_plans_zero_delta(self, base_kwargs):
        plan = build_and_solve(**base_kwargs)
        comparison = compare_plans(plan, plan)
        assert comparison["delta"]["objective_value_sgd"] == 0.0
