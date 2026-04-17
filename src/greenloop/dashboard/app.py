"""GreenLoop Farm OS — Streamlit Dashboard.

Single-screen dashboard integrating all 3 layers:
- Layer 1: XGBoost demand forecast with confidence intervals
- Layer 2: OR-Tools MILP daily plan optimization
- Layer 3: PPO RL environment control (live inference log)
"""

import time
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config — MUST be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GreenLoop Farm OS",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports (after page config)
# ---------------------------------------------------------------------------
from greenloop.dashboard.design_decisions import render_design_decisions_panel  # noqa: E402
from greenloop.data.loader import (  # noqa: E402
    load_crops,
    load_electricity,
    load_shipments,
    load_staff,
)

# Layer 1 imports — if xgboost fails to load (usually missing libomp on macOS),
# we fail loudly at dashboard startup rather than ship fake forecasts silently.
# The `greenloop` CLI handles the libomp dylib lookup before this point.
from greenloop.layer1.features import build_features  # noqa: E402
from greenloop.layer1.model import load_models, train_models  # noqa: E402
from greenloop.layer1.predict import predict_demand  # noqa: E402
from greenloop.layer2.exceptions import InfeasibleError  # noqa: E402
from greenloop.layer2.optimizer import build_and_solve  # noqa: E402
from greenloop.layer2.scenarios import apply_typhoon, compare_plans  # noqa: E402
from greenloop.layer3.environment import HydroFarmEnv  # noqa: E402
from greenloop.llm import LLMUnavailable, explain_plan, llm_is_configured  # noqa: E402

# Layer 3 PPO import — may fail without trained model
try:
    from greenloop.layer3.inference import load_agent, run_inference_step  # noqa: E402

    LAYER3_AGENT_AVAILABLE = True
except Exception:
    LAYER3_AGENT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def get_data():
    crops = load_crops()
    shipments = load_shipments()
    electricity = load_electricity()
    staff = load_staff()
    return crops, shipments, electricity, staff


@st.cache_data
def get_electricity_days(electricity):
    """Return sorted list of unique dates in electricity.csv."""
    return sorted(electricity["date"].unique())


@st.cache_data
def get_forecast(_shipments):
    """Run Layer 1 forecast. Returns dict {crop_id: {predicted_kg, lower_ci, upper_ci}}."""
    features = build_features(_shipments)
    models_dir = Path(__file__).resolve().parent.parent.parent.parent / "models"
    try:
        models = load_models(models_dir)
    except FileNotFoundError:
        models = train_models(features, models_dir)
    return predict_demand(models, features)


# ---------------------------------------------------------------------------
# Streamlit App
# ---------------------------------------------------------------------------
def main():
    crops, shipments, electricity_df, staff = get_data()
    available_days = get_electricity_days(electricity_df)

    # ── Header ──
    col_title, col_date = st.columns([3, 1])
    with col_title:
        st.title("GreenLoop Farm OS")
    with col_date:
        st.markdown(f"### {date.today().strftime('%d %b %Y')}")

    st.divider()

    # ── Sidebar: Inputs ──
    st.sidebar.header("Farm Parameters")
    selected_date = st.sidebar.selectbox(
        "Electricity tariff date",
        options=available_days,
        index=len(available_days) - 1,
        format_func=lambda d: d.strftime("%d %b %Y") if hasattr(d, "strftime") else str(d),
    )
    # Filter electricity to the selected day
    electricity = electricity_df[electricity_df["date"] == selected_date].copy()
    headcount = st.sidebar.slider("Available staff", 1, 10, 6)

    # ── Sidebar: Design decisions (Dimension A evidence for VC pitch) ──
    render_design_decisions_panel()

    # ── Layer 1: Demand Forecast ──
    forecast = get_forecast(shipments)

    # ── Layer 2: Optimize ──
    plan = _solve_plan(forecast, crops, electricity, staff, headcount)

    # ── Top KPI strip — most VC-relevant numbers above the fold ──
    _render_kpi_strip(plan)

    # ── Electricity tariff chart ──
    _render_electricity_chart(electricity)

    # ── Optional AI narrative (provider-agnostic; any OpenAI-compatible endpoint) ──
    _render_ai_explainer(forecast, plan)

    st.divider()

    # ── Layout: 2 columns ──
    left, right = st.columns([1, 2])

    with left:
        _render_forecast_table(forecast)

    with right:
        if plan:
            _render_plan(plan)
        else:
            st.warning("No feasible plan. Try increasing staff or relaxing constraints.")

    st.divider()

    # ── Bottom: RL Control + Scenario Testing ──
    bot_left, bot_right = st.columns(2)

    with bot_left:
        _render_rl_control()

    with bot_right:
        _render_scenario_testing(forecast, crops, electricity, staff, headcount, plan)


# ---------------------------------------------------------------------------
# Layer 2 solver
# ---------------------------------------------------------------------------
def _solve_plan(forecast, crops, electricity, staff, headcount):
    """Solve Layer 2 MILP. Return plan dict or None on infeasibility."""
    try:
        return build_and_solve(
            forecast=forecast,
            crops_df=crops,
            electricity_df=electricity,
            staff_df=staff,
            available_headcount=headcount,
        )
    except InfeasibleError as e:
        st.error(f"**No feasible plan:** {e}")
        if e.binding_constraint:
            st.info(f"**Suggestion:** {e.binding_constraint}")
        return None


# ---------------------------------------------------------------------------
# Forecast display
# ---------------------------------------------------------------------------
def _render_forecast_table(forecast):
    st.subheader("Demand Forecast (Layer 1)")

    crop_names = {
        "kai_lan": "Kai Lan",
        "baby_spinach": "Baby Spinach",
        "lettuce_mambo": "Lettuce (Mambo)",
        "chye_sim": "Chye Sim",
        "arugula": "Arugula",
        "pak_choi": "Pak Choi",
        "kale": "Kale",
        "basil_thai": "Thai Basil",
        "coriander": "Coriander",
        "mint": "Mint",
    }

    rows = []
    for crop_id, vals in forecast.items():
        pred = vals["predicted_kg"]
        lower = vals["lower_ci"]
        upper = vals["upper_ci"]
        buffer_pct = ((upper - pred) / pred * 100) if pred > 0 else 0
        rows.append(
            {
                "Crop": crop_names.get(crop_id, crop_id),
                "Predicted (kg)": f"{pred:.1f}",
                "Lower CI": f"{lower:.1f}",
                "Upper CI": f"{upper:.1f}",
                "Buffer": f"±{buffer_pct:.0f}%",
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    # CI bar chart
    fig = go.Figure()
    crops_sorted = list(forecast.keys())
    names = [crop_names.get(c, c) for c in crops_sorted]
    preds = [forecast[c]["predicted_kg"] for c in crops_sorted]
    lowers = [forecast[c]["lower_ci"] for c in crops_sorted]
    uppers = [forecast[c]["upper_ci"] for c in crops_sorted]
    errors_low = [p - lo for p, lo in zip(preds, lowers, strict=True)]
    errors_high = [u - p for u, p in zip(uppers, preds, strict=True)]

    fig.add_trace(
        go.Bar(
            x=names,
            y=preds,
            error_y=dict(type="data", symmetric=False, array=errors_high, arrayminus=errors_low),
            marker_color=[
                "#2ecc71",  # Arugula — green
                "#3498db",  # Baby Spinach — blue
                "#9b59b6",  # Thai Basil — purple
                "#e67e22",  # Chye Sim — orange
                "#e74c3c",  # Coriander — red
                "#1abc9c",  # Kai Lan — teal
                "#f1c40f",  # Kale — yellow
                "#2c3e50",  # Lettuce — dark blue
                "#e91e63",  # Mint — pink
                "#00bcd4",  # Pak Choi — cyan
            ],
            name="Predicted (kg)",
        )
    )
    fig.update_layout(
        title="Demand Forecast with 90% CI",
        yaxis_title="kg",
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# KPI header strip — most VC-relevant numbers above the fold
# ---------------------------------------------------------------------------
def _render_ai_explainer(forecast, plan):
    """Collapsed expander that, when opened, asks the configured LLM for a
    plain-English brief on today's plan. Degrades to a setup hint if no
    LLM is configured — never serves fake narrative."""
    with st.expander("AI narrative brief (plain English)", expanded=False):
        if plan is None:
            st.caption("The plan is infeasible; nothing to narrate.")
            return
        if not llm_is_configured():
            st.info(
                "Set `LLM_PROVIDER` + the matching `{PROVIDER}_API_KEY` / "
                "`{PROVIDER}_MODEL` in `.env` to enable AI commentary. "
                "Supported: `openai`, `zai`, `minimax`."
            )
            return
        if st.button("Generate brief", key="ai_explainer_btn"):
            with st.spinner("Asking the model…"):
                try:
                    narrative = explain_plan(forecast, plan)
                    st.markdown(narrative)
                except LLMUnavailable as e:
                    st.error(f"LLM unavailable: {e.reason}")
                except Exception as e:  # noqa: BLE001 — surface provider errors verbatim
                    st.error(f"LLM request failed: {type(e).__name__}: {e}")


def _render_electricity_chart(electricity):
    """Render a line chart of the day's hourly electricity tariff rates."""
    st.subheader("Electricity Tariff (24h)")
    electricity = electricity.sort_values("hour").reset_index(drop=True)
    peak_hours = set(range(8, 22))  # 8am–10pm

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(electricity["hour"]),
            y=list(electricity["tariff_rate_sgd_per_kwh"]),
            mode="lines+markers",
            line=dict(color="#3498db", width=2),
            marker=dict(size=6),
            name="Tariff (SGD/kWh)",
        )
    )
    # Shade peak hours
    for h in range(24):
        if h in peak_hours:
            fig.add_vrect(
                x0=h - 0.5, x1=h + 0.5,
                fillcolor="#e74c3c", opacity=0.06,
                line_width=0,
            )
    fig.update_layout(
        xaxis_title="Hour of day",
        yaxis_title="SGD/kWh",
        height=180,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(dtick=2, tick0=0),
        showlegend=False,
        annotations=[
            dict(x=3, y=electricity["tariff_rate_sgd_per_kwh"].max() + 0.01,
                 text="🌙 Off-peak (< 8am / ≥ 10pm)", showarrow=False,
                 font=dict(size=10, color="#2c3e50")),
            dict(x=15, y=electricity["tariff_rate_sgd_per_kwh"].max() + 0.01,
                 text="☀️ Peak (8am–10pm)", showarrow=False,
                 font=dict(size=10, color="#e74c3c")),
        ],
    )
    st.plotly_chart(fig, width="stretch")
    avg_rate = electricity["tariff_rate_sgd_per_kwh"].mean()
    st.caption(f"Average: **${avg_rate:.2f}/kWh** · Off-peak **$0.18** · Peak **$0.28**")


def _render_kpi_strip(plan):
    """Render the top-of-page KPI strip. Always visible, even when the plan is None."""
    c1, c2, c3, c4, c5 = st.columns(5)
    if plan is None:
        c1.metric("Profit (SGD)", "—")
        c2.metric("Revenue (SGD)", "—")
        c3.metric("Energy cost (SGD)", "—")
        c4.metric("Labour cost (SGD)", "—")
        c5.metric("Solve time", "—", help="MILP wall-clock, rounded to ms")
        return
    cost = plan.get("cost_breakdown", {}) or {}
    c1.metric("Profit (SGD)", f"${plan.get('objective_value_sgd', 0):,.2f}")
    c2.metric("Revenue (SGD)", f"${cost.get('revenue', 0):,.2f}")
    c3.metric("Energy cost (SGD)", f"${cost.get('electricity', 0):,.2f}")
    c4.metric("Labour cost (SGD)", f"${cost.get('labour', 0):,.2f}")
    solve_ms = plan.get("solve_time_ms", 0)
    c5.metric(
        "Solve time",
        f"{solve_ms:.0f} ms",
        help="MILP wall-clock. Sub-second solves let the Typhoon button re-plan in real time.",
    )


# ---------------------------------------------------------------------------
# Plan display
# ---------------------------------------------------------------------------
def _render_plan(plan):
    st.subheader("Today's Optimal Plan (Layer 2)")

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    cost = plan.get("cost_breakdown", {})
    revenue = cost.get("revenue", 0)
    total = plan.get("objective_value_sgd", 0)
    m1.metric("Revenue", f"${revenue:,.0f}")
    m2.metric("Profit", f"${total:,.0f}")
    m3.metric("Temp Target", f"{plan.get('room_temp_target_c', 22)}°C")
    m4.metric("Solve Time", f"{plan.get('solve_time_ms', 0)}ms")

    # LED Schedule chart
    led = plan.get("led_schedule", {})
    if led:
        fig_led = go.Figure()
        for tier_name, schedule in list(led.items())[:5]:  # Show top 5 tiers
            fig_led.add_trace(
                go.Bar(
                    x=list(range(24)),
                    y=schedule,
                    name=f"{tier_name} ({plan.get('rack_layout', {}).get(tier_name, '?')})",
                    opacity=0.7,
                )
            )
        fig_led.update_layout(
            title="LED Schedule (24h)",
            xaxis_title="Hour",
            yaxis_title="On/Off",
            height=220,
            margin=dict(l=20, r=20, t=40, b=20),
            barmode="group",
            showlegend=True,
            legend=dict(font=dict(size=9)),
        )
        st.plotly_chart(fig_led, width="stretch")

    # Staff shifts
    shifts = plan.get("staff_shifts", [])
    if shifts:
        shift_df = pd.DataFrame(shifts)
        st.dataframe(shift_df, width="stretch", hide_index=True)

    # Cost breakdown
    if cost:
        st.caption(
            f"Energy: ${cost.get('electricity', 0):,.0f} | "
            f"Labour: ${cost.get('labour', 0):,.0f} | "
            f"Waste: ${cost.get('waste_penalty', 0):,.0f}"
        )


# ---------------------------------------------------------------------------
# RL Control
# ---------------------------------------------------------------------------
def _render_rl_control():
    st.subheader("RL Control (Layer 3)")

    # Initialize env in session state
    if "rl_env" not in st.session_state:
        st.session_state.rl_env = HydroFarmEnv()
        st.session_state.rl_obs, _ = st.session_state.rl_env.reset()
        st.session_state.rl_step = 0
        st.session_state.rl_rewards = []

    env = st.session_state.rl_env
    obs = st.session_state.rl_obs

    # Try to load trained agent; fall back to random actions
    agent = None
    try:
        if LAYER3_AGENT_AVAILABLE:
            agent = load_agent()
    except FileNotFoundError:
        pass

    # Run a few steps on button press
    if st.button("▶ Run 10 steps"):
        for _ in range(10):
            if agent:
                action, obs, reward, info = run_inference_step(agent, env, obs)
            else:
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    obs, _ = env.reset()
                    st.session_state.rl_step = 0
                    st.session_state.rl_rewards = []
                    break

            st.session_state.rl_obs = obs
            st.session_state.rl_step += 1
            st.session_state.rl_rewards.append(reward)

    # Display current state
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Temperature", f"{obs[0]:.1f}°C", delta=f"{obs[6]:.1f}°C from target")
        st.metric("CO₂", f"{obs[2]:.0f} ppm")
    with col2:
        st.metric("Humidity", f"{obs[1]:.1f}%", delta=f"{obs[7]:.1f}% from target")
        st.metric("Moisture", f"{obs[3]:.2f}")

    st.caption(
        f"Step: {st.session_state.rl_step}/1440 | "
        f"Agent: {'PPO' if agent else 'Random'} | "
        f"Total reward: {sum(st.session_state.rl_rewards):.1f}"
    )

    # Reward chart
    if st.session_state.rl_rewards:
        st.line_chart(st.session_state.rl_rewards, height=150)

    if (info := st.session_state.get("rl_info")) and info.get("constraint_violation"):
        st.warning("Safety constraint triggered — action blocked")


# ---------------------------------------------------------------------------
# Scenario Testing
# ---------------------------------------------------------------------------
def _render_scenario_testing(
    forecast, crops, electricity, staff, headcount, current_plan
):
    st.subheader("Scenario Testing")

    if st.button("⚡ Typhoon Warning"):
        t0 = time.time()

        base_kwargs = dict(
            forecast=forecast,
            crops_df=crops,
            electricity_df=electricity,
            staff_df=staff,
            available_headcount=headcount,
        )

        typhoon_kwargs = apply_typhoon(base_kwargs)

        try:
            typhoon_plan = build_and_solve(**typhoon_kwargs)
            elapsed = (time.time() - t0) * 1000

            st.success(f"Re-optimized in {elapsed:.0f}ms")

            if current_plan:
                comparison = compare_plans(current_plan, typhoon_plan)
                delta = comparison.get("delta", {})

                c1, c2, c3 = st.columns(3)
                c1.metric(
                    "Profit Change",
                    f"${typhoon_plan.get('objective_value_sgd', 0):,.0f}",
                    delta=f"{delta.get('objective_value_sgd', 0):,.0f}",
                )
                c2.metric(
                    "Delivery Window",
                    "6 hours",
                    delta="-6h from normal",
                    delta_color="inverse",
                )
                c3.metric("Solve Time", f"{elapsed:.0f}ms")

                # Update Layer 3 targets
                if "rl_env" in st.session_state:
                    st.session_state.rl_env.update_targets(
                        {
                            "temp": typhoon_plan.get("room_temp_target_c", 22),
                        }
                    )
                    st.info("Layer 3 targets updated for Typhoon scenario")
            else:
                st.write(f"Typhoon plan profit: ${typhoon_plan.get('objective_value_sgd', 0):,.0f}")

        except InfeasibleError as e:
            elapsed = (time.time() - t0) * 1000
            st.error(f"Typhoon plan infeasible ({elapsed:.0f}ms): {e}")
            if e.binding_constraint:
                st.info(f"Try: {e.binding_constraint}")

    st.caption(
        "Typhoon Warning cuts delivery window from 12h → 6h.\n"
        "Layer 2 re-optimizes the entire farm plan in real time."
    )


if __name__ == "__main__":
    main()
