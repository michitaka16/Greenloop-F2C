"""Layer 5: Media AI — RAG Chatbot for Adopt a Kale Farm.

Ask questions about Adopt a Kale's produce, sustainability, and operations.
RAG-powered by ChromaDB + sentence-transformers + Claude API.
Falls back to demo-mode cache when no API key is configured.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure greenloop package is on path
src_path = Path(__file__).resolve().parents[1] / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Adopt a Kale — Media AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from greenloop.rag import RAGAgent
from greenloop.data.shared_data import load_farm_output

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history: list[dict] = []

if "rag_agent" not in st.session_state:
    st.session_state.rag_agent: RAGAgent | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_agent() -> RAGAgent:
    if st.session_state.rag_agent is None:
        agent = RAGAgent(
            persist_dir=str(Path(__file__).resolve().parents[1] / ".chroma_db"),
        )
        st.session_state.rag_agent = agent
    return st.session_state.rag_agent


def latency_color(ms: float) -> str:
    """Return a CSS color string for latency."""
    if ms < 300:
        return "#22c55e"   # green
    if ms < 500:
        return "#eab308"   # yellow
    return "#ef4444"       # red


def freshness_badge(freshness) -> tuple[str, str]:
    """Return (emoji, label) for a FreshnessScore status."""
    if freshness.status == "fresh":
        return "\u2705", "Fresh"
    if freshness.status == "stale":
        return "\u26a0\ufe0f", "Needs Update"
    return "\u274c", "Outdated"


def render_chat_message(role: str, content: str, metadata: dict | None = None):
    """Render a single chat message bubble."""
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    else:
        with st.chat_message("assistant"):
            st.markdown(content)
            if metadata:
                # Latency + freshness
                latency_ms = metadata.get("latency_ms", 0)
                color = latency_color(latency_ms)
                freshness = metadata.get("freshness")
                if freshness:
                    badge_emoji, badge_label = freshness_badge(freshness)
                    st.caption(
                        f"{badge_emoji} Knowledge base: {badge_label} &nbsp;"
                        f"\u23f1\ufe0f Latency: "
                        f"<span style='color:{color};font-weight:bold'>{latency_ms:.0f}ms</span>"
                        f" &nbsp; (target &lt;500ms)"
                    )
                else:
                    st.caption(
                        f"\u23f1\ufe0f Latency: "
                        f"<span style='color:{color};font-weight:bold'>{latency_ms:.0f}ms</span>"
                    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
st.title("\U0001f4ac Media AI — Farm Knowledge Assistant")
st.caption(
    "RAG-powered chatbot for Adopt a Kale Farm — produce, sustainability, and operations. "
    "Powered by ChromaDB + sentence-transformers"
)

# ── Farm AI Live Status ──────────────────────────────────────────────────
farm = load_farm_output()
if farm:
    rack_layout = farm.get("rack_layout", {})
    forecast = farm.get("forecast", {})
    led_schedule = farm.get("led_schedule", {})
    cv_summary = farm.get("cv_diagnosis_summary") or {}
    cost = farm.get("cost_breakdown", {})
    profit = farm.get("objective_value_sgd", 0)

    crop_names = {
        "kai_lan": "Kai Lan", "baby_spinach": "Baby Spinach",
        "lettuce_mambo": "Lettuce", "chye_sim": "Chye Sim",
        "arugula": "Arugula", "pak_choi": "Pak Choi",
        "kale": "Kale", "basil_thai": "Thai Basil",
        "coriander": "Coriander", "mint": "Mint",
    }
    crop_colors = {
        "kai_lan": "#1abc9c", "baby_spinach": "#3498db",
        "lettuce_mambo": "#2c3e50", "chye_sim": "#e67e22",
        "arugula": "#2ecc71", "pak_choi": "#00bcd4",
        "kale": "#f1c40f", "basil_thai": "#9b59b6",
        "coriander": "#e74c3c", "mint": "#e91e63",
    }

    with st.expander("🌾 Today's Farm AI Status — click to expand", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Today's Profit**")
            st.markdown(f"### ${profit:.2f}")
        with c2:
            st.markdown("**Revenue / Energy / Labour**")
            st.markdown(
                f"${cost.get('revenue', 0):.2f}"
                f" / ${abs(cost.get('electricity', 0)):.2f}"
                f" / ${abs(cost.get('labour', 0)):.2f}"
            )
        with c3:
            st.markdown("**Crop Health**")
            n_low = cv_summary.get("nitrogen_low_count", 0)
            w_stress = cv_summary.get("water_stress_count", 0)
            if n_low or w_stress:
                st.markdown(f"⚠️ {n_low} nitrogen low, {w_stress} water stress")
            else:
                st.markdown("✅ All racks healthy")

        # Growing now
        active_crops = set(rack_layout.values())
        growing = [crop_names.get(c, c) for c in active_crops if c in crop_names]
        if growing:
            st.markdown(f"**🌱 Growing today:** {', '.join(growing)}")

        # LED schedule summary
        if led_schedule:
            tier0 = led_schedule.get("tier_0", [])
            if tier0:
                on_hours = [i for i, v in enumerate(tier0) if v == 1]
                if on_hours:
                    st.markdown(
                        f"**💡 LED photoperiod:** Rack 0 on {min(on_hours):02d}:00–{max(on_hours):02d}:00"
                    )
        st.caption(f"Updated: {farm.get('plan_date', 'unknown')} · Source: Farm AI")
else:
    st.info("🌾 Run **Farm AI** first to see today's farm status here.")


# ── Sidebar: knowledge base status ────────────────────────────────────────
with st.sidebar:
    st.markdown("### Knowledge Base")
    agent = get_agent()
    freshness = agent.get_freshness()
    badge_emoji, badge_label = freshness_badge(freshness)

    freshness_color = {
        "fresh": "#22c55e",
        "stale": "#eab308",
        "critical": "#ef4444",
    }.get(freshness.status, "#9ca3af")

    st.markdown(
        f"**Status:** {badge_emoji} "
        f"<span style='color:{freshness_color};font-weight:bold'>{badge_label}</span>"
    )
    st.markdown(f"**Last updated:** {freshness.days_since_update} day(s) ago")
    st.progress(freshness.score, text=f"Freshness score: {freshness.score:.0%}")

    st.divider()
    st.markdown("### Quick Topics")
    topics = [
        "\U0001f331 Our crops & nutritional profiles",
        "\U0001f4a7 Water savings & sustainability",
        "\U0001f9f1 Pesticide-free growing",
        "\U0001f4cd Farm location & delivery",
        "\U0001f4b0 Pricing & ordering",
        "\U0001f96a Food miles & carbon footprint",
    ]
    for topic in topics:
        label = topic.replace("\U0001f331 ", "").replace("\U0001f4a7 ", "").replace("\U0001f9f1 ", "").replace("\U0001f4cd ", "").replace("\U0001f4b0 ", "").replace("\U0001f96a ", "")
        if st.button(topic, use_container_width=True, key=f"topic_{topic[:10]}"):
            st.session_state.chat_history.append({"role": "user", "content": label})
            # Natural re-render — no st.rerun() needed

    st.divider()
    st.markdown("### About")
    st.caption(
        "Adopt a Kale Farm OS · Layer 5: Media AI\n"
        "ChromaDB vector store · sentence-transformers embeddings"
    )

st.divider()

# ── Latency target indicator ─────────────────────────────────────────────
col_lat, col_clear = st.columns([4, 1])
with col_lat:
    st.markdown(
        "\u23f1\ufe0f **Latency target:** <span style='color:#22c55e;font-weight:bold'>< 500ms</span> "
        "(RAG retrieval + LLM generation)",
        unsafe_allow_html=True,
    )
with col_clear:
    if st.button("\U0001f5d1 Clear chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ── Chat history ──────────────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    render_chat_message(msg["role"], msg["content"], msg.get("metadata"))

# ── Input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about Adopt a Kale Farm..."):
    # Add user message
    st.session_state.chat_history.append(
        {"role": "user", "content": prompt}
    )
    render_chat_message("user", prompt)
    st.rerun()

# ── Generate assistant response ────────────────────────────────────────────
if st.session_state.chat_history:
    last_msg = st.session_state.chat_history[-1]
    if last_msg["role"] == "user" and "metadata" not in last_msg:
        # Need to generate
        question = last_msg["content"]
        with st.spinner("\u2728 Thinking..."):
            try:
                result = get_agent().ask(question)
                metadata = {
                    "sources": result.sources,
                    "latency_ms": result.latency_ms,
                    "freshness": result.freshness,
                    "from_cache": result.from_cache,
                }
            except Exception as exc:
                result = None
                metadata = {
                    "sources": [],
                    "latency_ms": 0,
                    "freshness": get_agent().get_freshness(),
                    "from_cache": False,
                }
                st.error(f"RAG error: {exc}")

        if result:
            # Update last message with metadata
            last_msg["metadata"] = metadata

            # Show assistant response
            render_chat_message("assistant", result.text, metadata)

            # Show demo mode hint if applicable
            if result.from_cache:
                st.caption(
                    "\U0001f3b2 Demo mode — configure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env` for full RAG."
                )

# ── Failure indicators ────────────────────────────────────────────────────
agent = get_agent()
freshness = agent.get_freshness()
if freshness.status == "critical":
    st.warning(
        "\u26a0\ufe0f Knowledge base has not been updated in over 30 days. "
        "Update files in `data/rag_knowledge/` and restart to refresh."
    )
