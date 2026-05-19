"""Adopt a Kale — Streamlit Dashboard.

Single-screen dashboard integrating all 4 layers:
- Layer 0: Integration Platform (6 external APIs)
- Layer 1: XGBoost demand forecast + MILP production optimization
- Layer 2: PPO RL environment control (live inference log)
- Layer 3: Media RAG + Retail segmentation + Logistics VRP
"""

import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config — MUST be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Adopt a Kale",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports (after page config)
# ---------------------------------------------------------------------------
from greenloop.dashboard.components.task_list import render_today_actions  # noqa: E402
from greenloop.dashboard.design_decisions import render_design_decisions_panel  # noqa: E402
from greenloop.data.loader import (  # noqa: E402
    load_crops,
    load_shipments,
    load_staff,
)
from greenloop.data.ema import load_live_electricity  # noqa: E402

# Layer 1 imports — if xgboost fails to load (usually missing libomp on macOS),
# we fail loudly at dashboard startup rather than ship fake forecasts silently.
# The `greenloop` CLI handles the libomp dylib lookup before this point.
from greenloop.layer1.features import build_features  # noqa: E402
from greenloop.layer1.model import load_models, train_models  # noqa: E402
from greenloop.layer1.predict import predict_demand  # noqa: E402
from greenloop.layer2.exceptions import InfeasibleError  # noqa: E402
from greenloop.layer2.feasibility_check import validate_constraints  # noqa: E402
from greenloop.layer2.objective import MODE_LABELS, ObjectiveWeights  # noqa: E402
from greenloop.layer2.optimizer import build_and_solve  # noqa: E402
from greenloop.layer2.forecast_band import compute_profit_band  # noqa: E402
from greenloop.layer2.scenarios import (  # noqa: E402
    TyphoonScenarioInput,
    apply_typhoon,
    compare_plans,
)
from greenloop.layer2.sustainability import (  # noqa: E402
    compute_sustainability_kpis,
    compute_weekly_sustainability,
)
from greenloop.layer3.environment import HydroFarmEnv  # noqa: E402
from greenloop.layer3.autonomy_gate import AutonomyGate, AutonomyMode  # noqa: E402
from greenloop.layer1b.simulation import (  # noqa: E402
    GROWTH_BADGES,
    NUTRITION_BADGES,
    diagnose_all_racks_simulated,
    diagnose_batch,
    filename_to_rack_id,
    mock_diagnose,
    mock_diagnose_from_image,
    RACK_SCENARIOS,
)
from greenloop.llm import LLMUnavailable, explain_plan, llm_is_configured  # noqa: E402
from greenloop.rag.agent import RAGAgent  # noqa: E402

# Governance — Deployment Gate
from greenloop.governance.deployment_gate import (  # noqa: E402
    DeploymentDecision,
    GateResult,
    GateStatus,
    evaluate_all_gates,
)
from greenloop.governance.implications_audit import (  # noqa: E402
    ImpactSeverity,
    ImplicationCategory,
    get_all_implications,
    get_stakeholder_impacts,
)

# Monitoring — Drift Detection
from greenloop.monitoring.drift_detector import (  # noqa: E402
    DriftSeverity,
    DriftType,
    get_all_drift_checks,
    run_all_checks,
)
from greenloop.rag.hitl import (  # noqa: E402
    Tone,
    TONE_LABELS,
    FeedbackRecord,
    QueryRecord,
    log_feedback,
    log_query,
    get_top_questions,
    get_feedback_summary,
    get_system_prompt,
)

# ---------------------------------------------------------------------------
# v6.2 Integration Platform helpers
# ---------------------------------------------------------------------------


def _get_live_electricity_df():
    """Load + cache live EMA electricity data in session_state (one API call per session)."""
    if "live_electricity_df" not in st.session_state:
        try:
            from greenloop.data.ema import load_live_electricity

            df = load_live_electricity(days=7)
            st.session_state["live_electricity_df"] = df
        except Exception:
            st.session_state["live_electricity_df"] = None
    return st.session_state.get("live_electricity_df")


def _get_avg_electricity_rate_for_date(selected_date: str) -> tuple[float, str]:
    """
    Return (rate_sgd_per_kwh, source_label) for the given date's representative rate.
    Uses the cached live EMA loader. Falls back to a sensible default.
    """
    df = _get_live_electricity_df()
    if df is not None and len(df) > 0 and "tariff_rate_sgd_per_kwh" in df.columns:
        day_df = df[df["date"] == selected_date]
        if len(day_df) > 0:
            rate = float(day_df["tariff_rate_sgd_per_kwh"].iloc[-1])
            return rate, "EMA / data.gov.sg"
        # Date not in live data — use last available
        rate = float(df["tariff_rate_sgd_per_kwh"].iloc[-1])
        return rate, "EMA / data.gov.sg (lag)"
    return 0.29, "Fallback (CSV)"


def _get_today_shopee_orders() -> tuple[float, str]:
    """Return (total_kg, source_label) for the latest available Shopee orders. Cached in session."""
    if "shopee_orders_cache" not in st.session_state:
        try:
            from greenloop.data.loader import load_orders
            df = load_orders()
            # Use the latest available date as proxy for today
            latest_date = df["date"].max()
            latest_df = df[df["date"] == latest_date]
            total_kg = float(latest_df["kg"].sum())
            date_str = pd.Timestamp(latest_date).strftime("%d %b %Y")
            st.session_state["shopee_orders_cache"] = (total_kg, f"Shopee / RedMart / F&B · {date_str}")
        except Exception:
            st.session_state["shopee_orders_cache"] = (0.0, "Load error")
    return st.session_state.get("shopee_orders_cache", (0.0, "Not loaded"))


def _get_shopee_crop_breakdown() -> tuple[pd.DataFrame, str]:
    """Return (crop_breakdown_df, date_str) for today's orders chart. Cached in session."""
    if "shopee_crop_cache" not in st.session_state:
        try:
            from greenloop.data.loader import load_orders
            df = load_orders()
            latest_date = df["date"].max()
            latest_df = df[df["date"] == latest_date]
            breakdown = (
                latest_df.groupby("crop_id")["kg"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )
            breakdown.columns = ["crop", "kg"]
            date_str = pd.Timestamp(latest_date).strftime("%d %b %Y")
            st.session_state["shopee_crop_cache"] = (breakdown, date_str)
        except Exception:
            st.session_state["shopee_crop_cache"] = (pd.DataFrame(columns=["crop", "kg"]), "N/A")
    return st.session_state.get("shopee_crop_cache", (pd.DataFrame(columns=["crop", "kg"]), "N/A"))


def _get_today_staff_summary() -> tuple[int, int, str]:
    """
    Return (on_duty_count, total_count, source_label) for staff availability.
    Uses sidebar slider/override values if available (set in session_state),
    otherwise falls back to staff.csv availability column.
    """
    # Priority 1: Manager override
    if st.session_state.get("override_active") and st.session_state.get("override_staff"):
        on_duty = int(st.session_state["override_staff"])
        total = on_duty  # override implies full control
        return on_duty, total, "Manager override"
    # Priority 2: Sidebar sliders (stored after sidebar renders)
    if "effective_headcount" in st.session_state:
        total = int(st.session_state.get("total_staff", 8))
        on_duty = int(st.session_state["effective_headcount"])
        return on_duty, total, "Sidebar sliders"
    # Fallback: read from staff.csv
    try:
        from greenloop.data.loader import load_staff
        staff_df = load_staff()
        total = len(staff_df)
        if "availability" in staff_df.columns:
            avail_lower = staff_df["availability"].astype(str).str.lower()
            on_duty = int(avail_lower.str.contains("avail", na=False).sum())
            if on_duty == 0:
                on_duty = total
            return on_duty, total, "staff.csv (availability)"
        return total, total, "staff.csv"
    except Exception:
        return 5, 5, "Fallback"


# Layer 3 PPO import — may fail without trained model
try:
    from greenloop.layer3.agent import HydroFarmAgent  # noqa: E402

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
    electricity = load_live_electricity()
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
    models_dir = Path(__file__).resolve().parent.parent.parent.parent / "models" / "layer1_v2"
    try:
        models = load_models(models_dir)
    except FileNotFoundError:
        models = train_models(features, models_dir)
    return predict_demand(models, features)


@st.cache_data(ttl=3600)
def get_weekly_sustainability(crops, electricity_df, staff):
    """Pre-compute sustainability KPIs for the last 7 available electricity days.

    Runs the optimizer once per day — cached for 1 hour to avoid recalculation
    on every dashboard interaction.
    """
    from greenloop.layer1.features import build_features as build_feats
    from greenloop.layer1.model import load_models, train_models
    from greenloop.layer1.predict import predict_demand as _predict
    from greenloop.layer1b.simulation import diagnose_all_racks_simulated

    all_dates = sorted(electricity_df["date"].unique())
    recent = all_dates[-7:]

    rows = []
    for day in recent:
        day_str = str(day)[:10]
        elec_day = electricity_df[electricity_df["date"] == day].copy()
        # Build forecast from shipments up to this day
        cutoff = pd.Timestamp(day) - pd.Timedelta(days=1)
        relevant = staff  # unused but kept for signature compatibility
        shipments_subset = load_shipments()
        shipments_subset = shipments_subset[pd.to_datetime(shipments_subset["date"]) <= cutoff]
        if len(shipments_subset) < 10:
            continue
        try:
            features = build_feats(shipments_subset)
            models_dir = Path(__file__).resolve().parent.parent.parent.parent / "models" / "layer1_v2"
            try:
                models = load_models(models_dir)
            except FileNotFoundError:
                models = train_models(features, models_dir)
            forecast = _predict(models, features)
            cv_diag = diagnose_all_racks_simulated()
            plan = build_and_solve(
                forecast=forecast,
                crops_df=crops,
                electricity_df=elec_day,
                staff_df=staff,
                available_headcount=6,
                cv_diagnosis=cv_diag,
            )
            kpis = compute_sustainability_kpis(plan, forecast, crops)
            rows.append({
                "date": day_str,
                "water_saved_l": kpis["water_saved_l"],
                "co2_avoided_kg": kpis["co2_avoided_kg"],
                "off_peak_pct": kpis["off_peak_energy_ratio_pct"],
            })
        except Exception:
            # Skip days where the optimizer fails (e.g. missing data)
            continue

    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["date", "water_saved_l", "co2_avoided_kg", "off_peak_pct"]
    )


# ---------------------------------------------------------------------------
# Streamlit App
# ---------------------------------------------------------------------------
def main():
    crops, shipments, electricity_df, staff = get_data()
    available_days = get_electricity_days(electricity_df)
    # ── Layer 1: Demand Forecast (needed by sidebar HITL overrides) ──
    forecast = get_forecast(shipments)

    # ── Header ──
    col_title, col_date = st.columns([3, 1])
    with col_title:
        st.title("Adopt a Kale")
    with col_date:
        st.markdown(f"### {date.today().strftime('%d %b %Y')}")

    # ── v6.2 Autopilot Status Badge ─────────────────────────────────────
    # v6.2: checks both typhoon_active (existing button) and typhoon_mode (promo trigger)
    typhoon_on = st.session_state.get("typhoon_mode") or st.session_state.get("typhoon_active")
    col_status, col_date_badge, col_farm = st.columns([2, 1, 1])
    with col_status:
        if typhoon_on:
            st.error("⚡ Typhoon Mode Active | Re-optimization in progress")
        elif st.session_state.get("override_active"):
            st.warning("👤 Manager Override Applied")
        else:
            st.success("✓ Autopilot Status: Plan Generated 06:00 SGT")
    with col_date_badge:
        st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    with col_farm:
        st.info("🏭 Jurong West Farm")

    # ── Sidebar: Farm AI ─────────────────────────────────────────────────
    st.sidebar.header("Farm AI")
    # ⚡ Electricity: date selector + 24h chart combined
    st.sidebar.subheader("⚡ Electricity Tariff")
    selected_date = st.sidebar.selectbox(
        "Select date",
        options=available_days,
        index=len(available_days) - 1,
        format_func=lambda d: d.strftime("%d %b %Y") if hasattr(d, "strftime") else str(d),
    )
    electricity = electricity_df[electricity_df["date"] == selected_date].copy()
    _render_electricity_sidebar(electricity_df, selected_date, electricity)

    # ── HITL: Optimization mode ──
    # ── HITL: Manual constraints ──
    with st.sidebar.expander("🔧 Override", expanded=False):
        st.markdown("**Exclude racks today:**")
        excluded_racks: list[int] = []
        for tier in range(10):
            crop = None
            if forecast is not None:
                # Try to get current crop from last plan if available
                crop = None
            if st.checkbox(f"Rack {tier}", value=False, key=f"exclude_rack_{tier}"):
                excluded_racks.append(tier)

        st.markdown("**Staff unavailable:**")
        unavailable_shifts: list[str] = []
        for shift in ["morning", "afternoon", "night"]:
            if st.checkbox(f"No {shift.capitalize()} shift", value=False, key=f"no_shift_{shift}"):
                unavailable_shifts.append(shift)

        if st.button("Apply override", use_container_width=True):
            validation = validate_constraints(excluded_racks, unavailable_shifts, forecast, crops)
            if not validation:
                st.success("Constraints validated — re-solving...")
                st.session_state["_hitl_excluded_racks"] = excluded_racks
                st.session_state["_hitl_unavailable_shifts"] = unavailable_shifts
            elif validation.severity == "error":
                st.error(validation.reason)
            else:
                st.warning(validation.reason if validation.reason else "Tight but feasible.")
                st.session_state["_hitl_excluded_racks"] = excluded_racks
                st.session_state["_hitl_unavailable_shifts"] = unavailable_shifts
        else:
            excluded_racks = st.session_state.get("_hitl_excluded_racks", [])
            unavailable_shifts = st.session_state.get("_hitl_unavailable_shifts", [])

    # ── Sidebar: Available Staff ──────────────────────────────────────────
    st.sidebar.divider()
    st.sidebar.subheader("👷 Available Staff")
    _farm_ops = staff[staff["role"] == "Farm Operations"]
    _logistics = staff[staff["role"] == "Logistics"]
    role_counts: dict[str, int] = {}
    if len(_farm_ops) > 0:
        available = st.sidebar.slider("Farm Operations", 0, len(_farm_ops), len(_farm_ops), key="staff_farm_ops")
        role_counts["Farm Operations"] = available
    if len(_logistics) > 0:
        available = st.sidebar.slider("Logistics", 0, len(_logistics), len(_logistics), key="staff_logistics")
        role_counts["Logistics"] = available
    st.sidebar.caption("Supervisor: 1 (fixed)")
    role_counts["Supervisor"] = 1
    headcount = sum(role_counts.values())
    st.session_state["effective_headcount"] = headcount
    st.session_state["total_staff"] = len(staff)

    # ── Sidebar: Design decisions (Dimension A evidence for VC pitch) ──
    render_design_decisions_panel()

    # ── v6.2 Integration Platform — Auto-Fetched Cards ─────────────────
    # (Moved after sidebar so staff slider values are available via session_state)
    st.markdown("##### 📡 Integration Platform — Auto-Fetched Data")
    st.caption("Phase 1 MVP: 2 live integrations (EMA Energy, Staff Calendar). Phase 2: full 6-API stack.")

    _today_sg = date.today().isoformat()
    rate, rate_source = _get_avg_electricity_rate_for_date(_today_sg)
    on_duty, total_staff, staff_source = _get_today_staff_summary()
    shopee_kg, shopee_source = _get_today_shopee_orders()

    cards_col1, cards_col2, cards_col3, cards_col4 = st.columns(4)

    with cards_col1:
        st.metric(
            label="⚡ EMA Energy",
            value=f"SGD {rate:.3f}/kWh",
            delta=f"✓ Live: {rate_source}",
            delta_color="off",
        )
        st.caption(f"Live · {date.today().strftime('%d %b %Y')} · {rate_source}")

    with cards_col2:
        st.metric(
            label="🛒 Shopee Orders",
            value=f"{shopee_kg:.1f} kg",
            delta=f"✓ {shopee_source}",
            delta_color="off",
        )
        st.caption("Live")

    with cards_col3:
        st.metric(
            label="📅 Staff (Calendar)",
            value=f"{on_duty} / {total_staff}",
            delta=f"✓ {staff_source}",
            delta_color="off",
        )
        st.caption("From sidebar sliders")

    with cards_col4:
        st.metric(
            label="🌧️ NEA Weather",
            value="33°C / 80%",
            delta="⚠️ Afternoon thunderstorm",
            delta_color="off",
        )
        st.caption("Mock data — NEA API Phase 2")

    # ── Shopee Orders Crop Breakdown ───────────────────────────────────
    crop_df, crop_date_str = _get_shopee_crop_breakdown()
    if len(crop_df) > 0:
        crop_colors_map = {
            "kai_lan": "#1abc9c",
            "spinach": "#3498db",
            "lettuce": "#2ecc71",
            "arugula": "#f1c40f",
            "chye_sim": "#e67e22",
        }
        crop_df["color"] = crop_df["crop"].map(
            lambda c: crop_colors_map.get(c, "#95a5a6")
        )
        fig_crop = px.bar(
            crop_df,
            x="crop",
            y="kg",
            color="color",
            color_discrete_map="identity",
            title=f"📦 Today's Orders by Crop — {crop_date_str}",
            labels={"kg": "kg", "crop": ""},
            text="kg",
        )
        fig_crop.update_layout(
            showlegend=False,
            xaxis_tickangle=-30,
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_crop, use_container_width=True)

    # Manager override (collapsed by default)
    with st.expander("✏️ Manager Override (when auto-fetched values need adjustment)"):
        oc1, oc2 = st.columns(2)
        with oc1:
            override_rate = st.number_input(
                "Electricity rate override (SGD/kWh)",
                value=rate,
                step=0.01,
                min_value=0.0,
                max_value=2.0,
                key="override_rate_input",
            )
            override_staff = st.number_input(
                "Staff count override",
                value=int(on_duty),
                min_value=1,
                max_value=20,
                key="override_staff_input",
            )
        with oc2:
            override_demand = st.number_input(
                "Order volume override (kg)",
                value=100,
                step=10,
                min_value=0,
                key="override_demand_input",
            )
            override_weather = st.selectbox(
                "Weather override",
                ["Normal", "Rain Expected", "Typhoon Alert"],
                key="override_weather_input",
            )

        col_apply, col_reset = st.columns(2)
        with col_apply:
            if st.button("Apply Override", key="apply_override_btn", use_container_width=True):
                st.session_state["override_active"] = True
                st.session_state["override_rate"] = override_rate
                st.session_state["override_staff"] = override_staff
                st.session_state["override_demand"] = override_demand
                st.session_state["override_weather"] = override_weather
                st.success("Override applied. Re-run optimization to see updated plan.")
        with col_reset:
            if st.session_state.get("override_active"):
                if st.button("🔄 Reset to Auto-Fetched", key="reset_override_btn", use_container_width=True):
                    for k in ["override_active", "override_rate", "override_staff", "override_demand", "override_weather"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()

    st.divider()

    # ── Layer 2: Optimize ──
    # Merge uploaded photo diagnoses into the simulation (photo takes priority per rack).
    cv_overrides: dict = st.session_state.get("rack_diagnoses", {})
    plan = _solve_plan(
        forecast,
        crops,
        electricity,
        staff,
        headcount,
        st.session_state.get("opt_mode", "balanced"),
        excluded_racks,
        unavailable_shifts,
        cv_diagnosis_overrides=cv_overrides if cv_overrides else None,
    )

    # ── Share Farm AI outputs with other pages ────────────────────────────
    if plan:
        from greenloop.data.shared_data import save_farm_output
        save_farm_output(plan, forecast)

    # ── Sidebar: Farm Environment 24h slider ────────────────────────────
    _render_environment_sidebar(plan, electricity_df)

    # ── Today's Actions — farm-manager task list ────────────────────────────
    render_today_actions(plan)

    # ── Transfer Learning diagnosis (Layer 1b) — above the fold ──
    _render_cv_diagnosis(plan, electricity_df)

    # ── Optional AI narrative (provider-agnostic; any OpenAI-compatible endpoint) ──
    _render_ai_explainer(forecast, plan)

    # ── Forecast: Demand & Rack Assignments (Layer 1 → 2) ──
    _render_forecast_horizontal(forecast, plan)

    st.divider()

    # ── Layer 2: Optimal Plan ──
    if plan:
        _render_plan(plan, electricity_df)
    else:
        st.warning("No feasible plan. Try increasing staff or relaxing constraints.")

    st.divider()

    # ── Sustainability KPIs ─────────────────────────────────────────────
    _render_sustainability_section(plan, forecast, crops, electricity_df, staff)

    # ── Bottom: RL Control + Scenario Testing ──
    bot_left, bot_right = st.columns(2)

    with bot_left:
        _render_rl_control()

    with bot_right:
        _render_scenario_testing(forecast, crops, electricity, staff, headcount, plan, st.session_state.get("opt_mode", "balanced"), excluded_racks, unavailable_shifts)

    st.divider()

    st.divider()

    # ── Media AI Chatbot (Layer 5 RAG) ──────────────────────────────────
    _render_media_ai_chat()


# ---------------------------------------------------------------------------
# Media AI Chatbot
# ---------------------------------------------------------------------------
_ADMIN_PASSWORD = "greenloop-admin"


def _render_media_ai_chat():
    """Media AI chatbot panel with HITL controls."""
    st.subheader("Media AI Chatbot (Layer 5)")

    # Persistent RAG agent and session state — init with error guard
    try:
        if "rag_agent" not in st.session_state:
            st.session_state.rag_agent = RAGAgent()
            st.session_state.rag_history: list[dict] = []
            st.session_state.rag_session_id = datetime.now().strftime("%Y%m%d%H%M%S")
            st.session_state.rag_tone = Tone.NEUTRAL
            st.session_state.rag_last_answer = ""

        agent = st.session_state.rag_agent
        history = st.session_state.rag_history
        agent_ready = True
        demo_mode = agent._is_demo_mode()
    except Exception as exc:
        st.error(f"Media AI failed to load: {exc}")
        agent_ready = False
        demo_mode = False
        history = []

    # Status bar
    if agent_ready:
        mode_label = "Demo mode (no LLM API key)" if demo_mode else "Live RAG + LLM"
        st.caption(f"🔗 Media AI · {mode_label} · Try: 'what crops do you grow', 'water savings', 'pesticides', 'location'")

    # Tone selector
    tone_keys = list(Tone)
    tone_labels = [TONE_LABELS[k] for k in tone_keys]
    current_idx = 1
    if agent_ready:
        try:
            current_idx = tone_keys.index(st.session_state.rag_tone)
        except ValueError:
            current_idx = 1  # default to Neutral

    selected_tone_label = st.radio(
        "Response tone",
        options=tone_labels,
        index=current_idx,
        horizontal=True,
        help="Sales: enthusiastic, ROI-focused. Technical: precise metrics. Neutral: balanced.",
        key="rag_tone_radio",
        disabled=not agent_ready,
    )
    if agent_ready:
        new_tone = Tone([k for k, v in TONE_LABELS.items() if v == selected_tone_label][0])
        if new_tone != st.session_state.rag_tone:
            st.session_state.rag_tone = new_tone

    # Chat history
    chat_container = st.container()
    with chat_container:
        if not agent_ready:
            st.warning("Media AI failed to initialize. Check your API keys in .env")
        for msg in history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])
                    # Feedback buttons
                    if msg.get("show_feedback", False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.button("👍 Good", key=f"good_{msg['_id']}")
                        with col2:
                            st.button("💬 Needs refinement", key=f"refine_{msg['_id']}")

    # Admin mode toggle
    with st.expander("🔒 Admin settings"):
        admin_password = st.text_input(
            "Admin password",
            type="password",
            help="Enter to unlock feedback analytics",
        )
        is_admin = admin_password == _ADMIN_PASSWORD

        if is_admin:
            st.success("Admin mode active")
            # Feedback summary
            summary = get_feedback_summary()
            c1, c2 = st.columns(2)
            with c1:
                st.metric("👍 Good", summary.get("good", 0))
            with c2:
                st.metric("💬 Needs refinement", summary.get("needs_refinement", 0))

            # Top-10 questions
            top_qs = get_top_questions(10)
            if top_qs:
                st.write("**Top 10 questions**")
                for i, (q, cnt) in enumerate(top_qs, 1):
                    st.write(f"{i}. ({cnt}) {q[:80]}")
            else:
                st.info("No queries logged yet.")
        else:
            if admin_password:
                st.warning("Incorrect password.")

    # Chat input
    if agent_ready and (question := st.chat_input("Ask about Adopt a Kale Farm...")):
        # Add to history
        st.session_state.rag_history.append({"role": "user", "content": question})
        st.session_state["_last_question"] = question
        st.chat_message("user").write(question)

        # Get answer
        answer_text = "Sorry, I encountered an error generating a response."
        try:
            tone = st.session_state.rag_tone
            system_prompt = get_system_prompt(tone, "You are a helpful assistant for Adopt a Kale Farm.")

            # Call RAG agent (uses demo-mode answers if no LLM API key)
            answer_obj = agent.ask(question)
            answer_text = answer_obj.text
            sources = ", ".join(answer_obj.sources) if answer_obj.sources else "none"

            # Log query
            log_query(QueryRecord(
                timestamp=datetime.now().isoformat(),
                question=question,
                answer=answer_text,
                tone=tone.value,
                sources=sources,
                latency_ms=answer_obj.latency_ms,
                from_cache=answer_obj.from_cache,
                session_id=st.session_state.rag_session_id,
            ))

        except Exception as exc:
            logger.exception("rag.ask_failed")
            answer_text = (
                "Sorry, I encountered an error generating a response. "
                "Please try again or rephrase your question."
            )

        msg_id = len(st.session_state.rag_history)
        st.session_state.rag_history.append({
            "role": "assistant",
            "content": answer_text,
            "show_feedback": True,
            "_id": msg_id,
        })
        st.session_state.rag_last_answer = answer_text
        st.rerun()

    # Handle feedback buttons (triggered by rerun after button click)
    # We check all button keys in session_state
    for key, val in st.session_state.items():
        if key.startswith("good_") and val:
            idx = int(key.split("_")[1])
            st.session_state[key] = False  # reset
            _log_feedback_for_message(idx, "good")
            st.rerun()
        elif key.startswith("refine_") and val:
            idx = int(key.split("_")[1])
            st.session_state[key] = False  # reset
            _log_feedback_for_message(idx, "needs_refinement")
            st.rerun()


def _log_feedback_for_message(msg_id: int, rating: str) -> None:
    """Log feedback for a specific message in rag_history."""
    history = st.session_state.get("rag_history", [])
    # Find the message
    target = None
    for msg in history:
        if msg.get("_id") == msg_id:
            target = msg
            break
    if target is None:
        return

    log_feedback(FeedbackRecord(
        timestamp=datetime.now().isoformat(),
        question=st.session_state.get("_last_question", ""),
        answer=target["content"],
        tone=st.session_state.get("rag_tone", Tone.NEUTRAL).value,
        rating=rating,
        session_id=st.session_state.get("rag_session_id", ""),
    ))
    # Show confirmation
    st.toast(f"Feedback recorded: {rating}")


# ---------------------------------------------------------------------------
# Layer 2 solver
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def _solve_plan(
    forecast,
    crops,
    electricity,
    staff,
    headcount,
    mode_key="balanced",
    excluded_racks=None,
    unavailable_shifts=None,
    cv_diagnosis_overrides: dict | None = None,
):
    """Solve Layer 2 MILP with CV diagnosis. Return plan dict or None on infeasibility."""
    # Run Layer 1b CV diagnosis across all 10 racks.
    cv_diagnosis = diagnose_all_racks_simulated()
    # Override with per-rack diagnoses from uploaded photos (session_state).
    # Per-rack diagnoses take priority over simulation for that rack.
    if cv_diagnosis_overrides:
        for rack_num, diag_result in cv_diagnosis_overrides.items():
            rack_id = f"tier_{rack_num}"
            if rack_id in cv_diagnosis:
                cv_diagnosis[rack_id] = diag_result

    objective_weights = ObjectiveWeights.from_mode(mode_key)

    try:
        return build_and_solve(
            forecast=forecast,
            crops_df=crops,
            electricity_df=electricity,
            staff_df=staff,
            available_headcount=headcount,
            cv_diagnosis=cv_diagnosis,
            excluded_racks=excluded_racks,
            unavailable_shifts=unavailable_shifts,
            objective_weights=objective_weights,
        )
    except InfeasibleError as e:
        st.error(f"**No feasible plan:** {e}")
        if e.binding_constraint:
            st.info(f"**Suggestion:** {e.binding_constraint}")
        return None


# ---------------------------------------------------------------------------
def _render_forecast_horizontal(forecast, plan):
    """Render forecast as a single horizontal row of rack cards + bar chart below."""
    st.subheader("Demand Forecast & Rack Assignments (Layer 1 → 2)")

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

    crop_colors = {
        "kai_lan": "#1abc9c",
        "baby_spinach": "#3498db",
        "lettuce_mambo": "#2c3e50",
        "chye_sim": "#e67e22",
        "arugula": "#2ecc71",
        "pak_choi": "#00bcd4",
        "kale": "#f1c40f",
        "basil_thai": "#9b59b6",
        "coriander": "#e74c3c",
        "mint": "#e91e63",
    }

    rack_layout = plan.get("rack_layout", {}) if plan else {}

    # ── Colour legend ──────────────────────────────────────────────────
    st.caption(
        "**Colour guide:** "
        "Border colour = crop variety · "
        "🔴 High = top 25% demand · "
        "🟡 Medium = mid 50% · "
        "🟢 Low = bottom 25% · "
        "Range = 90% CI (lower – upper)"
    )

    # ── Build rack rows ─────────────────────────────────────────────────
    rack_rows = []
    for tier_num in range(10):
        rack_id = f"tier_{tier_num}"
        crop_id = rack_layout.get(rack_id, None)
        if crop_id is None or crop_id not in forecast:
            continue
        vals = forecast[crop_id]
        pred = vals["predicted_kg"]
        lower = vals["lower_ci"]
        upper = vals["upper_ci"]
        buffer_pct = ((upper - pred) / pred * 100) if pred > 0 else 0
        all_preds = sorted(forecast[c]["predicted_kg"] for c in forecast)
        q75 = all_preds[int(len(all_preds) * 0.75)] if all_preds else pred
        q25 = all_preds[int(len(all_preds) * 0.25)] if all_preds else pred
        if pred >= q75:
            priority = "🔴 High"
        elif pred <= q25:
            priority = "🟢 Low"
        else:
            priority = "🟡 Medium"
        rack_rows.append({
            "Rack": f"Rack {tier_num}",
            "Crop": crop_names.get(crop_id, crop_id),
            "Demand (kg)": round(pred, 1),
            "Range": f"{lower:.1f} – {upper:.1f}",
            "Buffer": f"±{buffer_pct:.0f}%",
            "Priority": priority,
            "_crop_id": crop_id,
        })

    if not rack_rows:
        st.info("No rack assignments yet — click **Re-solve Layer 2** to generate.")
        return

    # Sort by demand descending
    rack_rows.sort(key=lambda r: r["Demand (kg)"], reverse=True)

    # ── Legend ───────────────────────────────────────────────────────────
    leg = st.columns([1, 1, 1, 1])
    with leg[0]:
        st.markdown("🔴 **High** — top 25% demand")
    with leg[1]:
        st.markdown("🟡 **Medium** — mid 50%")
    with leg[2]:
        st.markdown("🟢 **Low** — bottom 25%")
    with leg[3]:
        st.markdown("📊 Sorted by demand ↓")

    # ── Horizontal rack cards — one column per rack ────────────────────
    n = len(rack_rows)
    col_widths = [1] * n
    rack_cols = st.columns(col_widths)

    for i, r in enumerate(rack_rows):
        color = crop_colors.get(r["_crop_id"], "#888888")
        with rack_cols[i]:
            st.markdown(
                f"""
                <div style="
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 8px 10px;
                    text-align: center;
                    background: #fafafa;
                    height: 100%;
                ">
                    <div style="font-size:0.75em; color:#888;">{r["Rack"]}</div>
                    <div style="font-size:0.85em; font-weight:bold; color:{color};">{r["Crop"]}</div>
                    <div style="font-size:1.4em; font-weight:bold; color:{color};">{r["Demand (kg)"]} kg</div>
                    <div style="font-size:0.75em; color:#666;">{r["Priority"]}</div>
                    <div style="font-size:0.7em; color:#aaa; margin-top:2px;">{r["Range"]} kg</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Bar chart below ──────────────────────────────────────────────────
    sorted_crops = [row["_crop_id"] for row in rack_rows]
    sorted_names = [crop_names.get(c, c) for c in sorted_crops]
    sorted_preds = [forecast[c]["predicted_kg"] for c in sorted_crops]
    sorted_colors = [crop_colors.get(c, "#888888") for c in sorted_crops]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sorted_names,
        y=sorted_preds,
        marker_color=sorted_colors,
        name="Predicted (kg)",
    ))
    fig.update_layout(
        title="Crop demand — sorted by tomorrow's orders",
        yaxis_title="kg",
        height=200,
        margin=dict(l=10, r=10, t=30, b=60),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Rack Rebalancing Proposal ────────────────────────────────────────
    if not rack_rows or not plan:
        return

    cv_details = (
        plan.get("cv_diagnosis_summary", {})
        .get("details", {})
    )
    rack_layout = plan.get("rack_layout", {})

    priority_rank = {"High": 3, "Medium": 2, "Low": 1}

    # Compute mismatch score: high-demand crop on low-priority tier
    swap_proposals = []
    for r in rack_rows:
        tier_num = int(r["Rack"].replace("Rack ", ""))
        demand_rank = priority_rank.get(r["Priority"], 2)
        # Tiers 0-4 = upper (better), 5-9 = lower
        rack_rank = 2 if tier_num <= 4 else 1  # upper=2, lower=1
        mismatch = demand_rank - rack_rank  # positive = high demand on lower rack
        crop_id = r["_crop_id"]

        # Skip if harvest_ready or has nutrition issue — don't move those
        diag = cv_details.get(f"tier_{tier_num}", {})
        growth_stage = diag.get("growth_stage", "")
        nutrition = diag.get("nutrition_status", "normal")
        is_locked = growth_stage == "harvest_ready" or nutrition in ("nitrogen_low", "water_stress")

        swap_proposals.append({
            **r,
            "tier_num": tier_num,
            "demand_rank": demand_rank,
            "rack_rank": rack_rank,
            "mismatch": mismatch,
            "is_locked": is_locked,
            "_crop_id": crop_id,
        })

    # Sort by mismatch descending — worst mismatches first
    swap_proposals.sort(key=lambda x: x["mismatch"], reverse=True)

    # Build suggested swaps: high-demand on lower rack ↔ low-demand on upper rack
    upper_low_demand = [p for p in swap_proposals if p["rack_rank"] == 2 and p["demand_rank"] == 1 and not p["is_locked"]]
    lower_high_demand = [p for p in swap_proposals if p["rack_rank"] == 1 and p["demand_rank"] >= 2 and not p["is_locked"]]

    proposals = []
    for low in upper_low_demand[:3]:
        for high in lower_high_demand[:3]:
            proposals.append({
                "from": f"Rack {low['tier_num']} → {low['Crop']} (Low demand, upper tier — move down)",
                "to": f"Rack {high['tier_num']} → {high['Crop']} (High demand, lower tier — move up)",
            })
            break

    if proposals:
        st.markdown("**Rack Rebalancing Proposal** 💱")
        st.caption("High-demand crops on lower racks should swap with low-demand crops on upper racks. Locked racks (harvest-ready / nutrition issues) are excluded.")
        for p in proposals[:4]:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.info(f"⬇️ {p['from']}")
            with col2:
                st.success(f"⬆️ {p['to']}")


# ---------------------------------------------------------------------------
# Transfer Learning diagnosis (Layer 1b)
# ---------------------------------------------------------------------------
_CROP_NAMES = {
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


def _render_cv_diagnosis(plan, electricity_df):
    """Render the Transfer Learning diagnosis panel as a 10-rack grid.

    Each rack is a persistent card showing crop, image thumbnail, and diagnosis.
    State is held in session_state so uploads survive reruns.
    """
    st.subheader("🌡️ Farm Environment & Crop Health")

    # ── Temperature & Humidity Control (tariff-aware) ─────────────────────────
    PEAK_HOURS = set(range(8, 22))  # 8am–10pm peak tariff

    # Determine which date to use for tariff
    if plan and plan.get("plan_date"):
        selected_env_date = plan["plan_date"]
    else:
        selected_env_date = date.today().isoformat()

    env_elec = electricity_df[electricity_df["date"] == selected_env_date] if electricity_df is not None else None

    # MILP optimal temp from plan
    opt_temp = plan.get("room_temp_target_c") if plan else None

    # Compute tariff-aware 24h temp/humidity schedule
    temp_schedule: list[float] = []
    humidity_schedule: list[float] = []
    if env_elec is not None and len(env_elec) > 0:
        for hour in range(24):
            row = env_elec[env_elec["hour"] == hour]
            tariff = float(row["tariff_rate_sgd_per_kwh"].iloc[0]) if len(row) > 0 else 0.20
            avg_tariff = env_elec["tariff_rate_sgd_per_kwh"].mean()
            if tariff > avg_tariff * 1.2:
                # High tariff → raise temp to reduce compressor load, raise humidity
                temp_schedule.append(opt_temp + 2 if opt_temp else 24)
                humidity_schedule.append(75)
            elif tariff < avg_tariff * 0.8:
                # Low tariff → optimal growing conditions
                temp_schedule.append(opt_temp - 1 if opt_temp else 21)
                humidity_schedule.append(65)
            else:
                temp_schedule.append(opt_temp if opt_temp else 22)
                humidity_schedule.append(70)
    else:
        # Fallback: use MILP temp only
        for _ in range(24):
            temp_schedule.append(opt_temp if opt_temp else 22)
            humidity_schedule.append(70)

    current_hour = datetime.now().hour
    current_temp = temp_schedule[current_hour] if temp_schedule else (opt_temp or 22)
    current_humidity = humidity_schedule[current_hour] if humidity_schedule else 70

    # ── Current state (always visible) ─────────────────────────────────────
    now_col1, now_col2, now_col3, now_col4 = st.columns(4)
    hour_elec_now = env_elec[env_elec["hour"] == current_hour] if env_elec is not None and len(env_elec) > 0 else None
    tariff_now = float(hour_elec_now["tariff_rate_sgd_per_kwh"].iloc[0]) if hour_elec_now is not None and len(hour_elec_now) > 0 else None
    avg_tariff_now = env_elec["tariff_rate_sgd_per_kwh"].mean() if env_elec is not None and len(env_elec) > 0 else 0.20
    tariff_status = "🔴 Peak" if current_hour in PEAK_HOURS else "🟢 Off-peak"
    now_col1.metric("🌡️ Temperature", f"{current_temp:.0f}°C", "Current now")
    now_col2.metric("💧 Humidity", f"{current_humidity:.0f}%", "Current now")
    now_col3.metric("⚡ Tariff", f"SGD {tariff_now:.4f}/kWh" if tariff_now else "N/A", tariff_status)
    now_col4.metric("🕐 Hour", f"{current_hour:02d}:00", "Now")

    # ── Phase context ────────────────────────────────────────────────────────
    st.info(
        "ℹ️ **Phase 1:** Rack maintenance photographs each rack at ~7:30am → upload → "
        "supervisor reviews updated plan by 8:30am. "
        "**Phase 2** adds fixed ceiling cameras (auto-capture at 6am). "
        "**Phase 3** adds robot patrol for continuous monitoring. "
        "Same AI pipeline across all phases."
    )

    # Rack layout from Layer 2 plan
    rack_layout: dict[str, str] = plan.get("rack_layout", {}) if plan else {}

    # ── Session state initialisation ──────────────────────────────────────────
    if "rack_images" not in st.session_state:
        st.session_state.rack_images = {}  # {rack_num: bytes}
    if "rack_diagnoses" not in st.session_state:
        st.session_state.rack_diagnoses = {}  # {rack_num: DiagnosisResult}

    # ── Action bar ───────────────────────────────────────────────────────────
    col_demo, col_diagnose, col_reset, col_resolve = st.columns([1, 1, 1, 2])

    with col_demo:
        if st.button("🎬 Load demo set", use_container_width=True, help="Populate all 10 racks with demo images"):
            _load_demo_images(rack_layout)
            st.rerun()

    with col_diagnose:
        undiagnosed = [n for n in st.session_state.rack_images if n not in st.session_state.rack_diagnoses]
        if undiagnosed:
            label = f"▶ Diagnose {len(undiagnosed)} racks"
        else:
            label = "▶ Re-diagnose all" if st.session_state.rack_images else "▶ Diagnose all"
        if st.button(label, use_container_width=True, disabled=not st.session_state.rack_images):
            for rack_num in undiagnosed:
                image_bytes = st.session_state.rack_images[rack_num]
                rack_id = f"tier_{rack_num}"
                st.session_state.rack_diagnoses[rack_num] = mock_diagnose_from_image(
                    image_bytes, rack_id
                )
            st.rerun()

    with col_reset:
        if st.button("↻ Reset", use_container_width=True, help="Clear all images and diagnoses"):
            st.session_state.rack_images = {}
            st.session_state.rack_diagnoses = {}
            st.rerun()

    with col_resolve:
        has_diagnoses = bool(st.session_state.rack_diagnoses)
        if st.button(
            "Re-solve Layer 2 with diagnoses →",
            use_container_width=True,
            disabled=not has_diagnoses,
        ):
            st.rerun()

    # ── Rack grid (3 cols × 4 rows) ─────────────────────────────────────────
    rack_nums = list(range(10))
    rows_of_3 = [rack_nums[i : i + 3] for i in range(0, 10, 3)]
    for row_racks in rows_of_3:
        cols = st.columns(3)
        for col_idx, rack_num in enumerate(row_racks):
            with cols[col_idx]:
                _render_rack_card(rack_num, rack_layout)

    # ── Summary bar ──────────────────────────────────────────────────────────
    diagnosed = st.session_state.rack_diagnoses
    total = 10
    healthy = sum(1 for d in diagnosed.values() if d.nutrition_status == "normal")
    attention = sum(1 for d in diagnosed.values() if d.nutrition_status != "normal")
    st.markdown(
        f"**Summary:** {total} racks · "
        f"{len(diagnosed)} diagnosed · "
        f"✅ {healthy} healthy · "
        f"⚠️ {attention} need attention"
    )

    st.caption(
        "Dual-head EfficientNet-B0 transfer learning model. "
        "Simulated output for demo — real model requires PlantVillage + growth-stage dataset training."
    )


def _render_environment_sidebar(plan, electricity_df) -> None:
    """Render temperature & humidity 24h slider in the sidebar."""
    PEAK_HOURS = set(range(8, 22))

    if plan and plan.get("plan_date"):
        selected_env_date = plan["plan_date"]
    else:
        selected_env_date = date.today().isoformat()

    env_elec = electricity_df[electricity_df["date"] == selected_env_date] if electricity_df is not None else None
    opt_temp = plan.get("room_temp_target_c") if plan else None

    # Compute tariff-aware schedule
    temp_schedule: list[float] = []
    humidity_schedule: list[float] = []
    if env_elec is not None and len(env_elec) > 0:
        avg_tariff = env_elec["tariff_rate_sgd_per_kwh"].mean()
        for hour in range(24):
            row = env_elec[env_elec["hour"] == hour]
            tariff = float(row["tariff_rate_sgd_per_kwh"].iloc[0]) if len(row) > 0 else avg_tariff
            if tariff > avg_tariff * 1.2:
                temp_schedule.append(opt_temp + 2 if opt_temp else 24)
                humidity_schedule.append(75)
            elif tariff < avg_tariff * 0.8:
                temp_schedule.append(opt_temp - 1 if opt_temp else 21)
                humidity_schedule.append(65)
            else:
                temp_schedule.append(opt_temp if opt_temp else 22)
                humidity_schedule.append(70)
    else:
        for _ in range(24):
            temp_schedule.append(opt_temp if opt_temp else 22)
            humidity_schedule.append(70)

    current_hour = datetime.now().hour

    st.sidebar.divider()
    st.sidebar.subheader("🌡️ Farm Environment")

    # 24h slider in sidebar
    selected_hour = st.sidebar.slider(
        "Explore 24h transition",
        0, 23, current_hour,
    )
    display_temp = temp_schedule[selected_hour]
    display_humidity = humidity_schedule[selected_hour]
    hour_elec = env_elec[env_elec["hour"] == selected_hour] if env_elec is not None and len(env_elec) > 0 else None
    hour_tariff = float(hour_elec["tariff_rate_sgd_per_kwh"].iloc[0]) if hour_elec is not None and len(hour_elec) > 0 else None

    c1, c2 = st.sidebar.columns(2)
    c1.metric("🌡️ Temp", f"{display_temp:.0f}°C")
    c2.metric("💧 Humid", f"{display_humidity:.0f}%")
    c3, c4 = st.sidebar.columns(2)
    c3.metric("⚡ Tariff", f"{hour_tariff:.3f}" if hour_tariff else "N/A", "Peak" if selected_hour in PEAK_HOURS else "Off-peak")
    c4.metric("🕐 Time", f"{selected_hour:02d}:00")

    avg_t = env_elec["tariff_rate_sgd_per_kwh"].mean() if env_elec is not None and len(env_elec) > 0 else 0.20
    st.sidebar.caption(f"Avg tariff SGD {avg_t:.4f}/kWh · Band: 🔴>{avg_t*1.2:.3f} 🟢<{avg_t*0.8:.3f}")


def _render_rack_card(rack_num: int, rack_layout: dict[str, str]) -> None:
    """Render a single rack card in the grid."""
    rack_id = f"tier_{rack_num}"
    crop_id = rack_layout.get(rack_id, "unknown")
    crop_name = _CROP_NAMES.get(crop_id, crop_id)

    with st.container(border=True):
        # Row 1: Rack + crop
        st.markdown(f"**Rack {rack_num}** — {crop_name}")

        # Row 2: Image upload or thumbnail
        image_bytes = st.session_state.rack_images.get(rack_num)
        diagnosis = st.session_state.rack_diagnoses.get(rack_num)

        if image_bytes is not None:
            st.image(image_bytes, width=120)
        else:
            uploaded = st.file_uploader(
                "+ Upload",
                type=["jpg", "jpeg", "png"],
                key=f"rack_{rack_num}_upload",
            )
            if uploaded:
                img_bytes = uploaded.read()
                st.session_state.rack_images[rack_num] = img_bytes
                # Auto-diagnose on upload
                diag_result = mock_diagnose_from_image(img_bytes, rack_id)
                st.session_state.rack_diagnoses[rack_num] = diag_result
                # Clear plan cache so today's actions reflect new diagnosis immediately
                st.cache_data.clear()
                st.rerun()

        # Row 3: Diagnosis badge
        if diagnosis:
            n_label, n_emoji = NUTRITION_BADGES.get(
                diagnosis.nutrition_status, ("?", "❓")
            )
            g_label, g_emoji = GROWTH_BADGES.get(
                diagnosis.growth_stage, ("?", "❓")
            )
            st.markdown(f"{n_emoji} {n_label} · {g_emoji} {g_label}")
            st.caption(f"Conf: {diagnosis.nutrition_confidence:.0%} / {diagnosis.growth_confidence:.0%}")
            if diagnosis.is_simulated:
                st.caption("🖼️ Demo mode")
        else:
            st.caption("Awaiting image")


# Demo image filename → rack_num mapping for "Load demo set"
# Assignment: distribute demo images across racks to show variety
_DEMO_RACK_ASSIGNMENTS = [
    ("demo_kailan_healthy.jpg", 0),  # Healthy → harvest-ready rack
    ("demo_spinach_nitrogen.jpg", 3),  # Nitrogen low
    ("demo_lettuce_wilt.jpg", 4),  # Water stress
    # Remaining healthy racks reuse demo_kailan_healthy.jpg
    ("demo_kailan_healthy.jpg", 5),
    ("demo_kailan_healthy.jpg", 6),
    ("demo_kailan_healthy.jpg", 7),
    ("demo_kailan_healthy.jpg", 8),
    ("demo_kailan_healthy.jpg", 9),
    ("demo_kailan_healthy.jpg", 1),
    ("demo_kailan_healthy.jpg", 2),
]


def _load_demo_images(rack_layout: dict[str, str]) -> None:
    """Populate all 10 racks with preset demo images and use RACK_SCENARIOS for diagnoses.

    Demo images are stored for display purposes only. Diagnoses come from
    RACK_SCENARIOS so each rack shows its intended scenario (harvest_ready,
    mid, early, nitrogen_low, water_stress, etc.).
    """
    # demo_images lives at repo-root/data/demo_images (not src/data/)
    demo_dir = Path(__file__).resolve().parents[3] / "data" / "demo_images"

    images: dict[str, bytes] = {}
    diagnoses: dict[int, object] = {}

    for filename, rack_num in _DEMO_RACK_ASSIGNMENTS:
        img_path = demo_dir / filename
        if not img_path.exists():
            continue
        img_bytes = img_path.read_bytes()
        rack_id = f"tier_{rack_num}"
        images[rack_num] = img_bytes
        # Use RACK_SCENARIOS (correct demo scenarios), not image-hash-based random
        diagnoses[rack_num] = mock_diagnose(rack_id)

    st.session_state.rack_images = images
    st.session_state.rack_diagnoses = diagnoses


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
                "Supported: `openai`, `zai`, `minimax`, `anthropic`."
            )
            return

        # Simple cache keyed on plan hash — 5-minute TTL so the same plan
        # doesn't re-call the LLM on every widget interaction.
        @st.cache_data(ttl=300, show_spinner=False)
        def _cached_brief(plan_json: str) -> str:
            return explain_plan(forecast, plan)

        try:
            brief = _cached_brief(str(sorted(plan.items())))
        except LLMUnavailable as e:
            st.error(f"Brief unavailable — {e.reason}")
            return
        except Exception as e:  # noqa: BLE001
            st.error(f"Brief unavailable — re-check or refresh.")
            return

        st.markdown(brief)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Regenerate brief", key="ai_explainer_regen_btn"):
                _cached_brief.clear()
                st.rerun()
        with col2:
            st.caption(f"Refreshes in 5 min")



def _render_electricity_sidebar(electricity_df, selected_date, electricity):
    """Render the electricity date selector + 24h tariff chart in the sidebar.

    Uses live EMA data (via session_state cache) when available, falls back to CSV.
    """
    st.sidebar.divider()
    st.sidebar.subheader("⚡ Electricity Tariff")

    # ── Use live EMA data if available, otherwise CSV ───────────────────
    live_df = _get_live_electricity_df()
    if live_df is not None and selected_date in live_df["date"].values:
        elec = live_df[live_df["date"] == selected_date].sort_values("hour").reset_index(drop=True)
        _source = "EMA / data.gov.sg"
    else:
        elec = electricity.sort_values("hour").reset_index(drop=True)
        _source = "CSV fallback"

    peak_hours = set(range(8, 22))  # 8am–10pm

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(elec["hour"]),
            y=list(elec["tariff_rate_sgd_per_kwh"]),
            mode="lines+markers",
            line=dict(color="#3498db", width=2),
            marker=dict(size=5),
            name="Tariff (SGD/kWh)",
        )
    )
    # Shade peak hours
    for h in range(24):
        if h in peak_hours:
            fig.add_vrect(
                x0=h - 0.5, x1=h + 0.5,
                fillcolor="#e74c3c", opacity=0.08, line_width=0,
            )
    fig.update_layout(
        xaxis_title="Hour",
        yaxis_title="SGD/kWh",
        height=160,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(dtick=4, tick0=0),
        showlegend=False,
    )
    st.sidebar.plotly_chart(fig, use_container_width=True)

    avg_rate = elec["tariff_rate_sgd_per_kwh"].mean()
    off_peak = elec[~elec["hour"].isin(peak_hours)]["tariff_rate_sgd_per_kwh"].mean()
    peak_rate = elec[elec["hour"].isin(peak_hours)]["tariff_rate_sgd_per_kwh"].mean()
    st.sidebar.caption(
        f"Avg **${avg_rate:.3f}** · Off-peak **${off_peak:.2f}** · Peak **${peak_rate:.2f}** · {_source}"
    )


def _render_kpi_strip(plan):
    """Render the top-of-page KPI strip. Always visible, even when the plan is None."""
    c1, c2, c3, c4, c5 = st.columns(5)
    if plan is None:
        c1.metric("Forecasted Profit (SGD)", "—")
        c2.metric("Forecasted Revenue (SGD)", "—")
        c3.metric("Energy cost (SGD)", "—")
        c4.metric("Labour cost (SGD)", "—")
        c5.metric("Solve time", "—", help="MILP wall-clock, rounded to ms")
        return
    cost = plan.get("cost_breakdown", {}) or {}

    # Compute profit CI band from Layer 1 upper/lower CI
    band = None
    if all(
        k in plan for k in ("rack_layout", "crop_prices", "crop_spoilage", "uncertainty_buffers")
    ):
        try:
            from greenloop.data.loader import load_crops
            crops_df = load_crops()
            crops_df_indexed = crops_df.set_index("crop_id")
            # Build forecast dict from uncertainty_buffers (now includes lower_ci)
            forecast = {}
            for cid, buf in plan.get("uncertainty_buffers", {}).items():
                upper = buf.get("upper_ci", 0)
                lower = buf.get("lower_ci", upper * 0.65)  # fallback if lower_ci missing
                forecast[cid] = {
                    "predicted_kg": upper,
                    "lower_ci": lower,
                    "upper_ci": upper,
                }
            band = compute_profit_band(
                forecast,
                cost,
                plan.get("crop_prices", {}),
                plan.get("crop_spoilage", {}),
                plan.get("rack_layout", {}),
            )
        except Exception:
            band = None

    profit_val = band.profit_expected if band else plan.get("objective_value_sgd", 0)
    half_width = round((band.profit_high - band.profit_low) / 2, 2) if band else None
    delta_str = f"\u00b1 ${half_width:,.0f}" if half_width else None

    c1.metric(
        "Forecasted Profit (SGD)",
        f"${profit_val:,.2f}",
        delta=delta_str,
        help="MILP profit with Layer 1 XGBoost CI band (upper_ci production target).",
    )
    c2.metric(
        "Forecasted Revenue (SGD)",
        f"${cost.get('revenue', 0):,.2f}",
        help="Revenue using upper_ci production target (robust optimization).",
    )
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
def _render_plan(plan, electricity_df=None, mode_label: str = "Balanced"):

    # ── Optimization Mode (inside plan section) ─────────────────────────────
    if "opt_mode" not in st.session_state:
        st.session_state.opt_mode = "balanced"

    mode = st.session_state.opt_mode
    opt_icon = {"profit": "💰", "sustainability": "🌿", "balanced": "⚖️"}.get(mode, "⚖️")

    col_mode, col_btn = st.columns([4, 1])
    with col_mode:
        mode = st.segmented_control(
            "🎯 Optimisation mode",
            options=list(MODE_LABELS.keys()),
            default=st.session_state.opt_mode,
            format_func=lambda k: {
                "profit": "💰 Revenue",
                "sustainability": "🌿 Sustainable",
                "balanced": "⚖️ Balanced",
            }.get(k, k),
            key="opt_mode_ctrl",
        )
    with col_btn:
        if st.button("🔄 Re-solve", use_container_width=True, help="Clear cache and re-run MILP"):
            st.cache_data.clear()
            st.rerun()
    st.session_state.opt_mode = mode

    preview = {
        "profit":     {"crop": "High-value crops priority",  "led": "LED on anytime (cost not penalised)", "energy": "⚠️ Higher electricity bill", "trade": "Max revenue · more waste OK"},
        "sustainability": {"crop": "All crops equal weight",  "led": "LED shifted to off-peak (21:00–07:00)", "energy": "✓ Minimised electricity cost", "trade": "Lower revenue · longer grow cycles OK"},
        "balanced":  {"crop": "High-demand + high-margin mix", "led": "LED follows tariff schedule", "energy": "✓ Balanced electricity cost", "trade": "✓ Middle ground on all dimensions"},
    }
    p = preview[mode]
    st.caption(f"Crop: {p['crop']}  ·  LED: {p['led']}  ·  Energy: {p['energy']}  ·  {p['trade']}")

    mode_label = MODE_LABELS.get(mode, MODE_LABELS["balanced"])
    mode_badge = {"Profit": "💰", "Sustainability": "🌿", "Balanced": "⚖️"}.get(mode_label, "⚖️")
    st.subheader(f"Today's Optimal Plan (Layer 2) — {mode_badge} {mode_label} mode")

    cost = plan.get("cost_breakdown", {})
    led = plan.get("led_schedule", {})
    room_temp = plan.get("room_temp_target_c", 22)

    # ── LED Schedule (24h) ─────────────────────────────────────────────────
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
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            barmode="group",
            showlegend=True,
            legend=dict(font=dict(size=9)),
        )
        st.plotly_chart(fig_led, use_container_width=True)

    # ── Environment Schedule (24h, tariff-aware) ──────────────────────────
    # Build tariff-aware 24h temp & humidity schedule
    elec_col = electricity_df
    temp_schedule: list[float] = []
    humidity_schedule: list[float] = []
    if elec_col is not None and len(elec_col) > 0:
        avg_tariff = elec_col["tariff_rate_sgd_per_kwh"].mean()
        for hour in range(24):
            row = elec_col[elec_col["hour"] == hour]
            tariff = float(row["tariff_rate_sgd_per_kwh"].iloc[0]) if len(row) > 0 else 0.20
            if tariff > avg_tariff * 1.2:
                temp_schedule.append(room_temp + 2)
                humidity_schedule.append(75)
            elif tariff < avg_tariff * 0.8:
                temp_schedule.append(room_temp - 1)
                humidity_schedule.append(65)
            else:
                temp_schedule.append(room_temp)
                humidity_schedule.append(70)
    else:
        for _ in range(24):
            temp_schedule.append(room_temp)
            humidity_schedule.append(70)

    # Color bars by tariff band
    PEAK_HOURS = {17, 18, 19, 20, 21}
    peak_colors = ["rgba(255,80,80,0.5)" if h in PEAK_HOURS else "rgba(80,200,120,0.4)" for h in range(24)]

    fig_env = go.Figure()
    # Temperature line
    fig_env.add_trace(go.Scatter(
        x=list(range(24)),
        y=temp_schedule,
        mode="lines+markers",
        name="Temperature (°C)",
        line=dict(color="#e74c3c", width=2),
        marker=dict(size=6),
        yaxis="y1",
    ))
    # Humidity line
    fig_env.add_trace(go.Scatter(
        x=list(range(24)),
        y=humidity_schedule,
        mode="lines+markers",
        name="Humidity (%)",
        line=dict(color="#3498db", width=2, dash="dot"),
        marker=dict(size=6),
        yaxis="y2",
    ))
    # Tariff band background shading
    for h in range(24):
        color = "rgba(255,100,100,0.15)" if h in PEAK_HOURS else "rgba(80,200,120,0.08)"
        label = "Peak" if h in PEAK_HOURS else "Off-peak"
        fig_env.add_vrect(
            x0=h - 0.5, x1=h + 0.5,
            fillcolor=color, layer="below", line_width=0,
            annotation_text=label if h == 17 else None,
            annotation_position="top left",
        )
    fig_env.update_layout(
        title="Environment Schedule (24h) — tariff-aware",
        xaxis=dict(title="Hour", tickmode="linear", tick0=0, dtick=2),
        yaxis=dict(title="Temperature (°C)", side="left", range=[14, 32]),
        yaxis2=dict(title="Humidity (%)", side="right", overlaying="y", range=[40, 90]),
        height=200,
        margin=dict(l=20, r=60, t=40, b=20),
        showlegend=True,
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_env, use_container_width=True)

    st.caption(
        f"🔴 Peak tariff (17–21h): temp +2°C to reduce compressor load · "
        f"🟢 Off-peak (0–7h): optimal growing temp · "
        f"Solve time: {plan.get('solve_time_ms', 0):.1f}ms · "
        f"Energy: ${cost.get('electricity', 0):,.0f} · Labour: ${cost.get('labour', 0):,.0f}"
    )

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

    # ── CV Diagnosis impact summary ──
    cv_summary = plan.get("cv_diagnosis_summary")
    if cv_summary:
        with st.expander("CV Diagnosis impact on plan", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Racks diagnosed", cv_summary["num_diagnosed"])
            c2.metric(
                "Nitrogen low",
                cv_summary["nitrogen_low_count"],
                delta="+15% nutrient cost each" if cv_summary["nitrogen_low_count"] else None,
            )
            c3.metric(
                "Water stress",
                cv_summary["water_stress_count"],
                delta="+1× irrigation freq" if cv_summary["water_stress_count"] else None,
            )
            c4.metric(
                "Low confidence",
                cv_summary["low_confidence_count"],
                delta="±50% wider uncertainty band" if cv_summary["low_confidence_count"] else None,
            )
            # Per-rack detail table
            if cv_summary.get("details"):
                detail_rows = []
                for rack_id, detail in cv_summary["details"].items():
                    growth = detail.get("growth_stage", "?")
                    nutrition = detail.get("nutrition_status", "?")
                    gc = detail.get("growth_confidence", 0)
                    nc = detail.get("nutrition_confidence", 0)
                    # Derive yield impact from growth stage
                    ym = {"early": "×0.60", "mid": "×0.90", "harvest_ready": "×1.00"}.get(growth, "×1.00")
                    nm_cost = "+15% nutrient" if nutrition == "nitrogen_low" else (
                        "+1× water" if nutrition == "water_stress" else "normal"
                    )
                    detail_rows.append({
                        "Rack": rack_id,
                        "Growth": f"{growth} ({gc:.0%})",
                        "Nutrition": f"{nutrition} ({nc:.0%})",
                        "Yield mult": ym,
                        "Nutrient impact": nm_cost,
                    })
                st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Sustainability KPIs
# ---------------------------------------------------------------------------
def _render_sustainability_section(plan, forecast, crops, electricity_df, staff):
    """Render the Sustainability KPI section with metric cards and weekly chart."""
    st.subheader("🌱 Sustainability KPIs")

    if plan is None:
        st.warning("No plan available — sustainability KPIs cannot be computed.")
        return

    # Compute today's KPIs
    kpis = compute_sustainability_kpis(plan, forecast, crops)

    # 4 metric cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Water Saved Today",
        f"{kpis['water_saved_l']:,.0f} L",
        delta="95% vs conventional",
    )
    c2.metric(
        "CO₂ Avoided",
        f"{kpis['co2_avoided_kg']:,.1f} kg-CO₂",
        delta="87% reduction",
    )
    c3.metric(
        "Energy Efficiency",
        f"{kpis['energy_efficiency_kwh_per_kg']:.2f} kWh/kg",
        delta="target <2.5",
    )
    c4.metric(
        "Off-Peak Energy",
        f"{kpis['off_peak_energy_ratio_pct']:.1f}%",
        delta="target >70%",
    )

    # Weekly cumulative chart
    weekly_df = get_weekly_sustainability(crops, electricity_df, staff)
    if not weekly_df.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=list(weekly_df["date"]),
                y=list(weekly_df["water_saved_l"]),
                name="Water Saved (L)",
                marker_color="#27ae60",
            ),
        )
        fig.add_trace(
            go.Bar(
                x=list(weekly_df["date"]),
                y=list(weekly_df["co2_avoided_kg"]),
                name="CO₂ Avoided (kg)",
                marker_color="#2ecc71",
            ),
        )
        fig.update_layout(
            title="Weekly Sustainability — Water Saved & CO₂ Avoided",
            xaxis_title="Date",
            yaxis_title="Impact",
            barmode="group",
            height=260,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Weekly sustainability data is not yet available.")


# ---------------------------------------------------------------------------
# RL Control
# ---------------------------------------------------------------------------
def _render_rl_control():
    st.subheader("RL Control (Layer 3)")

    # Persistent gate, env, and agent across reruns
    if "rl_gate" not in st.session_state:
        env = HydroFarmEnv()
        obs, _ = env.reset()
        agent = HydroFarmAgent() if LAYER3_AGENT_AVAILABLE else None
        st.session_state.rl_gate = AutonomyGate(agent=agent, env=env)
        st.session_state.rl_history: list[dict] = []
        st.session_state.rl_episode_step = 0
        st.session_state.rl_current_obs = obs

    gate = st.session_state.rl_gate
    # v6.2: Auto-degrade to ADVISORY during typhoon or manager override
    _typhoon_on = bool(st.session_state.get("typhoon_mode") or st.session_state.get("typhoon_active"))
    _override_on = bool(st.session_state.get("override_active"))
    if _typhoon_on or _override_on:
        if "_preferred_mode" not in st.session_state:
            st.session_state["_preferred_mode"] = gate.get_mode()
        if gate.get_mode() != AutonomyMode.ADVISORY:
            gate.set_mode(AutonomyMode.ADVISORY)
    elif "_preferred_mode" in st.session_state:
        _pref = st.session_state.pop("_preferred_mode")
        if gate.get_mode() != _pref:
            gate.set_mode(_pref)
    history = st.session_state.rl_history

    # Autonomy mode selector
    mode_labels = {AutonomyMode.MANUAL: "Manual", AutonomyMode.ADVISORY: "Advisory", AutonomyMode.AUTONOMOUS: "Autonomous"}
    current_mode = gate.get_mode()
    mode_index = list(mode_labels.keys()).index(current_mode)
    selected_label = st.radio(
        "Autonomy",
        options=list(mode_labels.values()),
        index=mode_index,
        format_func=lambda x: x,
        horizontal=True,
        help="Manual: you approve every action. Advisory: agent acts, you can override. Autonomous: agent runs freely.",
    )
    selected_mode = AutonomyMode([k for k, v in mode_labels.items() if v == selected_label][0])
    if selected_mode != current_mode:
        gate.set_mode(selected_mode)
        st.session_state.rl_history = []
        st.session_state.rl_episode_step = 0
        obs, _ = gate._env.reset()
        st.session_state.rl_current_obs = obs
        st.rerun()

    # ── v6.2 Autonomy Mode Status Strip ────────────────────────────────
    _typhoon_on = bool(st.session_state.get("typhoon_mode") or st.session_state.get("typhoon_active"))
    _override_on = bool(st.session_state.get("override_active"))
    _degraded = _typhoon_on or _override_on

    _ac1, _ac2, _ac3 = st.columns([1, 2, 2])
    with _ac1:
        st.markdown("**🛡️ Autopilot Mode**")
    with _ac2:
        if _degraded:
            st.warning(f"**Advisory** ← Auto-degraded")
        elif gate.get_mode() == AutonomyMode.AUTONOMOUS:
            st.success(f"🤖 **{gate.mode_label}** — AI runs operations")
        elif gate.get_mode() == AutonomyMode.ADVISORY:
            st.info(f"🤝 **{gate.mode_label}** — AI proposes, human can override")
        else:
            st.info(f"👤 **{gate.mode_label}** — Human approves every action")
    with _ac3:
        if _degraded:
            _why = []
            if _typhoon_on: _why.append("Typhoon active")
            if _override_on: _why.append("Manager override")
            st.caption(f"⚠️ Reduced to Advisory: {' + '.join(_why)}")
        else:
            st.caption("ℹ️ Change mode with the radio above.")

    # Show pending proposed action in Manual mode
    if gate.get_mode() == AutonomyMode.MANUAL and gate.has_pending:
        pending_info = gate.pending_info
        st.info(f"**Proposed:** {pending_info.get('agent', '?')} agent — awaiting your approval")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Approve", key="approve_action"):
                gate.approve_pending()
                obs = gate._env._get_obs()
                last = gate._state.last_info
                step_n = gate._state.episode_step
                reward = last.get("reward", 0.0)
                st.session_state.rl_episode_step = step_n
                st.session_state.rl_current_obs = obs
                st.session_state.rl_history.append({
                    "step": step_n,
                    "obs": obs,
                    "action": gate._state.last_action,
                    "reward": reward,
                    "cumulative_reward": _cumulative_reward(history) + reward,
                    "info": last,
                })
                if last.get("constraint_violation"):
                    st.error("⚠ Constraint violation — Farm Manager alert")
                st.rerun()
        with col_b:
            if st.button("❌ Reject", key="reject_action"):
                rejected_action = gate.reject_pending()
                obs = gate._env._get_obs()
                last = gate._state.last_info
                step_n = gate._state.episode_step
                reward = last.get("reward", 0.0)
                st.session_state.rl_episode_step = step_n
                st.session_state.rl_current_obs = obs
                st.session_state.rl_history.append({
                    "step": step_n,
                    "obs": obs,
                    "action": rejected_action,
                    "reward": reward,
                    "cumulative_reward": _cumulative_reward(history) + reward,
                    "info": last,
                })
                if last.get("constraint_violation"):
                    st.error("⚠ Constraint violation — Farm Manager alert")
                st.rerun()

    st.caption(f"Mode: {gate.mode_label} | Step: {gate._state.episode_step}/1440 | Agent: {'PPO' if (gate._agent and gate._agent.is_real) else 'Random'}")

    # Run 1 step
    if st.button("▶ Step"):
        obs = st.session_state.rl_current_obs
        if gate.get_mode() == AutonomyMode.MANUAL:
            gate.step(obs)
        else:
            action, info, _ = gate.step(obs)
            obs = gate._env._get_obs()
            reward = info.get("reward", 0.0)
            step_n = gate._state.episode_step
            st.session_state.rl_episode_step = step_n
            st.session_state.rl_current_obs = obs
            st.session_state.rl_history.append({
                "step": step_n,
                "obs": obs,
                "action": action,
                "reward": reward,
                "cumulative_reward": _cumulative_reward(history) + reward,
                "info": info,
            })
            if info.get("constraint_violation"):
                st.error("⚠ Constraint violation — Farm Manager alert")

    # Safety alert for last completed step
    if history and history[-1]["info"].get("constraint_violation"):
        st.error("⚠ Constraint violation — Farm Manager alert")

    # Current observation
    latest = history[-1] if history else None
    if latest:
        obs = latest["obs"]
        step_num = latest["step"]
        cumulative = latest["cumulative_reward"]
        action = latest["action"]
        reward = latest["reward"]
    else:
        obs = st.session_state.rl_current_obs
        step_num = 0
        cumulative = 0.0
        action = None
        reward = 0.0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Temperature", f"{obs[0]:.1f}°C", delta=f"{obs[6]:+.1f}°C")
        st.metric("CO₂", f"{obs[2]:.0f} ppm", delta=f"{obs[8]:+.0f}")
    with col2:
        st.metric("Humidity", f"{obs[1]:.1f}%", delta=f"{obs[7]:+.1f}%")
        st.metric("Moisture", f"{obs[3]:.2f}", delta=f"{obs[9]:+.2f}")

    if action is not None:
        heater_labels = {-2: "Cool -2kW", -1: "Cool -1kW", 0: "Off", 1: "Heat +1kW", 2: "Heat +2kW"}
        pump_labels = {0: "OFF", 1: "30s", 2: "60s", 3: "120s"}
        vent_labels = {0: "LOW", 1: "MED", 2: "HIGH"}
        led_labels = {-1: "-10%", 0: "0%", 1: "+10%"}
        action_labels = [
            heater_labels.get(int(action[0]) - 2, f"Htr {int(action[0])-2}"),
            pump_labels.get(int(action[1]), f"Pump {action[1]}"),
            vent_labels.get(int(action[2]), f"Vent {action[2]}"),
            led_labels.get(int(action[3]) - 1, f"LED {action[3]}"),
        ]
        st.write("**Action:** " + " | ".join(action_labels))
        st.write(f"**Reward this step:** {reward:+.1f} | **Cumulative:** {cumulative:+.1f}")

    # Reward chart
    if len(history) > 1:
        rewards = [s["reward"] for s in history]
        st.line_chart(rewards, height=120)


def _cumulative_reward(history: list[dict]) -> float:
    """Sum of rewards in history (safe for empty list)."""
    if not history:
        return 0.0
    return sum(h["reward"] for h in history)


# ---------------------------------------------------------------------------
# Scenario Testing
# ---------------------------------------------------------------------------
def _render_scenario_testing(
    forecast, crops, electricity, staff, headcount, current_plan,
    mode_key="balanced", excluded_racks=None, unavailable_shifts=None,
):
    st.subheader("Scenario Testing")

    # v6.2: Activate / Clear Typhoon Scenario
    typhoon_col1, typhoon_col2 = st.columns([1, 3])
    with typhoon_col1:
        if not st.session_state.get("typhoon_active"):
            if st.button(
                "⚡ Activate Typhoon Scenario",
                type="primary",
                use_container_width=True,
                key="scenario_typhoon_trigger",
            ):
                st.session_state["typhoon_mode"] = True
                st.session_state["typhoon_active"] = True
                st.session_state["typhoon_needs_recompute"] = True
                st.rerun()
        else:
            if st.button(
                "🔄 Clear Typhoon Scenario",
                use_container_width=True,
                key="scenario_typhoon_clear",
            ):
                for k in ["typhoon_active", "typhoon_mode", "typhoon_needs_recompute",
                          "typhoon_plan_cache", "typhoon_elapsed_ms", "typhoon_error",
                          "typhoon_error_constraint"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
    with typhoon_col2:
        if st.session_state.get("typhoon_active"):
            st.error("⚡ Typhoon Scenario Active — Re-optimization running below.")
        else:
            st.info("💡 Activate a typhoon scenario to test AI response.")

    # v6.2: Red alert banner when typhoon is active
    if st.session_state.get("typhoon_active"):
        st.error(
            "⚠️ TYPHOON ACTIVE — 6h delivery window | "
            "Power outage: YES | UPS: 4h countdown active | "
            "Demand surge: +20% | Emergency harvest: triggered"
        )

        ups_hours = 4
        st.markdown(
            f"""
            <div style="
                background-color: #cc0000;
                color: white;
                padding: 16px 24px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
                margin: 12px 0;
                font-family: monospace;
            ">
            🔴 UPS COUNTDOWN: {ups_hours}h 00m REMAINING — EMERGENCY HARVEST ACTIVE
            </div>
            """,
            unsafe_allow_html=True,
        )

    # v6.2: Re-optimization triggered by button OR top-level promo;
    # result cached in session_state to avoid re-running on every Streamlit rerun.
    if st.session_state.get("typhoon_active"):
        if st.session_state.get("typhoon_needs_recompute", True):
            with st.spinner("Running typhoon re-optimization..."):
                t0 = time.time()
                scenario = TyphoonScenarioInput(
                    delivery_hours=6,
                    power_outage_probability=0.3,
                    ups_countdown_hours=4,
                    emergency_harvest=True,
                    demand_multiplier=1.2,
                    cold_storage_switch=True,
                    staff_reduced_pct=30,
                )
                base_kwargs = dict(
                    forecast=forecast,
                    crops_df=crops,
                    electricity_df=electricity,
                    staff_df=staff,
                    available_headcount=headcount,
                )
                typhoon_kwargs = apply_typhoon(base_kwargs, scenario)
                typhoon_kwargs["excluded_racks"] = excluded_racks or []
                typhoon_kwargs["unavailable_shifts"] = unavailable_shifts or []
                typhoon_kwargs["objective_weights"] = ObjectiveWeights.from_mode(mode_key)
                try:
                    typhoon_plan = build_and_solve(**typhoon_kwargs)
                    elapsed = (time.time() - t0) * 1000
                    st.session_state["typhoon_plan_cache"] = typhoon_plan
                    st.session_state["typhoon_elapsed_ms"] = elapsed
                    st.session_state["typhoon_error"] = None
                except InfeasibleError as e:
                    st.session_state["typhoon_plan_cache"] = None
                    st.session_state["typhoon_elapsed_ms"] = (time.time() - t0) * 1000
                    st.session_state["typhoon_error"] = str(e)
                    st.session_state["typhoon_error_constraint"] = (
                        e.binding_constraint if hasattr(e, "binding_constraint") else None
                    )
                st.session_state["typhoon_needs_recompute"] = False

        # Display cached results
        typhoon_plan = st.session_state.get("typhoon_plan_cache")
        elapsed = st.session_state.get("typhoon_elapsed_ms", 0)
        error_msg = st.session_state.get("typhoon_error")

        if error_msg:
            st.error(f"Typhoon plan infeasible ({elapsed:.0f}ms): {error_msg}")
            constraint = st.session_state.get("typhoon_error_constraint")
            if constraint:
                st.info(f"Try: {constraint}")
        elif typhoon_plan:
            st.success(f"Re-optimized in {elapsed:.0f}ms")
            if current_plan:
                comparison = compare_plans(current_plan, typhoon_plan)
                delta = comparison.get("delta", {})
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(
                    "Forecasted Profit",
                    f"${typhoon_plan.get('objective_value_sgd', 0):,.0f}",
                    delta=f"{delta.get('objective_value_sgd', 0):,.0f}",
                )
                m2.metric("Delivery Window", "6 hours", delta="-6h", delta_color="inverse")
                m3.metric("Power Outage", "ACTIVE", delta="-yield 100%", delta_color="inverse")
                m4.metric("Demand Surge", "+20%", delta="panic buying")
                if "rl_env" in st.session_state:
                    st.session_state.rl_env.update_targets(
                        {"temp": typhoon_plan.get("room_temp_target_c", 22)}
                    )
                    if hasattr(st.session_state.rl_env, "trigger_power_outage"):
                        st.session_state.rl_env.trigger_power_outage()
                    st.info("Layer 3 targets updated")
            else:
                st.write(f"Typhoon plan forecast profit: ${typhoon_plan.get('objective_value_sgd', 0):,.0f}")

    # Trigger button (only sets state + flags recompute)
    col_trigger, col_force = st.columns([3, 1])
    with col_trigger:
        if st.button("⚡ Typhoon Warning", type="primary", key="typhoon_main_btn"):
            st.session_state["typhoon_mode"] = True
            st.session_state["typhoon_active"] = True
            st.session_state["typhoon_needs_recompute"] = True
            st.rerun()
    with col_force:
        if st.session_state.get("typhoon_active"):
            if st.button("🔁 Re-solve", key="typhoon_force_recompute", help="Force re-optimization with current settings"):
                st.session_state["typhoon_needs_recompute"] = True
                st.rerun()

    st.caption(
        "Typhoon Warning: 6h delivery | 30% power outage probability | "
        "4h UPS countdown | +20% demand surge | Emergency harvest + cold storage"
    )

    # Deployment Gate — collapsible panel
    with st.expander("📋 Deployment Gate", expanded=False):
        _render_deployment_gate_panel()

    with st.expander("🎯 Implications Audit", expanded=False):
        _render_implications_audit_panel()

    with st.expander("📊 Drift Monitoring", expanded=False):
        _render_drift_monitoring_panel()


def _render_deployment_gate_panel():
    """Render deployment gate status as a read-only summary panel."""
    try:
        decision = evaluate_all_gates()
    except Exception as e:
        st.error(f"Gate evaluation failed: {e}")
        return

    col_status = st.columns(5)
    for i, gate_result in enumerate(decision.gate_results):
        with col_status[i]:
            if gate_result.status == GateStatus.PASS:
                st.success(f"Gate {gate_result.number}: PASS")
            elif gate_result.status == GateStatus.FAIL:
                st.error(f"Gate {gate_result.number}: FAIL")
            elif gate_result.status == GateStatus.CONDITIONAL:
                st.warning(f"Gate {gate_result.number}: CONDITIONAL")
            else:
                st.info(f"Gate {gate_result.number}: PENDING")
            st.caption(gate_result.name)

    st.divider()

    # Ship recommendation
    if decision.ship_recommended:
        st.success("Ship recommended — all gates PASS")
    else:
        st.error(f"Do NOT ship — {decision.overall_message}")

    if decision.restrictions:
        st.warning(f"Restriction: {decision.restrictions}")

    if decision.upgrade_conditions:
        st.write("**Upgrade conditions:**")
        for cond in decision.upgrade_conditions:
            st.write(f"  • {cond}")

    st.caption(f"Evaluated: {decision.evaluated_at}")


def _render_implications_audit_panel():
    """Render Phase 5 Implications Audit as a read-only 3-tab summary."""
    try:
        implications = get_all_implications()
        stakeholders = get_stakeholder_impacts()
    except Exception as e:
        st.error(f"Failed to load implications: {e}")
        return

    tab_data, tab_bias, tab_stakeholder = st.tabs([
        "📊 Overview",
        "⚖️ Bias by Layer",
        "👥 Stakeholder Impact",
    ])

    with tab_data:
        # Severity summary badges
        by_sev = {s: 0 for s in ImpactSeverity}
        for i in implications:
            by_sev[i.severity] += 1
        cols = st.columns(4)
        sev_items = [
            (ImpactSeverity.CRITICAL, "🔴 CRITICAL", cols[0]),
            (ImpactSeverity.HIGH, "🟠 HIGH", cols[1]),
            (ImpactSeverity.MEDIUM, "🟡 MEDIUM", cols[2]),
            (ImpactSeverity.LOW, "🟢 LOW", cols[3]),
        ]
        for sev, label, col in sev_items:
            with col:
                count = by_sev[sev]
                if count == 0:
                    st.metric(label, "0")
                elif sev == ImpactSeverity.CRITICAL:
                    st.error(f"{count} {label}")
                elif sev == ImpactSeverity.HIGH:
                    st.warning(f"{count} {label}")
                else:
                    st.info(f"{count} {label}")

        st.divider()
        unmitigated = [i for i in implications if not i.is_mitigated]
        if unmitigated:
            st.error(f"⚠️  {len(unmitigated)} implication(s) not yet mitigated")
        else:
            st.success("✅ All implications have mitigations documented")

        st.caption(
            "Full report: journal/phase5-implications-report.md | "
            "Run: uv run python scripts/run_implications_audit.py"
        )

    with tab_bias:
        data_bias = [
            i for i in implications if i.category == ImplicationCategory.DATA_BIAS
        ]
        decision_bias = [
            i for i in implications if i.category == ImplicationCategory.DECISION_BIAS
        ]
        st.write("**Data Bias**")
        for i in data_bias:
            sev_emoji = {
                ImpactSeverity.HIGH: "🟠",
                ImpactSeverity.MEDIUM: "🟡",
                ImpactSeverity.LOW: "🟢",
            }.get(i.severity, "⚪")
            st.write(f"  {sev_emoji} `{i.layer}`: {i.description[:100]}...")
            st.caption(f"  Mitigation: {i.mitigation[:120]}...")

        st.divider()
        st.write("**Decision Bias**")
        for i in decision_bias:
            sev_emoji = {
                ImpactSeverity.HIGH: "🟠",
                ImpactSeverity.MEDIUM: "🟡",
                ImpactSeverity.LOW: "🟢",
            }.get(i.severity, "⚪")
            st.write(f"  {sev_emoji} `{i.layer}`: {i.description[:100]}...")
            st.caption(f"  Mitigation: {i.mitigation[:120]}...")

    with tab_stakeholder:
        for s in stakeholders:
            net = len(s.positive_effects) - len(s.negative_effects)
            icon = "✅" if net > 0 else "⚖️" if net == 0 else "⚠️"
            with st.expander(f"{icon} {s.stakeholder} (net {net:+d})", expanded=False):
                st.write("**Positive:**")
                for p in s.positive_effects:
                    st.write(f"  + {p}")
                st.write("**Negative:**")
                for n in s.negative_effects:
                    st.write(f"  - {n}")
                st.write("**Mitigations:**")
                for m in s.mitigation_actions:
                    st.write(f"  • {m}")


if __name__ == "__main__":
    main()


def _render_drift_monitoring_panel():
    """Render Phase 13 Drift Monitoring as a read-only 3-tab summary."""
    try:
        checks = get_all_drift_checks()
        results = run_all_checks()
    except Exception as e:
        st.error(f"Failed to load drift checks: {e}")
        return

    # Group results by drift type
    feature_results = [
        (c, s, d) for (c, s, d) in results
        if c.drift_type == DriftType.FEATURE
    ]
    perf_results = [
        (c, s, d) for (c, s, d) in results
        if c.drift_type == DriftType.PERFORMANCE
    ]
    concept_results = [
        (c, s, d) for (c, s, d) in results
        if c.drift_type == DriftType.CONCEPT
    ]

    tab_feature, tab_perf, tab_concept = st.tabs([
        f"📈 Feature Drift ({len(feature_results)} checks)",
        f"📉 Performance Drift ({len(perf_results)} checks)",
        f"🔄 Concept Drift ({len(concept_results)} checks)",
    ])

    def _render_check_row(check: Any, severity: DriftSeverity, details: dict) -> None:
        sev_color = {
            DriftSeverity.OK: "✅",
            DriftSeverity.WARNING: "⚠️",
            DriftSeverity.ALERT: "🔔",
            DriftSeverity.CRITICAL: "🚨",
        }.get(severity, "⚪")
        st.write(f"{sev_color} `{check.name}`")
        st.caption(f"  {check.layer} | Action: {check.action_on_alert}")
        status = details.get("status", "ok")
        if status != "ok":
            msg = details.get("message", details.get("error", status))
            st.caption(f"  {status}: {str(msg)[:100]}")

    with tab_feature:
        counts = {s: 0 for s in DriftSeverity}
        for c, s, d in feature_results:
            counts[s] += 1
        cols = st.columns(4)
        for col, (sev, label) in zip(
            cols,
            [
                (DriftSeverity.OK, "✅ OK"),
                (DriftSeverity.WARNING, "⚠️ WARNING"),
                (DriftSeverity.ALERT, "🔔 ALERT"),
                (DriftSeverity.CRITICAL, "🚨 CRITICAL"),
            ],
        ):
            with col:
                if counts[sev] == 0:
                    st.metric(label, "0")
                else:
                    st.info(f"{counts[sev]} {label}")

        st.divider()
        for c, s, d in feature_results:
            _render_check_row(c, s, d)

        st.caption(
            "Feature drift: input distribution changes detected by KS test or volume shift. "
            "Run: uv run python scripts/run_drift_check.py"
        )

    with tab_perf:
        counts = {s: 0 for s in DriftSeverity}
        for c, s, d in perf_results:
            counts[s] += 1
        cols = st.columns(4)
        for col, (sev, label) in zip(
            cols,
            [
                (DriftSeverity.OK, "✅ OK"),
                (DriftSeverity.WARNING, "⚠️ WARNING"),
                (DriftSeverity.ALERT, "🔔 ALERT"),
                (DriftSeverity.CRITICAL, "🚨 CRITICAL"),
            ],
        ):
            with col:
                if counts[sev] == 0:
                    st.metric(label, "0")
                else:
                    st.info(f"{counts[sev]} {label}")

        st.divider()
        for c, s, d in perf_results:
            _render_check_row(c, s, d)

        st.caption(
            "Performance drift: RMSE ratio, solve time, confidence, feedback ratio. "
            "Run: uv run python scripts/run_drift_check.py"
        )

    with tab_concept:
        counts = {s: 0 for s in DriftSeverity}
        for c, s, d in concept_results:
            counts[s] += 1
        cols = st.columns(4)
        for col, (sev, label) in zip(
            cols,
            [
                (DriftSeverity.OK, "✅ OK"),
                (DriftSeverity.WARNING, "⚠️ WARNING"),
                (DriftSeverity.ALERT, "🔔 ALERT"),
                (DriftSeverity.CRITICAL, "🚨 CRITICAL"),
            ],
        ):
            with col:
                if counts[sev] == 0:
                    st.metric(label, "0")
                else:
                    st.info(f"{counts[sev]} {label}")

        st.divider()
        for c, s, d in concept_results:
            _render_check_row(c, s, d)

        st.caption(
            "Concept drift: relationship changes between predictions and outcomes. "
            "Run: uv run python scripts/run_drift_check.py"
        )

# ===== v6.2 Phase 1 Footer =====
st.divider()

with st.container():
    st.caption("📍 **Phase 1 MVP** — All metrics displayed are simulated values. Phase 1 pilot will validate the hypotheses below.")

    with st.expander("🧪 Phase 1 Validation Hypotheses (6)", expanded=False):
        st.markdown("""
        Each hypothesis has a pass threshold. If any fails, we redesign or pivot:

        1. **Manufacturing — Electricity savings**: LED time-shift saves ≥5% electricity (target: 5–15%)
        2. **Manufacturing — Waste reduction**: Demand forecast + order integration cuts waste ≥5pt (target: 5–10pt)
        3. **Integration Platform — Time savings**: Morning planning time reduced from 60min to <30min
        4. **Media — RAG accuracy**: RAG Chat answers ≥60% accuracy (human evaluation)
        5. **Logistics — Fuel savings**: Route optimization saves ≥5% fuel (target: 5–10%)
        6. **B2B SaaS viability**: ≥2 of 3 pilot farms show continuation intent at SGD 500/month

        *Methodology: Lean Startup Validated Learning. Each hypothesis is independently testable in the 6-month Phase 1 pilot.*
        """)

    st.caption("MGMT 655 Machine Learning for Decision Making | SMU Term 1 2026")
