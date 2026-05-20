"""Layer 3 — HydroFarmAgent: PPO inference wrapper for HydroFarmEnv.

Loads a trained PPO checkpoint from stable-baselines3 and exposes
a simple step()/run_episode() interface. Falls back to a random-agent
if no checkpoint exists.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from adoptakale.utils.config import MODELS_DIR

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_DIR = MODELS_DIR / "layer3"


class HydroFarmAgent:
    """PPO inference wrapper for HydroFarmEnv.

    Attributes:
        policy: The underlying stable-baselines3 PPO model (or None if fallback).
        is_real: True if a trained PPO model is loaded, False for random fallback.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        deterministic: bool = True,
    ):
        """Load a PPO agent or fall back to random actions.

        Args:
            model_path: Path to the .zip checkpoint. If None, uses
                models/layer3/ppo_hydrofarm_final.zip.
            deterministic: If True, use deterministic action selection
                (recommended for inference).
        """
        self.policy: "PPO | None" = None
        self.is_real: bool = False
        self._deterministic = deterministic
        self._model_path = model_path

        self._try_load()

    # ── Public API ────────────────────────────────────────────────────────

    def step(self, obs: np.ndarray) -> tuple[np.ndarray, dict]:
        """Select an action for the given observation.

        Args:
            obs: Current observation array (shape (n,)).

        Returns:
            Tuple of (action_array, info_dict).
            action_array has shape matching the env action space.
            info_dict contains 'action_names' (human-readable labels).
        """
        if self.policy is not None:
            action, _ = self.policy.predict(obs, deterministic=self._deterministic)
        else:
            # Random fallback — caller must provide action_space.sample()
            action = None  # type: ignore[assignment]

        info: dict[str, Any] = {
            "agent": "ppo" if self.is_real else "random",
        }
        return action, info

    def run_episode(
        self,
        env,  # noqa: ANN001
        n_steps: int | None = None,
        *,
        callback=None,  # noqa: ANN001
    ) -> list[dict]:
        """Run a fixed number of steps in the environment.

        Args:
            env: A HydroFarmEnv instance.
            n_steps: Number of steps to run. Defaults to env._max_steps (1440).
            callback: Optional callable(step_idx, obs, action, reward, info)
                called after each step.

        Returns:
            List of step dicts, each containing:
            - obs, action, reward, cumulative_reward, info
        """
        n_steps = n_steps if n_steps is not None else getattr(env, "_max_steps", 1440)
        obs, _ = env.reset()
        cumulative = 0.0
        history: list[dict] = []

        for step_idx in range(n_steps):
            action, agent_info = self.step(obs)
            if action is None:
                action = env.action_space.sample()
                agent_info = {"agent": "random"}

            obs, reward, terminated, truncated, info = env.step(action)
            cumulative += reward
            info.update(agent_info)

            step_record: dict[str, Any] = {
                "step": step_idx,
                "obs": obs.copy(),
                "action": action.copy() if hasattr(action, "copy") else action,
                "reward": float(reward),
                "cumulative_reward": cumulative,
                "info": info,
            }
            history.append(step_record)

            if callback:
                callback(step_idx, obs, action, reward, info)

            if terminated or truncated:
                break

        return history

    # ── Internals ─────────────────────────────────────────────────────────

    def _try_load(self) -> None:
        """Attempt to load the PPO checkpoint."""
        from stable_baselines3 import PPO

        model_path = self._model_path
        if model_path is None:
            model_path = str(_DEFAULT_MODEL_DIR / "ppo_hydrofarm_final.zip")

        resolved = Path(model_path)
        if not resolved.exists():
            logger.warning(
                "agent.fallback_random",
                extra={"reason": f"checkpoint not found at {resolved}"},
            )
            return

        try:
            self.policy = PPO.load(str(resolved))
            self.is_real = True
            logger.info("agent.loaded", extra={"model_path": str(resolved)})
        except Exception as exc:
            logger.warning(
                "agent.fallback_random",
                extra={"reason": str(exc), "model_path": str(resolved)},
            )
            self.policy = None
            self.is_real = False
