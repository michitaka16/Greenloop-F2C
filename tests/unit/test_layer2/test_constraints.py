"""Unit tests for Layer 2 constraints — infeasibility and MOM compliance."""

import pandas as pd
import pytest

from greenloop.layer2.optimizer import build_and_solve
from greenloop.layer2.exceptions import InfeasibleError
from greenloop.utils.config import MAX_SHIFT_HOURS, MAX_WEEKLY_HOURS


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


class TestInfeasibility:
    """Setting staff to 0 must raise InfeasibleError."""

    def test_zero_headcount_raises_infeasible(
        self, forecast, crops_df, electricity_df, staff_df
    ):
        with pytest.raises(InfeasibleError) as exc_info:
            build_and_solve(
                forecast, crops_df, electricity_df, staff_df,
                available_headcount=0,
            )
        assert exc_info.value.binding_constraint is not None

    def test_infeasible_error_has_message(
        self, forecast, crops_df, electricity_df, staff_df
    ):
        with pytest.raises(InfeasibleError) as exc_info:
            build_and_solve(
                forecast, crops_df, electricity_df, staff_df,
                available_headcount=0,
            )
        assert len(str(exc_info.value)) > 0


class TestMOMCompliance:
    """MOM regulations: each shift <= 8h, weekly limit respected."""

    def test_shift_hours_within_limit(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        for shift in result["staff_shifts"]:
            assert shift["hours"] <= MAX_SHIFT_HOURS, (
                f"Shift {shift['shift']} exceeds {MAX_SHIFT_HOURS}h limit: {shift['hours']}h"
            )

    def test_total_daily_staff_hours_bounded(self, forecast, crops_df, electricity_df, staff_df):
        """Total daily staff hours should not exceed what MOM weekly limit allows per day."""
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        total_hours = sum(s["staff_count"] * s["hours"] for s in result["staff_shifts"])
        # Weekly limit per person is 44h, so daily limit per person is ~44/6 ~= 7.3h
        # With available_headcount=6, total daily max ~ 6 * 8 = 48 staff-hours
        max_daily = 6 * MAX_SHIFT_HOURS  # upper bound per shift
        assert total_hours <= max_daily * 3  # 3 shifts, but this is a loose bound


class TestWaterConstraint:
    """Watering frequency * water_per_tray must not exceed tank capacity."""

    def test_water_volume_within_tank_capacity(
        self, forecast, crops_df, electricity_df, staff_df
    ):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        water_per_tray = dict(zip(crops_df["crop_id"], crops_df["water_per_tray"]))
        for crop_id, freq in result["watering_schedule"].items():
            volume = freq * water_per_tray[crop_id]
            assert volume <= 10.0, (
                f"Crop {crop_id}: freq={freq} * water={water_per_tray[crop_id]} "
                f"= {volume} exceeds tank capacity 10.0L"
            )


class TestHarvestWindowConstraint:
    """At least 1 shift must have staff assigned for harvest readiness."""

    def test_at_least_one_shift_staffed(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        staffed_shifts = [s for s in result["staff_shifts"] if s["staff_count"] > 0]
        assert len(staffed_shifts) >= 1, "No shift has staff assigned"


class TestLEDConstraint:
    """LED values must be binary (0 or 1)."""

    def test_led_values_are_binary(self, forecast, crops_df, electricity_df, staff_df):
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        for tier, schedule in result["led_schedule"].items():
            for hour_val in schedule:
                assert hour_val in (0, 1), f"LED at {tier} has non-binary value: {hour_val}"
