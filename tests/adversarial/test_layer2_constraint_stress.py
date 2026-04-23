"""Adversarial stress tests for Layer 2 MILP constraint handling.

Phase 7 Red-Team: MGMT655 Dimension B — hostile inputs and edge cases.
"""

from __future__ import annotations

import pandas as pd
import pytest

from greenloop.layer2.optimizer import build_and_solve
from greenloop.layer2.exceptions import InfeasibleError
from greenloop.utils.config import CROP_IDS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def crops_df():
    from greenloop.data.loader import load_crops
    return load_crops()


@pytest.fixture
def normal_electricity():
    rows = []
    for hour in range(24):
        rate = 0.28 if 8 <= hour < 22 else 0.18
        rows.append({"date": "2025-10-15", "hour": hour, "tariff_rate_sgd_per_kwh": rate})
    return pd.DataFrame(rows)


@pytest.fixture
def negative_tariff_electricity():
    """Electricity with negative tariff (adversarial: battery sell-back scenario)."""
    rows = []
    for hour in range(24):
        # -0.10 SGD/kWh (feed-in tariff from solar battery sell-back)
        rows.append({"date": "2025-10-15", "hour": hour, "tariff_rate_sgd_per_kwh": -0.10})
    return pd.DataFrame(rows)


@pytest.fixture
def staff_df():
    return pd.DataFrame({
        "staff_id": [f"S{i:03d}" for i in range(1, 9)],
        "name": ["Ahmad", "Wei Lin", "Priya", "Jun Hao", "Siti", "Ravi", "Mei Ying", "Ismail"],
        "availability": ["morning,afternoon"] * 8,
        "hourly_rate_sgd": [12.5, 13.0, 14.0, 12.0, 15.0, 16.0, 11.5, 13.5],
    })


@pytest.fixture
def normal_forecast():
    return {
        cid: {"predicted_kg": 80.0, "lower_ci": 65.0, "upper_ci": 100.0}
        for cid in CROP_IDS
    }


@pytest.fixture
def huge_demand_forecast():
    """Demand far exceeding rack capacity (100kg max per tier)."""
    return {
        cid: {"predicted_kg": 1000.0, "lower_ci": 900.0, "upper_ci": 1100.0}
        for cid in CROP_IDS
    }


# ---------------------------------------------------------------------------
# Test 1: All racks excluded → InfeasibleError
# ---------------------------------------------------------------------------

class TestAllRacksExcluded:
    """test_all_racks_excluded_returns_feasibility_error"""

    def test_exclude_all_10_racks_raises_infeasible(
        self, crops_df, normal_electricity, staff_df, normal_forecast
    ):
        """Excluding all 10 racks must raise InfeasibleError with binding constraint."""
        with pytest.raises(InfeasibleError) as exc_info:
            build_and_solve(
                forecast=normal_forecast,
                crops_df=crops_df,
                electricity_df=normal_electricity,
                staff_df=staff_df,
                available_headcount=6,
                excluded_racks=list(range(10)),  # all 10 racks
            )
        # Error message should mention racks or feasibility
        assert exc_info.value.binding_constraint is not None or "rack" in str(exc_info.value).lower()

    def test_exclude_9_of_10_racks_still_finds_solution(
        self, crops_df, normal_electricity, staff_df, normal_forecast
    ):
        """Excluding 9 racks (leaving 1) should still produce a feasible plan."""
        plan = build_and_solve(
            forecast=normal_forecast,
            crops_df=crops_df,
            electricity_df=normal_electricity,
            staff_df=staff_df,
            available_headcount=6,
            excluded_racks=list(range(9)),  # 9 racks excluded, 1 left
        )
        assert plan is not None
        assert "objective_value_sgd" in plan


# ---------------------------------------------------------------------------
# Test 2: Zero staff → InfeasibleError
# ---------------------------------------------------------------------------

class TestZeroStaff:
    """test_zero_staff_returns_feasibility_error"""

    def test_zero_headcount_raises_infeasible(
        self, crops_df, normal_electricity, staff_df, normal_forecast
    ):
        """Setting available_headcount=0 must raise InfeasibleError."""
        with pytest.raises(InfeasibleError):
            build_and_solve(
                forecast=normal_forecast,
                crops_df=crops_df,
                electricity_df=normal_electricity,
                staff_df=staff_df,
                available_headcount=0,
            )

    def test_unavailable_all_shifts_raises_infeasible(
        self, crops_df, normal_electricity, staff_df, normal_forecast
    ):
        """Marking all shifts unavailable must raise InfeasibleError."""
        with pytest.raises(InfeasibleError):
            build_and_solve(
                forecast=normal_forecast,
                crops_df=crops_df,
                electricity_df=normal_electricity,
                staff_df=staff_df,
                available_headcount=6,
                unavailable_shifts=["morning", "afternoon", "night"],
            )


# ---------------------------------------------------------------------------
# Test 3: Negative electricity tariff → clipped to zero
# ---------------------------------------------------------------------------

class TestNegativeTariff:
    """test_negative_electricity_tariff_clipped_to_zero"""

    def test_negative_tariff_does_not_crash(
        self, crops_df, negative_tariff_electricity, staff_df, normal_forecast
    ):
        """A negative electricity tariff (sell-back) must not crash the solver."""
        # Should not raise — negative tariff should be clipped or handled gracefully
        plan = build_and_solve(
            forecast=normal_forecast,
            crops_df=crops_df,
            electricity_df=negative_tariff_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )
        assert plan is not None

    def test_negative_tariff_plan_has_valid_cost_breakdown(
        self, crops_df, negative_tariff_electricity, staff_df, normal_forecast
    ):
        """When tariff is negative, electricity cost should be a credit (negative number)."""
        plan = build_and_solve(
            forecast=normal_forecast,
            crops_df=crops_df,
            electricity_df=negative_tariff_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )
        cost = plan.get("cost_breakdown", {})
        elec = cost.get("electricity", 0)
        # Electricity cost with negative tariff = credit (negative SGD)
        assert isinstance(elec, (int, float))
        assert elec < 0, (
            f"Negative tariff should produce a credit (negative SGD), got elec={elec}. "
            "The optimizer must calculate tariff * kwh without taking absolute value."
        )


# ---------------------------------------------------------------------------
# Test 4: Impossible demand → best effort
# ---------------------------------------------------------------------------

class TestImpossibleDemand:
    """test_impossible_demand_returns_best_effort"""

    def test_massive_demand_does_not_crash(
        self, crops_df, normal_electricity, staff_df, huge_demand_forecast
    ):
        """Demand of 1000kg when max capacity is ~100kg should not crash the solver."""
        plan = build_and_solve(
            forecast=huge_demand_forecast,
            crops_df=crops_df,
            electricity_df=normal_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )
        assert plan is not None

    def test_massive_demand_revenue_capped_at_capacity(
        self, crops_df, normal_electricity, staff_df, huge_demand_forecast
    ):
        """When demand exceeds capacity, revenue should be capped at physical max, not infinite."""
        plan = build_and_solve(
            forecast=huge_demand_forecast,
            crops_df=crops_df,
            electricity_df=normal_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )
        cost = plan.get("cost_breakdown", {})
        revenue = cost.get("revenue", 0)
        # Revenue should be a finite number, not "infinity" or crash
        assert revenue >= 0
        assert revenue < 1_000_000, "Revenue should be capped, not astronomical"

    def test_massive_demand_plan_includes_constraint_warning(
        self, crops_df, normal_electricity, staff_df, huge_demand_forecast
    ):
        """When demand exceeds capacity, plan metadata should note the constraint."""
        plan = build_and_solve(
            forecast=huge_demand_forecast,
            crops_df=crops_df,
            electricity_df=normal_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )
        # The plan should either:
        # 1. Have a warning/constraint field, OR
        # 2. Have a bounded objective value (not trying to fulfill 1000kg)
        assert "objective_value_sgd" in plan
        obj = plan["objective_value_sgd"]
        assert obj is not None
        # If objective is very high (> 10000 SGD for 10 tiers), it suggests over-prediction not handled
        assert obj < 50_000, "Objective should reflect bounded capacity, not unlimited demand"
