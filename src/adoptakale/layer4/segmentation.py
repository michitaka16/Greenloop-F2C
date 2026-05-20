"""K-Means customer segmentation with segment naming per spec."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from adoptakale.layer4.features import get_scaled_cols


@dataclass
class SegmentProfile:
    """Profiling output for a single cluster."""

    cluster_id: int
    size: int
    size_pct: float
    avg_frequency: float
    avg_basket_sgd: float
    organic_pct: float
    bulk_pct: float
    live_pct: float
    dominant_crop: str
    segment_name: str
    recommended_action: str


@dataclass
class ClusteringResult:
    """Result of K-Means clustering."""

    labels: np.ndarray
    k: int
    silhouette: float
    inertia: float
    profiles: list[SegmentProfile]


# Spec segment naming rules
_SEGMENT_RULES = [
    # (name, emoji, action, condition_fn)
    # condition_fn returns True if this segment's centroid matches the rule
    (
        "Organic Subscribers",
        "\U0001f33f",
        "Push subscription box with monthly organic bundle",
        lambda p: p.organic_pct > 60 and p.avg_frequency >= 6,
    ),
    (
        "Bulk Buyers",
        "\U0001f4e6",
        "Offer quarterly volume contract with 10% discount",
        lambda p: p.bulk_pct > 40 and p.avg_basket_sgd > 60,
    ),
    (
        "Live Commerce Fans",
        "\U0001f4f1",
        "Pre-notify before live streams; offer exclusive crop drops",
        lambda p: p.live_pct > 45,
    ),
    (
        "Casual Shoppers",
        "\U0001f6d2",
        "Retargeting campaigns; 'You're almost out of spinach' nudge",
        lambda p: p.avg_frequency < 5 and p.avg_basket_sgd < 35,
    ),
]


def name_segment(profile: SegmentProfile) -> tuple[str, str, str]:
    """Apply spec naming rules to a SegmentProfile."""
    for name, emoji, action, condition in _SEGMENT_RULES:
        if condition(profile):
            return name, emoji, action
    # Fallback: name by highest metric
    vals = {
        "organic": profile.organic_pct,
        "bulk": profile.bulk_pct,
        "live": profile.live_pct,
    }
    fallback_name = max(vals, key=vals.get)
    return (
        f"{fallback_name.title()} Buyers",
        "\U0001f6d2",
        "Seasonal crop previews and loyalty rewards",
    )


def cluster_customers(
    df: pd.DataFrame,
    k: int | None = None,
    k_range: range | None = None,
    random_state: int = 42,
) -> ClusteringResult:
    """Cluster customers using K-Means.

    Parameters
    ----------
    df : pd.DataFrame
        Output of load_features() — must contain scaled feature columns.
    k : int, optional
        Fixed number of clusters. If None, use silhouette-guided selection
        from k_range.
    k_range : range, optional
        Candidates for silhouette-guided selection. Default range(3, 7).
    random_state : int

    Returns
    -------
    ClusteringResult
        labels, selected k, silhouette score, inertia, per-cluster profiles.
    """
    if k_range is None:
        k_range = range(3, 7)
    if k is not None:
        k_range = range(k, k + 1)

    scaled_cols = get_scaled_cols()
    if not all(c in df.columns for c in scaled_cols):
        raise ValueError(
            f"DataFrame missing scaled feature columns. "
            f"Expected {scaled_cols}, got {list(df.columns)}"
        )

    X = df[scaled_cols].values
    n = len(X)

    if n < 3:
        raise ValueError(f"Need at least 3 customers, got {n}")

    # Silhouette-guided K selection
    silhouettes = {}
    inertias = {}
    models = {}

    for _k in k_range:
        km = KMeans(n_clusters=_k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X)
        silhouettes[_k] = silhouette_score(X, labels)
        inertias[_k] = km.inertia_
        models[_k] = km

    best_k = max(k_range, key=lambda _k: silhouettes[_k])
    best_sil = silhouettes[best_k]
    best_labels = models[best_k].labels_

    # Profile each cluster
    df_lab = df.copy()
    df_lab["_cluster"] = best_labels

    profiles = []
    total = len(df_lab)

    for cid in range(best_k):
        sub = df_lab[df_lab["_cluster"] == cid]
        size = len(sub)
        size_pct = size / total * 100
        avg_freq = sub["purchase_frequency"].mean()
        avg_basket = sub["avg_order_sgd"].mean()
        organic_pct = sub["organic_preference"].mean() * 100
        bulk_pct = sub["bulk_buyer"].mean() * 100
        live_pct = sub["live_commerce_active"].mean() * 100
        dominant_crop = sub["top_crop"].mode().iloc[0] if len(sub) > 0 else "N/A"

        profile = SegmentProfile(
            cluster_id=cid,
            size=size,
            size_pct=size_pct,
            avg_frequency=avg_freq,
            avg_basket_sgd=avg_basket,
            organic_pct=organic_pct,
            bulk_pct=bulk_pct,
            live_pct=live_pct,
            dominant_crop=dominant_crop,
            segment_name="",  # filled below
            recommended_action="",
        )
        name, emoji, action = name_segment(profile)
        profile.segment_name = name
        profile.recommended_action = action
        profiles.append(profile)

    return ClusteringResult(
        labels=best_labels,
        k=best_k,
        silhouette=best_sil,
        inertia=inertias[best_k],
        profiles=profiles,
    )
