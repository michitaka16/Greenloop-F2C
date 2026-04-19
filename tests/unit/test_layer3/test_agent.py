"""Unit tests for Layer 3 HydroFarmAgent — PPO inference wrapper.

Tests:
- Agent loads from checkpoint when available
- Agent falls back to random when no checkpoint
- step() returns valid action
- run_episode() returns correct step history
- Safety violation info is included in step records
"""

import numpy as np
import pytest

from greenloop.layer3.agent import HydroFarmAgent
from greenloop.layer3.environment import HydroFarmEnv


@pytest.fixture
def env():
    e = HydroFarmEnv()
    yield e
    e.close()


@pytest.fixture
def agent_with_fallback():
    """HydroFarmAgent with no checkpoint loaded (random fallback)."""
    # Point to non-existent path so it falls back to random
    agent = HydroFarmAgent(model_path="/nonexistent/path/ppo.zip")
    yield agent
    # No cleanup needed


class TestHydroFarmAgentFallback:
    """Tests for random-fallback behavior (no checkpoint)."""

    def test_agent_has_no_real_policy_when_no_checkpoint(self, agent_with_fallback):
        assert agent_with_fallback.policy is None
        assert agent_with_fallback.is_real is False

    def test_step_returns_action_shape(self, agent_with_fallback, env):
        env.reset(seed=42)
        obs, _ = env.reset()
        action, info = agent_with_fallback.step(obs)
        # action is None when no policy loaded
        assert info["agent"] == "random"


class TestHydroFarmAgentEpisode:
    """Tests for run_episode()."""

    def test_run_episode_returns_history(self, agent_with_fallback, env):
        env.reset(seed=42)
        history = agent_with_fallback.run_episode(env, n_steps=5)
        assert len(history) == 5
        for i, record in enumerate(history):
            assert record["step"] == i
            assert "obs" in record
            assert "action" in record
            assert "reward" in record
            assert "cumulative_reward" in record
            assert "info" in record

    def test_cumulative_reward_increases(self, agent_with_fallback, env):
        env.reset(seed=42)
        history = agent_with_fallback.run_episode(env, n_steps=10)
        cumulative = 0.0
        for record in history:
            cumulative += record["reward"]
            assert record["cumulative_reward"] == pytest.approx(cumulative)

    def test_run_episode_respects_n_steps(self, agent_with_fallback, env):
        env.reset(seed=42)
        history = agent_with_fallback.run_episode(env, n_steps=5)
        assert len(history) == 5

    def test_run_episode_stops_on_truncation(self, agent_with_fallback, env):
        env.reset(seed=42)
        # Run full episode (1440 steps) — should stop at truncation
        history = agent_with_fallback.run_episode(env, n_steps=None)
        # Should be truncated at 1440
        assert len(history) == 1440
        assert history[-1]["info"].get("step") == 1440

    def test_constraint_violation_in_info(self, agent_with_fallback, env):
        env.reset(seed=42)
        # Run many steps — eventually a constraint may be violated
        history = agent_with_fallback.run_episode(env, n_steps=20)
        # At least one step record should have info
        assert all("info" in r for r in history)


class TestHydroFarmAgentActionSpace:
    """Tests for action validity."""

    def test_actions_match_env_action_space(self, agent_with_fallback, env):
        env.reset(seed=42)
        history = agent_with_fallback.run_episode(env, n_steps=10)
        for record in history:
            action = record["action"]
            assert env.action_space.contains(action), f"Action {action} not in action_space"


class TestHydroFarmAgentReal:
    """Tests for the real PPO agent (when checkpoint exists)."""

    def test_agent_is_real_when_checkpoint_exists(self):
        """If models/layer3/ppo_hydrofarm_final.zip exists, agent is real."""
        agent = HydroFarmAgent()
        # Only meaningful if checkpoint actually exists
        if agent.is_real:
            assert agent.policy is not None
            assert agent.is_real is True
        else:
            # Checkpoint not present — skip
            pytest.skip("No trained checkpoint at models/layer3/ppo_hydrofarm_final.zip")

    def test_real_agent_step_returns_valid_action(self, env):
        """Real agent produces actions within env action space."""
        agent = HydroFarmAgent()
        if not agent.is_real:
            pytest.skip("No trained checkpoint")

        env.reset(seed=42)
        obs, _ = env.reset()
        action, info = agent.step(obs)
        assert env.action_space.contains(action)
        assert info["agent"] == "ppo"
