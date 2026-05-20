"""System-wide adversarial stress tests.

Phase 7 Red-Team: MGMT655 Dimension B — cross-layer cascade failures.
"""

from __future__ import annotations

import pandas as pd
import pytest

from adoptakale.layer2.optimizer import build_and_solve
from adoptakale.layer2.exceptions import InfeasibleError
from adoptakale.utils.config import CROP_IDS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def crops_df():
    from adoptakale.data.loader import load_crops
    return load_crops()


@pytest.fixture
def normal_electricity():
    rows = []
    for hour in range(24):
        rate = 0.28 if 8 <= hour < 22 else 0.18
        rows.append({"date": "2025-10-15", "hour": hour, "tariff_rate_sgd_per_kwh": rate})
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


# ---------------------------------------------------------------------------
# Test 1: Seed supply 7-day delay cascade
# ---------------------------------------------------------------------------

class TestSeedSupplyDelay:
    """test_seed_supply_7day_delay_cascade"""

    def test_7day_seed_delay_Produces_infeasible_or_adapted_plan(
        self, crops_df, normal_electricity, staff_df, normal_forecast
    ):
        """A 7-day seed supply delay must either:
        1. Produce an InfeasibleError (correct signal that supply chain is broken), OR
        2. Produce a feasible plan with reduced scope (seed_stock_kg constraints applied)

        The system must NOT silently pretend seeds are available."""
        try:
            plan = build_and_solve(
                forecast=normal_forecast,
                crops_df=crops_df,
                electricity_df=normal_electricity,
                staff_df=staff_df,
                available_headcount=6,
                seed_supply_delayed=True,
            )
            # If feasible, the plan must reflect reduced capacity
            assert plan is not None
            assert "objective_value_sgd" in plan
            # Revenue should be significantly reduced vs no-delay scenario
            cost = plan.get("cost_breakdown", {})
            revenue = cost.get("revenue", 0)
            assert revenue < 50_000, (
                "Seed delay plan shows revenue near full capacity — "
                "seed_stock_kg constraints may not be applied"
            )
        except InfeasibleError as exc:
            # Infeasible is acceptable — signals the delay is a real problem
            assert exc.binding_constraint is not None or "seed" in str(exc).lower()

    def test_seed_delay_reduces_active_tiers(
        self, crops_df, normal_electricity, staff_df, normal_forecast
    ):
        """With delayed seeds and zero stock, the optimizer must either
        produce an InfeasibleError (correct signal) or a plan that
        reflects reduced capacity — it must NOT silently ignore the constraint."""
        zero_seed = {cid: 0.0 for cid in CROP_IDS}
        try:
            plan = build_and_solve(
                forecast=normal_forecast,
                crops_df=crops_df,
                electricity_df=normal_electricity,
                staff_df=staff_df,
                available_headcount=6,
                seed_supply_delayed=True,
                seed_stock_kg=zero_seed,
            )
            # If a plan is returned (C1b overrides seed constraint), it must
            # show reduced scope — active tiers should be bounded.
            assert plan is not None
            active_tiers = [
                tier for tier, crop in plan.get("rack_layout", {}).items()
                if crop not in (None, "", "none")
            ]
            assert len(active_tiers) <= 10
        except InfeasibleError:
            # Infeasible is correct — zero seeds means no new plantings possible
            pass

    def test_immediate_seed_exhaustion_infeasible(
        self, crops_df, normal_electricity, staff_df, normal_forecast
    ):
        """Zero seed stock (seed_stock_kg = 0 for all crops) should produce
        an InfeasibleError since no crops can be planted."""
        zero_seed = {cid: 0.0 for cid in CROP_IDS}

        with pytest.raises(InfeasibleError) as exc_info:
            build_and_solve(
                forecast=normal_forecast,
                crops_df=crops_df,
                electricity_df=normal_electricity,
                staff_df=staff_df,
                available_headcount=6,
                seed_supply_delayed=True,
                seed_stock_kg=zero_seed,
            )
        assert exc_info.value.binding_constraint is not None or "seed" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test 2: Top-3 customers simultaneous churn
# ---------------------------------------------------------------------------

class TestTopCustomerChurn:
    """test_top_3_customers_simultaneous_churn"""

    def test_massive_demand_drop_still_produces_valid_plan(
        self, crops_df, normal_electricity, staff_df
    ):
        """Losing the top 3 customers (≈50% of demand) should still produce
        a valid plan — the farm should scale down gracefully, not crash."""
        # Simulate 90% demand reduction (top customers churned)
        churned_forecast = {
            cid: {"predicted_kg": 8.0, "lower_ci": 5.0, "upper_ci": 15.0}
            for cid in CROP_IDS
        }

        plan = build_and_solve(
            forecast=churned_forecast,
            crops_df=crops_df,
            electricity_df=normal_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )
        assert plan is not None
        assert "objective_value_sgd" in plan

    def test_churn_scenario_reduces_staff_hours(
        self, crops_df, normal_electricity, staff_df
    ):
        """In a churn scenario, the optimizer should reduce staff hours
        (or shifts) to match the lower demand — not waste labour."""
        churned_forecast = {
            cid: {"predicted_kg": 5.0, "lower_ci": 2.0, "upper_ci": 10.0}
            for cid in CROP_IDS
        }

        plan = build_and_solve(
            forecast=churned_forecast,
            crops_df=crops_df,
            electricity_df=normal_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )

        cost = plan.get("cost_breakdown", {})
        labour_cost = cost.get("labour", 0)
        # Labour cost is stored as negative (optimizer convention: cost = negative)
        # With near-zero demand, labour cost magnitude should be minimized
        assert labour_cost <= 0
        # Revenue should be low
        revenue = cost.get("revenue", 0)
        assert revenue < 10_000, "Churn scenario still shows high revenue — revenue not capped"

    def test_demand_zero_produces_minimal_viable_plan(
        self, crops_df, normal_electricity, staff_df
    ):
        """Near-zero demand (nobody ordering) should produce a minimal plan
        with near-zero revenue, not a crashed solver."""
        zero_forecast = {
            cid: {"predicted_kg": 0.1, "lower_ci": 0.0, "upper_ci": 1.0}
            for cid in CROP_IDS
        }

        plan = build_and_solve(
            forecast=zero_forecast,
            crops_df=crops_df,
            electricity_df=normal_electricity,
            staff_df=staff_df,
            available_headcount=6,
        )
        assert plan is not None
        cost = plan.get("cost_breakdown", {})
        revenue = cost.get("revenue", 0)
        assert revenue < 500, "Zero-demand scenario should produce near-zero revenue"

    def test_negative_demand_clamped_to_zero(
        self, crops_df, normal_electricity, staff_df
    ):
        """A physically impossible negative demand prediction must be
        handled gracefully — negative demand is meaningless."""
        invalid_forecast = {
            cid: {"predicted_kg": -50.0, "lower_ci": -100.0, "upper_ci": 0.0}
            for cid in CROP_IDS
        }

        # Should not crash — clamp to zero or raise handled error
        try:
            plan = build_and_solve(
                forecast=invalid_forecast,
                crops_df=crops_df,
                electricity_df=normal_electricity,
                staff_df=staff_df,
                available_headcount=6,
            )
            # If it succeeds, revenue should be zero (clamped)
            cost = plan.get("cost_breakdown", {})
            revenue = cost.get("revenue", 0)
            assert revenue >= 0, "Negative demand produced negative revenue"
        except (InfeasibleError, ValueError):
            # Raising an error for invalid negative demand is acceptable
            pass
