"""Schedule — harvest calendar + pause/skip + recipe suggestions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from lib.styles import (
    inject_css, inject_gamification_css, brand_header, pill,
    KALE, LEAF, LIME, CORAL, CREAM, HAIR, MUTED, INK, ASSETS, img_to_base64,
    recipe_card_html, delivery_card_skip_html,
)
from lib.mock_data import (
    UPCOMING_DELIVERIES, CROPS, SKIP_REASONS,
    RECIPES, get_recipe_for_crops,
)

# Session state for skip flow
if "skipped_dates" not in st.session_state:
    st.session_state.skipped_dates = []
if "show_skip_panel" not in st.session_state:
    st.session_state.show_skip_panel = False
if "skip_target" not in st.session_state:
    st.session_state.skip_target = None

st.set_page_config(page_title="Schedule — Adopt a Kale", page_icon="📅", layout="wide")
inject_css()
inject_gamification_css()
brand_header()

st.markdown(
    f"<div style='margin-bottom:0.5rem;'>{pill('VRP · 48ms solve', 'coral')}</div>"
    f"<h1 style='font-size:2.2rem;font-weight:800;color:{INK};margin:0;'>Your harvest calendar.</h1>"
    f"<p style='color:{MUTED};margin-top:0.5rem;'>Optimised for your weekly rhythm, weather-corrected.</p>",
    unsafe_allow_html=True,
)
st.write("")

# ────────────────────────────────────────────
# 🍳 This Week's Recipes — shown above calendar
# ────────────────────────────────────────────
st.markdown(
    f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
    f"text-transform:uppercase;color:{CORAL};margin-bottom:0.75rem;'>"
    f"🍳 RECIPE IDEAS — WHAT TO MAKE THIS WEEK</p>",
    unsafe_allow_html=True,
)

# Get crops from the next delivery
next_crops = []
for d in UPCOMING_DELIVERIES:
    for item in d["items"]:
        if "kale" in item.lower():
            next_crops.append("Curly Kale")
        if "basil" in item.lower():
            next_crops.append("Thai Basil")

recipes = get_recipe_for_crops(next_crops) if next_crops else RECIPES[:3]
recipe_col1, recipe_col2 = st.columns(2)
for i, recipe in enumerate(recipes):
    with [recipe_col1, recipe_col2][i % 2]:
        st.markdown(recipe_card_html(recipe), unsafe_allow_html=True)

st.markdown(
    f"<p style='font-size:0.75rem;color:{MUTED};margin:0.5rem 0 0 0;'>"
    f"Want personalised recipes? <a href='../pages/3_💬_Chat.py' "
    f"style='color:{KALE};font-weight:600;'>Ask your kale →</a></p>",
    unsafe_allow_html=True,
)

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ────────────────────────────────────────────
# ⏸ Pause / Skip Delivery
# ────────────────────────────────────────────
pause_col1, pause_col2 = st.columns([1, 2])
with pause_col1:
    st.markdown(
        f"<h2 style='color:{INK};font-weight:700;'>⏸ Pause or Skip</h2>",
        unsafe_allow_html=True,
    )
with pause_col2:
    st.markdown(
        f"<p style='color:{MUTED};font-size:0.85rem;margin-top:0.4rem;'>"
        f"Going on a trip or have travel plans? No penalty — "
        f"pause your delivery and your crops keep growing.</p>",
        unsafe_allow_html=True,
    )

st.write("")
if st.button("⏸  Skip / Pause a Delivery", type="primary", use_container_width=True):
    st.session_state.show_skip_panel = not st.session_state.show_skip_panel
    st.rerun()

if st.session_state.show_skip_panel:
    with st.container():
        st.markdown(
            f"<div style='background:{CREAM};border:1px solid {HAIR};border-radius:20px;padding:1.25rem;'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='font-weight:700;color:{INK};margin:0 0 0.75rem 0;'>"
            f"Which delivery would you like to skip?</p>",
            unsafe_allow_html=True,
        )
        for d in UPCOMING_DELIVERIES:
            date_key = d["date"]
            is_skipped = date_key in st.session_state.skipped_dates
            if d["can_skip"] and not is_skipped:
                skip_col1, skip_col2 = st.columns([4, 1])
                with skip_col1:
                    st.markdown(delivery_card_skip_html(d, is_skipped=False), unsafe_allow_html=True)
                with skip_col2:
                    reason = st.selectbox(
                        "Reason",
                        options=[""] + SKIP_REASONS,
                        key=f"reason_{date_key.replace(' ','_')}",
                        label_visibility="collapsed",
                    )
                    if st.button("Skip", key=f"skipbtn_{date_key.replace(' ','_')}", use_container_width=True):
                        if reason:
                            st.session_state.skipped_dates.append(date_key)
                            st.session_state.show_skip_panel = False
                            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Show skipped deliveries
if st.session_state.skipped_dates:
    st.write("")
    st.markdown(
        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{MUTED};margin-bottom:0.5rem;'>"
        f"SKIPPED DELIVERIES</p>",
        unsafe_allow_html=True,
    )
    for d in UPCOMING_DELIVERIES:
        if d["date"] in st.session_state.skipped_dates:
            undo_col1, undo_col2 = st.columns([4, 1])
            with undo_col1:
                st.markdown(delivery_card_skip_html(d, is_skipped=True), unsafe_allow_html=True)
            with undo_col2:
                if st.button("↩ Undo", key=f"undo_{d['date'].replace(' ','_')}", use_container_width=True):
                    st.session_state.skipped_dates.remove(d["date"])
                    st.rerun()

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ─────────────────────────────────
# Upcoming deliveries
# ─────────────────────────────────
st.markdown(
    f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
    f"text-transform:uppercase;color:{MUTED};margin-bottom:0.75rem;'>UPCOMING DELIVERIES</p>",
    unsafe_allow_html=True,
)
for d in UPCOMING_DELIVERIES:
    if d["date"] not in st.session_state.skipped_dates:
        items_html = "".join([
            f"<p style='margin:0;font-size:0.9rem;color:{INK};display:flex;align-items:center;gap:0.5rem;'>"
            f"<span style='color:{LEAF};'>🌱</span> {item}</p>"
            for item in d["items"]
        ])
        status_color = KALE if d["status"] == "scheduled" else MUTED
        status_bg = CREAM if d["status"] == "scheduled" else "transparent"
        status_border = f"1px solid {HAIR}" if d["status"] != "scheduled" else "none"

        st.markdown(
            f"""
            <div class="kale-card" style="margin-bottom:0.75rem;">
              <div style="display:flex;align-items:center;gap:1.5rem;">
                <div style="text-align:center;min-width:64px;flex-shrink:0;">
                  <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:{CORAL};margin:0;">{d['date'].split()[0]}</p>
                  <p style="font-size:2rem;font-weight:800;color:{KALE};line-height:1;margin:0.25rem 0 0 0;">
                    {d['date'].split()[1]}
                  </p>
                </div>
                <div style="flex:1;">
                  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
                    <span style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
                                 color:{MUTED};text-transform:uppercase;">
                      🚚 Delivery window 09:00–11:00
                    </span>
                  </div>
                  {items_html}
                </div>
                <div style="background:{status_bg};border:{status_border};color:{status_color};
                            padding:0.3rem 0.8rem;border-radius:999px;font-size:0.65rem;
                            font-weight:700;text-transform:uppercase;letter-spacing:0.15em;">
                  {d['status']}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ─────────────────────────────────
# Crop timeline
# ─────────────────────────────────
st.markdown(
    f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
    f"text-transform:uppercase;color:{MUTED};margin-bottom:0.75rem;'>GROWTH TIMELINE</p>",
    unsafe_allow_html=True,
)
for c in CROPS:
    pct = int(c["days_in"] / c["total_days"] * 100)
    st.markdown(
        f"""
        <div class="kale-card" style="margin-bottom:0.75rem;">
          <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">
            <div style="font-size:1.5rem;height:48px;width:48px;border-radius:14px;background:{CREAM};
                        display:flex;align-items:center;justify-content:center;">{c['emoji']}</div>
            <div style="flex:1;">
              <p style="font-size:0.7rem;color:{MUTED};margin:0;">{c['variety']}</p>
              <p style="font-weight:700;color:{INK};margin:0;font-size:1.05rem;">{c['name']}</p>
            </div>
            <p style="font-size:0.85rem;color:{MUTED};">Day {c['days_in']} / {c['total_days']}</p>
          </div>
          <div style="position:relative;height:32px;background:{CREAM};border-radius:999px;overflow:hidden;">
            <div style="position:absolute;inset:0 auto 0 0;width:{pct}%;
                        background:linear-gradient(90deg,{LEAF},{KALE});border-radius:999px;"></div>
            <div style="position:absolute;inset:0;display:flex;align-items:center;padding:0 0.85rem;">
              <span style="font-size:0.75rem;font-weight:700;color:white;
                           text-shadow:0 1px 2px rgba(0,0,0,0.15);">{pct}% mature</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Sidebar
with st.sidebar:
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"<div style='text-align:center;padding:1rem 0;'>"
        f"<img src='data:image/png;base64,{leaf_b64}' width='60' height='72'/>"
        f"<h2 style='color:{KALE};margin:0.5rem 0 0 0;font-weight:800;'>Adopt a Kale</h2></div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<div style='padding:0.5rem 1rem;background:{CREAM};border-radius:12px;'>"
        f"<p style='margin:0;font-size:0.65rem;font-weight:700;letter-spacing:0.15em;color:{MUTED};'>SKIP COUNT</p>"
        f"<p style='margin:0.2rem 0;font-weight:800;color:{KALE};font-size:1.5rem;'>{len(st.session_state.skipped_dates)}</p>"
        f"<p style='margin:0;font-size:0.7rem;color:{MUTED};'>deliveries skipped</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<p style='color:{MUTED};font-size:0.75rem;'>"
        f"Skipped harvests are donated to NTUC Food Bank. "
        f"You receive an ESG impact badge in your profile.</p>",
        unsafe_allow_html=True,
    )
