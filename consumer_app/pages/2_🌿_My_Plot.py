"""My Plot — Adopt a Kale app centerpiece."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from lib.styles import (
    inject_css, brand_header, eyebrow, pill, maturity_ring_html, progress_card,
    KALE, LEAF, LIME, CORAL, CREAM, PAPER, HAIR, MUTED, INK, ASSETS, img_to_base64,
)
from lib.mock_data import SARAH, CROPS, STATUS, UPCOMING_DELIVERIES, RECENT_EVENTS

st.set_page_config(page_title="My Plot — Adopt a Kale", page_icon="🌿", layout="wide")
inject_css()
brand_header()

# ───────────────────────────────────────────
# Greeting
# ───────────────────────────────────────────
st.markdown(
    f"<p style='color:{MUTED};margin:0;'>Good morning, {SARAH['name'].split()[0]}.</p>"
    f"<h1 style='font-size:2.2rem;font-weight:800;color:{INK};margin:0.25rem 0 1.5rem 0;'>"
    f"Your kale is <span style='color:{KALE};'>{STATUS['maturity']}% ready</span>.</h1>",
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────
# Hero card — two columns (ring left, details right)
# ───────────────────────────────────────────
with st.container():
    st.markdown(
        f"<div style='background:white;border:1px solid {HAIR};border-radius:24px;overflow:hidden;'>",
        unsafe_allow_html=True,
    )
    hero_left, hero_right = st.columns([1, 1])

    with hero_left:
        left_html = (
            "<div style='background:linear-gradient(135deg," + CREAM + " 0%,white 50%," + PAPER + " 100%);"
            "padding:2.5rem 2rem;text-align:center;border-right:1px solid " + HAIR + ";'>"
            "<div style='margin-bottom:1.5rem;'>" + pill("FOR DINNER", "coral") + "</div>"
            + maturity_ring_html(STATUS['maturity'], size=240)
            + "<p style='margin-top:2.5rem;color:" + MUTED + ";font-size:0.85rem;'>Plot #042 · Day 31 of 42</p>"
            "</div>"
        )
        st.markdown(left_html, unsafe_allow_html=True)

    with hero_right:
        right_html = (
            "<div style='padding:2.5rem 2rem;'>"
            "<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:" + CORAL + ";margin:0;'>Now growing</p>"
            "<h2 style='font-size:1.8rem;font-weight:800;color:" + INK + ";margin:0.4rem 0;'>Curly Kale <span style='color:" + MUTED + ";font-weight:400;'>+ Thai Basil</span></h2>"
            "<p style='color:" + MUTED + ";margin:0 0 1.5rem 0;font-size:0.9rem;'>Singapore vertical farm · run by AI 24/7</p>"
            "<div style='background:" + KALE + ";color:" + LIME + ";border-radius:16px;padding:1rem 1.25rem;'>"
            "<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:rgba(199,230,107,0.75);margin:0;'>Next harvest</p>"
            "<p style='font-size:1.8rem;font-weight:800;color:white;margin:0.25rem 0;'>" + SARAH['next_harvest'] + "</p>"
            "<p style='font-size:0.85rem;color:rgba(199,230,107,0.9);margin:0;'>Auto-tuned at " + STATUS['last_tuned'] + " · weather-corrected</p>"
            "</div></div>"
        )
        st.markdown(right_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# Stats row under hero
stat_cols = st.columns(4)
stats_data = [
    ("🌱", "Crops", len(CROPS), ""),
    ("📅", "Day", f"{SARAH['days_in']}/{SARAH['total_days']}", ""),
    ("💧", "Water", STATUS['water_used_l'], "L this week"),
    ("⚡", "Energy", STATUS['energy_kwh'], "kWh/wk"),
]
for col, (emoji, label, value, sub) in zip(stat_cols, stats_data):
    with col:
        st.markdown(
            f"""
            <div style="background:{CREAM};border-radius:16px;padding:1rem;display:flex;align-items:center;gap:0.75rem;">
              <div style="font-size:1.5rem;">{emoji}</div>
              <div>
                <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;
                          text-transform:uppercase;color:{MUTED};margin:0;">{label}</p>
                <p style="font-weight:700;color:{INK};margin:0;font-size:1rem;">
                    {value}<span style="font-size:0.7rem;font-weight:400;color:{MUTED};margin-left:0.25rem;">{sub}</span>
                </p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# CTA buttons
st.write("")
btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 2])
with btn_col1:
    if st.button("💬  Ask your kale", type="primary", use_container_width=True):
        st.switch_page("pages/3_💬_Chat.py")
with btn_col2:
    if st.button("📅  Schedule", type="secondary", use_container_width=True):
        st.switch_page("pages/4_📅_Schedule.py")
with btn_col3:
    if st.button("📷  Plant Camera", type="secondary", use_container_width=True):
        st.switch_page("pages/6_📷_PlantCamera.py")

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ───────────────────────────────────────────
# What's growing
# ───────────────────────────────────────────
crop_h_col1, crop_h_col2 = st.columns([3, 1])
with crop_h_col1:
    st.markdown(f"<h2 style='color:{INK};font-weight:700;'>What's in your plot</h2>",
                unsafe_allow_html=True)
with crop_h_col2:
    if st.button("See full schedule →", type="secondary", use_container_width=True):
        st.switch_page("pages/4_📅_Schedule.py")

cgrid_cols = st.columns(2)
for i, crop in enumerate(CROPS):
    with cgrid_cols[i % 2]:
        progress_card(
            label=crop["name"],
            value=crop["days_in"],
            total=crop["total_days"],
            emoji=crop["emoji"],
            variety=crop["variety"],
        )

# ───────────────────────────────────────────
# Two columns: deliveries + activity
# ───────────────────────────────────────────
st.write("")
del_col, act_col = st.columns(2)

with del_col:
    deliveries_html = ""
    for d in UPCOMING_DELIVERIES:
        items_html = "".join([f"<p style='margin:0;font-size:0.9rem;color:{INK};'>{item}</p>"
                              for item in d['items']])
        deliveries_html += f"""
        <div style="display:flex;gap:1rem;padding:0.75rem 0;border-bottom:1px solid {HAIR};">
          <div style="text-align:center;flex-shrink:0;min-width:56px;">
            <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                      text-transform:uppercase;color:{CORAL};margin:0;">
              {d['date'].split()[0]}
            </p>
            <p style="font-size:1.6rem;font-weight:800;color:{KALE};line-height:1;margin:0.25rem 0 0 0;">
              {d['date'].split()[1]}
            </p>
          </div>
          <div style="flex:1;border-left:1px solid {HAIR};padding-left:1rem;">
            {items_html}
            <p style="margin:0.25rem 0 0 0;font-size:0.7rem;color:{MUTED};
                      text-transform:capitalize;">{d['status']}</p>
          </div>
        </div>
        """
    st.markdown(
        f"""
        <div class="kale-card">
          <h3 style="margin:0 0 0.75rem 0;color:{INK};">📅 Upcoming deliveries</h3>
          {deliveries_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

with act_col:
    events_html = ""
    for e in RECENT_EVENTS[:5]:
        events_html += f"""
        <div style="display:flex;gap:0.75rem;padding:0.6rem 0;border-bottom:1px solid {HAIR};">
          <div style="height:32px;width:32px;border-radius:999px;background:{CREAM};
                      display:flex;align-items:center;justify-content:center;flex-shrink:0;">🌱</div>
          <div style="flex:1;">
            <p style="margin:0;color:{INK};font-size:0.9rem;line-height:1.4;">{e['text']}</p>
            <p style="margin:0.15rem 0 0 0;font-size:0.7rem;color:{MUTED};">{e['time']}</p>
          </div>
        </div>
        """
    st.markdown(
        f"""
        <div class="kale-card">
          <h3 style="margin:0 0 0.75rem 0;color:{INK};">✨ Recent activity</h3>
          {events_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────
# Lifetime stats — dark card
# ───────────────────────────────────────────
st.write("")
st.markdown(
    f"""
    <div class="kale-card-dark">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.5rem;align-items:center;">
        <div>
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;
                    text-transform:uppercase;color:rgba(199,230,107,0.75);margin:0;">Total grown</p>
          <p style="font-size:2.2rem;font-weight:800;color:white;margin:0.25rem 0;">
            {SARAH['total_kg_grown']} kg
          </p>
          <p style="font-size:0.8rem;color:rgba(199,230,107,0.85);margin:0;">since you joined</p>
        </div>
        <div>
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;
                    text-transform:uppercase;color:rgba(199,230,107,0.75);margin:0;">Deliveries</p>
          <p style="font-size:2.2rem;font-weight:800;color:white;margin:0.25rem 0;">
            {SARAH['total_deliveries']}
          </p>
          <p style="font-size:0.8rem;color:rgba(199,230,107,0.85);margin:0;">all on time</p>
        </div>
        <div>
          <p style="color:rgba(199,230,107,0.85);margin:0;font-size:0.9rem;">
              Want more? Upgrade to <strong style="color:white;">Pro</strong> for 4–5 crops.
          </p>
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
        f"""
        <div style='padding:0.5rem 1rem;background:{CREAM};border-radius:12px;'>
          <p style='margin:0;font-size:0.65rem;font-weight:700;letter-spacing:0.15em;color:{MUTED};'>
              SIGNED IN AS
          </p>
          <p style='margin:0.2rem 0;font-weight:700;color:{INK};'>{SARAH['name']}</p>
          <p style='margin:0;font-size:0.7rem;color:{MUTED};'>
              {SARAH['tier']} tier · Plot #{SARAH['plot_id']}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
