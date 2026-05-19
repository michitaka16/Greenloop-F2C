"""Chat — Ask your kale anything. Mock RAG-style responses."""

import sys
from pathlib import Path
# Deduplicated: only add consumer_app/ to sys.path once
_app_dir = str(Path(__file__).parent.parent)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import streamlit as st
from lib.styles import (
    inject_css, brand_header, eyebrow, pill,
    KALE, LEAF, LIME, CORAL, CREAM, HAIR, MUTED, INK, ASSETS, img_to_base64,
    recipe_card_html,
)
from lib.mock_data import mock_response, SUGGESTED_QUESTIONS
from lib.mock_data import RECIPES, get_recipe_for_crops, CROPS

st.set_page_config(page_title="Ask your kale — Adopt a Kale", page_icon="💬", layout="wide")
inject_css()
brand_header()

# Init chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "user", "content": "How's my kale doing?", "citations": []},
        {
            "role": "kale",
            "content": (
                "Your **curly kale** is 74% mature, on track for **May 28** harvest. It entered "
                "final growth phase yesterday. The leaves are firming up nicely — expecting around "
                "200g of harvest based on current biomass."
            ),
            "citations": [
                {"source": "Plot 042 sensors", "snippet": "Day 31 of 42, biomass 184g, leaf area 0.42m²"},
                {"source": "Growth model", "snippet": "Predicted yield: 200g ± 20g (95% CI)"},
            ],
        },
    ]

# Header
col_a, col_b = st.columns([3, 1])
with col_a:
    st.markdown(
        f"<div style='margin-bottom:0.5rem;'>{pill('RAG · <500ms', 'coral')}</div>"
        f"<h1 style='font-size:2.2rem;font-weight:800;color:{INK};margin:0;'>Ask your kale.</h1>"
        f"<p style='color:{MUTED};margin-top:0.5rem;'>Grounded in your plot's real-time "
        f"sensors and AI decisions.</p>",
        unsafe_allow_html=True,
    )
with col_b:
    if st.button("🔄  Clear chat", use_container_width=True, type="secondary"):
        st.session_state.chat_history = []
        st.rerun()

st.write("")

# Display chat history
leaf_b64 = img_to_base64(ASSETS / "leaf-lime.png")
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        col_spacer, col_msg = st.columns([1, 3])
        with col_msg:
            st.markdown(
                f"""
                <div style="display:flex;justify-content:flex-end;">
                  <div style="background:{KALE};color:white;padding:0.75rem 1.2rem;
                              border-radius:20px;border-bottom-right-radius:6px;max-width:80%;">
                    {msg['content']}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        col_msg, col_spacer = st.columns([4, 1])
        with col_msg:
            st.markdown(
                f"""
                <div style="display:flex;gap:0.75rem;align-items:flex-start;">
                  <div style="height:36px;width:36px;border-radius:999px;background:{KALE};
                              display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <img src="data:image/png;base64,{leaf_b64}" width="20" height="24"/>
                  </div>
                  <div style="background:white;border:1px solid {HAIR};padding:1rem 1.25rem;
                              border-radius:20px;border-top-left-radius:6px;flex:1;line-height:1.6;">
                    {msg['content']}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Citations
            if msg.get("citations"):
                cite_col, _ = st.columns([4, 1])
                with cite_col:
                    st.markdown(
                        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
                        f"text-transform:uppercase;color:{MUTED};margin:0.75rem 0 0.5rem 3rem;'>Sources</p>",
                        unsafe_allow_html=True,
                    )
                    for c in msg["citations"]:
                        st.markdown(
                            f"""
                            <div style="background:{CREAM};border-radius:14px;padding:0.5rem 0.9rem;
                                        margin-left:3rem;margin-bottom:0.4rem;font-size:0.8rem;">
                              <p style="font-weight:700;color:{KALE};margin:0;">{c['source']}</p>
                              <p style="color:{INK}AA;margin:0;">{c['snippet']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            # Recipe cards (if response contains recipes)
            if msg.get("recipes"):
                st.markdown(
                    f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
                    f"text-transform:uppercase;color:{CORAL};margin:0.75rem 0 0.5rem 0;'>"
                    f"🍳 Recipes You Can Make</p>",
                    unsafe_allow_html=True,
                )
                for recipe in msg["recipes"][:3]:
                    st.markdown(recipe_card_html(recipe), unsafe_allow_html=True)
    st.write("")

# Suggested questions (only if conversation has 0–1 user messages)
user_msg_count = sum(1 for m in st.session_state.chat_history if m["role"] == "user")
if user_msg_count <= 1:
    st.markdown(
        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{MUTED};margin-top:1rem;'>✨ Try asking</p>",
        unsafe_allow_html=True,
    )
    sq_cols = st.columns(min(3, len(SUGGESTED_QUESTIONS)))
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        if i >= 3:
            break
        with sq_cols[i]:
            if st.button(q, key=f"sq_{i}", use_container_width=True, type="secondary"):
                st.session_state.chat_history.append({"role": "user", "content": q, "citations": []})
                response = mock_response(q)
                st.session_state.chat_history.append({
                    "role": "kale",
                    "content": response["text"],
                    "citations": response["citations"],
                    "recipes": response.get("recipes"),
                })
                st.rerun()

# Chat input
st.write("")
user_input = st.chat_input("How's my kale today?")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input, "citations": []})
    response = mock_response(user_input)
    st.session_state.chat_history.append({
        "role": "kale",
        "content": response["text"],
        "citations": response["citations"],
        "recipes": response.get("recipes"),
    })
    st.rerun()

# Sidebar
with st.sidebar:
    leaf_b64s = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"<div style='text-align:center;padding:1rem 0;'>"
        f"<img src='data:image/png;base64,{leaf_b64s}' width='60' height='72'/>"
        f"<h2 style='color:{KALE};margin:0.5rem 0 0 0;font-weight:800;'>Adopt a Kale</h2></div>",
        unsafe_allow_html=True,
    )
