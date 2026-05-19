"""Alerts — crisis notification center with demo trigger."""

import sys
from pathlib import Path
# Deduplicated: only add consumer_app/ to sys.path once
_app_dir = str(Path(__file__).parent.parent)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import streamlit as st
from lib.styles import (
    inject_css, inject_gamification_css, brand_header, pill,
    KALE, LEAF, LIME, CORAL, CREAM, HAIR, MUTED, INK, ASSETS, img_to_base64,
    alert_banner_html,
)
from lib.mock_data import (
    DEMO_ACTIVE_ALERTS, create_alert, SARAH, ALERT_TEMPLATES,
)

st.set_page_config(page_title="Alerts — Adopt a Kale", page_icon="🔔", layout="wide")
inject_css()
inject_gamification_css()
brand_header()

# ── Session state ──────────────────────────────
if "active_alerts" not in st.session_state:
    st.session_state.active_alerts = list(DEMO_ACTIVE_ALERTS)
if "alert_history" not in st.session_state:
    st.session_state.alert_history = [
        {
            "id": "alert-crop-ready-001",
            "type": "crop_ready",
            "severity": "info",
            "icon": "🌿",
            "title": "Your Kale Is Ready!",
            "body": "Your Curly Kale has reached peak biomass at 210g. Harvest window: May 27–29.",
            "action_label": "Track Harvest",
            "action": None,
            "timestamp": "May 15, 09:00 SGT",
            "dismissed": True,
        },
        {
            "id": "alert-delivery-001",
            "type": "delivery_delay",
            "severity": "info",
            "icon": "🚚",
            "title": "Delivery Rescheduled",
            "body": "Your Wednesday delivery has been automatically shifted to Thursday 8–10am due to heavy rain advisory.",
            "action_label": None,
            "action": None,
            "timestamp": "May 12, 06:15 SGT",
            "dismissed": True,
        },
        {
            "id": "alert-defense-001",
            "type": "defense_report",
            "severity": "info",
            "icon": "🛡️",
            "title": "PPO Defense Report: 24h Climate Summary",
            "body": (
                "The PPO RL agent defended your rack 1,247 times over the last 24 hours — "
                "adjusting humidity 38×, LED intensity 62×, and nutrient flow 14×. "
                "Your kale earned a +0.04 reward bonus. No action required."
            ),
            "action_label": "View Full Report",
            "action": None,
            "timestamp": "May 18, 06:00 SGT",
            "dismissed": True,
        },
    ]
if "dismissed_alerts" not in st.session_state:
    st.session_state.dismissed_alerts = set()

# ── Helpers ───────────────────────────────────
SEVERITY_COLORS = {
    "critical": ("#DC2626", "#FEE2E2"),
    "warning":  ("#D97706", "#FEF3C7"),
    "info":     ("#059669", "#D1FAE5"),
}

def severity_label(sev):
    return {
        "critical": "🔴 CRITICAL",
        "warning":  "🟡 WARNING",
        "info":     "🟢 INFO",
    }.get(sev, sev.upper())

# ── Header ────────────────────────────────────
st.markdown(
    f"<div style='margin-bottom:0.5rem;'>{pill('LIVE · Real-time', 'coral')}</div>"
    f"<h1 style='font-size:2.2rem;font-weight:800;color:{INK};margin:0;'>Crisis Center</h1>"
    f"<p style='color:{MUTED};margin-top:0.5rem;'>"
    f"When the AI acts to protect your plot, you'll see it here first.</p>",
    unsafe_allow_html=True,
)
st.write("")

# ── Active Alerts Banner (full-width) ─────────
active = [a for a in st.session_state.active_alerts
          if a["id"] not in st.session_state.dismissed_alerts]

if active:
    st.markdown(
        f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{CORAL};margin-bottom:0.5rem;'>"
        f"⚠️ ACTIVE ALERTS ({len(active)})</p>",
        unsafe_allow_html=True,
    )
    for alert in active:
        st.markdown(alert_banner_html(alert), unsafe_allow_html=True)
        col_dismiss, col_action = st.columns([1, 3])
        with col_dismiss:
            if st.button("✓ Mark All Clear", use_container_width=True):
                st.session_state.dismissed_alerts.add(alert["id"])
                # Move to history
                history_entry = {**alert, "dismissed": False, "timestamp": "May 19, 06:00 SGT"}
                st.session_state.alert_history.insert(0, history_entry)
                st.rerun()
        with col_action:
            if alert.get("action"):
                st.button(f"{alert['action']} →", use_container_width=True, type="primary")
        st.write("")
else:
    st.markdown(
        f"""
        <div style="background:#D1FAE5;border-radius:20px;padding:1.5rem;text-align:center;">
            <p style="font-size:3rem;margin:0;">✅</p>
            <p style="font-weight:700;color:#065F46;margin:0.5rem 0 0 0;font-size:1.1rem;">All Clear</p>
            <p style="color:#065F46;margin:0.25rem 0 0 0;font-size:0.85rem;">No active alerts. Your plot is safe.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ── Alert History ─────────────────────────────
st.markdown(
    f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
    f"text-transform:uppercase;color:{MUTED};margin-bottom:0.75rem;'>ALERT HISTORY</p>",
    unsafe_allow_html=True,
)

history_entries = [h for h in st.session_state.alert_history
                   if h.get("dismissed", False) or h["id"] in st.session_state.dismissed_alerts]

if history_entries:
    for h in history_entries:
        bg_color = SEVERITY_COLORS.get(h.get("severity"), SEVERITY_COLORS["info"])[1]
        border_color = SEVERITY_COLORS.get(h.get("severity"), SEVERITY_COLORS["info"])[0]
        st.markdown(
            f"""
            <div style="background:{bg_color};border-left:4px solid {border_color};
                        border-radius:12px;padding:1rem 1.25rem;margin-bottom:0.75rem;">
              <div style="display:flex;align-items:flex-start;gap:0.75rem;">
                <div style="font-size:1.25rem;line-height:1;padding-top:0.1rem;">{h.get('icon','ℹ️')}</div>
                <div style="flex:1;">
                  <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.3rem;">
                    <p style="font-weight:700;color:{INK};margin:0;font-size:0.95rem;">{h.get('title','')}</p>
                    <span style="font-size:0.6rem;font-weight:700;letter-spacing:0.15em;
                                 text-transform:uppercase;padding:0.15rem 0.5rem;
                                 border-radius:999px;background:{border_color}20;color:{border_color};">
                        {severity_label(h.get('severity','info'))}
                    </span>
                  </div>
                  <p style="color:{MUTED};font-size:0.8rem;margin:0 0 0.5rem 0;">{h.get('timestamp','')}</p>
                  <p style="color:{INK};font-size:0.85rem;margin:0;line-height:1.5;">{h.get('body','')}</p>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No past alerts to show.")

st.markdown('<hr class="kale-hr"/>', unsafe_allow_html=True)

# ── Demo Trigger Section ─────────────────────
st.markdown(
    f"<div style='background:#FEF9C3;border:1px solid #EAB308;border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;'>"
    f"<p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;"
    f"text-transform:uppercase;color:#854D0E;margin:0 0 0.25rem 0;'>"
    f"🧪 DEMO MODE — TRIGGER ALERTS</p>"
    f"<p style='color:#713F12;font-size:0.8rem;margin:0;'>"
    f"Trigger simulated alerts to preview how the AI protects your plot. "
    f"These alerts are for demonstration only and do not affect your real crops.</p></div>",
    unsafe_allow_html=True,
)

demo_options = [
    {
        "type": "typhoon_harvest",
        "icon": "🌀",
        "title": "Typhoon — Emergency Harvest",
        "desc": "Power anomaly detected. AI triggers emergency harvest to protect crops.",
        "severity": "critical",
    },
    {
        "type": "power_outage",
        "icon": "⚡",
        "title": "Power Outage",
        "desc": "Grid failure. UPS backup activates. PPO RL agent goes into defense mode.",
        "severity": "warning",
    },
    {
        "type": "surprise_upgrade",
        "icon": "🎁",
        "title": "Surprise Upgrade!",
        "desc": "Surplus yield from your rack. AI upgraded your delivery with free rare herbs.",
        "severity": "info",
    },
    {
        "type": "defense_report",
        "icon": "🛡️",
        "title": "PPO Defense Report",
        "desc": "Daily climate defense summary from the RL agent — how it protected your rack today.",
        "severity": "info",
    },
    {
        "type": "food_pairing",
        "icon": "🍽️",
        "title": "K-Means Food Pairing",
        "desc": "Your crop data matched 847 similar households. Top pairing: kale + edamame.",
        "severity": "info",
    },
    {
        "type": "donation_skipped",
        "icon": "💚",
        "title": "Skip → Donation Confirmed",
        "desc": "Your skipped delivery was donated to NTUC Food Bank. ESG badge earned!",
        "severity": "info",
    },
]

demo_cols = st.columns(3)
for i, opt in enumerate(demo_options):
    with demo_cols[i % 3]:
        border_color = SEVERITY_COLORS.get(opt["severity"], SEVERITY_COLORS["info"])[0]
        bg = f"{border_color}10"
        st.markdown(
            f"""
            <div style="background:{bg};border:1px solid {border_color}40;border-radius:16px;
                        padding:1rem;margin-bottom:0.75rem;">
              <div style="font-size:1.75rem;margin-bottom:0.5rem;">{opt['icon']}</div>
              <p style="font-weight:700;color:{INK};margin:0 0 0.25rem 0;font-size:0.9rem;">{opt['title']}</p>
              <p style="color:{MUTED};font-size:0.75rem;margin:0 0 0.75rem 0;line-height:1.4;">{opt['desc']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Trigger {opt['title']}", key=f"demo_{opt['type']}",
                    use_container_width=True, type="secondary"):
            # Build appropriate alert
            if opt["type"] == "typhoon_harvest":
                new_alert = create_alert("typhoon_harvest", date="today")
            elif opt["type"] == "power_outage":
                new_alert = create_alert("power_outage", date="today")
            elif opt["type"] == "surprise_upgrade":
                new_alert = {
                    "id": f"alert-surprise-{opt['type']}",
                    "type": "surprise_upgrade",
                    "severity": "info",
                    "icon": "🎁",
                    "title": "Surprise Upgrade Applied!",
                    "body": (
                        "Your rack produced a surplus harvest — 23% above the weekly baseline. "
                        "The AI automatically upgraded your delivery with free Edible Flowers "
                        "🌸 (normally a Sprout-tier crop). This is what long-term membership earns."
                    ),
                    "action_label": "See My Upgraded Delivery",
                    "action": None,
                }
            elif opt["type"] == "defense_report":
                new_alert = {
                    "id": f"alert-defense-{opt['type']}",
                    "type": "defense_report",
                    "severity": "info",
                    "icon": "🛡️",
                    "title": "PPO Defense Report: Climate Shield Active",
                    "body": (
                        "The PPO RL agent defended your rack 1,247 times in the last 24h: "
                        "humidity adjusted 38×, LED intensity 62×, nutrient flow 14×. "
                        "Your crop earned a +0.04 reward bonus. "
                        "No intervention needed — the AI handled everything autonomously."
                    ),
                    "action_label": "View 24h Defense Log",
                    "action": None,
                }
            elif opt["type"] == "food_pairing":
                new_alert = {
                    "id": f"alert-food-{opt['type']}",
                    "type": "food_pairing",
                    "severity": "info",
                    "icon": "🍽️",
                    "title": "K-Means Pairing: Kale + Edamame",
                    "body": (
                        "Your consumption pattern (847 similar households in the K-Means cluster) "
                        "suggests kale + edamame is the top-rated pairing for your taste profile. "
                        "Try it this week — the AI will include a free sample in your next delivery."
                    ),
                    "action_label": "Browse More Pairings",
                    "action": None,
                }
            elif opt["type"] == "donation_skipped":
                new_alert = {
                    "id": f"alert-donation-{opt['type']}",
                    "type": "donation_skipped",
                    "severity": "info",
                    "icon": "💚",
                    "title": "Your Skip Became a Donation!",
                    "body": (
                        "When you skip a delivery, your crops don't go to waste. "
                        "2.1kg of fresh produce was donated to NTUC Food Bank on your behalf. "
                        "You've earned the 🌍 ESG Guardian badge for turning a skip into social impact."
                    ),
                    "action_label": "View ESG Impact",
                    "action": None,
                }
            else:
                new_alert = create_alert("crop_ready", date="today")

            st.session_state.active_alerts = [a for a in st.session_state.active_alerts
                                               if a["id"] not in st.session_state.dismissed_alerts]
            st.session_state.active_alerts.append(new_alert)
            st.rerun()

# ── Sidebar ────────────────────────────────────
with st.sidebar:
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"<div style='text-align:center;padding:1rem 0;'>"
        f"<img src='data:image/png;base64,{leaf_b64}' width='60' height='72'/>"
        f"<h2 style='color:{KALE};margin:0.5rem 0 0 0;font-weight:800;'>Adopt a Kale</h2></div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    unread = len([a for a in st.session_state.active_alerts
                  if a["id"] not in st.session_state.dismissed_alerts])
    st.markdown(
        f"<div style='padding:0.5rem 1rem;background:{'#FEE2E2' if unread > 0 else CREAM};"
        f"border-radius:12px;'>"
        f"<p style='margin:0;font-size:0.65rem;font-weight:700;letter-spacing:0.15em;color:{MUTED};'>"
        f"ACTIVE ALERTS</p>"
        f"<p style='margin:0.2rem 0;font-weight:800;color:{'#DC2626' if unread > 0 else KALE};"
        f"font-size:1.5rem;'>{unread}</p>"
        f"<p style='margin:0;font-size:0.7rem;color:{MUTED};'>"
        f"{'Needs attention' if unread > 0 else 'All clear'}</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<p style='color:{MUTED};font-size:0.75rem;'>"
        f"Alerts are generated by the AI when it takes action to protect your crops — "
        f"no alerts means everything is running perfectly.</p>",
        unsafe_allow_html=True,
    )
