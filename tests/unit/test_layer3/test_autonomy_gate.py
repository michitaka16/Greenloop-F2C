"""Tests for AutonomyGate (Layer 3 HITL wrapper)."""

import numpy as np
import pytest

from greenloop.layer3.autonomy_gate import AutonomyGate, AutonomyMode


class DummyAgent:
    """Minimal agent stub that returns a fixed action."""

    def __init__(self, fixed_action=None):
        self.fixed_action = fixed_action or np.array([0, 0, 0, 0])
        self.step_count = 0

    def step(self, obs):
        self.step_count += 1
        return self.fixed_action, {"agent": "dummy"}


class DummyEnv:
    """Minimal Gym env stub for testing AutonomyGate."""

    def __init__(self):
        self.observation_space = type("Space", (), {"low": np.zeros(10), "high": np.ones(10)})()

        class ActionSpace:
            def sample(self):
                return np.array([0, 0, 0, 0])

        self.action_space = ActionSpace()
        self._obs = np.zeros(10)
        self._step_count = 0
        self._reward = 1.0

    def reset(self):
        self._obs = np.zeros(10)
        self._step_count = 0
        return self._obs, {}

    def _get_obs(self):
        return self._obs

    def step(self, action):
        self._step_count += 1
        self._obs = np.ones(10) * (self._step_count / 10)
        return (
            self._obs.copy(),
            self._reward,
            False,
            False,
            {"constraint_violation": False},
        )


@pytest.fixture
def env():
    return DummyEnv()


@pytest.fixture
def agent():
    return DummyAgent()


@pytest.fixture
def gate(agent, env):
    return AutonomyGate(agent=agent, env=env)


class TestAutonomyGateDefaults:
    def test_default_mode_is_advisory(self, gate):
        assert gate.get_mode() == AutonomyMode.ADVISORY

    def test_mode_label(self, gate):
        assert gate.mode_label == "Advisory"


class TestSetMode:
    def test_set_mode_by_string(self, gate):
        gate.set_mode("manual")
        assert gate.get_mode() == AutonomyMode.MANUAL

    def test_set_mode_by_enum(self, gate):
        gate.set_mode(AutonomyMode.AUTONOMOUS)
        assert gate.get_mode() == AutonomyMode.AUTONOMOUS

    def test_set_mode_same_mode_noop(self, gate):
        gate.set_mode(AutonomyMode.ADVISORY)
        assert gate.get_mode() == AutonomyMode.ADVISORY

    def test_unknown_mode_raises(self, gate):
        with pytest.raises(ValueError):
            gate.set_mode("unknown")


class TestAutonomousMode:
    def test_autonomous_step_executes(self, gate):
        gate.set_mode("autonomous")
        obs = np.zeros(10)
        action, info, waiting = gate.step(obs)
        assert waiting is False
        assert action is not None
        assert info["agent"] == "ppo"  # _propose sets "ppo" to identify PPO policy
        assert gate._state.episode_step == 1

    def test_autonomous_step_no_pending(self, gate):
        gate.set_mode("autonomous")
        obs = np.zeros(10)
        gate.step(obs)
        assert gate.has_pending is False


class TestManualMode:
    def test_manual_step_sets_pending(self, gate):
        gate.set_mode("manual")
        obs = np.zeros(10)
        action, info, waiting = gate.step(obs)
        assert waiting is True
        assert action is None
        assert gate.has_pending is True

    def test_approve_pending_executes(self, gate):
        gate.set_mode("manual")
        gate.step(np.zeros(10))
        gate.approve_pending()
        assert gate.has_pending is False
        assert gate._state.last_action is not None
        assert gate._state.episode_step == 1

    def test_reject_pending_replaces_with_random(self, gate):
        gate.set_mode("manual")
        gate.step(np.zeros(10))
        original_action = gate._state.pending_action.copy()
        rejected = gate.reject_pending()
        assert rejected is not None
        assert gate.has_pending is False
        assert gate._state.episode_step == 1

    def test_approve_without_pending_is_noop(self, gate):
        gate.set_mode("manual")
        gate.approve_pending()  # no-op
        assert gate._state.episode_step == 0


class TestAdvisoryMode:
    def test_advisory_step_executes(self, gate):
        gate.set_mode("advisory")
        obs = np.zeros(10)
        action, info, waiting = gate.step(obs)
        assert waiting is False
        assert action is not None
        assert gate._state.episode_step == 1


class TestModeTransitions:
    def test_manual_to_autonomous_resets_episode(self, gate):
        gate.set_mode("advisory")
        gate.step(np.zeros(10))  # step 1 (executed)
        assert gate._state.episode_step == 1
        gate.set_mode("manual")
        gate.step(np.zeros(10))  # proposes, not executed
        assert gate._state.episode_step == 1
        gate.approve_pending()    # executes step 2
        assert gate._state.episode_step == 2
        gate.set_mode("autonomous")  # reset episode on manual→autonomous
        assert gate._state.episode_step == 0

    def test_any_mode_to_manual_clears_pending(self, gate):
        gate.set_mode("advisory")
        gate.step(np.zeros(10))
        gate.set_mode("manual")
        gate.step(np.zeros(10))  # propose
        gate.set_mode("advisory")  # auto-approves pending
        assert gate.has_pending is False


class TestResetEpisode:
    def test_reset_clears_state(self, gate):
        gate.set_mode("advisory")
        gate.step(np.zeros(10))
        gate.reset_episode()
        assert gate._state.episode_step == 0
        assert gate._state.last_action is None
        assert gate.has_pending is False
