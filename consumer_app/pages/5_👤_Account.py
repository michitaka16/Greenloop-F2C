"""Account — subscription + settings."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from lib.styles import (
    inject_css, brand_header, pill,
    KALE, LEAF, LIME, CORAL, CREAM, HAIR, MUTED, INK, ASSETS, img_to_base64,
)
from lib.mock_data import SARAH

st.set_page_config(page_title="Account — Adopt a Kale", page_icon="👤", layout="wide")
inject_css()
brand_header()

# Profile header
col_avatar, col_info, _ = st.columns([1, 4, 2])
with col_avatar:
    st.markdown(
        f"<div style='height:80px;width:80px;border-radius:999px;background:{KALE};"
        f"display:flex;align-items:center;justify-content:center;color:{LIME};"
        f"font-size:2rem;font-weight:800;'>{SARAH['initial']}</div>",
        unsafe_allow_html=True,
    )
with col_info:
    st.markdown(
        f"<h1 style='font-size:1.8rem;font-weight:800;color:{INK};margin:0;'>{SARAH['name']}</h1>"
        f"<p style='color:{MUTED};margin:0;'>{SARAH['flat']} · {SARAH['hood']}</p>",
        unsafe_allow_html=True,
    )

st.write("")

# Subscription card
st.markdown(
    f"""
    <div class="kale-card" style="margin-bottom:1rem;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;">
        <div>
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;
                    text-transform:uppercase;color:{MUTED};margin:0;">Current plan</p>
          <h2 style="font-size:1.6rem;font-weight:800;color:{INK};margin:0.25rem 0;">
              {SARAH['tier']} tier
          </h2>
          <p style="font-size:0.85rem;color:{MUTED};margin:0;">
            Plot #{SARAH['plot_id']} · started {SARAH['started_at']}
          </p>
        </div>
        <div>{pill("ACTIVE", "kale")}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Billing and upgrade buttons
b_col1, b_col2 = st.columns(2)
with b_col1:
    st.button("💳  Billing & invoices", use_container_width=True, type="secondary")
with b_col2:
    st.button("⬆  Upgrade to Real", use_container_width=True, type="primary")

st.write("")

# Preferences
st.markdown(f"<h3 style='color:{INK};margin-bottom:0.5rem;'>⚙️  Preferences</h3>",
            unsafe_allow_html=True)

prefs = [
    ("WhatsApp updates", "Weekly + on harvest", True),
    ("Delivery window",  "Saturday morning",   None),
    ("Pause subscription", "For travel or holidays", None),
]
for label, value, on in prefs:
    badge_html = (
        f"<div style='background:{CREAM};color:{KALE};padding:0.3rem 0.8rem;"
        f"border-radius:999px;font-size:0.65rem;font-weight:700;letter-spacing:0.15em;'>ON</div>"
        if on else ""
    )
    button_html = "" if on else (
        f"<div style='color:{KALE};font-weight:700;font-size:0.85rem;cursor:pointer;'>Change →</div>"
    )
    st.markdown(
        f"""
        <div class="kale-card" style="margin-bottom:0.5rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <p style="font-weight:600;color:{INK};margin:0;">{label}</p>
              <p style="font-size:0.8rem;color:{MUTED};margin:0;">{value}</p>
            </div>
            {badge_html}{button_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.markdown(f"<p style='text-align:center;color:{MUTED};font-size:0.8rem;'>🚪 Sign out</p>",
            unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"<div style='text-align:center;padding:1rem 0;'>"
        f"<img src='data:image/png;base64,{leaf_b64}' width='60' height='72'/>"
        f"<h2 style='color:{KALE};margin:0.5rem 0 0 0;font-weight:800;'>Adopt a Kale</h2></div>",
        unsafe_allow_html=True,
    )
