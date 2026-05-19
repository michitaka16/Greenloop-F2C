"""My Plot — Adopt a Kale app centerpiece."""

import sys
from pathlib import Path
# Add consumer_app/ to sys.path (deduped to avoid breaking existing imports)
_APP_DIR = str(Path(__file__).parent.parent)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import streamlit as st
from lib.styles import (
    inject_css, inject_gamification_css, brand_header, eyebrow, pill, maturity_ring_html,
    progress_card, confetti_html, badge_card, leaderboard_row,
    esg_card_html, growth_chart_svg, status_badge_html, alert_banner_html,
    KALE, LEAF, LIME, CORAL, CREAM, PAPER, HAIR, MUTED, INK, ASSETS, img_to_base64,
)
from lib.mock_data import (
    SARAH, CROPS, STATUS, UPCOMING_DELIVERIES, RECENT_EVENTS,
    MILESTONES, SARAH_BADGES, LEADERBOARD,
    get_earned_badges, get_next_badge, get_leaderboard_position,
    SARAH_STATUS, WEEKLY_GROWTH_LOG,
    get_status_tier, get_next_status_tier, get_esg_impact,
    DEMO_ACTIVE_ALERTS,
)

# ── Gamification session state ─────────────────────
if "show_confetti" not in st.session_state:
    st.session_state.show_confetti = False
if "celebration_shown" not in st.session_state:
    st.session_state.celebration_shown = False

# Trigger confetti if harvest day just completed (demo: auto-trigger once)
if not st.session_state.celebration_shown and SARAH["days_in"] >= 31:
    st.session_state.show_confetti = True
    st.session_state.celebration_shown = True

st.set_page_config(page_title="My Plot — Adopt a Kale", page_icon="🌿", layout="wide")
inject_css()
inject_gamification_css()
brand_header()

# ── Confetti celebration ───────────────────────────
if st.session_state.get("show_confetti"):
    st.markdown(confetti_html(), unsafe_allow_html=True)
    st.session_state.show_confetti = False

# ── Active alerts session state ───────────────────────
if "active_alerts" not in st.session_state:
    st.session_state.active_alerts = DEMO_ACTIVE_ALERTS.copy()

# ── Alert banners ───────────────────────────────────
for alert in st.session_state.active_alerts:
    st.markdown(alert_banner_html(alert), unsafe_allow_html=True)
if st.session_state.active_alerts:
    st.write("")

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
btn_col1, btn_col2, btn_col3, btn_col4, _ = st.columns([1, 1, 1, 1, 2])
with btn_col1:
    if st.button("💬  Ask your kale", type="primary", use_container_width=True):
        st.switch_page("pages/3_💬_Chat.py")
with btn_col2:
    if st.button("📅  Schedule", type="secondary", use_container_width=True):
        st.switch_page("pages/4_📅_Schedule.py")
with btn_col3:
    if st.button("📷  Plant Camera", type="secondary", use_container_width=True):
        st.switch_page("pages/6_📷_PlantCamera.py")
with btn_col4:
    if st.button("🎉  Share & NFT", type="secondary", use_container_width=True):
        st.switch_page("pages/7_🎉_Celebration.py")

# ────────────────────────────────────────────
# 📊 My Portfolio — ESG + Growth Chart
# ────────────────────────────────────────────
esg = get_esg_impact(SARAH["total_kg_grown"])
current_tier = get_status_tier(SARAH_STATUS["tenure_months"])
market_value = SARAH["total_kg_grown"] * 8

st.markdown(f"<h2 style='color:{INK};font-weight:700;margin-bottom:0.75rem;'>📊 My Portfolio</h2>", unsafe_allow_html=True)
portfolio_col1, portfolio_col2 = st.columns([1, 1])
with portfolio_col1:
    st.markdown(esg_card_html(
        water_saved_l=esg["water_saved_l"],
        co2_saved_kg=esg["co2_saved_kg"],
        trees_equiv=esg["trees_equiv"],
    ), unsafe_allow_html=True)
with portfolio_col2:
    st.markdown(growth_chart_svg(WEEKLY_GROWTH_LOG), unsafe_allow_html=True)

st.write("")
# Asset value strip
asset_col1, asset_col2, asset_col3 = st.columns(3)
with asset_col1:
    st.markdown(
        f"<div class='kale-card' style='text-align:center;'>"
        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0;'>Portfolio Value</p>"
        f"<p style='font-size:1.8rem;font-weight:800;color:{KALE};margin:0.3rem 0 0 0;'>S${market_value:.0f}</p>"
        f"<p style='font-size:0.65rem;color:{MUTED};margin:0;'>kg grown × S$8/kg premium</p></div>",
        unsafe_allow_html=True,
    )
with asset_col2:
    st.markdown(
        f"<div class='kale-card' style='text-align:center;'>"
        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0;'>Water Saved</p>"
        f"<p style='font-size:1.8rem;font-weight:800;color:{KALE};margin:0.3rem 0 0 0;'>{esg['water_saved_l']:.0f}L</p>"
        f"<p style='font-size:0.65rem;color:{MUTED};margin:0;'>vs conventional farming</p></div>",
        unsafe_allow_html=True,
    )
with asset_col3:
    st.markdown(
        f"<div class='kale-card' style='text-align:center;'>"
        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0;'>CO₂ Avoided</p>"
        f"<p style='font-size:1.8rem;font-weight:800;color:{KALE};margin:0.3rem 0 0 0;'>{esg['co2_saved_kg']:.1f}kg</p>"
        f"<p style='font-size:0.65rem;color:{MUTED};margin:0;'>vs conventional farming</p></div>",
        unsafe_allow_html=True,
    )

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ───────────────────────────────────────────
# Achievements — Badges
# ───────────────────────────────────────────
earned = get_earned_badges()
next_badge = get_next_badge()
rank = get_leaderboard_position()

ach_col1, ach_col2 = st.columns([3, 1])
with ach_col1:
    st.markdown(f"<h2 style='color:{INK};font-weight:700;'>🏆 My Achievements</h2>", unsafe_allow_html=True)
with ach_col2:
    st.markdown(
        f"<p style='color:{MUTED};font-size:0.85rem;text-align:right;margin-top:0.6rem;'>"
        f"Rank #{rank} on the leaderboard · {len(earned)}/{len(MILESTONES)} badges</p>",
        unsafe_allow_html=True,
    )

badge_cols = st.columns(len(SARAH_BADGES))
for i, badge in enumerate(SARAH_BADGES):
    with badge_cols[i]:
        unlocked = badge["earned"]
        st.markdown(badge_card(badge, unlocked=unlocked), unsafe_allow_html=True)

if next_badge:
    st.write("")
    next_col1, next_col2 = st.columns([3, 1])
    with next_col1:
        st.markdown(
            f"<div class='kale-card' style='display:flex;align-items:center;gap:1rem;'>"
            f"<div style='font-size:1.8rem;'>🔒</div>"
            f"<div>"
            f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0;'>NEXT BADGE</p>"
            f"<p style='font-weight:700;color:{INK};margin:0.2rem 0;'>{next_badge['emoji']} {next_badge['title']}</p>"
            f"<p style='font-size:0.75rem;color:{MUTED};margin:0;'>Criterion: {next_badge['criterion']}</p>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with next_col2:
        st.markdown(
            f"<div style='text-align:center;padding:1rem;'>"
            f"<p style='font-size:3rem;margin:0;'>🎯</p>"
            f"<p style='color:{KALE};font-weight:700;font-size:0.8rem;margin:0.25rem 0 0 0;'>1 harvest away!</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ───────────────────────────────────────────
# Leaderboard
# ───────────────────────────────────────────
st.write("")
with st.expander("🏅 See how you compare — Singapore Growers Leaderboard"):
    st.markdown(
        f"<p style='font-size:0.75rem;color:{MUTED};margin-bottom:1rem;'>"
        f"Updated daily · {len(LEADERBOARD)} growers tracked</p>",
        unsafe_allow_html=True,
    )
    for entry in LEADERBOARD:
        is_sarah = entry["name"] == "Sarah T."
        st.markdown(
            leaderboard_row(
                rank=entry["rank"],
                name=entry["name"],
                plot=entry["plot"],
                badges=entry["badges"],
                kg_grown=entry["kg_grown"],
                deliveries=entry["deliveries"],
                tier=entry["tier"],
                hood=entry["hood"],
                is_sarah=is_sarah,
            ),
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<p style='font-size:0.7rem;color:{MUTED};text-align:center;margin-top:0.75rem;'>"
        f"↑ Complete 1 more delivery to reach #2</p>",
        unsafe_allow_html=True,
    )

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

# ────────────────────────────────────────────
# 🌿 My Gardener Status
# ────────────────────────────────────────────
next_tier = get_next_status_tier(SARAH_STATUS["tenure_months"])
current_tier = get_status_tier(SARAH_STATUS["tenure_months"])
next_tier_progress = 0
if next_tier:
    next_tier_progress = (SARAH_STATUS["tenure_months"] / next_tier["min_months"]) * 100

st.markdown(f"<h2 style='color:{INK};font-weight:700;'>🌿 My Gardener Status</h2>", unsafe_allow_html=True)
status_col1, status_col2, status_col3 = st.columns([1, 1, 1])
with status_col1:
    st.markdown(
        f"<div class='kale-card' style='text-align:center;'>"
        f"{status_badge_html(current_tier, glow=SARAH_STATUS['is_founding_gardener'], is_founding=SARAH_STATUS['is_founding_gardener'])}"
        f"<p style='font-size:0.7rem;color:{MUTED};margin:0.5rem 0 0 0;'>{SARAH_STATUS['tenure_months']} month{'s' if SARAH_STATUS['tenure_months'] != 1 else ''} · {SARAH['hood']}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
with status_col2:
    perks_html = "".join([f"<p style='margin:0.15rem 0;font-size:0.75rem;color:{INK};'>✅ {p}</p>" for p in current_tier["perks"]])
    st.markdown(
        f"<div class='kale-card'>"
        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0 0 0.5rem 0;'>YOUR PERKS</p>"
        f"{perks_html}</div>",
        unsafe_allow_html=True,
    )
with status_col3:
    if next_tier:
        st.markdown(
            f"<div class='kale-card'>"
            f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0 0 0.5rem 0;'>NEXT: {next_tier['emoji']} {next_tier['id']}</p>"
            f"<p style='font-size:0.8rem;color:{INK};margin:0 0 0.5rem 0;'>{next_tier['min_months'] - SARAH_STATUS['tenure_months']} months away</p>"
            f"<div style='height:8px;background:{CREAM};border-radius:999px;overflow:hidden;'>"
            f"<div style='height:100%;width:{next_tier_progress:.0f}%;background:{current_tier['color']};border-radius:999px;'></div>"
            f"</div>"
            f"<p style='font-size:0.7rem;color:{MUTED};margin:0.3rem 0 0 0;'>{', '.join(next_tier['perks'][:2])} + more</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='kale-card' style='text-align:center;padding:2rem;'>"
            f"<p style='font-size:2rem;margin:0;'>👑</p>"
            f"<p style='font-weight:700;color:{INK};margin:0.5rem 0 0 0;'>Master Gardener</p>"
            f"<p style='font-size:0.75rem;color:{MUTED};'>You have reached the top tier!</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

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
