"""Integration tests for manual constraints (excluded racks, unavailable shifts)."""

import pandas as pd
import pytest

from adoptakale.layer2.exceptions import InfeasibleError
from adoptakale.layer2.optimizer import build_and_solve
from adoptakale.utils.config import CROP_IDS, SHIFTS


@pytest.fixture
def base_data():
    """Shared base data for constraint tests."""
    rows = []
    for hour in range(24):
        rate = 0.28 if 8 <= hour < 22 else 0.18
        rows.append({"date": "2025-10-15", "hour": hour, "tariff_rate_sgd_per_kwh": rate})
    electricity_df = pd.DataFrame(rows)

    staff_df = pd.DataFrame({
        "staff_id": [f"S{i:03d}" for i in range(1, 9)],
        "name": [f"Staff{i}" for i in range(1, 9)],
        "availability": [
            "morning,afternoon", "morning,afternoon", "morning",
            "afternoon,night", "morning,afternoon,night", "night",
            "morning,afternoon", "afternoon,night",
        ],
        "hourly_rate_sgd": [12.5, 13.0, 14.0, 12.0, 15.0, 16.0, 11.5, 13.5],
    })

    forecast = {cid: {"predicted_kg": 80.0, "lower_ci": 65.0, "upper_ci": 100.0} for cid in CROP_IDS}
    return electricity_df, staff_df, forecast


@pytest.fixture
def crops_df():
    from adoptakale.data.loader import load_crops
    return load_crops()


class TestExcludedRacks:
    """Excluding racks via HITL override."""

    def test_exclude_one_rack_succeeds(self, base_data, crops_df):
        electricity_df, staff_df, forecast = base_data
        plan = build_and_solve(
            forecast, crops_df, electricity_df, staff_df,
            excluded_racks=[0],
        )
        assert plan is not None
        # Rack 0 should not appear in the layout
        assert "tier_0" not in plan["rack_layout"]
        # Other racks should still be assigned
        assert len(plan["rack_layout"]) == 10 - 1  # 1 tier excluded

    def test_excluded_racks_in_result_dict(self, base_data, crops_df):
        electricity_df, staff_df, forecast = base_data
        plan = build_and_solve(forecast, crops_df, electricity_df, staff_df, excluded_racks=[3, 7])
        assert plan["excluded_racks"] == [3, 7]

    def test_exclude_all_tiers_infeasible(self, base_data, crops_df):
        electricity_df, staff_df, forecast = base_data
        with pytest.raises(InfeasibleError):
            build_and_solve(
                forecast, crops_df, electricity_df, staff_df,
                excluded_racks=list(range(10)),
            )


class TestUnavailableShifts:
    """Marking shifts as unavailable via HITL override."""

    def test_one_shift_unavailable_succeeds(self, base_data, crops_df):
        electricity_df, staff_df, forecast = base_data
        plan = build_and_solve(
            forecast, crops_df, electricity_df, staff_df,
            unavailable_shifts=["night"],
        )
        assert plan is not None
        # Night shift should have 0 staff
        night_shifts = [s for s in plan["staff_shifts"] if s["shift"] == "night"]
        assert all(s["staff_count"] == 0 for s in night_shifts)

    def test_unavailable_shifts_in_result_dict(self, base_data, crops_df):
        electricity_df, staff_df, forecast = base_data
        plan = build_and_solve(
            forecast, crops_df, electricity_df, staff_df,
            unavailable_shifts=["morning", "afternoon"],
        )
        assert "morning" in plan["unavailable_shifts"]
        assert "afternoon" in plan["unavailable_shifts"]


class TestCombinedConstraints:
    """Excluded racks + unavailable shifts together."""

    def test_both_constraints_succeed(self, base_data, crops_df):
        electricity_df, staff_df, forecast = base_data
        plan = build_and_solve(
            forecast, crops_df, electricity_df, staff_df,
            excluded_racks=[0, 1],
            unavailable_shifts=["night"],
        )
        assert plan is not None
        assert plan["excluded_racks"] == [0, 1]
        assert plan["unavailable_shifts"] == ["night"]
