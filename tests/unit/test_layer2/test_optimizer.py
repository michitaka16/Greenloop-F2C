"""Unit tests for Layer 2 MILP optimizer — solver returns valid plan with all expected keys."""

import pandas as pd
import pytest

from greenloop.layer2.optimizer import build_and_solve
from greenloop.layer2.exceptions import InfeasibleError
from greenloop.utils.config import CROP_IDS


@pytest.fixture
def crops_df():
    return pd.DataFrame({
        "crop_id": ["kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim", "arugula"],
        "name": ["Kai Lan", "Baby Spinach", "Lettuce (Mambo)", "Japanese Chye Sim", "Arugula"],
        "growth_days": [35, 25, 30, 28, 21],
        "optimal_temp": [22.0, 20.0, 21.0, 22.0, 19.0],
        "water_per_tray": [2.5, 2.0, 2.2, 2.3, 1.8],
        "led_hours_per_day": [16, 14, 14, 15, 12],
        "price_sgd_per_kg": [4.5, 6.0, 3.8, 4.0, 8.0],
        "spoilage_rate": [0.06, 0.08, 0.07, 0.05, 0.04],
    })


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
    return {
        "kai_lan": {"predicted_kg": 120.5, "lower_ci": 100.0, "upper_ci": 141.0},
        "baby_spinach": {"predicted_kg": 95.0, "lower_ci": 80.0, "upper_ci": 110.0},
        "lettuce_mambo": {"predicted_kg": 88.0, "lower_ci": 70.0, "upper_ci": 106.0},
        "chye_sim": {"predicted_kg": 105.0, "lower_ci": 90.0, "upper_ci": 120.0},
        "arugula": {"predicted_kg": 72.0, "lower_ci": 60.0, "upper_ci": 84.0},
    }


class TestOptimizerReturnStructure:
    """Solver must return a plan dict with all expected keys and valid types."""

    def test_returns_dict(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        assert isinstance(result, dict)

    def test_has_all_required_keys(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        required_keys = {
            "plan_date", "objective_value_sgd", "solve_time_ms",
            "led_schedule", "staff_shifts", "rack_layout",
            "room_temp_target_c", "watering_schedule",
            "cost_breakdown", "uncertainty_buffers",
        }
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    def test_objective_value_is_numeric(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        assert isinstance(result["objective_value_sgd"], (int, float))

    def test_solve_time_positive(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        assert result["solve_time_ms"] >= 0

    def test_led_schedule_structure(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        led = result["led_schedule"]
        assert isinstance(led, dict)
        assert len(led) == 10  # 10 rack tiers
        for tier_key, schedule in led.items():
            assert tier_key.startswith("tier_")
            assert len(schedule) == 24  # 24 hours
            for val in schedule:
                assert val in (0, 1)  # binary on/off

    def test_staff_shifts_structure(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        shifts = result["staff_shifts"]
        assert isinstance(shifts, list)
        assert len(shifts) == 3  # 3 shifts
        for s in shifts:
            assert "shift" in s
            assert "staff_count" in s
            assert "hours" in s
            assert s["shift"] in ("morning", "afternoon", "night")
            assert 0 <= s["staff_count"] <= 6
            assert s["hours"] <= 8

    def test_rack_layout_assigns_all_tiers(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        layout = result["rack_layout"]
        assert isinstance(layout, dict)
        assert len(layout) == 10
        for tier_key, crop_id in layout.items():
            assert tier_key.startswith("tier_")
            assert crop_id in CROP_IDS

    def test_room_temp_within_bounds(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        temp = result["room_temp_target_c"]
        assert 18 <= temp <= 26

    def test_watering_schedule_structure(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        watering = result["watering_schedule"]
        assert isinstance(watering, dict)
        for crop_id, freq in watering.items():
            assert crop_id in CROP_IDS
            assert 1 <= freq <= 4

    def test_cost_breakdown_has_components(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        breakdown = result["cost_breakdown"]
        assert "revenue" in breakdown
        assert "electricity" in breakdown
        assert "labour" in breakdown
        assert "waste_penalty" in breakdown
        assert breakdown["revenue"] > 0
        assert breakdown["electricity"] <= 0
        assert breakdown["labour"] <= 0
        assert breakdown["waste_penalty"] <= 0

    def test_uncertainty_buffers_present(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        buffers = result["uncertainty_buffers"]
        assert isinstance(buffers, dict)
        for crop_id in CROP_IDS:
            assert crop_id in buffers
            assert "upper_ci" in buffers[crop_id]
            assert "buffer_pct" in buffers[crop_id]

    def test_each_tier_assigned_exactly_one_crop(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        layout = result["rack_layout"]
        # Each tier has exactly one crop
        assert all(isinstance(v, str) for v in layout.values())

    def test_tariff_override(self, forecast, crops_df, electricity_df, staff_df):
        """Custom tariff_rate should affect the electricity cost."""
        plan_default = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        plan_high = build_and_solve(
            forecast, crops_df, electricity_df, staff_df, tariff_rate=0.50
        )
        # Higher tariff should lead to equal or higher electricity cost (more negative)
        assert plan_high["cost_breakdown"]["electricity"] <= plan_default["cost_breakdown"]["electricity"]
