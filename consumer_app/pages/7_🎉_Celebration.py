"""Celebration — Share harvest card + NFT minting flow."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from lib.styles import (
    inject_css, inject_gamification_css, brand_header, pill,
    KALE, LEAF, LIME, CORAL, CREAM, HAIR, MUTED, INK, ASSETS,
    share_card_html, nft_card_html, confetti_html,
)
from lib.mock_data import (
    SARAH, get_earned_badges, get_share_card_data, get_leaderboard_position,
    MILESTONES, MINTED_NFTS, HARVEST_CERTIFICATE_NFT,
)

st.set_page_config(
    page_title="Celebration — Adopt a Kale",
    page_icon="🎉",
    layout="wide",
)
inject_css()
inject_gamification_css()
brand_header()

# Session state for NFT minting flow
if "wallet_connected" not in st.session_state:
    st.session_state.wallet_connected = False
if "nft_minting" not in st.session_state:
    st.session_state.nft_minting = False
if "nft_minted" not in st.session_state:
    st.session_state.nft_minted = False

# ── Celebration confetti on load ─────────────────
st.markdown(confetti_html(), unsafe_allow_html=True)

st.markdown(
    f"<h1 style='font-size:2.2rem;font-weight:800;color:{INK};margin:0;'>🎉 Celebration!</h1>"
    f"<p style='color:{MUTED};margin-top:0.5rem;'>"
    f"Share your harvest or mint an NFT certificate of your grow.</p>",
    unsafe_allow_html=True,
)

st.write("")

# ── Tab: Share Card | NFT Mint ──────────────────
tab1, tab2 = st.tabs(["📱  Share Harvest Card", "🔗  Mint NFT Certificate"])

# ════════════════════════════════════════════════
# TAB 1 — Share Harvest Card
# ════════════════════════════════════════════════
with tab1:
    share_data = get_share_card_data()
    earned = get_earned_badges()
    rank = get_leaderboard_position()

    st.markdown(
        f"<p style='color:{MUTED};margin-bottom:1.5rem;'>"
        f"Generate a beautiful harvest card to share on Instagram, Twitter, or WhatsApp.</p>",
        unsafe_allow_html=True,
    )

    # Preview card
    card_html = share_card_html(share_data)
    st.markdown(card_html, unsafe_allow_html=True)

    st.write("")

    # Platform share buttons
    st.markdown(
        f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{MUTED};margin-bottom:0.75rem;'>Share to</p>",
        unsafe_allow_html=True,
    )

    col_ig, col_tw, col_ws, col_download = st.columns(4)
    with col_ig:
        st.markdown(
            f"<a href='https://instagram.com' target='_blank'>"
            f"<div style='background:linear-gradient(135deg,#833AB4,#E1306C,#F77737);"
            f"color:white;padding:0.7rem;border-radius:999px;text-align:center;"
            f"font-weight:700;font-size:0.85rem;'>📸 Instagram</div></a>",
            unsafe_allow_html=True,
        )
    with col_tw:
        st.markdown(
            f"<a href='https://twitter.com/intent/tweet?text=I%20just%20harvested%20{share_data['kg_grown']}kg%20of%20{share_data['crop']}%20from%20my%20Adopt%20a%20Kale%20plot!%20🌱%20%23Singapore%20%23UrbanFarming' target='_blank'>"
            f"<div style='background:#1DA1F2;color:white;padding:0.7rem;border-radius:999px;"
            f"text-align:center;font-weight:700;font-size:0.85rem;'>𝕏 Twitter</div></a>",
            unsafe_allow_html=True,
        )
    with col_ws:
        st.markdown(
            f"<a href='https://wa.me/?text=I%20just%20harvested%20{share_data['kg_grown']}kg%20of%20{share_data['crop']}%20from%20my%20Adopt%20a%20Kale%20plot!%20🌱' target='_blank'>"
            f"<div style='background:#25D366;color:white;padding:0.7rem;border-radius:999px;"
            f"text-align:center;font-weight:700;font-size:0.85rem;'>💬 WhatsApp</div></a>",
            unsafe_allow_html=True,
        )
    with col_download:
        # Download as HTML file (self-contained, works offline)
        card_with_style = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
        * {{ margin:0;padding:0;box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
               background:#F8F4EC;min-height:100vh;display:flex;align-items:center;
               justify-content:center;padding:1rem; }}
        </style>
        </head>
        <body>{card_html}</body>
        </html>
        """
        st.download_button(
            "⬇️  Download Card",
            data=card_with_style.encode("utf-8"),
            file_name="my_harvest_card.html",
            mime="text/html",
            use_container_width=True,
        )

    st.write("")
    st.info("📱 Tip: Screenshot the card above and upload directly to Instagram Stories for best results!")

    # Share stats
    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin-top:1.5rem;">
          <div class="kale-card" style="text-align:center;">
            <p style="font-size:2rem;font-weight:800;color:{KALE};margin:0;">{share_data['kg_grown']} kg</p>
            <p style="font-size:0.7rem;color:{MUTED};margin:0.25rem 0 0 0;">Total harvested</p>
          </div>
          <div class="kale-card" style="text-align:center;">
            <p style="font-size:2rem;font-weight:800;color:{KALE};margin:0;">{share_data['deliveries']}</p>
            <p style="font-size:0.7rem;color:{MUTED};margin:0.25rem 0 0 0;">Deliveries</p>
          </div>
          <div class="kale-card" style="text-align:center;">
            <p style="font-size:2rem;font-weight:800;color:{KALE};margin:0;">#{rank}</p>
            <p style="font-size:0.7rem;color:{MUTED};margin:0.25rem 0 0 0;">SG Rank</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════
# TAB 2 — NFT Minting Flow
# ════════════════════════════════════════════════
with tab2:
    if st.session_state.nft_minted:
        # ── Success state ──
        st.balloons()
        st.success("🎉 NFT minted successfully!")
        st.write("")

        minted = MINTED_NFTS[0]
        st.markdown(nft_card_html(minted), unsafe_allow_html=True)

        st.write("")
        col_explore, col_copy = st.columns(2)
        with col_explore:
            st.markdown(
                '<a href="https://opensea.io/assets/matic/0x0000000000000000000000000000000000000000/%s" target="_blank">'
                '<div style="background:#208BBF;color:white;padding:0.8rem;border-radius:999px;'
                'text-align:center;font-weight:700;">🔍 View on OpenSea</div></a>' % minted["token_id"],
                unsafe_allow_html=True,
            )
        with col_copy:
            st.button("📋  Copy Transaction Hash", use_container_width=True)

        st.write("")
        st.markdown(
            f"<p style='font-size:0.75rem;color:{MUTED};text-align:center;'>"
            f"This is a demo NFT minted on Polygon Mumbai testnet. "
            f"Production minting requires MetaMask + MATIC tokens.</p>",
            unsafe_allow_html=True,
        )
        if st.button("🔄  Mint Another"):
            st.session_state.nft_minted = False
            st.session_state.wallet_connected = False
            st.rerun()

    elif st.session_state.wallet_connected:
        # ── Pre-mint: show certificate preview + mint button ──
        cert = HARVEST_CERTIFICATE_NFT
        col_preview, col_info = st.columns([1, 1])

        with col_preview:
            st.markdown(nft_card_html({
                "crop": cert["crop"],
                "variety": cert["variety"],
                "harvest_date": cert["harvest_date"],
                "biomass_g": cert["biomass_g"],
                "total_kg_grown": cert["total_kg_grown"],
                "token_id": cert["token_id"],
                "plot_id": cert["plot_id"],
                "wallet_address": cert["wallet_address"],
                "tx_hash": cert["tx_hash"],
            }), unsafe_allow_html=True)

        with col_info:
            st.markdown(
                f"""
                <div class="kale-card">
                  <h3 style="margin:0 0 1rem 0;color:{INK};">🌿 Harvest NFT Certificate</h3>
                  <p style="font-size:0.85rem;color:{MUTED};margin-bottom:1rem;line-height:1.6;">
                    Mint an immutable, on-chain record of your harvest.
                    This NFT proves you grew <strong>{cert['crop']}</strong> on
                    <strong>Plot #{cert['plot_id']}</strong> — forever.
                  </p>
                  <div style="background:{CREAM};border-radius:12px;padding:0.75rem;margin-bottom:0.75rem;">
                    <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0;">CONTRACT</p>
                    <p style="font-size:0.8rem;font-family:monospace;color:{INK};margin:0.2rem 0 0 0;">GreenLoopNFT.sol · Polygon</p>
                  </div>
                  <div style="background:{CREAM};border-radius:12px;padding:0.75rem;margin-bottom:1rem;">
                    <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:{MUTED};margin:0;">ESTIMATED GAS</p>
                    <p style="font-size:0.9rem;font-weight:700;color:{INK};margin:0.2rem 0 0 0;">~0.003 MATIC (~$0.01)</p>
                  </div>
                  <p style="font-size:0.75rem;color:{MUTED};margin:0;">
                    Demo: no real MATIC will be charged.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        col_mint, col_back = st.columns([1, 1])
        with col_mint:
            if st.button("🔗  Mint NFT Now", type="primary", use_container_width=True):
                st.session_state.nft_minting = True
                st.rerun()

        if st.session_state.nft_minting:
            with st.spinner("Confirming in wallet... (demo)"):
                import time
                time.sleep(2)
                st.session_state.nft_minting = False
                st.session_state.nft_minted = True
                st.rerun()

        with col_back:
            if st.button("←  Back", use_container_width=True):
                st.session_state.wallet_connected = False
                st.rerun()

    else:
        # ── Connect Wallet screen ──
        st.markdown(
            f"""
            <div style="text-align:center;padding:3rem 1rem;">
              <div style="font-size:5rem;margin-bottom:1.5rem;">🔗</div>
              <h2 style="color:{INK};font-weight:800;margin:0 0 0.5rem 0;">Connect Your Wallet</h2>
              <p style="color:{MUTED};font-size:0.9rem;max-width:360px;margin:0 auto 2rem auto;line-height:1.6;">
                Mint your harvest as an NFT on Polygon blockchain.
                You'll need a Web3 wallet (MetaMask, WalletConnect).
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col2:
            if st.button("🐍  MetaMask", use_container_width=True):
                st.session_state.wallet_connected = True
                st.rerun()
        with w_col1:
            st.button("🔗  WalletConnect", disabled=True, use_container_width=True)
        with w_col3:
            st.button("👻  Phantom", disabled=True, use_container_width=True)

        st.write("")
        st.markdown(
            f"<p style='font-size:0.75rem;color:{MUTED};text-align:center;'>"
            f"No wallet? Your harvest data is saved locally. "
            f"Minting is optional — your certificate is still beautiful! "
            f"<a href='#' style='color:{KALE};'>Learn more about NFTs</a></p>",
            unsafe_allow_html=True,
        )

        st.info("Demo mode: clicking 'MetaMask' connects a mock wallet. No real transaction occurs.")

# Sidebar
with st.sidebar:
    from lib.styles import img_to_base64
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
              CERTIFICATE PREVIEW
          </p>
          <p style='margin:0.2rem 0;font-weight:700;color:{INK};'>{SARAH['name']}</p>
          <p style='margin:0;font-size:0.7rem;color:{MUTED};'>
              {SARAH['tier']} tier · Plot #{SARAH['plot_id']}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<p style='color:{MUTED};font-size:0.75rem;'>"
        f"Share cards and NFT certificates are linked to your plot's harvest history.</p>",
        unsafe_allow_html=True,
    )
