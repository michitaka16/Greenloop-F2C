"""Unit tests for Layer 3 HydroFarmEnv — PPO RL environment control.

These tests validate the gymnasium.Env contract, physics model, safety
enforcement, and reward computation for the hydroponic farm environment.
"""

import math

import gymnasium as gym
import numpy as np
import pytest

from greenloop.layer3.environment import HydroFarmEnv


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def env():
    """Fresh HydroFarmEnv with default targets."""
    e = HydroFarmEnv()
    yield e
    e.close()


@pytest.fixture
def env_with_targets():
    """HydroFarmEnv with custom targets."""
    targets = {"temp": 25.0, "humidity": 70.0, "co2": 900.0, "moisture": 0.5}
    e = HydroFarmEnv(targets=targets)
    yield e
    e.close()


# ---------------------------------------------------------------------------
# Test: reset returns valid observation
# ---------------------------------------------------------------------------

def test_reset_returns_valid_observation(env):
    obs, info = env.reset(seed=42)
    assert isinstance(obs, np.ndarray), "Observation must be a numpy array"
    assert obs.shape == (10,), f"Expected shape (10,), got {obs.shape}"
    assert obs.dtype == np.float32, f"Expected float32, got {obs.dtype}"
    assert env.observation_space.contains(obs), (
        f"Observation {obs} is outside observation_space bounds"
    )
    assert isinstance(info, dict), "Info must be a dict"


# ---------------------------------------------------------------------------
# Test: step returns correct shapes and types
# ---------------------------------------------------------------------------

def test_step_returns_correct_shapes(env):
    env.reset(seed=42)
    action = env.action_space.sample()
    result = env.step(action)
    assert len(result) == 5, "step() must return (obs, reward, terminated, truncated, info)"
    obs, reward, terminated, truncated, info = result

    assert isinstance(obs, np.ndarray), "obs must be ndarray"
    assert obs.shape == (10,), f"obs shape must be (10,), got {obs.shape}"
    assert obs.dtype == np.float32
    assert isinstance(reward, float), f"reward must be float, got {type(reward)}"
    assert isinstance(terminated, bool), f"terminated must be bool, got {type(terminated)}"
    assert isinstance(truncated, bool), f"truncated must be bool, got {type(truncated)}"
    assert isinstance(info, dict), "info must be a dict"


# ---------------------------------------------------------------------------
# Test: observation_space contains observations after steps
# ---------------------------------------------------------------------------

def test_observation_space_contains_observations(env):
    obs, _ = env.reset(seed=42)
    assert env.observation_space.contains(obs)
    for _ in range(50):
        action = env.action_space.sample()
        obs, _, terminated, truncated, _ = env.step(action)
        assert env.observation_space.contains(obs), (
            f"Observation {obs} fell outside observation_space after step"
        )
        if terminated or truncated:
            break


# ---------------------------------------------------------------------------
# Test: action_space sample is valid and works in step
# ---------------------------------------------------------------------------

def test_action_space_sample_is_valid(env):
    env.reset(seed=42)
    for _ in range(20):
        action = env.action_space.sample()
        assert env.action_space.contains(action), f"Sampled action {action} not in action_space"
        obs, reward, terminated, truncated, info = env.step(action)
        # Should not raise
        assert obs is not None
        if terminated or truncated:
            break


# ---------------------------------------------------------------------------
# Test: episode terminates at 1440 steps
# ---------------------------------------------------------------------------

def test_episode_terminates_at_1440_steps(env):
    env.reset(seed=42)
    neutral_action = np.array([2, 0, 1, 1])  # heater=0, pump=OFF, vent=MED, led=0%
    for step_num in range(1440):
        obs, reward, terminated, truncated, info = env.step(neutral_action)
        if step_num < 1439:
            assert not truncated, f"Episode truncated early at step {step_num}"
        else:
            assert truncated, "Episode must be truncated at step 1440"


# ---------------------------------------------------------------------------
# Test: safety escalation blocks dangerous action
# ---------------------------------------------------------------------------

def test_safety_escalation_blocks_dangerous_action(env):
    obs, _ = env.reset(seed=42)
    # Warm up temperature close to upper safety limit.
    # Safety blocks when projected temp (temp + kw*0.5) exceeds 35.
    # For +2kW (effect=+1.0), need temp >= 34.0 for projected > 35.
    heat_action = np.array([4, 0, 0, 1])  # heater=+2kW
    for _ in range(200):
        obs, _, _, _, _ = env.step(heat_action)
        if env.temp >= 34.0:
            break

    # Now attempt +2kW again when temp is at or above 34
    assert env.temp >= 34.0, (
        f"Could not heat environment to 34C (got {env.temp}C). "
        "Physics model may need adjustment."
    )
    obs, _, _, _, info = env.step(heat_action)
    # The safety check should have blocked the heater
    assert info.get("constraint_violation") is True, (
        f"Expected constraint_violation=True when temp={env.temp:.1f}C "
        f"(projected would be {env.temp + 1.0:.1f}C, limit=35C)"
    )


# ---------------------------------------------------------------------------
# Test: reward is always finite (never NaN or Inf)
# ---------------------------------------------------------------------------

def test_reward_is_finite(env):
    env.reset(seed=42)
    for _ in range(200):
        action = env.action_space.sample()
        _, reward, terminated, truncated, _ = env.step(action)
        assert math.isfinite(reward), f"Reward is not finite: {reward}"
        if terminated or truncated:
            break


# ---------------------------------------------------------------------------
# Test: update_targets changes setpoints
# ---------------------------------------------------------------------------

def test_update_targets_changes_setpoints(env):
    env.reset(seed=42)
    assert env.target_temp == 22.0
    assert env.target_humidity == 65.0
    assert env.target_co2 == 800.0
    assert env.target_moisture == 0.6

    env.update_targets({"temp": 28.0, "humidity": 75.0, "co2": 1000.0, "moisture": 0.7})
    assert env.target_temp == 28.0
    assert env.target_humidity == 75.0
    assert env.target_co2 == 1000.0
    assert env.target_moisture == 0.7


def test_update_targets_partial(env):
    """Partial update should only change specified targets."""
    env.reset(seed=42)
    env.update_targets({"temp": 30.0})
    assert env.target_temp == 30.0
    assert env.target_humidity == 65.0  # unchanged


# ---------------------------------------------------------------------------
# Test: gymnasium env_checker passes
# ---------------------------------------------------------------------------

def test_env_checker_passes():
    env = HydroFarmEnv()
    from gymnasium.utils.env_checker import check_env
    # check_env raises or warns on violations
    check_env(env, skip_render_check=True)
    env.close()


# ---------------------------------------------------------------------------
# Test: custom targets in constructor
# ---------------------------------------------------------------------------

def test_custom_targets_constructor(env_with_targets):
    env_with_targets.reset(seed=42)
    assert env_with_targets.target_temp == 25.0
    assert env_with_targets.target_humidity == 70.0
    assert env_with_targets.target_co2 == 900.0
    assert env_with_targets.target_moisture == 0.5


# ---------------------------------------------------------------------------
# Test: physics model — heater raises temperature
# ---------------------------------------------------------------------------

def test_heater_raises_temperature(env):
    obs, _ = env.reset(seed=42)
    initial_temp = obs[0]
    # Apply +2kW heating for 10 steps
    heat_action = np.array([4, 0, 1, 1])  # heater=+2, pump=OFF, vent=MED, led=0%
    for _ in range(10):
        obs, _, _, _, _ = env.step(heat_action)
    assert obs[0] > initial_temp, "Heater should raise temperature"


# ---------------------------------------------------------------------------
# Test: physics model — pump increases moisture
# ---------------------------------------------------------------------------

def test_pump_increases_moisture(env):
    obs, _ = env.reset(seed=42)
    initial_moisture = obs[3]
    # Run pump at max for 10 steps
    pump_action = np.array([2, 3, 1, 1])  # heater=0, pump=120s, vent=MED, led=0%
    for _ in range(10):
        obs, _, _, _, _ = env.step(pump_action)
    assert obs[3] > initial_moisture, "Pump should increase soil moisture"


# ---------------------------------------------------------------------------
# Test: reward penalizes safety violations
# ---------------------------------------------------------------------------

def test_reward_penalizes_safety_violations(env):
    env.reset(seed=42)
    # Get baseline reward at near-target conditions
    neutral_action = np.array([2, 0, 1, 1])
    _, baseline_reward, _, _, _ = env.step(neutral_action)

    # Force temperature out of safety bounds by direct state manipulation
    env.temp = 36.0  # above TEMP_SAFETY_MAX=35
    _, violation_reward, _, _, _ = env.step(neutral_action)
    assert violation_reward < baseline_reward, (
        "Reward should be lower when safety limits are violated"
    )


# ---------------------------------------------------------------------------
# Test: LED schedule follows 6-22 hours
# ---------------------------------------------------------------------------

def test_led_schedule(env):
    env.reset(seed=42)
    neutral_action = np.array([2, 0, 1, 1])

    # Step to hour 3 (step 180) — LED should be off
    for _ in range(180):
        obs, _, _, _, _ = env.step(neutral_action)
    assert obs[5] == 0.0, "LED should be off at hour 3"

    # Step to hour 12 (step 720) — LED should be on
    for _ in range(540):
        obs, _, _, _, _ = env.step(neutral_action)
    assert obs[5] == 1.0, "LED should be on at hour 12"
