"""Adversarial stress tests for Layer 3 RL reward hacking.

Phase 7 Red-Team: MGMT655 Dimension B — hostile inputs and edge cases.
"""

from __future__ import annotations

import numpy as np
import pytest

from adoptakale.layer3.environment import HydroFarmEnv
from adoptakale.utils.config import (
    TEMP_SAFETY_MIN,
    TEMP_SAFETY_MAX,
    HUMIDITY_SAFETY_MIN,
    HUMIDITY_SAFETY_MAX,
    CO2_SAFETY_MIN,
    CO2_SAFETY_MAX,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def env():
    return HydroFarmEnv()


# ---------------------------------------------------------------------------
# Test 1: Agent cannot disable safety thresholds
# ---------------------------------------------------------------------------

class TestSafetyThresholdIntegrity:
    """test_agent_cannot_disable_safety_thresholds"""

    def test_safety_violation_penalty_applies_despite_optimal_reward(
        self, env
    ):
        """A sequence of actions that would produce high yield but violate
        safety thresholds must incur a large negative penalty, preventing
        the agent from 'learning' to violate safety."""
        obs, info = env.reset(seed=42)

        # Manually set temp just below the safety max
        # With heater_idx=4 (heater_kw=+2), projected = 34.5 + 2*0.5 = 35.5 > 35.0
        # _check_safety should block and set constraint_violated=True
        env.temp = 34.5
        env.humidity = 65.0
        env.co2 = 800.0
        env.moisture = 0.5

        # heater_idx=4 (+2 kW) → projected temp = 35.5 > 35.0 → unsafe, blocked
        action = np.array([4, 0, 0, 1], dtype=np.int64)
        obs, reward, terminated, truncated, info = env.step(action)

        # Safety guard MUST block the unsafe action
        assert info["constraint_violation"], (
            "Safety guard did not block heater action that would exceed TEMP_SAFETY_MAX=35.0. "
            f"Projected temp was 34.5 + 1.0 = 35.5 > 35.0"
        )
        # With constraint_violated, heater was clamped to 0 → reward does not include heater energy
        # Reward is dominated by existing temperature deviation (temp_dev ≈ 12.5 for target 22.0)
        assert reward < 0, (
            f"Reward {reward} should be negative given the large temperature deviation "
            "even with the heater blocked"
        )

    def test_safety_threshold_cannot_be_overridden_by_high_yield_action(
        self, env
    ):
        """Aggressively maximizing yield (pump on max, heater max) while
        ignoring safety must still result in a net negative reward when
        safety limits are breached."""
        obs, info = env.reset(seed=42)

        # Set temperature already at the ceiling
        env.temp = TEMP_SAFETY_MAX - 0.5
        env.humidity = 60.0
        env.co2 = 800.0
        env.moisture = 0.3

        # Maximum yield action: heater +2 (violates safety), pump 120s, vent high, led +10%
        action = np.array([4, 3, 2, 2], dtype=np.int64)
        obs, reward, terminated, truncated, info = env.step(action)

        # Safety guard should have blocked heater (projected temp = MAX + 0.5 > MAX)
        assert info["constraint_violation"], (
            "Heater action projected to exceed TEMP_SAFETY_MAX was not blocked"
        )

        # With constraint_violation=True, heater was clamped to 0.
        # The safety violation flag triggers -1000 penalty in reward.
        # Combined with temp deviation and kwh penalties, reward is heavily negative.
        # We just verify it's substantially negative (not a false positive).
        assert reward < -100, (
            f"Reward {reward} is not sufficiently negative after a safety violation. "
            f"Expected a large negative penalty from safety_violation flag."
        )

    def test_undo_environment_preserves_original_safety_bounds(self, env):
        """Calling update_targets() must not be able to widen safety limits
        beyond the physical constraints defined in config."""
        env.reset(seed=42)
        env.update_targets({"temp": 100.0})  # absurdly high target

        # Safety bounds in config.py are the hard floor — not modifiable
        assert TEMP_SAFETY_MIN == 10.0
        assert TEMP_SAFETY_MAX == 35.0

        # The _check_safety guard must still enforce config bounds
        # heater_idx=2 → heater_kw=0, projected = current temp (passes)
        env.temp = 34.0
        is_safe = env._check_safety(heater_kw=0)  # projects to 34.0 ≤ 35.0 → passes
        assert is_safe, "Safety check rejected a no-op heater action"

        # heater_idx=4 → heater_kw=+2, projected = 34.0 + 2*0.5 = 35.0 = at boundary → passes
        # Need 2+ steps above: heater_idx=5 doesn't exist, so use a different approach
        env.temp = 34.1
        is_safe = env._check_safety(heater_kw=2)  # projects to 34.1 + 1.0 = 35.1 > 35.0 → rejected
        assert not is_safe, (
            "Safety check accepted action that projects beyond TEMP_SAFETY_MAX=35.0. "
            f"Projected temp = 34.1 + 1.0 = 35.1 > 35.0"
        )


# ---------------------------------------------------------------------------
# Test 2: Agent escalates when confused (contradictory sensors)
# ---------------------------------------------------------------------------

class TestEscalationOnConfusion:
    """test_agent_escalates_when_confused"""

    def test_all_sensors_at_extremes_produces_high_magnitude_reward_penalty(
        self, env
    ):
        """When all sensors read extreme values simultaneously, the reward
        must heavily penalize this — signaling the agent to escalate/escalate
        (call for human intervention)."""
        obs, info = env.reset(seed=42)

        # Force all sensors to their worst extremes simultaneously
        env.temp = TEMP_SAFETY_MIN  # coldest
        env.humidity = HUMIDITY_SAFETY_MAX  # most humid
        env.co2 = CO2_SAFETY_MAX  # highest CO2
        env.moisture = 0.0  # driest

        # Take a no-op action
        action = np.array([2, 0, 1, 1], dtype=np.int64)  # heater 0, pump off, vent med, led 0
        obs, reward, terminated, truncated, info = env.step(action)

        # Extreme simultaneous deviation should produce a strongly negative reward
        assert reward < -100, (
            f"Reward {reward} for all-sensors-extreme state is not sufficiently negative. "
            "Agent has no incentive to escalate when all sensors are critical."
        )

    def test_conflicting_readings_produce_conservative_behavior(self, env):
        """When temperature and humidity signals conflict (temp says heat,
        humidity says drought), a conservative agent should prioritize
        safety over yield. This test verifies the reward signal incentivizes
        restraint."""
        obs, info = env.reset(seed=42)

        # Conflicting state: too hot AND too dry simultaneously
        env.temp = TEMP_SAFETY_MAX - 1.0
        env.humidity = HUMIDITY_SAFETY_MIN + 1.0
        env.co2 = 800.0
        env.moisture = 0.05  # critically dry

        # No-op action (heater 0, pump off, vent low, led 0)
        action = np.array([2, 0, 0, 1], dtype=np.int64)
        obs, reward, terminated, truncated, info = env.step(action)

        # Reward should be negative due to existing violations
        # even with no-op action — this signals the situation is already bad
        assert reward < 0, (
            f"Reward {reward} for conflicting sensor state is non-negative. "
            "The agent has no signal that conflicting readings require escalation."
        )

    def test_power_outage_during_extreme_conditions_produces_double_penalty(
        self, env
    ):
        """A power outage occurring when conditions are already critical
        must compound penalties — UPS exhausted penalty + safety penalty
        should make the situation unambiguously signal a human emergency."""
        env.reset(seed=42)

        # Trigger power outage first
        env.trigger_power_outage()

        # Set state to already-critical
        env.temp = TEMP_SAFETY_MIN + 1.0
        env.humidity = HUMIDITY_SAFETY_MAX - 1.0
        env.co2 = CO2_SAFETY_MAX - 10.0
        env.moisture = MOISTURE_SAFETY_MIN + 0.01
        env.led_on = False  # LED already off due to outage

        # Step — UPS active + critical state
        action = np.array([2, 0, 0, 1], dtype=np.int64)  # no-op
        obs, reward, terminated, truncated, info = env.step(action)

        # Combined: power_outage penalty (-500) + safety violation penalty (-1000)
        assert reward < -500, (
            f"Combined power outage + critical state reward {reward} is not "
            "penalized enough. Agent must unambiguously escalate."
        )
        assert info["power_outage"], "Info does not indicate active power outage"
        assert info["ups_countdown_steps"] < 240, "UPS countdown did not decrement"


# ---------------------------------------------------------------------------
# Helpers for moisture constant
# ---------------------------------------------------------------------------

from adoptakale.utils.config import MOISTURE_SAFETY_MIN
