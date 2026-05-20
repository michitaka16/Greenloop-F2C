"""Layer 4: Retail AI — Customer Behavioural Segmentation.

Clusters Adopt a Kale's customer base into behavioural segments using K-Means.
Read-only analytics — does not modify any data files.
"""

import sys
from pathlib import Path

# Ensure adoptakale package is on path
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
from adoptakale.data.loader import load_customers, load_orders
from adoptakale.layer4.features import load_features
from adoptakale.layer4.segmentation import cluster_customers, name_segment
from adoptakale.layer4.visualization import reduce_pca, reduce_umap

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
            f"Bulk buyer: **{profile.bulk_pct * 100:.0f}%**  \n"
            f"Live commerce: **{profile.live_pct * 100:.0f}%**  \n"
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

table_rows = []
for profile in result.profiles:
    name, emoji, action = name_segment(profile)
    table_rows.append({
        "Segment": f"{emoji} {name}",
        "Size": profile.size,
        "Size %": f"{profile.size_pct:.1f}%",
        "Avg basket (SGD)": f"${profile.avg_basket_sgd:.2f}",
        "Bulk buyer %": f"{profile.bulk_pct * 100:.0f}%",
        "Live commerce %": f"{profile.live_pct * 100:.0f}%",
        "Top crop": profile.dominant_crop,
        "Recommended action": action,
    })

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
