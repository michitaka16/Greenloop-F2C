# Layer 4: Retail AI — Customer Behavioural Segmentation

## Overview

Layer 4 is a read-only analytics page (`pages/2_retail.py`) that clusters GreenLoop's customer base into behavioural segments using K-Means. It does not affect Layer 1/2/3 outputs. It exists so the farm's sales team can prioritise outreach by segment.

---

## Data Model

### Input: `data/customers.csv`

| Column | Type | Description |
|---|---|---|
| `customer_id` | str | Primary key, e.g. `C001` |
| `name` | str | Display name |
| `customer_type` | str | `B2B` or `B2C` |
| `first_order_date` | date | First order date |
| `organic_certified` | bool | Customer only/mostly buys organic crops |
| `primary_channel` | str | `app`, `delivery`, `live` |

### Input: `data/orders.csv`

| Column | Type | Description |
|---|---|---|
| `order_id` | str | Primary key, e.g. `O001` |
| `customer_id` | str | FK to customers.csv |
| `date` | date | Order date |
| `crop_id` | str | Crop ordered |
| `kg` | float | Kilograms ordered |
| `sgd_total` | float | Total SGD value |
| `channel` | str | `app`, `delivery`, `live` |
| `is_live_commerce` | bool | Ordered during live stream |

---

## Feature Engineering

### Features

| Feature | Formula | Range |
|---|---|---|
| `purchase_frequency` | `n_orders / months_since_first_order` | [0, ∞) |
| `avg_order_sgd` | `mean(sgd_total) per customer` | [0, ∞) |
| `bulk_buyer` | `1 if mean(kg) > 5 else 0` | {0, 1} |
| `live_commerce_share` | `count(is_live_commerce=True) / n_orders` | [0, 1] |
| `crop_diversity` | `unique_crop_ids / 10` (normalised) | [0, 1] |

### Preprocessing

1. Drop customers with < 3 orders (not enough behavioural signal)
2. `StandardScaler` on all 5 features before clustering
3. K-Means with `n_init=10`, `random_state=42`

---

## Clustering Algorithm

### K-Means (selected)

- **Why K-Means over DBSCAN:** DBSCAN produces unclassifiable "noise" points — not actionable for a sales team
- **Why K-Means over Hierarchical:** O(n²) memory is prohibitive at 10K customers; K-Means is O(n)
- **Random state:** `random_state=42` — deterministic on fixed synthetic dataset

### K Selection

1. Compute silhouette score for `k ∈ {3, 4, 5}`
2. Select `k` with highest silhouette score
3. If `k=3` ties with `k=4`, prefer `k=4` (more actionable granularity)
4. If best silhouette < 0.35, display a warning in the UI — segments may not be actionable

### Cluster Profiling

For each cluster, compute:

```python
{
    "size": n_customers,
    "size_pct": n_customers / total * 100,
    "avg_frequency": mean(purchase_frequency),
    "avg_basket_sgd": mean(avg_order_sgd),
    "bulk_buyer_pct": mean(bulk_buyer) * 100,
    "live_commerce_share": mean(live_commerce_share),
    "dominant_crop": mode(top_crop),
}
```

---

## Segment Naming

Segments are named by the **dominant behavioural characteristic**. Names are paired with a recommended action.

| Segment Name | Key Behaviour | Recommended Action |
|---|---|---|
| **Organic Subscribers** | High frequency (8–12/month), organic crops, small regular baskets | Push subscription box with monthly organic bundle |
| **Bulk Contract Buyers** | Low frequency (1–3/month), large kg (>5kg/order), price-sensitive | Offer quarterly volume contract with 10% discount |
| **Live Commerce Hunters** | High `live_commerce_share` (>50%), medium frequency, novelty crops | Pre-notify before live streams; offer exclusive drops |
| **Casual Top-up** | Low frequency (1–4/month), small basket (<$30), single crop | Retargeting campaigns; "You're almost out of kale" nudge |

Naming logic is deterministic from cluster centroids (highest feature value wins).

---

## Visualisation

### UMAP Scatter Plot

- UMAP with `n_components=2`, `n_neighbors=15`, `min_dist=0.1`, `random_state=42`
- X/Y axes: UMAP1, UMAP2 (no interpretable meaning — just cluster geometry)
- Colour: cluster label
- Hover: customer name + segment name + avg basket SGD

### PCA (supplementary)

- PCA with `n_components=2` for comparison
- Used in pitch slides for deterministic reproducibility

### Elbow + Silhouette Validation Chart

- Inertia (K-Means) and silhouette score plotted for k ∈ {3, 4, 5}
- Used to justify K selection to a VC audience

---

## UI Components

### KPI Strip

Four metric cards showing for each segment:
- Segment name
- Size (% of total customers)
- Avg basket (SGD/month)
- Top crop

### Scatter Plot

Full-width UMAP scatter, coloured by cluster, with legend.

### Segment Detail Table

| Segment | Size | Avg basket (SGD) | Bulk buyer % | Live commerce % | Top crop | Recommended action |
|---|---|---|---|---|---|---|

### Recommendation Cards

One card per segment with:
- Segment name + emoji
- Size and avg basket
- Key behavioural facts (bulk buyer %, live commerce share)
- Recommended action in plain English

---

## Streamlit Page Layout

```
pages/2_retail.py
├── st.set_page_config(page_title="GreenLoop — Retail AI")
├── load data (customers.csv + orders.csv)
├── build features + scale
├── cluster with K-Means
├── profile segments
├── render UMAP scatter
├── render segment table
└── render recommendation cards
```

---

## Failure Modes

| Failure | Behaviour |
|---|---|
| `customers.csv` missing | Show error with setup instructions |
| `orders.csv` missing | Show error with setup instructions |
| < 10 customers | Show warning: "Not enough data to segment" |
| All customers in 1 cluster | Show warning: "No natural segments found — try adding more features" |
| Silhouette < 0.35 | Show warning: "Segments overlap — interpret with caution" |
| UMAP computation fails | Fall back to PCA scatter plot with note |

---

## Constraints

- **Read-only:** Layer 4 does not modify any data files
- **Simulated data only:** No real PII; all customer data is synthetic
- **No new API keys:** Only uses `sklearn`, `umap-learn`, `pandas`, `numpy`
- **Sub-3-second load:** UMAP on 500 customers must complete in < 3s
