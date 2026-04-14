# Layer 2 — Constraint Optimisation (OR-Tools MILP)

## Goal

Given Layer 1 targets, find the daily operating plan that maximises profit subject to
MOM regulations, safety limits, and operational constraints. Solve in < 5 seconds.

## Solver

Google OR-Tools CP-SAT solver (handles mixed integer + constraint problems, free,
Apache 2.0 licensed). Import: `from ortools.sat.python import cp_model`

Alternative: OR-Tools linear solver with MILP backend (`pywraplp`). Either works at
this scale.

## Objective Function

```
Maximise:
  Revenue       (SGD/kg × predicted_kg)
  − Electricity (tariff_rate × LED_kwh × hours)
  − Labour      (hourly_rate × staff_count × shift_hours)
  − Waste_loss  (spoilage_rate × over_production_kg)
```

All terms in SGD. Financial calculations always in SGD (hard constraint).

### Why MILP Over Heuristic/Greedy (Dimension A Decision #3)

- MILP guarantees optimal solution (greedy only guarantees local optimum)
- Constraint satisfaction is proven (greedy may violate MOM limits silently)
- Adding new constraints (Typhoon scenario) requires zero algorithm changes — just add constraint
- Solve time < 1 second at this scale — no performance reason to simplify
- The Typhoon demo specifically proves that MILP can re-optimise instantly when constraints change,
  which is impossible with a hardcoded heuristic

## Decision Variables

| Variable | Type | Domain | Count (5 crops, 10 tiers, 24h) |
|----------|------|--------|-------------------------------|
| LED on/off per rack tier per hour | Binary | {0, 1} | 10 × 24 = 240 |
| Staff per shift | Integer | [0, max_headcount] | 3 shifts |
| Crop-to-tier assignment | Binary | {0, 1} | 5 × 10 = 50 |
| Room temperature target | Integer | [18, 26] (°C, scaled) | 1 |
| Watering frequency per tray | Integer | [1, 4] (times/day) | 5 crops |

Total: ~300 variables. Trivial for OR-Tools.

## Hard Constraints (Infeasible if violated)

### MOM Labour Regulations
```python
# Max 8h per shift
for shift in shifts:
    model.Add(shift_hours[shift] <= 8)

# Max 44h per staff per week
for staff_id in staff_ids:
    model.Add(sum(hours[staff_id, shift] for shift in week_shifts) <= 44)
```

### LED Safety Ceiling
```python
# LED intensity per tier cannot exceed fire safety limit
for tier in tiers:
    for hour in range(24):
        model.Add(led_intensity[tier, hour] <= led_max[tier])
```

### Water Volume Limit
```python
# Total water per crop tray cannot exceed tank capacity
for crop in crops:
    model.Add(water_freq[crop] * water_per_cycle[crop] <= tank_capacity[crop])
```

### Harvest Timing Window
```python
# Harvest must occur within ±12h of optimal time
for crop in crops:
    model.Add(harvest_hour[crop] >= optimal_hour[crop] - 12)
    model.Add(harvest_hour[crop] <= optimal_hour[crop] + 12)
```

## Soft Constraints (Penalty Terms)

### Off-Peak Electricity Preference
```python
# SP Group tariff: peak hours get penalty multiplier
peak_hours = range(8, 22)  # 8am-10pm
for tier in tiers:
    for hour in peak_hours:
        # Add penalty to objective for peak-hour LED usage
        peak_penalty += led_on[tier, hour] * peak_multiplier
```

### Workload Balance
```python
# If any shift > 120% of average → penalty
avg_load = total_hours / num_shifts
for shift in shifts:
    overload = shift_hours[shift] - int(1.2 * avg_load)
    model.Add(overload_penalty[shift] >= overload)
    model.Add(overload_penalty[shift] >= 0)
```

## Uncertainty Propagation (Dimension A Decision #4)

**How CI from Layer 1 feeds into Layer 2:**

```python
# Use upper_ci as production target — automatically builds buffer
for crop in crops:
    forecast = layer1_output[crop]
    # Production must meet at least the upper CI to handle demand uncertainty
    model.Add(production_kg[crop] >= forecast['upper_ci'])
    # But don't overproduce beyond a waste threshold
    model.Add(production_kg[crop] <= forecast['upper_ci'] * 1.1)
```

This means high-variance crops (kai lan: wide CI) get larger production buffers,
while stable crops (lettuce: narrow CI) get tighter targets. The buffer size
per crop is logged in the decision output.

## Typhoon Scenario (Demo Wow Moment)

When the Typhoon button is pressed:

```python
# Change constraint: delivery slots from 12h to 6h
model.Add(delivery_end_hour <= delivery_start_hour + 6)  # was + 12

# Re-solve — OR-Tools produces new plan in < 1 second
solver = cp_model.CpSolver()
status = solver.Solve(model)
```

The entire plan (LED schedule, staff shifts, harvest timing) updates to reflect
the tighter delivery window. Dashboard shows the before/after comparison.

## Output Contract

```python
{
    "plan_date": "2026-04-12",
    "objective_value_sgd": 1842.50,  # maximised profit
    "solve_time_ms": 47,
    "led_schedule": {
        "tier_1": [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1],  # 24h binary
        ...
    },
    "staff_shifts": [
        {"shift": "morning", "staff_count": 3, "hours": 8},
        {"shift": "afternoon", "staff_count": 2, "hours": 8},
        {"shift": "night", "staff_count": 1, "hours": 6}
    ],
    "rack_layout": {
        "tier_1": "kai_lan", "tier_2": "baby_spinach", ...
    },
    "room_temp_target_c": 22,
    "watering_schedule": {
        "kai_lan": 3, "baby_spinach": 2, ...  # times per day
    },
    "cost_breakdown": {
        "revenue": 2500.00,
        "electricity": -380.00,
        "labour": -245.00,
        "waste_penalty": -32.50
    },
    "uncertainty_buffers": {
        "kai_lan": {"upper_ci": 168.3, "production_target": 168.3, "buffer_pct": 39.7},
        "lettuce": {"upper_ci": 105.2, "production_target": 105.2, "buffer_pct": 8.1}
    }
}
```

## Edge Cases

- Infeasible plan (constraints can't all be satisfied): solver returns INFEASIBLE.
  Dashboard shows which constraint is binding and suggests relaxation.
- Typhoon + low staff: if 6h delivery window + limited headcount makes the plan
  infeasible, show the trade-off: "Need 1 more staff member OR relax delivery window to 8h."
