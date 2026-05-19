"""Adopt a Kale — Home / Landing page."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from lib.styles import (
    inject_css, brand_header, hero, eyebrow,
    KALE, LEAF, LIME, CORAL, CREAM, HAIR, MUTED, INK, ASSETS, img_to_base64,
)
from lib.mock_data import TIERS

st.set_page_config(
    page_title="Adopt a Kale",
    page_icon="🥬",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ───────────────────────────────────────────
# Top brand bar
# ───────────────────────────────────────────
brand_header()

# ───────────────────────────────────────────
# Hero: two columns (copy left, leaves right)
# ───────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    eyebrow("Singapore · 2026")
    hero(
        headline="Adopt<br>a Kale.",
        subhead="Your apartment's vegetable patch.",
        description=(
            "80% of Singaporeans live in HDB flats. No garden. No allotment. "
            "We give you a real vertical-farm plot — grown by AI, harvested for your dinner."
        ),
    )

    st.write("")
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("🌱  Start your plot", type="primary", use_container_width=True):
            st.switch_page("pages/1_🚀_Start.py")
    with btn_col2:
        if st.button("👀  See Sarah's plot", type="secondary", use_container_width=True):
            st.switch_page("pages/2_🌿_My_Plot.py")

    st.caption("From S$10/mo · Cancel anytime · Singapore-grown · Pesticide-free")

with col_right:
    # Stack the two leaves with relative positioning via HTML
    leaf_dark = img_to_base64(ASSETS / "leaf-dark.png")
    leaf_lime = img_to_base64(ASSETS / "leaf-lime.png")
    st.markdown(
        f"""
        <div style="position:relative;height:380px;">
          <img src="data:image/png;base64,{leaf_dark}" width="260" height="312"
               style="position:absolute;right:0;top:0;"/>
          <img src="data:image/png;base64,{leaf_lime}" width="130" height="156"
               style="position:absolute;right:200px;top:160px;opacity:0.9;"/>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ───────────────────────────────────────────
# Three tier section
# ───────────────────────────────────────────
eyebrow("Three tiers · One brand")
st.markdown(
    f"<h2 style='font-size:2.2rem;font-weight:800;color:{INK};margin-bottom:1.5rem;'>"
    "Pick how much garden you want.</h2>",
    unsafe_allow_html=True,
)

tier_cols = st.columns(3)
for i, tier in enumerate(TIERS):
    with tier_cols[i]:
        is_premium = tier["id"] == "Pro"
        is_recommended = tier.get("recommended", False)
        bg = KALE if is_premium else "white"
        text_color = LIME if is_premium else INK
        muted_color = LIME + "CC" if is_premium else MUTED
        accent = CORAL if is_premium else (KALE if is_recommended else LEAF)
        border = f"2px solid {KALE}" if is_recommended else (f"1px solid {KALE}" if is_premium else f"1px solid {HAIR}")
        shadow = "box-shadow: 0 8px 24px rgba(45,80,22,0.08);" if is_recommended else ""

        recommended_badge = (
            f"<div style='position:absolute;top:-10px;left:24px;background:{CORAL};color:white;"
            f"font-size:0.6rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;"
            f"padding:0.25rem 0.75rem;border-radius:999px;'>Most popular</div>"
            if is_recommended else ""
        )

        features_html = "".join([
            f"<li style='font-size:0.85rem;color:{muted_color};margin-bottom:0.25rem;'>"
            f"✓ {f}</li>"
            for f in tier["features"]
        ])

        st.markdown(
            f"""
            <div style="position:relative;background:{bg};border-radius:24px;padding:2rem;
                        border:{border};{shadow}min-height:380px;">
              {recommended_badge}
              <div style="width:48px;height:6px;background:{accent};border-radius:999px;margin-bottom:1.5rem;"></div>
              <p style="font-size:0.7rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;
                        color:{accent};margin:0;">{tier['id']}</p>
              <p style="font-size:3rem;font-weight:800;color:{text_color};margin:0.5rem 0 1rem 0;">
                S${tier['price']}<span style="font-size:0.9rem;color:{muted_color};font-weight:400;"> / month</span>
              </p>
              <p style="color:{text_color};margin-bottom:1.5rem;">{tier['body']}</p>
              <ul style="list-style:none;padding:0;margin:0;">
                {features_html}
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# Footer
st.markdown(
    f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                font-size:0.75rem;color:{MUTED};padding:1rem 0;">
      <span style="font-weight:700;letter-spacing:0.25em;color:{KALE};">ADOPT A KALE</span>
      <span>© 2026 Adopt a Kale F2C · Singapore · MGMT 655 Capstone</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar branding
with st.sidebar:
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"""
        <div style="text-align:center;padding:1rem 0;">
            <img src="data:image/png;base64,{leaf_b64}" width="60" height="72"/>
            <h2 style="color:{KALE};margin:0.5rem 0 0 0;font-weight:800;">Adopt a Kale</h2>
            <p style="color:{MUTED};font-size:0.75rem;margin:0;">Singapore's AI garden share</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<p style='color:{MUTED};font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;font-weight:700;'>"
        "Demo navigation</p>",
        unsafe_allow_html=True,
    )
