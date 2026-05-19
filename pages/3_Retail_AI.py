"""Layer 4: Retail AI — Customer Behavioural Segmentation.

Clusters Adopt a Kale's customer base into behavioural segments using K-Means.
Read-only analytics — does not modify any data files.
"""

import sys
from pathlib import Path

# Ensure greenloop package is on path
src_path = Path(__file__).resolve().parents[1] / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Adopt a Kale — Retail AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from greenloop.data.loader import load_customers, load_orders
from greenloop.data.shared_data import load_farm_output
from greenloop.layer4.features import load_features
from greenloop.layer4.segmentation import cluster_customers, name_segment
from greenloop.layer4.visualization import reduce_pca, reduce_umap

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_and_build():
    """Load data, build features, cluster, profile."""
    customers = load_customers()
    orders = load_orders()
    df_features = load_features()
    result = cluster_customers(df_features)
    return customers, orders, df_features, result


def render_segment_cards(profiles, result_labels):
    """Render one recommendation card per segment."""
    cols = st.columns(len(profiles))
    for col, profile in zip(cols, profiles):
        name, emoji, action = name_segment(profile)
        col.markdown(
            f"### {emoji} {name}\n"
            f"**{profile.size} customers ({profile.size_pct:.1f}%)**\n\n"
            f"Avg basket: **${profile.avg_basket_sgd:.2f}** / order  \n"
            f"Frequency: **{profile.avg_frequency:.1f}** orders/mo  \n"
            f"Bulk buyer: **{profile.bulk_buyer_pct:.0f}%**  \n"
            f"Live commerce: **{profile.live_commerce_share*100:.0f}%**  \n"
            f"Top crop: **{profile.dominant_crop}**\n\n"
            f"**{action}**"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
st.title("\U0001f3ea Retail AI — Customer Segmentation")
st.caption("Behavioural clustering powered by K-Means · Synthetic demo data")

with st.spinner("Loading data & clustering customers..."):
    try:
        customers, orders, df_features, result = load_and_build()
    except FileNotFoundError as e:
        st.error(
            f"Missing data file: {e}\n\n"
            "Run `python scripts/generate_retail_data.py` first to generate "
            "synthetic customer and order data."
        )
        st.stop()
    except ValueError as e:
        st.error(f"Data error: {e}")
        st.stop()

# ---------------------------------------------------------------------------
# KPI Strip
# ---------------------------------------------------------------------------
total_customers = len(df_features)
total_orders = len(orders)
avg_basket = orders["sgd_total"].mean()
silhouette = result.silhouette

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Customers segmented", f"{total_customers}")
kpi2.metric("Total orders", f"{total_orders}")
kpi3.metric("Avg basket (SGD)", f"${avg_basket:.2f}")
kpi4.metric("Silhouette score", f"{silhouette:.3f}")

# ── Today's Orders Summary (latest available date) ──────────────────────
latest_date = orders["date"].max()
latest_orders = orders[orders["date"] == latest_date]
date_str = pd.Timestamp(latest_date).strftime("%d %b %Y")

st.subheader(f"📦 Today's Orders — {date_str}")

today_col1, today_col2, today_col3 = st.columns(3)
today_col1.metric("Orders", str(len(latest_orders)))
today_col2.metric("Total Weight", f"{latest_orders['kg'].sum():.1f} kg")
today_col3.metric("Revenue", f"${latest_orders['sgd_total'].sum():.2f}")

# Crop breakdown
crop_breakdown = (
    latest_orders.groupby("crop_id")["kg"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
crop_breakdown.columns = ["Crop", "kg"]
crop_colors_map = {
    "kai_lan": "#1abc9c",
    "spinach": "#3498db",
    "lettuce": "#2ecc71",
    "arugula": "#f1c40f",
    "chye_sim": "#e67e22",
}
crop_breakdown["color"] = crop_breakdown["Crop"].map(
    lambda c: crop_colors_map.get(c, "#95a5a6")
)
fig_today = px.bar(
    crop_breakdown,
    x="Crop",
    y="kg",
    color="color",
    color_discrete_map="identity",
    title=f"kg by crop — {date_str}",
    labels={"kg": "kg", "Crop": ""},
    text="kg",
)
fig_today.update_layout(
    showlegend=False,
    xaxis_tickangle=-30,
    height=220,
    margin=dict(l=20, r=20, t=40, b=20),
)
st.plotly_chart(fig_today, use_container_width=True)

st.divider()

# ── Farm AI Forecast Panel ───────────────────────────────────────────────
farm = load_farm_output()
if farm:
    forecast = farm.get("forecast", {})
    rack_layout = farm.get("rack_layout", {})

    crop_names = {
        "kai_lan": "Kai Lan", "baby_spinach": "Baby Spinach",
        "lettuce_mambo": "Lettuce", "chye_sim": "Chye Sim",
        "arugula": "Arugula", "pak_choi": "Pak Choi",
        "kale": "Kale", "basil_thai": "Thai Basil",
        "coriander": "Coriander", "mint": "Mint",
    }
    crop_colors = {
        "kai_lan": "#1abc9c", "baby_spinach": "#3498db",
        "lettuce_mambo": "#2c3e50", "chye_sim": "#e67e22",
        "arugula": "#2ecc71", "pak_choi": "#00bcd4",
        "kale": "#f1c40f", "basil_thai": "#9b59b6",
        "coriander": "#e74c3c", "mint": "#e91e63",
    }

    st.subheader("📦 Farm AI — Tomorrow's Demand Forecast")

    # Derive which crops are growing this cycle
    active_crops = set(rack_layout.values()) & set(forecast.keys())

    # Summary
    total_kg = sum(forecast[c].get("predicted_kg", 0) for c in active_crops)
    c1, c2 = st.columns(2)
    c1.metric("Predicted Total Demand", f"{total_kg:.1f} kg")
    c2.metric("Crops in Production", f"{len(active_crops)} varieties")
    st.caption(f"Source: Farm AI · Plan date: {farm.get('plan_date', 'unknown')}")

    # Demand cards per active crop
    forecast_rows = []
    for crop_id in active_crops:
        vals = forecast[crop_id]
        all_preds = sorted(forecast[c].get("predicted_kg", 0) for c in forecast)
        all_preds_sorted = sorted(all_preds)
        q75 = all_preds_sorted[int(len(all_preds_sorted) * 0.75)] if all_preds else 0
        q25 = all_preds_sorted[int(len(all_preds_sorted) * 0.25)] if all_preds else 0
        pred = vals.get("predicted_kg", 0)
        badge = "🔴 High" if pred >= q75 else ("🟢 Low" if pred <= q25 else "🟡 Medium")
        forecast_rows.append({
            "crop_id": crop_id,
            "crop": crop_names.get(crop_id, crop_id),
            "pred_kg": round(pred, 1),
            "lower": round(vals.get("lower_ci", 0), 1),
            "upper": round(vals.get("upper_ci", 0), 1),
            "badge": badge,
            "color": crop_colors.get(crop_id, "#888888"),
        })
    forecast_rows.sort(key=lambda r: r["pred_kg"], reverse=True)

    cols = st.columns(min(len(forecast_rows), 5))
    for i, r in enumerate(forecast_rows):
        with cols[i % len(cols)]:
            color = r["color"]
            st.markdown(
                f"""
                <div style="border:2px solid {color}; border-radius:6px;
                            padding:8px; text-align:center; margin-bottom:4px;">
                    <div style="font-size:0.9em; font-weight:bold; color:{color};">{r["crop"]}</div>
                    <div style="font-size:1.2em; font-weight:bold;">{r["pred_kg"]} kg</div>
                    <div style="font-size:0.7em; color:#aaa;">{r["lower"]}–{r["upper"]} kg</div>
                    <div style="font-size:0.75em; margin-top:2px;">{r["badge"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
else:
    st.info("🌾 Run **Farm AI** first to see tomorrow's demand forecast here.")
    st.divider()

# ---------------------------------------------------------------------------
# Scatter Plot
# ---------------------------------------------------------------------------
st.subheader("Customer Segments (PCA)")

scaled_cols = [c for c in df_features.columns if c.endswith("_scaled")]
X = df_features[scaled_cols].values
from sklearn.decomposition import PCA
pca_2d = PCA(n_components=2)
X_pca = pca_2d.fit_transform(X)

df_plot = df_features.copy()
df_plot["cluster"] = result.labels
df_plot["pca_1"] = X_pca[:, 0]
df_plot["pca_2"] = X_pca[:, 1]

# Name segments for hover
cluster_names = {}
for profile in result.profiles:
    name, emoji, _ = name_segment(profile)
    cluster_names[profile.cluster_id] = f"{emoji} {name}"

df_plot["segment"] = df_plot["cluster"].map(cluster_names)

fig = px.scatter(
    df_plot,
    x="pca_1",
    y="pca_2",
    color="segment",
    hover_data={
        "pca_1": False,
        "pca_2": False,
        "segment": True,
        "customer_id": True,
        "avg_order_sgd": ":.2f",
        "purchase_frequency": ":.1f",
    },
    title=f"K={result.k} clusters · Silhouette={silhouette:.3f}",
)
fig.update_layout(
    height=500,
    legend_title_text="Segment",
    xaxis_title="PC1",
    yaxis_title="PC2",
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Segment Detail Table
# ---------------------------------------------------------------------------
st.subheader("Segment Detail")

farm = load_farm_output()
forecast = farm.get("forecast", {}) if farm else {}
crop_names_inv = {
    "kai_lan": "kai_lan", "baby spinach": "baby_spinach",
    "lettuce": "lettuce_mambo", "chye sim": "chye_sim",
    "arugula": "arugula", "pak choi": "pak_choi",
    "kale": "kale", "thai basil": "basil_thai",
    "coriander": "coriander", "mint": "mint",
}

table_rows = []
for profile in result.profiles:
    name, emoji, action = name_segment(profile)
    table_rows.append({
        "Segment": f"{emoji} {name}",
        "Size": profile.size,
        "Size %": f"{profile.size_pct:.1f}%",
        "Avg basket (SGD)": f"${profile.avg_basket_sgd:.2f}",
        "Bulk buyer %": f"{profile.bulk_buyer_pct:.0f}%",
        "Live commerce %": f"{profile.live_commerce_share*100:.0f}%",
        "Top crop": profile.dominant_crop,
        "Recommended action": action,
    })

# Annotate Top crop with Farm AI demand forecast
if forecast:
    for row in table_rows:
        top = row.get("Top crop", "")
        cid = crop_names_inv.get(top.lower(), top.lower().replace(" ", "_"))
        if cid in forecast:
            row["Top crop"] = f"{top} → {forecast[cid]['predicted_kg']:.1f} kg"

st.dataframe(
    pd.DataFrame(table_rows),
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------------------------
# Recommendation Cards
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Segment Action Plan")

# Re-build df with cluster labels for card rendering
df_card = df_features.copy()
df_card["cluster"] = result.labels

profile_map = {p.cluster_id: p for p in result.profiles}
card_profiles = [profile_map[i] for i in range(result.k)]

render_segment_cards(card_profiles, result.labels)

# ---------------------------------------------------------------------------
# Failure mode notices
# ---------------------------------------------------------------------------
if silhouette < 0.35:
    st.warning(
        "\u26a0\ufe0f Silhouette score is low ("
        f"{silhouette:.3f} < 0.35). "
        "Segments overlap significantly — interpret with caution."
    )

if len(set(result.labels)) == 1:
    st.warning(
        "\u26a0\ufe0f All customers fell into a single cluster. "
        "No natural segments found — try adding more features."
    )
