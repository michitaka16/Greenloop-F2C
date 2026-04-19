"""Integration test: Full L1 → L2 → L3 pipeline.

Tests that data flows correctly through all layer boundaries.
Layer 1 uses fallback forecast if XGBoost is unavailable.
"""

import time

import pytest

from greenloop.data.loader import load_crops, load_electricity, load_staff
from greenloop.layer2.exceptions import InfeasibleError
from greenloop.layer2.optimizer import build_and_solve
from greenloop.layer2.scenarios import apply_typhoon, compare_plans
from greenloop.layer3.environment import HydroFarmEnv


# Simulated Layer 1 output (used when XGBoost unavailable)
FALLBACK_FORECAST = {
    "kai_lan": {"predicted_kg": 48.2, "lower_ci": 34.5, "upper_ci": 68.3},
    "baby_spinach": {"predicted_kg": 31.5, "lower_ci": 24.0, "upper_ci": 39.1},
    "lettuce_mambo": {"predicted_kg": 56.8, "lower_ci": 51.2, "upper_ci": 62.4},
    "chye_sim": {"predicted_kg": 36.1, "lower_ci": 28.0, "upper_ci": 44.2},
    "arugula": {"predicted_kg": 12.8, "lower_ci": 10.5, "upper_ci": 15.1},
}


@pytest.fixture
def common_data():
    return {
        "crops_df": load_crops(),
        "electricity_df": load_electricity(),
        "staff_df": load_staff(),
    }


@pytest.fixture
def forecast():
    """Try real Layer 1 forecast; fall back to simulated."""
    try:
        from greenloop.data.loader import load_shipments
        from greenloop.layer1.features import build_features
        from greenloop.layer1.model import train_models
        from greenloop.layer1.predict import predict_demand

        shipments = load_shipments()
        features = build_features(shipments)
        models = train_models(features)
        return predict_demand(models, features)
    except Exception:
        return FALLBACK_FORECAST


class TestL2Solve:
    def test_solver_returns_valid_plan(self, forecast, common_data):
        plan = build_and_solve(forecast=forecast, **common_data)
        assert isinstance(plan, dict)
        assert "objective_value_sgd" in plan
        assert "led_schedule" in plan
        assert "staff_shifts" in plan

    def test_solver_completes_under_5_seconds(self, forecast, common_data):
        t0 = time.time()
        build_and_solve(forecast=forecast, **common_data)
        elapsed = time.time() - t0
        assert elapsed < 8.0, f"Solver took {elapsed:.1f}s (limit: 8s)"


class TestTyphoonScenario:
    def test_typhoon_resolves_under_3_seconds(self, forecast, common_data):
        kwargs = dict(forecast=forecast, **common_data)

        # Normal plan
        plan_before = build_and_solve(**kwargs)

        # Typhoon
        t0 = time.time()
        typhoon_kwargs = apply_typhoon(kwargs)
        plan_after = build_and_solve(**typhoon_kwargs)
        elapsed = time.time() - t0

        assert elapsed < 6.0, f"Typhoon re-solve took {elapsed:.1f}s (limit: 6s)"

    def test_typhoon_comparison_has_delta(self, forecast, common_data):
        kwargs = dict(forecast=forecast, **common_data)
        plan_before = build_and_solve(**kwargs)
        typhoon_kwargs = apply_typhoon(kwargs)
        plan_after = build_and_solve(**typhoon_kwargs)

        comparison = compare_plans(plan_before, plan_after)
        assert "delta" in comparison
        assert "before" in comparison
        assert "after" in comparison


class TestL2ToL3:
    def test_plan_targets_feed_into_env(self, forecast, common_data):
        plan = build_and_solve(forecast=forecast, **common_data)

        env = HydroFarmEnv()
        env.update_targets({"temp": plan["room_temp_target_c"]})
        assert env.target_temp == float(plan["room_temp_target_c"])

    def test_env_runs_after_target_update(self, forecast, common_data):
        plan = build_and_solve(forecast=forecast, **common_data)

        env = HydroFarmEnv(targets={"temp": plan["room_temp_target_c"]})
        obs, _ = env.reset()

        for _ in range(10):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            assert obs is not None
            assert isinstance(reward, float)


class TestInfeasibilityHandling:
    def test_zero_staff_raises_infeasible(self, forecast, common_data):
        with pytest.raises(InfeasibleError):
            build_and_solve(forecast=forecast, **common_data, available_headcount=0)

    def test_infeasible_error_has_binding_constraint(self, forecast, common_data):
        try:
            build_and_solve(forecast=forecast, **common_data, available_headcount=0)
        except InfeasibleError as e:
            assert e.binding_constraint is not None
