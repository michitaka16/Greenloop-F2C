"""GreenLoop Farm OS — Streamlit Dashboard.

Single-screen dashboard integrating all 3 layers:
- Layer 1: XGBoost demand forecast with confidence intervals
- Layer 2: OR-Tools MILP daily plan optimization
- Layer 3: PPO RL environment control (live inference log)
"""

import time
from datetime import date, datetime
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
    diagnose_batch,
    filename_to_rack_id,
    mock_diagnose_from_image,
    RACK_SCENARIOS,
)
from greenloop.llm import LLMUnavailable, explain_plan, llm_is_configured  # noqa: E402
from greenloop.rag.agent import RAGAgent  # noqa: E402
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
            models_dir = Path(__file__).resolve().parent.parent.parent.parent / "models"
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

    # ── HITL: Optimization mode ──
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Optimization Mode")
    mode = st.sidebar.radio(
        "Objective",
        options=list(MODE_LABELS.values()),
        index=2,  # Balanced default
        format_func=lambda x: x,
        help="Profit: maximise revenue. Sustainability: minimise energy/waste. Balanced: trade-off.",
    )
    mode_key = next(k for k, v in MODE_LABELS.items() if v == mode)

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

    # ── Sidebar: Design decisions (Dimension A evidence for VC pitch) ──
    render_design_decisions_panel()

    # ── Layer 2: Optimize ──
    plan = _solve_plan(
        forecast,
        crops,
        electricity,
        staff,
        headcount,
        mode_key,
        excluded_racks,
        unavailable_shifts,
    )

    # ── Transfer Learning diagnosis (Layer 1b) — above the fold ──
    _render_cv_diagnosis(plan)

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

    # ── Sustainability KPIs ─────────────────────────────────────────────
    _render_sustainability_section(plan, forecast, crops, electricity_df, staff)

    # ── Bottom: RL Control + Scenario Testing ──
    bot_left, bot_right = st.columns(2)

    with bot_left:
        _render_rl_control()

    with bot_right:
        _render_scenario_testing(forecast, crops, electricity, staff, headcount, plan, mode_key, excluded_racks, unavailable_shifts)

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

    # Persistent RAG agent and session state
    if "rag_agent" not in st.session_state:
        st.session_state.rag_agent = RAGAgent()
        st.session_state.rag_history: list[dict] = []
        st.session_state.rag_session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.rag_tone = Tone.NEUTRAL
        st.session_state.rag_last_answer = ""

    agent = st.session_state.rag_agent
    history = st.session_state.rag_history

    # Tone selector
    tone_keys = list(Tone)
    tone_labels = [TONE_LABELS[k] for k in tone_keys]
    current_idx = tone_keys.index(st.session_state.rag_tone)
    selected_tone_label = st.radio(
        "Response tone",
        options=tone_labels,
        index=current_idx,
        horizontal=True,
        help="Sales: enthusiastic, ROI-focused. Technical: precise metrics. Neutral: balanced.",
    )
    new_tone = Tone([k for k, v in TONE_LABELS.items() if v == selected_tone_label][0])
    if new_tone != st.session_state.rag_tone:
        st.session_state.rag_tone = new_tone

    # Chat history
    chat_container = st.container()
    with chat_container:
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
    if question := st.chat_input("Ask about GreenLoop Farm..."):
        # Add to history
        st.session_state.rag_history.append({"role": "user", "content": question})
        st.session_state["_last_question"] = question
        st.chat_message("user").write(question)

        # Get answer
        try:
            # Apply tone modifier
            base_system = (
                "You are a helpful assistant for GreenLoop Farm — a hydroponic vertical farm in Singapore. "
                "Answer questions using ONLY the provided context. "
                "If the answer is not in the context, say you don't know. "
                "Be concise, factual, and mention specific numbers when available."
            )
            tone = st.session_state.rag_tone
            system_prompt = get_system_prompt(tone, base_system)

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
def _solve_plan(
    forecast,
    crops,
    electricity,
    staff,
    headcount,
    mode_key="balanced",
    excluded_racks=None,
    unavailable_shifts=None,
):
    """Solve Layer 2 MILP with CV diagnosis. Return plan dict or None on infeasibility."""
    # Run Layer 1b CV diagnosis across all 10 racks.
    cv_diagnosis = diagnose_all_racks_simulated()

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


def _render_cv_diagnosis(plan):
    """Render the Transfer Learning diagnosis panel as a 10-rack grid.

    Each rack is a persistent card showing crop, image thumbnail, and diagnosis.
    State is held in session_state so uploads survive reruns.
    """
    st.subheader("Crop Health & Growth Diagnosis (Transfer Learning)")

    # ── Phase context ────────────────────────────────────────────────────────
    st.info(
        "ℹ️ **Phase 1 pilot:** farm managers photograph racks manually. "
        "**Phase 2** uses fixed ceiling cameras. **Phase 3** uses robot patrol. "
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
        st.button(
            "Re-solve Layer 2 with diagnoses →",
            use_container_width=True,
            disabled=not has_diagnoses,
        )

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
    """Populate all 10 racks with preset demo images and run diagnoses."""
    demo_dir = Path(__file__).resolve().parent.parent.parent / "data" / "demo_images"

    images: dict[str, bytes] = {}
    diagnoses: dict[int, object] = {}

    for filename, rack_num in _DEMO_RACK_ASSIGNMENTS:
        img_path = demo_dir / filename
        if not img_path.exists():
            continue
        img_bytes = img_path.read_bytes()
        rack_id = f"tier_{rack_num}"
        images[rack_num] = img_bytes
        diagnoses[rack_num] = mock_diagnose_from_image(img_bytes, rack_id)

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
                x0=h - 0.5,
                x1=h + 0.5,
                fillcolor="#e74c3c",
                opacity=0.06,
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
            dict(
                x=3,
                y=electricity["tariff_rate_sgd_per_kwh"].max() + 0.01,
                text="🌙 Off-peak (< 8am / ≥ 10pm)",
                showarrow=False,
                font=dict(size=10, color="#2c3e50"),
            ),
            dict(
                x=15,
                y=electricity["tariff_rate_sgd_per_kwh"].max() + 0.01,
                text="☀️ Peak (8am–10pm)",
                showarrow=False,
                font=dict(size=10, color="#e74c3c"),
            ),
        ],
    )
    st.plotly_chart(fig, width="stretch")
    avg_rate = electricity["tariff_rate_sgd_per_kwh"].mean()
    st.caption(f"Average: **${avg_rate:.2f}/kWh** · Off-peak **$0.18** · Peak **$0.28**")


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
def _render_plan(plan):
    st.subheader("Today's Optimal Plan (Layer 2)")

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    cost = plan.get("cost_breakdown", {})
    revenue = cost.get("revenue", 0)
    total = plan.get("objective_value_sgd", 0)

    # Compute profit CI band
    band = None
    if all(k in plan for k in ("rack_layout", "crop_prices", "crop_spoilage", "uncertainty_buffers")):
        try:
            from greenloop.data.loader import load_crops
            crops_df = load_crops().set_index("crop_id")
            forecast = {}
            for cid, buf in plan.get("uncertainty_buffers", {}).items():
                upper = buf.get("upper_ci", 0)
                lower = buf.get("lower_ci", upper * 0.65)
                forecast[cid] = {"predicted_kg": upper, "lower_ci": lower, "upper_ci": upper}
            band = compute_profit_band(
                forecast,
                cost,
                plan.get("crop_prices", {}),
                plan.get("crop_spoilage", {}),
                plan.get("rack_layout", {}),
            )
        except Exception:
            band = None

    half_width = round((band.profit_high - band.profit_low) / 2, 2) if band else None
    delta_str = f"\u00b1 ${half_width:,.0f}" if half_width else None

    m1.metric("Forecasted Revenue", f"${revenue:,.0f}")
    m2.metric(
        "Forecasted Profit",
        f"${(band.profit_expected if band else total):,.0f}",
        delta=delta_str,
    )
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

    # Red alert banner when typhoon is active
    if st.session_state.get("typhoon_active"):
        st.error(
            "⚠️ TYPHOON ACTIVE — 6h delivery window | "
            "Power outage: YES | UPS: 4h countdown active | "
            "Demand surge: +20% | Emergency harvest: triggered"
        )

        # Live countdown display (4 hours = 240 minutes)
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

        if st.button("Clear Typhoon Scenario"):
            st.session_state.typhoon_active = False
            st.rerun()
        st.divider()

    if st.button("⚡ Typhoon Warning", type="primary"):
        st.session_state.typhoon_active = True
        t0 = time.time()

        # Build scenario with full typhoon parameters
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
        # Carry HITL constraints into typhoon scenario
        typhoon_kwargs["excluded_racks"] = excluded_racks or []
        typhoon_kwargs["unavailable_shifts"] = unavailable_shifts or []
        typhoon_kwargs["objective_weights"] = ObjectiveWeights.from_mode(mode_key)

        try:
            typhoon_plan = build_and_solve(**typhoon_kwargs)
            elapsed = (time.time() - t0) * 1000

            st.success(f"Re-optimized in {elapsed:.0f}ms")

            if current_plan:
                comparison = compare_plans(current_plan, typhoon_plan)
                delta = comparison.get("delta", {})

                # Expanded metrics row
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(
                    "Forecasted Profit",
                    f"${typhoon_plan.get('objective_value_sgd', 0):,.0f}",
                    delta=f"{delta.get('objective_value_sgd', 0):,.0f}",
                )
                m2.metric(
                    "Delivery Window",
                    "6 hours",
                    delta="-6h",
                    delta_color="inverse",
                )
                m3.metric(
                    "Power Outage",
                    "ACTIVE",
                    delta="-yield 100%",
                    delta_color="inverse",
                )
                m4.metric(
                    "Demand Surge",
                    "+20%",
                    delta="panic buying",
                )

                # Update Layer 3 targets
                if "rl_env" in st.session_state:
                    st.session_state.rl_env.update_targets(
                        {
                            "temp": typhoon_plan.get("room_temp_target_c", 22),
                        }
                    )
                    # Trigger power outage in RL env if available
                    if hasattr(st.session_state.rl_env, "trigger_power_outage"):
                        st.session_state.rl_env.trigger_power_outage()
                    st.info("Layer 3 targets updated — power outage triggered in RL environment")
            else:
                st.write(f"Typhoon plan forecast profit: ${typhoon_plan.get('objective_value_sgd', 0):,.0f}")

        except InfeasibleError as e:
            elapsed = (time.time() - t0) * 1000
            st.error(f"Typhoon plan infeasible ({elapsed:.0f}ms): {e}")
            if e.binding_constraint:
                st.info(f"Try: {e.binding_constraint}")

    st.caption(
        "Typhoon Warning: 6h delivery | 30% power outage probability | "
        "4h UPS countdown | +20% demand surge | Emergency harvest + cold storage"
    )


if __name__ == "__main__":
    main()
