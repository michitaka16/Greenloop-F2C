"""Layer 3 — HydroFarmEnv: Gymnasium environment for PPO-based hydroponic farm control.

Simulates a Singapore vertical hydroponic farm with simplified linear physics.
The agent controls heater/cooler, irrigation pump, ventilation, and LED intensity
to maintain crop-optimal conditions while respecting safety constraints.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from greenloop.utils.config import (
    CO2_SAFETY_MAX,
    CO2_SAFETY_MIN,
    HUMIDITY_SAFETY_MAX,
    HUMIDITY_SAFETY_MIN,
    TEMP_SAFETY_MAX,
    TEMP_SAFETY_MIN,
)


class HydroFarmEnv(gym.Env):
    """Gymnasium environment for hydroponic farm RL control.

    Observation (10-dim float32):
        0: temperature (deg C)
        1: humidity (%)
        2: CO2 (ppm)
        3: soil moisture (0-1)
        4: time_of_day (0-1)
        5: led_state (0 or 1)
        6: temp_deviation from target
        7: humidity_deviation from target
        8: co2_deviation from target
        9: moisture_deviation from target

    Action (MultiDiscrete [5, 4, 3, 3]):
        dim 0 — heater/cooler: {0: -2kW, 1: -1kW, 2: 0kW, 3: +1kW, 4: +2kW}
        dim 1 — pump duration:  {0: OFF, 1: 30s, 2: 60s, 3: 120s}
        dim 2 — ventilation:    {0: LOW, 1: MED, 2: HIGH}
        dim 3 — LED fine-tune:  {0: -10%, 1: 0%, 2: +10%}
    """

    metadata = {"render_modes": ["human"]}

    # Pump duration lookup (seconds)
    _PUMP_DURATIONS = [0, 30, 60, 120]

    # LED adjustment lookup (fractional)
    _LED_ADJUSTMENTS = [-0.1, 0.0, 0.1]

    # Ventilation effects on humidity
    _VENT_HUMIDITY_EFFECTS = [0.5, 0.0, -1.0]

    # Ventilation effects on CO2 (LOW = less fresh air, HIGH = more)
    _VENT_CO2_EFFECTS = [-30, 0, 30]

    # Singapore ambient temperature for drift calculation
    _AMBIENT_TEMP = 28.0

    def __init__(self, targets: dict | None = None, render_mode: str | None = None):
        super().__init__()

        self.render_mode = render_mode

        # Default targets (Layer 2 can override via update_targets)
        self.target_temp: float = 22.0
        self.target_humidity: float = 65.0
        self.target_co2: float = 800.0
        self.target_moisture: float = 0.6

        if targets:
            self.update_targets(targets)

        # Observation space: 10 dimensions
        self.observation_space = spaces.Box(
            low=np.array(
                [10, 20, 200, 0, 0, 0, -20, -50, -500, -1], dtype=np.float32
            ),
            high=np.array(
                [40, 100, 2000, 1, 1, 1, 20, 50, 500, 1], dtype=np.float32
            ),
        )

        # Action space: MultiDiscrete [heater(5), pump(4), vent(3), led(3)]
        self.action_space = spaces.MultiDiscrete([5, 4, 3, 3])

        self._max_steps: int = 1440  # 24 hours at 1-minute intervals

        # State variables (initialized in reset)
        self.temp: float = 0.0
        self.humidity: float = 0.0
        self.co2: float = 0.0
        self.moisture: float = 0.0
        self.led_on: bool = False
        self._step_count: int = 0
        self._constraint_violated: bool = False
        self._rng: np.random.Generator = np.random.default_rng()

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        """Reset environment to initial conditions.

        Returns:
            (observation, info) tuple.
        """
        super().reset(seed=seed, options=options)
        self._rng = np.random.default_rng(seed)

        # Initial state: near-target with small noise
        self.temp = self.target_temp + self._rng.normal(0, 1.0)
        self.humidity = self.target_humidity + self._rng.normal(0, 2.0)
        self.co2 = self.target_co2 + self._rng.normal(0, 20.0)
        self.moisture = np.clip(
            self.target_moisture + self._rng.normal(0, 0.02), 0.0, 1.0
        )

        # Clamp to observation bounds
        self.temp = float(np.clip(self.temp, 10.0, 40.0))
        self.humidity = float(np.clip(self.humidity, 20.0, 100.0))
        self.co2 = float(np.clip(self.co2, 200.0, 2000.0))

        self._step_count = 0
        self._constraint_violated = False
        self.led_on = False

        return self._get_obs(), self._get_info()

    def step(
        self, action: np.ndarray
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Execute one time-step (1 minute) of the simulation.

        Args:
            action: MultiDiscrete action [heater, pump, vent, led].

        Returns:
            (observation, reward, terminated, truncated, info).
        """
        # Decode actions
        heater_kw = int(action[0]) - 2  # {-2, -1, 0, +1, +2}
        pump_dur = self._PUMP_DURATIONS[int(action[1])]
        vent_level = int(action[2])  # 0=LOW, 1=MED, 2=HIGH
        led_adj = self._LED_ADJUSTMENTS[int(action[3])]  # noqa: F841 — reserved for future LED dimming

        # Safety check BEFORE applying heater
        self._constraint_violated = False
        if not self._check_safety(heater_kw):
            heater_kw = 0  # Block unsafe action
            self._constraint_violated = True

        # --- Physics Model (simplified linear) ---

        # Temperature: heater effect + ambient drift + noise
        heater_effect = heater_kw * 0.5
        ambient_drift = (self._AMBIENT_TEMP - self.temp) * 0.01
        self.temp += heater_effect + ambient_drift + self._rng.normal(0, 0.1)
        self.temp = float(np.clip(self.temp, 5.0, 45.0))

        # Humidity: ventilation reduces, pump increases
        vent_effect = self._VENT_HUMIDITY_EFFECTS[vent_level]
        pump_effect = pump_dur * 0.003
        self.humidity += vent_effect + pump_effect + self._rng.normal(0, 0.5)
        self.humidity = float(np.clip(self.humidity, 20.0, 100.0))

        # CO2: ventilation brings in fresh air, plants consume during light
        vent_co2 = self._VENT_CO2_EFFECTS[vent_level]
        plant_uptake = -3.0 if self.led_on else -0.5
        self.co2 += vent_co2 + plant_uptake + self._rng.normal(0, 5.0)
        self.co2 = float(np.clip(self.co2, 200.0, 2000.0))

        # Soil moisture: pump adds, evaporation removes
        pump_moisture = pump_dur * 0.0005
        evaporation = -0.0002
        self.moisture = float(
            np.clip(self.moisture + pump_moisture + evaporation, 0.0, 1.0)
        )

        # LED state from schedule (on during hours 6-22)
        hour = (self._step_count % 1440) / 60.0
        self.led_on = 6.0 <= hour < 22.0

        self._step_count += 1
        truncated = self._step_count >= self._max_steps

        obs = self._get_obs()
        reward = self._compute_reward()
        info = self._get_info()

        return obs, reward, False, truncated, info

    def update_targets(self, targets: dict) -> None:
        """Update setpoints mid-episode (called when Layer 2 re-solves).

        Args:
            targets: Dict with optional keys 'temp', 'humidity', 'co2', 'moisture'.
        """
        if "temp" in targets:
            self.target_temp = float(targets["temp"])
        if "humidity" in targets:
            self.target_humidity = float(targets["humidity"])
        if "co2" in targets:
            self.target_co2 = float(targets["co2"])
        if "moisture" in targets:
            self.target_moisture = float(targets["moisture"])

    def _get_obs(self) -> np.ndarray:
        """Build the 10-dimensional observation vector."""
        time_of_day = (self._step_count % 1440) / 1440.0
        led_state = 1.0 if self.led_on else 0.0
        temp_dev = self.temp - self.target_temp
        humidity_dev = self.humidity - self.target_humidity
        co2_dev = self.co2 - self.target_co2
        moisture_dev = self.moisture - self.target_moisture

        obs = np.array(
            [
                self.temp,
                self.humidity,
                self.co2,
                self.moisture,
                time_of_day,
                led_state,
                temp_dev,
                humidity_dev,
                co2_dev,
                moisture_dev,
            ],
            dtype=np.float32,
        )

        # Clip to observation space bounds to guarantee containment
        obs = np.clip(obs, self.observation_space.low, self.observation_space.high)
        return obs

    def _compute_reward(self) -> float:
        """Compute reward based on deviation from targets and safety."""
        temp_dev = abs(self.temp - self.target_temp)
        humidity_dev = abs(self.humidity - self.target_humidity)
        co2_dev = abs(self.co2 - self.target_co2)
        moisture_dev = abs(self.moisture - self.target_moisture)

        # Safety violation check
        safety_flag = (
            self.temp < TEMP_SAFETY_MIN
            or self.temp > TEMP_SAFETY_MAX
            or self.humidity < HUMIDITY_SAFETY_MIN
            or self.humidity > HUMIDITY_SAFETY_MAX
            or self.co2 < CO2_SAFETY_MIN
            or self.co2 > CO2_SAFETY_MAX
        )

        reward = (
            +1.0  # yield progress per step (constant small positive)
            - 0.5 * temp_dev
            - 0.1 * humidity_dev
            - 0.01 * co2_dev
            - 5.0 * moisture_dev
            - 100.0 * float(safety_flag)
        )

        return float(reward)

    def _check_safety(self, heater_kw: int) -> bool:
        """Return True if the proposed heater action is safe.

        Blocks the action if projected temperature would exceed safety limits.
        """
        projected_temp = self.temp + heater_kw * 0.5
        return TEMP_SAFETY_MIN <= projected_temp <= TEMP_SAFETY_MAX

    def _get_info(self) -> dict:
        """Build the info dict returned by reset() and step()."""
        return {
            "constraint_violation": self._constraint_violated,
            "step": self._step_count,
            "temp": self.temp,
            "humidity": self.humidity,
            "co2": self.co2,
            "moisture": self.moisture,
        }
