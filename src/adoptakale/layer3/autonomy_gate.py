"""AutonomyGate — Human-in-the-Loop wrapper for HydroFarmAgent.

Wraps a HydroFarmAgent + HydroFarmEnv and enforces three autonomy modes:

- **manual**: Agent proposes; human must explicitly approve each action.
- **advisory**: Agent proposes; human can accept or reject after seeing it.
- **autonomous**: Agent acts freely; human watches and can override at any time.

Mode transitions
---------------
- Any → manual : pending action is discarded; episode continues.
- manual → advisory : pending action auto-approved and executed.
- manual → autonomous : pending action auto-approved; episode is reset.
- advisory → autonomous : pending action auto-approved.
- autonomous → manual : episode continues.
- advisory → manual : pending action discarded.

Episode reset
-------------
When switching from manual to autonomous, the environment is reset so the
RL agent starts fresh rather than continuing from a state that was
pending human review.

Usage
-----
>>> gate = AutonomyGate(agent=HydroFarmAgent(), env=HydroFarmEnv())
>>> gate.set_mode("advisory")
>>> result = gate.step(obs)   # returns proposed action; waits if manual
>>> gate.approve_pending()    # human approves
>>> gate.step(obs)            # continues
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class AutonomyMode(Enum):
    """Autonomy levels, ordered by increasing agent freedom."""

    MANUAL = "manual"       # Human approves every action
    ADVISORY = "advisory"  # Agent acts; human can override
    AUTONOMOUS = "autonomous"  # Agent acts freely


@dataclass
class GateState:
    """Mutable state carried inside AutonomyGate."""

    mode: AutonomyMode = AutonomyMode.ADVISORY
    pending_action: np.ndarray | None = None       # awaiting human approval
    pending_info: dict[str, Any] = field(default_factory=dict)
    last_action: np.ndarray | None = None          # most recent executed action
    last_info: dict[str, Any] = field(default_factory=dict)
    episode_step: int = 0
    episode_reset_required: bool = False


class AutonomyGate:
    """HITL wrapper for RL agent + env interaction.

    Parameters
    ----------
    agent : HydroFarmAgent
        The underlying RL agent (or None for random actions via env.sample).
    env : HydroFarmEnv
        The farm environment.
    """

    def __init__(
        self,
        agent,  # noqa: ANN001 — HydroFarmAgent (import causes side-effects)
        env,  # noqa: ANN001 — HydroFarmEnv
    ):
        self._agent = agent
        self._env = env
        self._state = GateState()

    # ── Public API ────────────────────────────────────────────────────────

    def set_mode(self, mode: str | AutonomyMode) -> None:
        """Switch autonomy mode.

        Mode string is case-insensitive.
        Raises ValueError for unknown modes.
        """
        if isinstance(mode, str):
            mode = AutonomyMode(mode.lower())

        old = self._state.mode
        if mode == old:
            return

        # Discard pending action on any mode change
        self._state.pending_action = None
        self._state.pending_info = {}

        # Manual → autonomous: reset episode (fresh start for the agent)
        if old == AutonomyMode.MANUAL and mode == AutonomyMode.AUTONOMOUS:
            self._env.reset()
            self._state.episode_step = 0
            logger.info("autonomy_gate.episode_reset", extra={"from": old.value, "to": mode.value})

        self._state.mode = mode
        logger.info("autonomy_gate.mode_changed", extra={"from": old.value, "to": mode.value})

    def get_mode(self) -> AutonomyMode:
        """Return current autonomy mode."""
        return self._state.mode

    def approve_pending(self) -> None:
        """Human approves the pending proposed action.

        Executes the pending action in the environment and clears the pending
        queue. Safe to call when there is no pending action (no-op).
        """
        if self._state.pending_action is None:
            return
        action = self._state.pending_action
        info = self._state.pending_info
        self._state.pending_action = None
        self._state.pending_info = {}
        self._execute(action, info)

    def reject_pending(self) -> np.ndarray | None:
        """Human rejects the pending proposed action.

        Replaces it with a random action sampled from the environment's
        action space, executes it, and clears the pending queue.

        Returns
        -------
        np.ndarray
            The replacement (random) action that was executed.
        """
        if self._state.pending_action is None:
            # Nothing to reject — sample and execute a random action
            action = self._env.action_space.sample()
            info = {"agent": "random", "gate_rejected": False}
        else:
            # Reject proposed; use random
            action = self._env.action_space.sample()
            info = {"agent": "random", "gate_rejected": True}
        self._state.pending_action = None
        self._state.pending_info = {}
        self._execute(action, info)
        return action

    def step(self, obs: np.ndarray) -> tuple[np.ndarray | None, dict[str, Any], bool]:
        """Take one environment step according to current mode.

        Parameters
        ----------
        obs : np.ndarray
            Current environment observation.

        Returns
        -------
        Tuple of (action, info, waiting)
            action  : The action that will be/was executed (None in manual
                      mode before approval).
            info    : Step info dict (includes 'gate_mode', 'agent', etc.).
            waiting : True if the caller should wait for approve/reject before
                      calling step() again.
        """
        mode = self._state.mode

        if mode == AutonomyMode.MANUAL:
            # Propose action and wait for human approval
            proposed, info = self._propose(obs)
            self._state.pending_action = proposed
            self._state.pending_info = info
            return None, {**info, "gate_mode": mode.value, "gate_waiting": True}, True

        elif mode == AutonomyMode.ADVISORY:
            # Execute immediately; human can override next step
            proposed, info = self._propose(obs)
            self._execute(proposed, info)
            return proposed, {**info, "gate_mode": mode.value, "gate_waiting": False}, False

        else:  # AUTONOMOUS
            proposed, info = self._propose(obs)
            self._execute(proposed, info)
            return proposed, {**info, "gate_mode": mode.value, "gate_waiting": False}, False

    def reset_episode(self) -> None:
        """Manually reset the RL episode (same as env.reset())."""
        self._env.reset()
        self._state.episode_step = 0
        self._state.pending_action = None
        self._state.pending_info = {}
        self._state.last_action = None
        self._state.last_info = {}
        logger.info("autonomy_gate.episode_reset", extra={"reason": "manual"})

    @property
    def mode_label(self) -> str:
        """Human-readable label for the current mode."""
        labels = {
            AutonomyMode.MANUAL: "Manual",
            AutonomyMode.ADVISORY: "Advisory",
            AutonomyMode.AUTONOMOUS: "Autonomous",
        }
        return labels[self._state.mode]

    @property
    def has_pending(self) -> bool:
        """True if an action is awaiting human approval."""
        return self._state.pending_action is not None

    @property
    def pending_info(self) -> dict[str, Any]:
        """Info dict for the pending proposed action."""
        return self._state.pending_info

    # ── Internals ─────────────────────────────────────────────────────────

    def _propose(self, obs: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        """Get agent's proposed action for the current observation."""
        if self._agent is not None:
            action, info = self._agent.step(obs)
            info["agent"] = "ppo"
        else:
            action = self._env.action_space.sample()
            info = {"agent": "random"}
        return action, info

    def _execute(self, action: np.ndarray, info: dict[str, Any]) -> None:
        """Execute an action in the environment and update state."""
        obs, reward, terminated, truncated, env_info = self._env.step(action)
        env_info.update(info)
        self._state.last_action = action
        self._state.last_info = env_info
        self._state.episode_step += 1
        logger.debug(
            "autonomy_gate.step_executed",
            extra={"step": self._state.episode_step, "agent": info.get("agent")},
        )
