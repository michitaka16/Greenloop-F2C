"""Custom CSS + reusable Streamlit components for Adopt a Kale brand."""

import base64
from pathlib import Path
import streamlit as st

# ──────────────────────────────────────────────────
# Brand tokens
# ──────────────────────────────────────────────────
KALE   = "#2D5016"
LEAF   = "#7BA05B"
LIME   = "#C7E66B"
CORAL  = "#E07856"
PAPER  = "#FAF7F0"
CREAM  = "#F8F4EC"
INK    = "#1A1A1A"
MUTED  = "#6B7280"
HAIR   = "#E5E1D8"
BG     = "#FFFFFF"

ASSETS = Path(__file__).parent.parent / "assets"


# ──────────────────────────────────────────────────
# Global CSS — inject once per page
# ──────────────────────────────────────────────────
GLOBAL_CSS = f"""
<style>
/* hide Streamlit chrome we don't want */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ visibility: hidden; }}

/* base typography */
html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: {INK};
}}

/* tighten default container width */
.block-container {{
    max-width: 1100px;
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
}}

/* Sidebar branding */
[data-testid="stSidebar"] {{
    background: {PAPER};
    border-right: 1px solid {HAIR};
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
    color: {KALE};
}}

/* Primary buttons — kale */
.stButton > button,
.stDownloadButton > button,
[data-testid="stForm"] button[kind="primary"] {{
    background: {KALE} !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 8px rgba(45,80,22,0.15) !important;
}}
.stButton > button:hover {{
    background: #1f3a0f !important;
    transform: translateY(-1px) !important;
}}

/* Secondary (kind="secondary") buttons — cream */
.stButton > button[kind="secondary"] {{
    background: {CREAM} !important;
    color: {KALE} !important;
    border: 1px solid {HAIR} !important;
    box-shadow: none !important;
}}
.stButton > button[kind="secondary"]:hover {{
    border-color: {KALE} !important;
}}

/* Custom card style applied via div */
.kale-card {{
    background: white;
    border: 1px solid {HAIR};
    border-radius: 24px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.kale-card-dark {{
    background: {KALE};
    color: {LIME};
    border-radius: 24px;
    padding: 1.5rem;
}}
.kale-card-dark h1, .kale-card-dark h2, .kale-card-dark h3 {{ color: white; }}

/* Pill / Badge */
.kale-pill {{
    display: inline-block;
    background: {CREAM};
    color: {KALE};
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}}
.kale-pill-coral {{
    background: rgba(224,120,86,0.10);
    color: {CORAL};
    border: 1px solid rgba(224,120,86,0.20);
}}
.kale-pill-kale {{
    background: {KALE};
    color: {LIME};
}}

/* Big metric */
.kale-metric {{
    font-size: 2.5rem;
    font-weight: 800;
    color: {KALE};
    line-height: 1;
}}
.kale-metric-label {{
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: {MUTED};
}}

/* Section heading */
.kale-eyebrow {{
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: {CORAL};
    margin-bottom: 0.5rem;
}}

/* Progress bar override */
.stProgress > div > div {{
    background: {LEAF} !important;
}}
.stProgress > div {{
    background: {CREAM} !important;
}}

/* Chat */
[data-testid="stChatMessage"] {{
    background: white;
    border: 1px solid {HAIR};
    border-radius: 18px;
    padding: 0.5rem;
}}

/* Hairline separator */
.kale-hr {{
    height: 1px;
    background: {HAIR};
    border: none;
    margin: 2rem 0;
}}

/* Hero heading */
.kale-hero {{
    font-size: 4rem;
    font-weight: 800;
    color: {KALE};
    line-height: 0.95;
    letter-spacing: -0.02em;
    margin-bottom: 1.5rem;
}}
.kale-subhead {{
    font-size: 1.4rem;
    font-style: italic;
    color: {CORAL};
    font-weight: 600;
    margin-bottom: 0.5rem;
}}
</style>
"""


def inject_css():
    """Call at top of every page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def img_to_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def brand_header():
    """Render brand mark + wordmark at top of page."""
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:2rem;">
            <img src="data:image/png;base64,{leaf_b64}" width="28" height="34"/>
            <span style="font-weight:700;letter-spacing:0.25em;color:{KALE};font-size:0.8rem;">
                ADOPT A KALE
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, variant: str = "default") -> str:
    """Return HTML for a brand pill (use inside st.markdown)."""
    cls = {"default": "kale-pill", "coral": "kale-pill kale-pill-coral", "kale": "kale-pill kale-pill-kale"}[variant]
    return f'<span class="{cls}">{text}</span>'


def eyebrow(text: str):
    st.markdown(f'<p class="kale-eyebrow">{text}</p>', unsafe_allow_html=True)


def hero(headline: str, subhead: str = "", description: str = ""):
    """Big landing-style headline."""
    html = f'<h1 class="kale-hero">{headline}</h1>'
    if subhead:
        html += f'<p class="kale-subhead">{subhead}</p>'
    if description:
        html += f'<p style="font-size:1.05rem;color:{INK};max-width:42rem;">{description}</p>'
    st.markdown(html, unsafe_allow_html=True)


def metric(value: str, label: str, sub: str = ""):
    sub_html = f'<p style="font-size:0.75rem;color:{MUTED};margin-top:0.25rem;">{sub}</p>' if sub else ""
    st.markdown(
        f"""
        <div class="kale-card" style="text-align:left;">
            <p class="kale-metric-label">{label}</p>
            <p class="kale-metric">{value}</p>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def maturity_ring_html(percent: int, size: int = 240) -> str:
    """SVG progress ring with kale leaf in center."""
    stroke = 12
    radius = (size - stroke) / 2
    circumference = 2 * 3.14159 * radius
    offset = circumference - (percent / 100) * circumference
    leaf_b64 = img_to_base64(ASSETS / "leaf-dark.png")
    inner_size = int(size * 0.5)
    inner_h = int(inner_size * 1.2)
    return f"""
    <div style="position:relative;width:{size}px;height:{size}px;margin:auto;">
      <svg width="{size}" height="{size}" style="transform:rotate(-90deg);">
        <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="{CREAM}" stroke-width="{stroke}"/>
        <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="{LEAF}" stroke-width="{stroke}"
                stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
      </svg>
      <img src="data:image/png;base64,{leaf_b64}" width="{inner_size}" height="{inner_h}"
           style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);"/>
      <div style="position:absolute;bottom:-12px;left:50%;transform:translateX(-50%);
                  background:white;border:1px solid {HAIR};border-radius:999px;
                  padding:0.4rem 1rem;font-weight:700;color:{KALE};font-size:1.4rem;">
        {percent}<span style="font-size:0.9rem;font-weight:400;color:{MUTED};">%</span>
      </div>
    </div>
    """


def progress_card(label: str, value: int, total: int, emoji: str = "🌱", variety: str = ""):
    pct = int(value / total * 100)
    st.markdown(
        f"""
        <div class="kale-card" style="margin-bottom:0.75rem;">
          <div style="display:flex;align-items:center;gap:1rem;">
            <div style="font-size:2rem;width:48px;height:48px;border-radius:14px;background:{CREAM};
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;">{emoji}</div>
            <div style="flex:1;min-width:0;">
              <p style="font-size:0.7rem;color:{MUTED};margin:0;">{variety}</p>
              <p style="font-weight:700;color:{INK};margin:0;font-size:1.05rem;">{label}</p>
              <div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.5rem;">
                <div style="flex:1;height:6px;background:{CREAM};border-radius:999px;overflow:hidden;">
                  <div style="height:100%;width:{pct}%;background:{LEAF};border-radius:999px;"></div>
                </div>
                <span style="font-size:0.75rem;font-weight:700;color:{KALE};">{pct}%</span>
              </div>
              <p style="font-size:0.7rem;color:{MUTED};margin-top:0.25rem;">Day {value} of {total}</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
