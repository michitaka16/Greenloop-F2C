"""Onboarding wizard — tier + crop selection."""

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
)
from lib.mock_data import TIERS, CROP_OPTIONS

st.set_page_config(page_title="Start your plot — Adopt a Kale", page_icon="🚀", layout="wide")
inject_css()
brand_header()

# Session state init
if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 0
if "onboarding_tier" not in st.session_state:
    st.session_state.onboarding_tier = None
if "onboarding_crops" not in st.session_state:
    st.session_state.onboarding_crops = []

step = st.session_state.onboarding_step

# Progress indicator
prog_cols = st.columns(8)
for i, c in enumerate(prog_cols):
    with c:
        if i < step:
            color = LEAF
            width = "20px"
        elif i == step:
            color = KALE
            width = "32px"
        else:
            color = HAIR
            width = "20px"
        st.markdown(
            f"<div style='height:4px;background:{color};width:{width};border-radius:999px;margin:1rem auto;'></div>",
            unsafe_allow_html=True,
        )

st.write("")

# ─────────────────────────────────
# Step 0: Welcome
# ─────────────────────────────────
if step == 0:
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"""
        <div style="text-align:center;max-width:600px;margin:2rem auto;">
            <img src="data:image/png;base64,{leaf_b64}" width="120" height="144"/>
            <div style="margin:1.5rem 0;">{pill("WELCOME", "coral")}</div>
            <h1 style="font-size:3rem;font-weight:800;color:{KALE};margin:0;">
                Let's start your plot.
            </h1>
            <p style="font-size:1.2rem;color:{INK};margin-top:1.5rem;">
                Three minutes. Three questions. Then your AI gets to work growing your first crop.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Begin →", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 1
            st.rerun()
    st.caption("<center>No card needed for trial</center>", unsafe_allow_html=True)

    # ── Founding Gardener callout ───────────────
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#1a3a0f,#2D5016);
                    border-radius:20px;padding:1.25rem 1.5rem;margin-top:2rem;
                    border:1px solid #4a7c3f;">
            <div style="display:flex;align-items:center;gap:1rem;">
                <div style="font-size:2rem;">🌟</div>
                <div style="flex:1;">
                    <p style="font-weight:700;color:#C7E66B;margin:0;font-size:0.8rem;
                               letter-spacing:0.1em;text-transform:uppercase;">Founding Gardener</p>
                    <p style="color:rgba(255,255,255,0.9);margin:0.25rem 0 0 0;font-size:0.85rem;">
                        Join before <strong style="color:#C7E66B;">May 31, 2026</strong> and lock in
                        <strong style="color:#C7E66B;">founding member perks</strong> — pulsing badge,
                        exclusive pre-launch crops, and name on the wall.
                    </p>
                </div>
                <div style="background:#C7E66B;color:#1a3a0f;padding:0.4rem 0.8rem;
                            border-radius:999px;font-size:0.7rem;font-weight:700;white-space:nowrap;">
                    12 days left
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────
# Step 1: Tier selection
# ─────────────────────────────────
elif step == 1:
    eyebrow("Step 1 of 3")
    st.markdown(
        f"<h1 style='font-size:2.5rem;font-weight:800;color:{INK};margin:0;'>"
        "How much garden do you want?</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<p style='color:{MUTED};margin-top:0.5rem;'>Pick a tier. You can change anytime.</p>",
                unsafe_allow_html=True)
    st.write("")

    standard_pro = [t for t in TIERS if not t.get("enterprise")]
    enterprise = [t for t in TIERS if t.get("enterprise")]

    for tier in standard_pro:
        selected = st.session_state.onboarding_tier == tier["id"]
        check = "●" if selected else "○"
        check_color = KALE if selected else HAIR
        border = f"2px solid {KALE}" if selected else f"1px solid {HAIR}"
        shadow = "box-shadow: 0 4px 16px rgba(45,80,22,0.10);" if selected else ""
        is_premium = tier["id"] == "Pro"
        price_color = "#C7E66B" if is_premium else INK
        recommended = (
            f"<span style='background:{CORAL};color:white;font-size:0.6rem;font-weight:700;"
            f"letter-spacing:0.15em;padding:0.2rem 0.6rem;border-radius:999px;'>MOST POPULAR</span>"
            if tier.get("recommended") else ""
        )
        features_html = " · ".join([f"&#10003; {f}" for f in tier["features"]])
        price_html = "S$" + str(tier['price']) + " <span style='font-size:0.8rem;font-weight:400;color:#6B7280;'>/ mo</span>"
        tier_html = (
            "<div style='background:white;border:" + border + ";border-radius:24px;padding:1.5rem;margin-bottom:0.75rem;" + shadow + "'>"
            "<div style='display:flex;align-items:flex-start;gap:1rem;'>"
            "<div style='font-size:1.5rem;color:" + check_color + ";line-height:1;'>" + check + "</div>"
            "<div style='flex:1;'>"
            "<div style='display:flex;align-items:baseline;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.4rem;'>"
            "<h3 style='margin:0;color:" + INK + ";'>" + tier['id'] + "</h3>"
            + recommended + "<span style='margin-left:auto;font-size:1.6rem;font-weight:800;color:" + price_color + ";'>" + price_html + "</span>"
            "</div>"
            "<p style='margin:0;color:" + INK + ";'>" + tier['body'] + "</p>"
            "<p style='margin:0.5rem 0 0 0;font-size:0.75rem;color:#6B7280;'>" + features_html + "</p>"
            "</div></div></div>"
        )
        st.markdown(tier_html, unsafe_allow_html=True)
        if st.button(f"Pick {tier['id']}", key=f"tier_{tier['id']}", use_container_width=True,
                     type="primary" if selected else "secondary"):
            st.session_state.onboarding_tier = tier["id"]
            st.session_state.onboarding_crops = []
            st.rerun()

    # Enterprise section — contact sales
    for tier in enterprise:
        features_html = " · ".join([f"&#10003; {f}" for f in tier["features"]])
        price_html = "S$" + str(tier['price']) + " <span style='font-size:0.8rem;font-weight:400;color:rgba(199,230,107,0.7);'>/ mo</span>"
        ent_html = (
            "<div style='background:linear-gradient(135deg,#1a3a0f,#2D5016);border-radius:24px;"
            "padding:1.5rem;border:2px solid #4a7c3f;'>"
            "<div style='display:flex;align-items:flex-start;gap:1rem;flex-wrap:wrap;'>"
            "<div style='flex:1;min-width:200px;'>"
            "<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;"
            "color:#C7E66B;margin:0;'>" + tier['id'] + "</p>"
            "<p style='font-size:2rem;font-weight:800;color:white;margin:0.5rem 0;'>" + price_html + "</p>"
            "<p style='color:rgba(255,255,255,0.85);font-size:0.9rem;margin:0;'>" + tier['body'] + "</p>"
            "<p style='margin:0.5rem 0 0 0;font-size:0.75rem;color:rgba(199,230,107,0.7);'>" + features_html + "</p>"
            "</div>"
            "</div></div>"
        )
        st.markdown(ent_html, unsafe_allow_html=True)
        if st.button(f"Contact sales", key=f"tier_{tier['id']}", use_container_width=True, type="secondary"):
            st.info("Our corporate team will reach out within 24 hours. Email us at enterprise@greenloop.sg")

    st.write("")
    nav1, _, nav2 = st.columns([1, 2, 1])
    with nav1:
        if st.button("← Back", use_container_width=True, type="secondary"):
            st.session_state.onboarding_step = 0
            st.rerun()
    with nav2:
        if st.button("Continue →", use_container_width=True, type="primary",
                     disabled=st.session_state.onboarding_tier is None):
            st.session_state.onboarding_step = 2
            st.rerun()

# ─────────────────────────────────
# Step 2: Crop selection
# ─────────────────────────────────
elif step == 2:
    selected_tier = next(t for t in TIERS if t["id"] == st.session_state.onboarding_tier)
    crop_limit = selected_tier["crops"]

    eyebrow("Step 2 of 3")
    st.markdown(
        f"<h1 style='font-size:2.5rem;font-weight:800;color:{INK};margin:0;'>"
        "Pick your first crops.</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{MUTED};margin-top:0.5rem;'>"
        f"You picked <strong style='color:{KALE};'>{selected_tier['id']}</strong>. "
        f"Choose up to {crop_limit} {'crop' if crop_limit == 1 else 'crops'}.</p>",
        unsafe_allow_html=True,
    )
    st.write("")

    # 3-column grid for crops
    crop_rows = [CROP_OPTIONS[i:i+3] for i in range(0, len(CROP_OPTIONS), 3)]
    for row in crop_rows:
        cols = st.columns(3)
        for col, crop in zip(cols, row):
            with col:
                selected = crop["id"] in st.session_state.onboarding_crops
                at_limit = (not selected) and (len(st.session_state.onboarding_crops) >= crop_limit)

                border = f"2px solid {KALE}" if selected else f"1px solid {HAIR}"
                bg = "white" if not at_limit else f"{CREAM}66"
                check_html = (
                    f"<div style='display:inline-flex;align-items:center;justify-content:center;"
                    f"height:24px;width:24px;border-radius:999px;background:{KALE};color:white;"
                    f"font-weight:700;margin-top:0.5rem;'>✓</div>"
                    if selected else ""
                )

                st.markdown(
                    f"""
                    <div style="background:{bg};border:{border};border-radius:20px;padding:1.5rem;
                                text-align:center;margin-bottom:0.5rem;opacity:{0.5 if at_limit else 1};">
                      <div style="font-size:3rem;line-height:1;">{crop['emoji']}</div>
                      <p style="font-weight:700;color:{INK};margin:0.75rem 0 0 0;">{crop['name']}</p>
                      {check_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if not at_limit:
                    if st.button(("Remove" if selected else "Add"),
                                 key=f"crop_{crop['id']}", use_container_width=True,
                                 type="primary" if selected else "secondary"):
                        if selected:
                            st.session_state.onboarding_crops.remove(crop["id"])
                        else:
                            st.session_state.onboarding_crops.append(crop["id"])
                        st.rerun()

    st.caption(f"Selected: {len(st.session_state.onboarding_crops)} / {crop_limit}")

    st.write("")
    nav1, _, nav2 = st.columns([1, 2, 1])
    with nav1:
        if st.button("← Back", key="back2", use_container_width=True, type="secondary"):
            st.session_state.onboarding_step = 1
            st.rerun()
    with nav2:
        if st.button("Continue →", key="next2", use_container_width=True, type="primary",
                     disabled=len(st.session_state.onboarding_crops) == 0):
            st.session_state.onboarding_step = 3
            st.rerun()

# ─────────────────────────────────
# Step 3: Confirmation
# ─────────────────────────────────
elif step == 3:
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    tier = next(t for t in TIERS if t["id"] == st.session_state.onboarding_tier)
    n_crops = len(st.session_state.onboarding_crops)

    st.markdown(
        f"""
        <div style="text-align:center;max-width:600px;margin:2rem auto;">
            <div style="position:relative;display:inline-block;">
                <img src="data:image/png;base64,{leaf_b64}" width="140" height="168"/>
                <div style="position:absolute;bottom:0;right:-8px;background:{CORAL};
                            height:56px;width:56px;border-radius:999px;color:white;
                            display:flex;align-items:center;justify-content:center;font-size:1.5rem;">
                    ✓
                </div>
            </div>
            <div style="margin:1.5rem 0;">{pill("PLOT RESERVED", "coral")}</div>
            <h1 style="font-size:3rem;font-weight:800;color:{KALE};margin:0;">
                Welcome to your plot.
            </h1>
            <p style="font-size:1.15rem;color:{INK};margin-top:1.5rem;line-height:1.6;">
                Your <strong>{tier['id']}</strong> tier is ready. We've allocated <strong>Plot #042</strong>
                with your {n_crops} chosen {'crop' if n_crops == 1 else 'crops'}. AI will start
                growing tomorrow at 06:00 SGT.
            </p>
            <div style="background:{CREAM};border-radius:20px;padding:1.5rem;margin:2rem 0;text-align:left;">
                <p style="font-size:0.7rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;
                          color:{MUTED};margin:0;">First harvest</p>
                <p style="font-size:1.8rem;font-weight:800;color:{KALE};margin:0.25rem 0;">~ 6 weeks</p>
                <p style="font-size:0.85rem;color:{MUTED};margin:0;">
                    We'll WhatsApp you weekly, and your app shows live status anytime.
                </p>
            </div>
            <div style="background:linear-gradient(135deg,#1a3a0f,#2D5016);
                        border-radius:16px;padding:1rem 1.25rem;margin-top:1rem;
                        border:1px solid #4a7c3f;text-align:left;">
                <p style="font-weight:700;color:#C7E66B;margin:0;font-size:0.75rem;
                           letter-spacing:0.1em;text-transform:uppercase;">🌟 You're a Founding Gardener!</p>
                <p style="color:rgba(255,255,255,0.85);margin:0.4rem 0 0 0;font-size:0.8rem;">
                    Pre-launch cohort · Exclusive badge · Named on the wall of fame
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Open my plot →", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 0  # reset for next time
            st.switch_page("pages/2_🌿_My_Plot.py")

# Sidebar
with st.sidebar:
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"<div style='text-align:center;padding:1rem 0;'>"
        f"<img src='data:image/png;base64,{leaf_b64}' width='60' height='72'/>"
        f"<h2 style='color:{KALE};margin:0.5rem 0 0 0;font-weight:800;'>Adopt a Kale</h2></div>",
        unsafe_allow_html=True,
    )
