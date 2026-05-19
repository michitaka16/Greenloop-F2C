# Streamlit Dashboard Specification

## Layout (Single Screen, No Scrolling)

```
+--------------------------------------------------+
|  Adopt a Kale          [Today: 12 Apr 2026]  |
+---------------+----------------------------------+
| INPUTS        |  TODAY'S OPTIMAL PLAN            |
| Electricity   |  LED Schedule  [bar chart 24h]   |
| tariff rate   |  Staff Shifts  [gantt-style]     |
| Headcount     |  Rack Layout   [heatmap]         |
| Ship targets  |  Projected ROI [metric card]     |
+---------------+----------------------------------+
| DEMAND FORECAST (Layer 1)                         |
| Crop table with predicted_kg + CI bars            |
+---------------+----------------------------------+
| RL CONTROL    |  SCENARIO TESTING                |
| [LIVE LOG]    |  [Typhoon Button]                |
| Temp: 22.3C   |  -> cuts delivery window 50%     |
| Action: +0kW  |  -> Layer 2 re-optimises         |
| CO2: 412ppm   |  -> Layer 3 adjusts harvest time |
+---------------+----------------------------------+
```

## Sections

### Top Bar
- App title: "Adopt a Kale"
- Current date display
- Farm name / logo area

### Left Column: Inputs (User Controls)

```python
st.sidebar.header("Farm Parameters")
tariff_rate = st.sidebar.number_input("Electricity rate (SGD/kWh)", value=0.28)
headcount = st.sidebar.slider("Available staff", 1, 10, 6)
# Per-crop shipping targets could be auto-filled from Layer 1
```

Farm managers adjust inputs here. Changes trigger Layer 2 re-optimization.

### Top Right: Today's Optimal Plan (Layer 2 Output)

| Component | Streamlit Widget | Data Source |
|-----------|-----------------|-------------|
| LED Schedule | st.bar_chart (24 bars, on/off per tier) | Layer 2 output |
| Staff Shifts | Plotly Gantt chart or st.dataframe | Layer 2 output |
| Rack Layout | Plotly heatmap (crop × tier) | Layer 2 output |
| Projected ROI | st.metric (big number + delta) | Layer 2 objective value |

### Middle: Demand Forecast (Layer 1 Output)

Table with one row per crop:

| Crop | Predicted (kg) | Lower CI | Upper CI | Buffer |
|------|---------------|----------|----------|--------|
| Kai Lan | 120.5 | 85.2 | 168.3 | ±39.7% |
| Baby Spinach | 95.0 | 82.1 | 108.4 | ±13.9% |

Plus a bar chart showing CI ranges per crop (horizontal error bars).

### Bottom Left: RL Control Live Log (Layer 3 Output)

```python
rl_placeholder = st.empty()
# Updated every ~100ms during inference loop
rl_placeholder.markdown(f"""
**Temp**: {temp:.1f}°C (target: {target_temp}°C)
**Action**: {action_label}
**CO2**: {co2:.0f}ppm
**Reward**: {reward:.2f}
""")
```

Shows the PPO agent making decisions in real time. Use st.empty() for
live-updating text, or st.line_chart for a rolling time series.

### Bottom Right: Scenario Testing

```python
if st.button("⚡ Typhoon Warning"):
    # 1. Modify delivery constraint
    new_delivery_hours = 6  # was 12

    # 2. Re-run Layer 2 MILP
    new_plan = optimize(forecast, constraints={**base_constraints,
                        'delivery_hours': new_delivery_hours})

    # 3. Update Layer 3 targets
    env.update_targets(new_plan['targets'])

    # 4. Show before/after comparison
    st.write(f"ROI change: {old_roi:.0f} → {new_plan['roi']:.0f} SGD")
    st.write(f"Solve time: {new_plan['solve_time_ms']}ms")
```

The button must:
1. Change the constraint
2. Re-solve in < 3 seconds
3. Update all dashboard panels
4. Show the delta (before → after)

## Implementation Notes

### Performance
- Layer 1 (XGBoost prediction): < 100ms
- Layer 2 (OR-Tools solve): < 1 second
- Layer 3 (PPO inference): < 10ms per step
- Typhoon re-solve: < 3 seconds total including UI update

### State Management
- Use st.session_state for current plan, forecast, and env state
- Avoid re-running the entire pipeline on every Streamlit rerun
- Cache model loading with @st.cache_resource

### Streamlit Specifics
- Use st.columns() for side-by-side layout
- Use st.tabs() if needed for additional views
- Use plotly for interactive charts (st.plotly_chart)
- Keep everything on one page — no multi-page app
- Test at 1920×1080 resolution (demo projector)

## What NOT to Build

- No login/auth (single user demo)
- No database (CSV in memory)
- No multi-tenant (single farm)
- No real-time sensor connection (simulated data)
- No mobile responsive (desktop demo only)
