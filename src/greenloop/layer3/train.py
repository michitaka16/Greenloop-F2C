"""Layer 3 — PPO training for HydroFarmEnv.

Trains a Stable-Baselines3 PPO agent on the hydroponic farm environment.
Saves checkpoints at configurable intervals and returns the path to the
final trained model.
"""

from __future__ import annotations

import logging
from pathlib import Path

from greenloop.utils.config import MODELS_DIR

logger = logging.getLogger(__name__)

_DEFAULT_SAVE_DIR = MODELS_DIR / "layer3"


def train_agent(
    env=None,
    total_timesteps: int = 500_000,
    save_dir: str | Path | None = None,
    checkpoint_freq: int = 100_000,
    seed: int = 42,
) -> str:
    """Train a PPO agent on HydroFarmEnv.

    Args:
        env: A gymnasium-compatible environment. If None, creates a HydroFarmEnv.
        total_timesteps: Total training timesteps.
        save_dir: Directory for model checkpoints. Defaults to models/layer3/.
        checkpoint_freq: Save a checkpoint every N timesteps.
        seed: Random seed for reproducibility.

    Returns:
        Absolute path to the final saved model (.zip).
    """
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import CheckpointCallback

    from greenloop.layer3.environment import HydroFarmEnv

    if env is None:
        env = HydroFarmEnv()
        env.reset(seed=seed)

    save_path = Path(save_dir) if save_dir else _DEFAULT_SAVE_DIR
    save_path.mkdir(parents=True, exist_ok=True)

    checkpoint_callback = CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path=str(save_path),
        name_prefix="ppo_hydrofarm",
        verbose=1,
    )

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        seed=seed,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )

    logger.info(
        "train.start",
        extra={
            "total_timesteps": total_timesteps,
            "save_dir": str(save_path),
            "checkpoint_freq": checkpoint_freq,
        },
    )

    model.learn(
        total_timesteps=total_timesteps,
        callback=checkpoint_callback,
        progress_bar=False,
    )

    final_path = save_path / "ppo_hydrofarm_final"
    model.save(str(final_path))

    logger.info(
        "train.complete",
        extra={"model_path": str(final_path.with_suffix(".zip"))},
    )

    env.close()
    return str(final_path.with_suffix(".zip"))
