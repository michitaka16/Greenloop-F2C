"""Layer 5: Media AI — RAG Chatbot for Adopt a Kale Farm.

Ask questions about Adopt a Kale's produce, sustainability, and operations.
RAG-powered by ChromaDB + sentence-transformers + Claude API.
Falls back to demo-mode cache when no API key is configured.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure adoptakale package is on path
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
from adoptakale.rag import RAGAgent

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
                # Sources
                if metadata.get("sources"):
                    sources = metadata["sources"]
                    if sources and sources != ["demo_cache"]:
                        st.caption(
                            "\u2699 **Sources:** " + ", ".join(sources)
                        )
                    elif sources == ["demo_cache"]:
                        st.caption(
                            "\U0001f3b2 **Demo mode** — configure LLM API key for full RAG"
                        )
                # Latency
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
        if st.button(topic, use_container_width=True, key=f"topic_{topic[:10]}"):
            st.session_state.chat_history.append(
                {"role": "user", "content": topic.replace("\U0001f331 ", "").replace("\U0001f4a7 ", "").replace("\U0001f9f1 ", "").replace("\U0001f4cd ", "").replace("\U0001f4b0 ", "").replace("\U0001f96a ", "")}
            )
            st.rerun()

    st.divider()
    st.markdown("### About")
    st.caption(
        "Adopt a Kale · Layer 5: Media AI\n"
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

            # Show demo mode banner if applicable
            if result.from_cache:
                st.info(
                    "\U0001f3b2 **Demo mode** — responses are cached samples. "
                    "Configure `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env` "
                    "to enable full RAG with live retrieval."
                )

# ── Failure indicators ────────────────────────────────────────────────────
agent = get_agent()
freshness = agent.get_freshness()
if freshness.status == "critical":
    st.warning(
        "\u26a0\ufe0f Knowledge base has not been updated in over 30 days. "
        "Update files in `data/rag_knowledge/` and restart to refresh."
    )
