# Dimension A Evidence — COC Decision Log

## 7 Required Design Decisions

### Decision 1: Why XGBoost over linear regression for demand forecasting

**Context**: Need to predict weekly crop demand from historical shipments, weather,
prices, and calendar features.

**Decision**: XGBoost (gradient boosted trees)

**Rationale**:
- Crop demand has nonlinear interactions: price sensitivity changes by season,
  weather effects vary by crop type. Linear regression assumes additive effects
  and misses these interactions.
- XGBoost handles mixed feature types (continuous, categorical, binary) natively
  without manual feature engineering.
- Built-in feature importance rankings enable model interpretability — farm
  managers can see WHY demand is predicted high/low.
- Robust to outliers in simulated data (tree-based models are less sensitive to
  extreme values than linear models).
- Native support for quantile regression (Decision #2).

**Rejected alternative**: Linear regression — assumes linearity, requires manual
interaction terms, poor at capturing seasonal patterns without extensive feature
engineering.

---

### Decision 2: Why quantile regression for confidence intervals (not ±1 std)

**Context**: Layer 2 MILP needs confidence intervals to build uncertainty buffers
for production planning.

**Decision**: XGBoost quantile regression (3 models at q=0.05, 0.50, 0.95)

**Rationale**:
- ±1 standard deviation assumes errors follow a normal (Gaussian) distribution.
  Crop demand errors are often skewed: kai lan has occasional demand spikes that
  pull the upper tail far from the mean.
- Quantile regression makes NO distributional assumption — it directly estimates
  the conditional quantile.
- This produces asymmetric intervals when the data warrants it: kai lan might have
  lower_ci = -20% and upper_ci = +60% from the median.
- The intervals feed directly into Layer 2: upper_ci sets the production target,
  meaning high-variance crops automatically get larger buffers.

**Rejected alternative**: ±1 std — assumes symmetry and normality, underestimates
tail risk for volatile crops, overestimates for stable ones.

**Upgrade path**: Conformal prediction could provide finite-sample coverage
guarantees, but adds implementation complexity beyond course scope.

---

### Decision 3: Why MILP over heuristic / greedy scheduling

**Context**: Need to find the daily operating plan (LED schedule, staff shifts,
rack layout, temperature, watering) that maximises profit.

**Decision**: Mixed Integer Linear Programming via Google OR-Tools

**Rationale**:
- MILP guarantees the globally optimal solution. A greedy algorithm only finds a
  local optimum — it might schedule LEDs in cheap hours but miss that rearranging
  the rack layout would save more.
- Constraint satisfaction is provable. When we say "MOM limits are never violated,"
  the solver mathematically guarantees this. A heuristic might violate constraints
  in edge cases.
- Adding new constraints (Typhoon scenario) requires zero algorithm changes — just
  add the constraint to the model and re-solve. A hardcoded heuristic needs
  rewriting for every new scenario.
- Solve time is < 1 second at our scale (~300 variables). There is no performance
  reason to sacrifice optimality.
- The Typhoon demo specifically proves that MILP can re-optimise the entire farm in
  real time — impossible with a hardcoded rule-based system.

**Rejected alternative**: Greedy/heuristic — no optimality guarantee, can't handle
constraint changes dynamically, harder to extend for new scenarios.

---

### Decision 4: How uncertainty propagation from L1 CI → L2 constraint works

**Context**: Layer 1 produces confidence intervals. Layer 2 needs to use them for
robust planning.

**Decision**: Use upper_ci (95th percentile) as the MILP production target

**Mechanism**:
1. Layer 1 outputs per crop: predicted_kg (median), lower_ci (5th), upper_ci (95th)
2. Layer 2 sets production_kg[crop] >= upper_ci as a hard constraint
3. This means we plan for the upper end of likely demand
4. High-variance crops (kai lan: wide CI) get large buffers
5. Stable crops (lettuce: narrow CI) get small buffers
6. Buffer size = (upper_ci - predicted_kg) / predicted_kg × 100%

**Result**: The system automatically produces more of volatile crops as insurance
against demand spikes, while keeping stable crops lean. The buffer cost appears
in the MILP objective as potential waste_loss, so the optimizer balances buffer
size against waste cost.

**Trade-off**: Using upper_ci increases production cost (more resources, potential
waste) but reduces stockout risk. Farm managers could adjust by choosing a different
quantile (e.g., 80th instead of 95th) to trade off cost vs risk.

---

### Decision 5: Why PPO over DQN for the RL agent

**Context**: Layer 3 RL agent controls temperature, humidity, CO2, and watering
using discrete actions.

**Decision**: Proximal Policy Optimization (PPO)

**Rationale**:
- **Action space handling**: Our action space is MultiDiscrete (5 × 4 × 3 × 3 = 180
  combinations). PPO handles MultiDiscrete natively. DQN would need to flatten this
  to a single discrete space of 180 actions, losing the structure of independent
  action dimensions.
- **Training stability**: PPO's clipped surrogate objective prevents catastrophic
  policy updates. DQN with experience replay can suffer from non-stationary targets
  and requires careful tuning of target network update frequency.
- **Sample efficiency**: PPO with GAE (Generalized Advantage Estimation) is more
  sample-efficient for our environment where each episode is 1440 steps.
- **Implementation maturity**: stable-baselines3's PPO implementation is the most
  widely used and tested. Fewer gotchas in practice.

**Rejected alternative**: DQN — requires action flattening, less stable training,
epsilon-greedy exploration is crude for our continuous state space.

---

### Decision 6: How the reward function balances yield vs energy vs safety

**Context**: The RL agent must simultaneously track environmental targets, minimize
energy use, and never violate safety constraints.

**Decision**: Weighted sum reward with escalating penalties

```python
reward = (
    + 1.0 * yield_progress_per_step
    - 5.0 * kwh_over_target
    - 10.0 * temp_deviation_celsius
    - 50.0 * wastewater_litre_exceeded
    - 1000.0 * safety_incident_flag
)
```

**Weight rationale** (in ascending severity):
- **yield_progress (+1.0)**: Small positive signal each step to encourage productive
  actions. Without this, the agent learns to "do nothing" as the lowest-penalty strategy.
- **energy_over_target (-5.0)**: 5× the yield reward — energy waste is costly but
  recoverable (you just pay more). This encourages efficiency without overriding
  plant health.
- **temperature_deviation (-10.0)**: 10× yield — temperature directly affects crop
  quality. Deviations compound (2°C off for 6 hours damages crop).
- **wastewater_exceeded (-50.0)**: 50× yield — water waste has environmental impact
  and regulatory implications. Harder to recover from.
- **safety_incident (-1000.0)**: 1000× yield — overwhelming penalty ensures the agent
  treats safety as inviolable. Any action that would breach safety limits is worse
  than any possible benefit.

**Design intent**: The penalty scale creates a clear priority ordering:
Safety >> Waste >> Temperature >> Energy >> Yield. The agent can trade energy for
temperature (worth 2×), but can never trade safety for anything.

---

### Decision 7: Why escalation logic is set at the chosen thresholds

**Context**: When the RL agent's actions would exceed hard constraints, the system
must intervene.

**Decision**: Pre-action safety check with action blocking and dashboard alert

**Thresholds**:
| Variable | Operating Target | Safety Limit | Reasoning |
|----------|-----------------|-------------|-----------|
| Temperature | 22°C | 10-35°C | Below 10°C: crop damage in minutes. Above 35°C: heat stress kills seedlings. |
| Humidity | 65% | 40-90% | Below 40%: tip burn on leafy greens. Above 90%: fungal disease risk. |
| CO2 | 800ppm | 300-1500ppm | Below 300: suboptimal photosynthesis. Above 1500: worker safety concern. |
| Moisture | 0.6 | 0.1-0.95 | Below 0.1: root desiccation. Above 0.95: root rot. |

**Why wide margins**: The safety limits are set wider than operating targets
(target 22°C, limit 35°C) so the RL agent has room to explore and correct drift
before hitting hard limits. Tight safety limits would make training impossible —
the agent would trigger escalation on every slightly suboptimal action.

**Escalation process**:
1. Before executing action, project its effect on each variable
2. If projected value exceeds safety limit → block the action, apply no-op instead
3. Log the blocked action and reason to the ConstraintViolationAlert queue
4. Dashboard shows the alert in the RL Control panel
5. Agent receives the observation from the blocked state (not the projected state)

**Key design choice**: The agent never executes beyond defined bounds. This is
a hard architectural decision — we chose safety over learning. The alternative
(let the agent violate and learn from the negative reward) risks crop damage
during training and is unacceptable for a production system.
