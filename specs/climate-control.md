# Layer 3 — RL Environment Control (PPO)

## Goal

Monitor live sensor readings and issue corrective micro-commands when values
drift from Layer 2 targets. Pre-trained on a simulated gymnasium environment.

## Architecture

```
Layer 2 targets (temp, humidity, etc.)
        ↓
HydroFarmEnv (gymnasium.Env)
  - Simulates farm physics
  - Receives PPO actions
  - Returns observations + reward
        ↓
PPO Agent (stable-baselines3)
  - Observes state
  - Outputs discrete action
  - Pre-trained for 500K steps
        ↓
Streamlit live log panel
```

## HydroFarmEnv Specification

### State Space (Observations)

```python
observation_space = spaces.Box(
    low=np.array([10.0, 20.0, 200.0, 0.0, 0.0, 0.0, -20.0, -50.0, -500.0, -1.0]),
    high=np.array([40.0, 100.0, 2000.0, 1.0, 1.0, 1.0, 20.0, 50.0, 500.0, 1.0]),
    dtype=np.float32
)
```

| Index | Variable | Unit | Range |
|-------|----------|------|-------|
| 0 | Room temperature | °C | 10-40 |
| 1 | Humidity | % | 20-100 |
| 2 | CO2 level | ppm | 200-2000 |
| 3 | Soil moisture zone 1 | 0-1 | 0.0-1.0 |
| 4 | Time of day | normalised | 0.0-1.0 |
| 5 | LED schedule state | 0/1 | from Layer 2 |
| 6 | Temp deviation from target | °C | -20 to +20 |
| 7 | Humidity deviation from target | % | -50 to +50 |
| 8 | CO2 deviation from target | ppm | -500 to +500 |
| 9 | Moisture deviation from target | | -1 to +1 |

### Action Space (MultiDiscrete)

```python
action_space = spaces.MultiDiscrete([5, 4, 3, 3])
```

| Dimension | Actions | Meaning |
|-----------|---------|---------|
| 0: Heater/cooler | {0,1,2,3,4} → {-2,-1,0,+1,+2} kW | Temperature adjustment |
| 1: Pump | {0,1,2,3} → {OFF, 30s, 60s, 120s} | Watering duration |
| 2: Ventilation | {0,1,2} → {LOW, MED, HIGH} | Airflow setting |
| 3: LED fine-tune | {0,1,2} → {-10%, 0%, +10%} | Light adjustment from schedule |

Total action combinations: 5 × 4 × 3 × 3 = 180

### Why PPO Over DQN (Dimension A Decision #5)

- PPO handles MultiDiscrete natively; DQN would need to flatten to 180 discrete actions
- PPO's clipped surrogate objective prevents catastrophic policy updates during training
- PPO is more sample-efficient with advantage estimation (GAE)
- stable-baselines3 PPO is the most battle-tested implementation
- DQN's epsilon-greedy exploration is crude for continuous state spaces

### Reward Function (Dimension A Decision #6)

```python
def _compute_reward(self) -> float:
    reward = (
        + 1.0 * self.yield_progress_per_step
        - 5.0 * self.kwh_over_target
        - 10.0 * abs(self.temp_deviation_celsius)
        - 50.0 * self.wastewater_litre_exceeded
        - 1000.0 * self.safety_incident_flag
    )
    return reward
```

**Balance rationale**:
- yield_progress (+1.0): small positive reward each step to encourage productive actions
- kwh_over_target (-5.0): energy cost penalty — 5x yield to prefer efficiency
- temp_deviation (-10.0): moderate penalty for comfort drift — want tight tracking
- wastewater (-50.0): large penalty for waste — environmental + cost concern
- safety_incident (-1000.0): overwhelming penalty ensures agent never risks safety

**Tuning risk**: The -1000 safety penalty may cause the agent to freeze (do nothing
= guaranteed no safety incident). If training produces a passive agent, reduce to
-100 and add a small positive reward for maintaining conditions within bounds.

### Physics Model (Simplified Linear)

```python
def step(self, action):
    # Temperature dynamics
    heater_effect = (action[0] - 2) * 0.5  # kW → °C/step
    ambient_drift = (self.ambient_temp - self.temp) * 0.01  # thermal leak
    self.temp += heater_effect + ambient_drift + np.random.normal(0, 0.1)

    # Humidity dynamics
    vent_effect = [0.5, 0, -0.5][action[2]]  # ventilation reduces humidity
    pump_effect = [0, 0.2, 0.4, 0.8][action[1]]  # pumping increases humidity
    self.humidity += vent_effect + pump_effect + np.random.normal(0, 0.5)

    # CO2 dynamics
    vent_co2_effect = [-20, 0, 20][action[2]]  # ventilation brings in fresh air
    plant_uptake = -2.0 if self.led_on else -0.5  # plants consume CO2 under light
    self.co2 += vent_co2_effect + plant_uptake + np.random.normal(0, 5)

    # Soil moisture
    pump_moisture = [0, 0.02, 0.04, 0.08][action[1]]
    evaporation = -0.01
    self.moisture = np.clip(self.moisture + pump_moisture + evaporation, 0, 1)
```

### Episode Structure

- Episode length: 24h (1440 steps at 1-min intervals)
- Reset: randomise initial conditions within plausible ranges
- Truncation: after 1440 steps (one full day)
- Target values: received from Layer 2 at episode start

### Escalation Logic (Dimension A Decision #7)

```python
def _check_safety(self, action) -> bool:
    """Returns True if action is safe, False if it would violate a hard constraint."""
    projected_temp = self.temp + self._project_heater_effect(action[0])
    if projected_temp > 35.0 or projected_temp < 10.0:
        self.constraint_violations.append(ConstraintViolationAlert(
            variable="temperature",
            projected_value=projected_temp,
            limit="10-35°C",
            action_blocked=True
        ))
        return False
    # ... similar checks for humidity, CO2, moisture
    return True
```

**Threshold rationale**: Safety bounds are set wider than operating targets (target
22°C, safety limit 35°C) so the agent has room to correct drift before hitting
hard limits. The escalation triggers an alert to the dashboard, not a crash.

## Training Configuration

```python
from stable_baselines3 import PPO

model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    verbose=1
)
model.learn(total_timesteps=500_000)
model.save("ppo_hydro_v1")
```

Training time estimate: 1-3 hours on laptop CPU.

Save checkpoints at 200K, 300K, 500K steps. Use the best-performing one.

## Streamlit Integration

```python
# Load checkpoint at app startup
model = PPO.load("ppo_hydro_v1")

# Run inference in background (or in Streamlit main loop)
obs = env.reset()
while True:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, truncated, info = env.step(action)

    # Stream to Streamlit
    placeholder.write(f"Temp: {obs[0]:.1f}°C | Action: {action[0]-2:+d}kW | CO2: {obs[2]:.0f}ppm")

    if done or truncated:
        obs = env.reset()
    time.sleep(0.1)  # ~10 FPS for live feel
```

## Testing Requirements

### HydroFarmEnv unit tests (CRITICAL — highest risk item)

```python
def test_env_reset_returns_valid_observation():
    env = HydroFarmEnv()
    obs, info = env.reset()
    assert env.observation_space.contains(obs)

def test_env_step_returns_correct_shapes():
    env = HydroFarmEnv()
    obs, _ = env.reset()
    action = env.action_space.sample()
    obs, reward, done, truncated, info = env.step(action)
    assert env.observation_space.contains(obs)
    assert isinstance(reward, float)

def test_safety_escalation_blocks_dangerous_action():
    env = HydroFarmEnv()
    env.temp = 34.0  # near upper safety limit
    action = [4, 0, 0, 1]  # +2kW heating → would exceed 35°C
    obs, reward, done, truncated, info = env.step(action)
    assert info.get('constraint_violation') is True
    assert env.temp <= 35.0  # action was blocked

def test_episode_terminates_at_1440_steps():
    env = HydroFarmEnv()
    env.reset()
    for _ in range(1440):
        _, _, done, truncated, _ = env.step(env.action_space.sample())
    assert done or truncated
```
