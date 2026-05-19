"""Plant Camera — Live rack monitoring + AI crop diagnosis."""

import sys
from pathlib import Path
# Deduplicated: only add consumer_app/ to sys.path once
_app_dir = str(Path(__file__).parent.parent)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import streamlit as st
from lib.styles import (
    inject_css, brand_header, pill,
    KALE, LEAF, LIME, CORAL, CREAM, HAIR, MUTED, INK, ASSETS, img_to_base64,
)
from lib.mock_data import CAMERA, CAMERA_TIMELINE, CROPS

st.set_page_config(page_title="Plant Camera — Adopt a Kale", page_icon="📷", layout="wide")
inject_css()
brand_header()

st.markdown(
    f"<h1 style='font-size:2.2rem;font-weight:800;color:{INK};margin:0;'>"
    f"🌿 Your plot, live.</h1>"
    f"<p style='color:{MUTED};margin-top:0.5rem;'>"
    f"Fixed camera · {CAMERA['rack_id']} · Auto-capture every {CAMERA['interval_hours']}h</p>",
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────
# Camera status bar
# ───────────────────────────────────────────
status_col1, status_col2, status_col3, status_col4 = st.columns(4)
with status_col1:
    st.markdown(
        f"""
        <div class="kale-card" style="padding:0.75rem;text-align:center;">
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:{MUTED};margin:0;">Status</p>
          <p style="font-size:1.1rem;font-weight:800;color:{KALE};margin:0.25rem 0 0 0;">
            {pill("● LIVE", "kale")}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with status_col2:
    st.markdown(
        f"""
        <div class="kale-card" style="padding:0.75rem;text-align:center;">
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:{MUTED};margin:0;">Last capture</p>
          <p style="font-size:1rem;font-weight:700;color:{INK};margin:0.25rem 0 0 0;">{CAMERA['last_capture']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with status_col3:
    st.markdown(
        f"""
        <div class="kale-card" style="padding:0.75rem;text-align:center;">
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:{MUTED};margin:0;">Camera</p>
          <p style="font-size:1rem;font-weight:700;color:{INK};margin:0.25rem 0 0 0;">{CAMERA['rack_id']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with status_col4:
    st.markdown(
        f"""
        <div class="kale-card" style="padding:0.75rem;text-align:center;">
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:{MUTED};margin:0;">Capture interval</p>
          <p style="font-size:1rem;font-weight:700;color:{INK};margin:0.25rem 0 0 0;">{CAMERA['interval_hours']} hours</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ───────────────────────────────────────────
# Main camera view + AI diagnosis (2 columns)
# ───────────────────────────────────────────
# Load demo image for the "live" view (kailan healthy = current crop)
demo_img = img_to_base64(Path(__file__).parent.parent.parent / "data" / "demo_images" / "demo_kailan_healthy.jpg")

cam_col, diag_col = st.columns([3, 2])

with cam_col:
    st.markdown(
        f"""
        <div style="position:relative;border-radius:20px;overflow:hidden;border:2px solid {KALE};">
          <img src="data:image/jpeg;base64,{demo_img}"
               style="width:100%;display:block;"/>
          <div style="position:absolute;top:12px;left:12px;">
            {pill("● LIVE", "kale")}
          </div>
          <div style="position:absolute;bottom:0;left:0;right:0;
                      background:linear-gradient(transparent,rgba(0,0,0,0.6));
                      padding:1rem 1rem 0.75rem 1rem;">
            <p style="color:white;font-size:0.8rem;font-weight:600;margin:0;">
              {CAMERA['rack_id']} · {CAMERA['last_capture']} · Curly Kale Day 31
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Timeline strip
    st.markdown(
        f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{MUTED};margin:1rem 0 0.5rem 0;'>📅 Growth timeline</p>",
        unsafe_allow_html=True,
    )

    thumb_cols = st.columns(len(CAMERA_TIMELINE))
    for i, shot in enumerate(CAMERA_TIMELINE):
        with thumb_cols[i]:
            is_today = shot["day"] == 31
            border = f"2px solid {KALE}" if is_today else f"1px solid {HAIR}"
            score_color = KALE if shot["health_score"] >= 90 else (CORAL if shot["health_score"] < 80 else LEAF)
            st.markdown(
                f"""
                <div style="border:{border};border-radius:12px;overflow:hidden;text-align:center;
                            background:white;padding-bottom:0.5rem;">
                  <img src="data:image/jpeg;base64,{demo_img}"
                       style="width:100%;display:block;aspect-ratio:16/9;object-fit:cover;"/>
                  <p style="font-size:0.6rem;font-weight:700;color:{INK};margin:0.25rem 0 0 0;">Day {shot['day']}</p>
                  <p style="font-size:0.65rem;color:{score_color};margin:0;font-weight:700;">{shot['health_score']}%</p>
                  <p style="font-size:0.55rem;color:{MUTED};margin:0.1rem 0 0 0;">{shot['date']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

with diag_col:
    diag = CAMERA["ai_diagnosis"]
    score = diag["health_score"]
    score_color = KALE if score >= 90 else (CORAL if score < 80 else LEAF)

    anomaly_html = ""
    if diag["anomalies"]:
        anomaly_list = "<br>".join([f"• {a}" for a in diag["anomalies"]])
        anomaly_html = (
            f"<div style='background:rgba(224,120,86,0.1);border:1px solid rgba(224,120,86,0.3);"
            f"border-radius:12px;padding:0.6rem;margin-bottom:0.5rem;'>"
            f"<p style='font-size:0.65rem;font-weight:700;color:{CORAL};margin:0;'>⚠ Anomalies detected</p>"
            f"<p style='font-size:0.8rem;color:{INK};margin:0.25rem 0 0 0;'>"
            f"{anomaly_list}</p></div>"
        )

    st.markdown(
        f"""
        <div class="kale-card" style="margin-bottom:0.75rem;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
            <p style="font-size:0.7rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:{MUTED};margin:0;">
              AI Diagnosis · EfficientNet-B0
            </p>
            <div style="text-align:center;">
              <p style="font-size:2.2rem;font-weight:800;color:{score_color};line-height:1;margin:0;">{score}</p>
              <p style="font-size:0.6rem;color:{MUTED};margin:0;">/ 100</p>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-bottom:1rem;">
            <div style="background:{CREAM};border-radius:12px;padding:0.6rem;">
              <p style="font-size:0.6rem;color:{MUTED};margin:0;">Crop</p>
              <p style="font-weight:700;color:{INK};margin:0.15rem 0 0 0;font-size:0.9rem;">{diag['crop']}</p>
            </div>
            <div style="background:{CREAM};border-radius:12px;padding:0.6rem;">
              <p style="font-size:0.6rem;color:{MUTED};margin:0;">Stage</p>
              <p style="font-weight:700;color:{INK};margin:0.15rem 0 0 0;font-size:0.9rem;">{diag['growth_stage']}</p>
            </div>
            <div style="background:{CREAM};border-radius:12px;padding:0.6rem;">
              <p style="font-size:0.6rem;color:{MUTED};margin:0;">Nutrition</p>
              <p style="font-weight:700;color:{KALE};margin:0.15rem 0 0 0;font-size:0.9rem;">{diag['nutrition_status']}</p>
            </div>
            <div style="background:{CREAM};border-radius:12px;padding:0.6rem;">
              <p style="font-size:0.6rem;color:{MUTED};margin:0;">Leaf area</p>
              <p style="font-weight:700;color:{INK};margin:0.15rem 0 0 0;font-size:0.9rem;">{diag['leaf_area_m2']} m²</p>
            </div>
          </div>

          <div style="background:{CREAM};border-radius:12px;padding:0.75rem;margin-bottom:0.75rem;">
            <p style="font-size:0.6rem;color:{MUTED};margin:0;">Biomass</p>
            <p style="font-weight:800;color:{INK};margin:0.15rem 0 0 0;font-size:1.3rem;">{diag['biomass_g']}g</p>
          </div>

          {anomaly_html}

          <div style="background:rgba(45,80,22,0.06);border-radius:12px;padding:0.75rem;">
            <p style="font-size:0.6rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:{MUTED};margin:0;">AI Recommendation</p>
            <p style="font-size:0.85rem;color:{INK};margin:0.4rem 0 0 0;line-height:1.5;">{diag['recommendation']}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Anomaly history
    st.markdown(
        f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{MUTED};margin:0.5rem 0 0.5rem 0;'>📋 Anomaly history</p>",
        unsafe_allow_html=True,
    )
    anomaly_events = [
        {"date": "Apr 15", "text": "Slight leaf yellowing — nutrient pH adjusted from 5.6 to 5.8"},
        {"date": "Mar 30", "text": "Minor aphid detected — IPM released lacewing larvae"},
    ]
    for e in anomaly_events:
        st.markdown(
            f"""
            <div style="display:flex;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid {HAIR};">
              <div style="height:28px;width:28px;border-radius:999px;background:{CREAM};
                          display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.8rem;">⚠️</div>
              <div style="flex:1;">
                <p style="margin:0;font-size:0.8rem;color:{INK};line-height:1.4;">{e['text']}</p>
                <p style="margin:0.1rem 0 0 0;font-size:0.65rem;color:{MUTED};">{e['date']}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")

# ───────────────────────────────────────────
# Sensor readings strip
# ───────────────────────────────────────────
st.markdown(
    f"<h2 style='font-size:1.2rem;font-weight:800;color:{INK};margin-bottom:0.75rem;'>"
    f"📊 Live sensor readings</h2>",
    unsafe_allow_html=True,
)

sensor_cols = st.columns(5)
sensor_data = [
    ("🌡", "Temperature", "22.4°C", "Optimal 20–24°C"),
    ("💧", "Humidity", "68%", "Target 65–70%"),
    ("💡", "PPFD", "240 µmol/m²/s", "Optimal for kale"),
    ("⚗️", "pH Level", "5.8", "Target 5.6–6.0"),
    ("📈", "CO₂", "798 ppm", "Optimal < 800 ppm"),
]
for col, (emoji, label, value, note) in zip(sensor_cols, sensor_data):
    with col:
        st.markdown(
            f"""
            <div class="kale-card" style="text-align:center;padding:0.75rem;">
              <p style="font-size:1.3rem;margin:0;">{emoji}</p>
              <p style="font-size:0.6rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0.25rem 0 0 0;">{label}</p>
              <p style="font-size:1.2rem;font-weight:800;color:{KALE};margin:0.25rem 0 0 0;">{value}</p>
              <p style="font-size:0.65rem;color:{LEAF};margin:0;">{note}</p>
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
              CAMERA SETTINGS
          </p>
          <p style='margin:0.2rem 0;font-size:0.75rem;color:{INK};'>Interval: {CAMERA['interval_hours']}h auto</p>
          <p style='margin:0;font-size:0.75rem;color:{INK};'>Rack: {CAMERA['rack_id']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<p style='color:{MUTED};font-size:0.75rem;'>"
        f"Cameras auto-capture daily at 06:00 SGT. "
        f"Pro tier includes 24/7 live stream. "
        f"Contact sales for camera upgrade.</p>",
        unsafe_allow_html=True,
    )
