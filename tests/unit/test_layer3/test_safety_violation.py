"""Unit tests for Layer 3 safety violation escalation.

Verifies that forcing temperature outside safety bounds triggers:
- Heavy reward penalty (-1000)
- constraint_violation flag = True in info dict
- The red alert in the dashboard UI would be shown
"""

import numpy as np
import pytest

from adoptakale.layer3.environment import HydroFarmEnv


@pytest.fixture
def env():
    e = HydroFarmEnv()
    yield e
    e.close()


class TestSafetyViolationEscalation:
    """Test 3: Safety violation escalation — red alert and agent stops acting."""

    def test_temp_above_max_triggers_violation(self, env):
        """Temperature above TEMP_SAFETY_MAX sets constraint_violation=True."""
        env.reset(seed=42)
        # Move temp above safety max
        env.temp = 40.0  # TEMP_SAFETY_MAX = 35
        neutral_action = np.array([2, 0, 1, 1])  # heater=0, pump=OFF, vent=MED
        _, _, _, _, info = env.step(neutral_action)
        assert info["constraint_violation"] is True

    def test_temp_below_min_triggers_violation(self, env):
        """Temperature below TEMP_SAFETY_MIN sets constraint_violation=True."""
        env.reset(seed=42)
        env.temp = 4.0  # TEMP_SAFETY_MIN = 10
        neutral_action = np.array([2, 0, 1, 1])
        _, _, _, _, info = env.step(neutral_action)
        assert info["constraint_violation"] is True

    def test_safety_violation_reduces_reward_by_1000(self, env):
        """A safety violation reduces reward by exactly 1000.0 on top of other penalties."""
        env.reset(seed=42)

        # Set near-target conditions (minimal other penalties)
        env.temp = env.target_temp
        env.humidity = env.target_humidity
        env.co2 = env.target_co2
        env.moisture = env.target_moisture
        env._cumulative_kwh = 0.0
        env._wastewater_exceeded = False
        neutral_action = np.array([2, 0, 1, 1])
        baseline_reward = env._compute_reward()

        # Force temperature out of safety bounds (40°C, well above MAX=35)
        # This triggers safety_violation penalty of -1000 PLUS temp_deviation penalty
        env.temp = 40.0
        violation_reward = env._compute_reward()

        # Safety penalty is -1000. Additional temp_dev penalty: |40-22|=18, 18*10=180
        # Total drop = 1000 + 180 = 1180
        reward_drop = baseline_reward - violation_reward
        assert abs(reward_drop - 1180.0) < 0.01, (
            f"Expected reward drop of 1180 (1000 safety + 180 temp_dev), got {reward_drop:.1f}"
        )
        # Verify the safety_violation flag is causing the large penalty
        # by checking the reward is below -1000 (meaning safety penalty applied)
        assert violation_reward < -900, (
            f"Violation reward {violation_reward} should be well below -900"
        )

    def test_violation_flag_resets_after_safe_step(self, env):
        """constraint_violation resets to False on the next safe step."""
        env.reset(seed=42)
        env.temp = 40.0  # force violation
        neutral_action = np.array([2, 0, 1, 1])
        _, _, _, _, info1 = env.step(neutral_action)
        assert info1["constraint_violation"] is True

        # Safe step
        env.temp = env.target_temp
        _, _, _, _, info2 = env.step(neutral_action)
        assert info2["constraint_violation"] is False

    def test_unsafe_heater_action_is_blocked(self, env):
        """Applying +2kW heater when near MAX temp triggers constraint_violation."""
        env.reset(seed=42)
        # Bring temp close to the blocking threshold via neutral physics
        # Projected = temp + heater_kw*0.5 → block when projected > 35
        # With heater_kw=2: projected = temp + 1 → block when temp >= 34
        hot_action = np.array([4, 0, 1, 1])  # +2kW heater
        for _ in range(200):
            obs, _, _, _, info = env.step(hot_action)
            if obs[0] >= 34.0:
                break

        # Verify temp is >= 34 (heater was effective until now)
        assert env.temp >= 34.0, (
            f"Could not heat to 34°C (got {env.temp:.2f}). Test precondition not met."
        )
        # Next +2kW step should be blocked
        _, _, _, _, info = env.step(hot_action)
        assert info["constraint_violation"] is True, (
            f"Expected constraint_violation=True when temp={env.temp:.2f} "
            f"(projected would be {env.temp + 1.0:.2f}°C, limit=35°C)"
        )

    def test_wastewater_exceeded_triggers_50_penalty(self, env):
        """30+ consecutive pump-on steps adds -50 to the reward."""
        env.reset(seed=42)
        env._consecutive_pump_steps = 30

        # Reward with wastewater exceeded
        env._wastewater_exceeded = True
        env._cumulative_kwh = 0.0
        env.temp = env.target_temp
        env.humidity = env.target_humidity
        env.co2 = env.target_co2
        env.moisture = env.target_moisture
        reward_exceeded = env._compute_reward()

        # Reward without wastewater exceeded
        env._wastewater_exceeded = False
        reward_normal = env._compute_reward()

        # Difference should be 50 (exceeded has 50 less reward than normal)
        assert abs((reward_normal - reward_exceeded) - 50.0) < 0.01, (
            f"Expected wastewater penalty of 50, got {reward_normal - reward_exceeded:.1f}"
        )

    def test_kwh_over_target_penalised(self, env):
        """Cumulative kWh above target incurs -5 per kWh penalty."""
        env.reset(seed=42)
        env._cumulative_kwh = 0.0
        env._wastewater_exceeded = False
        env.temp = env.target_temp

        # Reward at zero kWh
        reward_baseline = env._compute_reward()

        # Add 2 kWh over target
        env._cumulative_kwh = 2.0
        reward_2kwh = env._compute_reward()

        # 2 kWh over target → 2 * 5 = 10 penalty
        assert abs((reward_baseline - reward_2kwh) - 10.0) < 0.01, (
            f"Expected 10-point penalty for 2kWh over target, "
            f"got {reward_baseline - reward_2kwh:.1f}"
        )

    def test_temp_deviation_penalised_per_degree(self, env):
        """Every degree of temperature deviation costs -10 in reward."""
        env.reset(seed=42)
        env._cumulative_kwh = 0.0
        env._wastewater_exceeded = False
        env.humidity = env.target_humidity
        env.co2 = env.target_co2
        env.moisture = env.target_moisture

        env.temp = env.target_temp + 3.0  # 3°C deviation
        reward_3deg = env._compute_reward()

        env.temp = env.target_temp + 5.0  # 5°C deviation
        reward_5deg = env._compute_reward()

        # 2 additional degrees → 2 * 10 = 20 additional penalty
        assert abs((reward_3deg - reward_5deg) - 20.0) < 0.01, (
            f"Expected 20-point additional penalty for 2°C extra deviation, "
            f"got {reward_3deg - reward_5deg:.1f}"
        )
