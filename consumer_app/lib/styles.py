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


# ────────────────────────────────────────────
# Gamification — Confetti animation
# ────────────────────────────────────────────
GAMIFICATION_CSS = """
/* Confetti keyframes */
@keyframes confetti-fall {
  0%   { transform: translateY(-100px) rotate(0deg); opacity: 1; }
  100% { transform: translateY(600px) rotate(720deg); opacity: 0; }
}
@keyframes badge-unlock {
  0%   { transform: scale(0) rotate(-20deg); opacity: 0; }
  60%  { transform: scale(1.2) rotate(5deg);  opacity: 1; }
  100% { transform: scale(1) rotate(0deg);    opacity: 1; }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes pulse-glow {
  0%,100% { box-shadow: 0 0 8px rgba(199,230,107,0.4); }
  50%     { box-shadow: 0 0 24px rgba(199,230,107,0.8); }
}
.confetti-piece {
  position: fixed;
  top: -20px;
  width: 12px;
  height: 12px;
  border-radius: 2px;
  animation: confetti-fall linear forwards;
  pointer-events: none;
  z-index: 9999;
}
.badge-unlocked {
  animation: badge-unlock 0.7s cubic-bezier(0.34,1.56,0.64,1) forwards;
}
.badge-locked {
  filter: grayscale(1);
  opacity: 0.4;
}
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-weight: 800;
  font-size: 0.8rem;
}
.rank-1 { background: linear-gradient(135deg,#FFD700,#FFA500); color: white; }
.rank-2 { background: linear-gradient(135deg,#C0C0C0,#9E9E9E); color: white; }
.rank-3 { background: linear-gradient(135deg,#CD7F32,#A0522D); color: white; }
.rank-other { background: #F8F4EC; color: #6B7280; }
.share-card {
  border-radius: 20px;
  overflow: hidden;
  border: 2px solid #2D5016;
  max-width: 540px;
}
.nft-card {
  background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
  border: 1px solid #C7E66B;
  border-radius: 20px;
  padding: 1.5rem;
  color: white;
}
"""


def inject_gamification_css():
    st.markdown(f"<style>{GAMIFICATION_CSS}</style>", unsafe_allow_html=True)


def confetti_html() -> str:
    colors = ["#2D5016","#7BA05B","#C7E66B","#E07856","#FFD700","#FF6B6B","#4ECDC4"]
    pieces = ""
    for i in range(60):
        color = colors[i % len(colors)]
        left = (i * 37 + 13) % 100
        delay = (i * 0.07) % 4
        size = 8 + (i % 8)
        pieces += (
            f"<div class='confetti-piece' style='"
            f"left:{left}%;"
            f"background:{color};"
            f"width:{size}px;height:{size}px;"
            f"animation-duration:{(2.5 + i%3)}s;"
            f"animation-delay:{delay}s;'></div>"
        )
    return f"<div style='position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;overflow:hidden;'>{pieces}</div>"


def badge_card(badge: dict, unlocked: bool = True) -> str:
    cls = "badge-unlocked" if unlocked else "badge-locked"
    lock_icon = "" if unlocked else "🔒"
    earned_str = f"<p style='font-size:0.65rem;color:{MUTED};margin:0.2rem 0 0 0;'>Earned {badge.get('earned_date','')}</p>" if unlocked else ""
    return f"""
    <div class='kale-card' style='text-align:center;padding:1rem;flex:1;min-width:110px;'>
      <div style='font-size:2.2rem;margin-bottom:0.5rem;{"" if unlocked else "filter:grayscale(1);opacity:0.4;"}'>
        {lock_icon}{badge['emoji']}
      </div>
      <p style='font-weight:700;color:{INK};font-size:0.75rem;margin:0;'>{badge['title']}</p>
      <p style='font-size:0.65rem;color:{MUTED};margin:0.2rem 0;'>{badge['description']}</p>
      {earned_str}
    </div>
    """


def leaderboard_row(rank: int, name: str, plot: str, badges: int, kg_grown: float,
                    deliveries: int, tier: str, hood: str, is_sarah: bool = False) -> str:
    bg = "#F8F4EC" if is_sarah else "white"
    border = f"2px solid {KALE}" if is_sarah else f"1px solid {HAIR}"
    rank_cls = f"rank-{rank}" if rank <= 3 else "rank-other"
    rank_label = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
    return f"""
    <div style='display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0.75rem;
                background:{bg};border:{border};border-radius:12px;margin-bottom:0.4rem;'>
      <div class='rank-badge {rank_cls}' style='flex-shrink:0;'>
        {rank_label if rank <= 3 else rank}
      </div>
      <div style='flex:1;'>
        <p style='font-weight:700;color:{INK};margin:0;font-size:0.9rem;'>{name}
          <span style='font-size:0.65rem;color:{MUTED};font-weight:400;'> · {tier}</span>
        </p>
        <p style='font-size:0.65rem;color:{MUTED};margin:0;'>📍 {hood} · {plot}</p>
      </div>
      <div style='text-align:right;flex-shrink:0;'>
        <p style='font-weight:800;color:{KALE};margin:0;font-size:0.9rem;'>{kg_grown}kg</p>
        <p style='font-size:0.6rem;color:{MUTED};margin:0;'>{badges} badges · {deliveries} deliveries</p>
      </div>
    </div>
    """


def share_card_html(data: dict) -> str:
    return f"""
    <div class='share-card' style='font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;'>
      <div style='background:linear-gradient(135deg,#2D5016 0%,#4A7C2E 100%);padding:2rem 1.5rem;text-align:center;'>
        <p style='color:rgba(199,230,107,0.8);font-size:0.7rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;margin:0;'>Adopt a Kale</p>
        <h1 style='color:white;font-size:1.6rem;font-weight:800;margin:0.25rem 0;'>My Harvest Report</h1>
        <p style='color:rgba(255,255,255,0.75);font-size:0.8rem;margin:0;'>Plot #{data['plot_id']} · {data['date']}</p>
      </div>
      <div style='background:white;padding:1.5rem;'>
        <div style='display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem;'>
          <div style='font-size:3rem;'>🥬</div>
          <div>
            <p style='font-weight:800;color:#1A1A1A;font-size:1.1rem;margin:0;'>{data['crop']}</p>
            <p style='color:#6B7280;font-size:0.8rem;margin:0;'>{data['variety']} · {data['tier']} tier</p>
          </div>
        </div>
        <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;margin-bottom:1.25rem;'>
          <div style='background:#F8F4EC;border-radius:12px;padding:0.75rem;text-align:center;'>
            <p style='font-size:1.5rem;font-weight:800;color:#2D5016;margin:0;'>{data['kg_grown']}</p>
            <p style='font-size:0.65rem;color:#6B7280;margin:0;'>kg grown</p>
          </div>
          <div style='background:#F8F4EC;border-radius:12px;padding:0.75rem;text-align:center;'>
            <p style='font-size:1.5rem;font-weight:800;color:#2D5016;margin:0;'>{data['deliveries']}</p>
            <p style='font-size:0.65rem;color:#6B7280;margin:0;'>deliveries</p>
          </div>
          <div style='background:#F8F4EC;border-radius:12px;padding:0.75rem;text-align:center;'>
            <p style='font-size:1.5rem;font-weight:800;color:#2D5016;margin:0;'>{data['badges']}</p>
            <p style='font-size:0.65rem;color:#6B7280;margin:0;'>badges</p>
          </div>
        </div>
        <p style='font-size:0.75rem;color:#6B7280;text-align:center;margin:0;'>
          🌱 Grown with AI in Singapore · @AdoptaKaleSG
        </p>
      </div>
    </div>
    """


def nft_card_html(nft: dict) -> str:
    return f"""
    <div class='nft-card'>
      <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;'>
        <p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#C7E66B;margin:0;'>
          🌿 GreenLoop Harvest NFT
        </p>
        <span style='background:#C7E66B;color:#1A1A1A;font-size:0.6rem;font-weight:800;padding:0.2rem 0.6rem;border-radius:999px;'>MINTED</span>
      </div>
      <div style='text-align:center;padding:1rem 0;'>
        <div style='font-size:4rem;margin-bottom:0.5rem;'>🥬</div>
        <h3 style='color:white;font-size:1.2rem;margin:0 0 0.25rem 0;'>{nft['crop']}</h3>
        <p style='color:rgba(199,230,107,0.7);font-size:0.8rem;margin:0;'>{nft['variety']} · Plot #{nft['plot_id']}</p>
      </div>
      <div style='display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-bottom:1rem;'>
        <div style='background:rgba(255,255,255,0.08);border-radius:10px;padding:0.6rem;'>
          <p style='font-size:0.6rem;color:rgba(255,255,255,0.5);margin:0;'>HARVEST DATE</p>
          <p style='font-weight:700;color:white;font-size:0.85rem;margin:0.1rem 0 0 0;'>{nft['harvest_date']}</p>
        </div>
        <div style='background:rgba(255,255,255,0.08);border-radius:10px;padding:0.6rem;'>
          <p style='font-size:0.6rem;color:rgba(255,255,255,0.5);margin:0;'>BIOMASS</p>
          <p style='font-weight:700;color:white;font-size:0.85rem;margin:0.1rem 0 0 0;'>{nft['biomass_g']}g</p>
        </div>
        <div style='background:rgba(255,255,255,0.08);border-radius:10px;padding:0.6rem;'>
          <p style='font-size:0.6rem;color:rgba(255,255,255,0.5);margin:0;'>TOTAL GROWN</p>
          <p style='font-weight:700;color:white;font-size:0.85rem;margin:0.1rem 0 0 0;'>{nft['total_kg_grown']} kg</p>
        </div>
        <div style='background:rgba(255,255,255,0.08);border-radius:10px;padding:0.6rem;'>
          <p style='font-size:0.6rem;color:rgba(255,255,255,0.5);margin:0;'>TOKEN ID</p>
          <p style='font-weight:700;color:#C7E66B;font-size:0.85rem;margin:0.1rem 0 0 0;'>#{nft['token_id']}</p>
        </div>
      </div>
      <div style='background:rgba(255,255,255,0.05);border-radius:10px;padding:0.6rem;margin-bottom:0.75rem;'>
        <p style='font-size:0.6rem;color:rgba(255,255,255,0.4);margin:0;'>WALLET</p>
        <p style='font-family:monospace;font-size:0.75rem;color:#C7E66B;margin:0.1rem 0 0 0;'>{nft['wallet_address']}</p>
      </div>
      <div style='background:rgba(255,255,255,0.05);border-radius:10px;padding:0.6rem;'>
        <p style='font-size:0.6rem;color:rgba(255,255,255,0.4);margin:0;'>TX HASH</p>
        <p style='font-family:monospace;font-size:0.7rem;color:rgba(255,255,255,0.6);margin:0.1rem 0 0 0;word-break:break-all;'>{nft['tx_hash']}</p>
      </div>
    </div>
    """

# ────────────────────────────────────────────
# ESG Impact Card — water saved / CO2 reduced
# ────────────────────────────────────────────
def esg_card_html(water_saved_l: float, co2_saved_kg: float, trees_equiv: float) -> str:
    return f"""
    <div style='background:linear-gradient(135deg,#2D5016 0%,#1a3a0f 100%);border-radius:20px;padding:1.25rem;color:white;'>
      <p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:rgba(199,230,107,0.7);margin:0 0 1rem 0;'>
        🌱 Your ESG Impact Since Joining
      </p>
      <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;'>
        <div style='background:rgba(255,255,255,0.1);border-radius:14px;padding:0.75rem;text-align:center;'>
          <p style='font-size:1.6rem;font-weight:800;color:#7BA05B;margin:0;'>💧</p>
          <p style='font-size:1.3rem;font-weight:800;color:white;margin:0.2rem 0;'>-{water_saved_l:.0f}L</p>
          <p style='font-size:0.6rem;color:rgba(255,255,255,0.6);margin:0;'>water saved</p>
          <p style='font-size:0.55rem;color:rgba(255,255,255,0.4);margin:0.2rem 0 0 0;'>vs conventional</p>
        </div>
        <div style='background:rgba(255,255,255,0.1);border-radius:14px;padding:0.75rem;text-align:center;'>
          <p style='font-size:1.6rem;font-weight:800;color:#7BA05B;margin:0;'>🌍</p>
          <p style='font-size:1.3rem;font-weight:800;color:white;margin:0.2rem 0;'>-{co2_saved_kg:.1f}kg</p>
          <p style='font-size:0.6rem;color:rgba(255,255,255,0.6);margin:0;'>CO2 avoided</p>
          <p style='font-size:0.55rem;color:rgba(255,255,255,0.4);margin:0.2rem 0 0 0;'>vs conventional</p>
        </div>
        <div style='background:rgba(255,255,255,0.1);border-radius:14px;padding:0.75rem;text-align:center;'>
          <p style='font-size:1.6rem;font-weight:800;color:#C7E66B;margin:0;'>🌳</p>
          <p style='font-size:1.3rem;font-weight:800;color:#C7E66B;margin:0.2rem 0;'>~{trees_equiv:.1f}</p>
          <p style='font-size:0.6rem;color:rgba(255,255,255,0.6);margin:0;'>trees worth</p>
          <p style='font-size:0.55rem;color:rgba(255,255,255,0.4);margin:0.2rem 0 0 0;'>CO2 offset</p>
        </div>
      </div>
    </div>
    """


# ────────────────────────────────────────────
# Growth Chart — 8-week SVG bar chart
# ────────────────────────────────────────────
def growth_chart_svg(growth_log: list) -> str:
    if not growth_log:
        return "<p style='color:#6B7280;font-size:0.8rem;'>No growth data yet.</p>"
    values = [d["kg"] for d in growth_log]
    labels = [d["week"] for d in growth_log]
    max_val = max(values) if values else 1
    chart_w, chart_h = 560, 160
    bar_w = chart_w / len(values) - 8
    gap = 8
    bars_svg = ""
    for i, (v, lbl) in enumerate(zip(values, labels)):
        bh = max(4, (v / max_val) * (chart_h - 30))
        x = i * (bar_w + gap) + gap / 2
        y = chart_h - bh - 20
        bars_svg += (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
            f'rx="4" fill="#2D5016" opacity="0.85"/>'
            f'<text x="{x + bar_w/2:.1f}" y="{chart_h - 5}" '
            f'text-anchor="middle" font-size="9" fill="#6B7280">{lbl}</text>'
            f'<text x="{x + bar_w/2:.1f}" y="{y - 4}" '
            f'text-anchor="middle" font-size="9" font-weight="700" fill="#2D5016">{v:.1f}kg</text>'
        )
    return f"""
    <div style="background:white;border:1px solid #E5E1D8;border-radius:16px;padding:1rem;">
      <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:#6B7280;margin:0 0 0.75rem 0;">
        📈 8-Week Growth Portfolio
      </p>
      <svg viewBox="0 0 {chart_w} {chart_h}" width="100%" style="overflow:visible;">
        {bars_svg}
      </svg>
    </div>
    """


# ────────────────────────────────────────────
# Status Badge — loyalty tier with optional glow
# ────────────────────────────────────────────
def status_badge_html(tier: dict, glow: bool = False, is_founding: bool = False) -> str:
    color = tier.get("color", "#7BA05B")
    glow_cls = "pulse-glow" if glow else ""
    founding_tag = "🌟" if is_founding else ""
    return (
        f'<span class="{glow_cls}" style="'
        f'display:inline-flex;align-items:center;gap:0.3rem;'
        f'background:{color};color:white;'
        f'padding:0.3rem 0.75rem;border-radius:999px;'
        f'font-size:0.7rem;font-weight:700;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.15);">'
        f'{founding_tag}{tier["emoji"]} {tier["id"]}</span>'
    )


# ────────────────────────────────────────────
# Alert Banner — crisis notification
# ────────────────────────────────────────────
def alert_banner_html(alert: dict) -> str:
    severity = alert.get("severity", "info")
    configs = {
        "critical": ("#DC2626", "#FEF2F2"),
        "warning":  ("#D97706", "#FFFBEB"),
        "info":     ("#2D5016", "#F0FDF4"),
    }
    bg, border = configs.get(severity, configs["info"])
    action_btn = (
        f'<button style="background:white;border:none;border-radius:999px;'
        f'padding:0.4rem 1rem;font-weight:700;font-size:0.75rem;cursor:pointer;">'
        f'{alert.get("action_label","Action")}</button>'
        if alert.get("action_label") else ""
    )
    return f"""
    <div style="background:{bg};border:1.5px solid {border};border-radius:16px;padding:0.9rem 1.25rem;
                margin-bottom:0.75rem;display:flex;align-items:flex-start;gap:0.75rem;">
      <div style="font-size:1.5rem;flex-shrink:0;">{alert.get("icon","ℹ️")}</div>
      <div style="flex:1;min-width:0;">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem;flex-wrap:wrap;">
          <p style="font-weight:800;color:white;font-size:0.9rem;margin:0;">{alert.get("title","")}</p>
          {action_btn}
        </div>
        <p style="font-size:0.8rem;color:rgba(255,255,255,0.85);margin:0.3rem 0 0 0;line-height:1.5;">
          {alert.get("body","")}
        </p>
      </div>
    </div>
    """


# ────────────────────────────────────────────
# Recipe Card — horizontal layout
# ────────────────────────────────────────────
def recipe_card_html(recipe: dict) -> str:
    ingredients_html = " · ".join(recipe.get("ingredients", [])[:3])
    return f"""
    <div style="display:flex;align-items:center;gap:1rem;background:white;border:1px solid #E5E1D8;
                border-radius:16px;padding:0.9rem 1.1rem;margin-bottom:0.6rem;">
      <div style="font-size:2rem;flex-shrink:0;">{recipe.get("emoji","🍽️")}</div>
      <div style="flex:1;min-width:0;">
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem;">
          <p style="font-weight:700;color:#1A1A1A;font-size:0.9rem;margin:0;">{recipe.get("name","")}</p>
          <span style="background:#F8F4EC;color:#6B7280;font-size:0.6rem;font-weight:600;
                       padding:0.15rem 0.5rem;border-radius:999px;">{recipe.get("meal","")}</span>
        </div>
        <p style="font-size:0.72rem;color:#6B7280;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
          {ingredients_html}
        </p>
      </div>
      <div style="font-size:0.65rem;font-weight:700;color:#2D5016;flex-shrink:0;">View →</div>
    </div>
    """


# ────────────────────────────────────────────
# Delivery Card with Skip — for Schedule page
# ────────────────────────────────────────────
def delivery_card_skip_html(delivery: dict, is_skipped: bool = False) -> str:
    items_html = "".join([f"<p style='margin:0;font-size:0.85rem;color:#1A1A1A;'>{item}</p>"
                          for item in delivery.get("items", [])])
    status_color = "#6B7280" if is_skipped else "#2D5016"
    strikethrough = "text-decoration:line-through;opacity:0.5;" if is_skipped else ""
    date_parts = delivery["date"].split()
    return f"""
    <div style="display:flex;gap:1rem;padding:0.75rem 0;border-bottom:1px solid #E5E1D8;{strikethrough}">
      <div style="text-align:center;flex-shrink:0;min-width:56px;">
        <p style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                  color:{status_color};margin:0;">{date_parts[0]}</p>
        <p style="font-size:1.5rem;font-weight:800;color:{status_color};line-height:1;margin:0.2rem 0 0 0;">
          {date_parts[1]}</p>
      </div>
      <div style="flex:1;border-left:1px solid #E5E1D8;padding-left:1rem;">
        {items_html}
        <p style="margin:0.25rem 0 0 0;font-size:0.65rem;color:#6B7280;text-transform:capitalize;">
          {delivery.get("status","")}{" · SKIPPED" if is_skipped else ""}
        </p>
      </div>
    </div>
    """

# ────────────────────────────────────────────
def alert_toast_html(alert: dict) -> str:
    """Small toast notification for non-blocking alerts."""
    sev = alert.get("severity", "info")
    bg, border, text = {
        "critical": ("#FEE2E2", "#DC2626", "#991B1B"),
        "warning":  ("#FEF3C7", "#D97706", "#92400E"),
        "info":     ("#D1FAE5", "#059669", "#065F46"),
    }.get(sev, ("#D1FAE5", "#059669", "#065F46"))
    return f"""
    <div style="background:{bg};border-left:4px solid {border};
                border-radius:8px;padding:0.6rem 1rem;margin-bottom:0.5rem;
                display:flex;align-items:center;gap:0.75rem;">
      <span style="font-size:1.1rem;">{alert.get("icon","ℹ️")}</span>
      <div style="flex:1;">
        <p style="font-weight:700;color:{text};font-size:0.8rem;margin:0;">{alert.get("title","")}</p>
        <p style="color:{text};font-size:0.75rem;margin:0.15rem 0 0 0;opacity:0.85;">{alert.get("body","")[:80]}…</p>
      </div>
    </div>
    """

