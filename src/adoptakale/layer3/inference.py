"""Layer 3 — PPO inference for HydroFarmEnv.

Loads a trained PPO checkpoint and runs single-step or multi-step inference
against the hydroponic farm environment.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from adoptakale.utils.config import MODELS_DIR

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_DIR = MODELS_DIR / "layer3"


def load_agent(model_path: str | None = None):
    """Load a trained PPO agent from a checkpoint.

    Args:
        model_path: Path to the .zip model file. If None, looks for the
            default final checkpoint at models/layer3/ppo_hydrofarm_final.zip.

    Returns:
        A stable_baselines3.PPO model instance ready for inference.

    Raises:
        FileNotFoundError: If the model file does not exist at the given path.
    """
    from stable_baselines3 import PPO

    if model_path is None:
        model_path = str(_DEFAULT_MODEL_DIR / "ppo_hydrofarm_final.zip")

    resolved = Path(model_path)
    if not resolved.exists():
        raise FileNotFoundError(
            f"No trained model found at {resolved}. "
            f"Train one first with adoptakale.layer3.train.train_agent()."
        )

    model = PPO.load(str(resolved))
    logger.info("agent.loaded", extra={"model_path": str(resolved)})
    return model


def run_inference_step(
    model, env, obs: np.ndarray
) -> tuple[np.ndarray, np.ndarray, float, dict]:
    """Run one inference step using the trained model.

    Args:
        model: A loaded PPO model (from load_agent).
        env: The gymnasium environment instance.
        obs: Current observation array (shape (10,), float32).

    Returns:
        Tuple of (action, new_obs, reward, info).
        - action: The action array chosen by the policy.
        - new_obs: The observation after taking the action.
        - reward: The scalar reward received.
        - info: The info dict from the environment step.
    """
    action, _states = model.predict(obs, deterministic=True)
    new_obs, reward, terminated, truncated, info = env.step(action)
    info["terminated"] = terminated
    info["truncated"] = truncated
    return action, new_obs, float(reward), info


def run_episode(
    model, env, max_steps: int | None = None
) -> tuple[list[float], dict]:
    """Run a full episode and collect rewards.

    Args:
        model: A loaded PPO model.
        env: The gymnasium environment instance.
        max_steps: Override for max steps (defaults to env._max_steps).

    Returns:
        Tuple of (rewards_list, summary_dict).
        - rewards_list: List of per-step rewards.
        - summary_dict: Episode summary with total_reward, steps, final_obs.
    """
    obs, _ = env.reset()
    rewards: list[float] = []
    steps = 0
    limit = max_steps if max_steps is not None else getattr(env, "_max_steps", 1440)

    for _ in range(limit):
        action, obs, reward, info = run_inference_step(model, env, obs)
        rewards.append(reward)
        steps += 1
        if info.get("terminated") or info.get("truncated"):
            break

    summary = {
        "total_reward": sum(rewards),
        "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
        "steps": steps,
        "final_temp": float(obs[0]),
        "final_humidity": float(obs[1]),
        "final_co2": float(obs[2]),
        "final_moisture": float(obs[3]),
    }

    logger.info(
        "episode.complete",
        extra=summary,
    )

    return rewards, summary
