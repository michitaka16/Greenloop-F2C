"""K-Means customer segmentation with silhouette-guided K selection."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


@dataclass
class SegmentProfile:
    """Profiling output for a single cluster."""

    cluster_id: int
    size: int
    size_pct: float
    avg_frequency: float
    avg_basket_sgd: float
    avg_kg: float
    bulk_buyer_pct: float
    live_commerce_share: float
    crop_diversity: float
    dominant_crop: str
    organic_pct: float


@dataclass
class ClusteringResult:
    """Result of K-Means clustering."""

    labels: np.ndarray
    k: int
    silhouette: float
    inertia: float
    profiles: list[SegmentProfile]


_FEATURE_COLS = [
    "purchase_frequency",
    "avg_basket_sgd",
    "bulk_buyer",
    "live_commerce_share",
    "crop_diversity",
]
_SCALED_SUFFIX = "_scaled"
_SCALED_COLS = [f"{c}{_SCALED_SUFFIX}" for c in _FEATURE_COLS]


def cluster_customers(
    df: pd.DataFrame,
    k_range: range | None = None,
    random_state: int = 42,
) -> ClusteringResult:
    """Cluster customers using K-Means with silhouette-guided K selection.

    Parameters
    ----------
    df : pd.DataFrame
        Output of build_features() — must contain scaled feature columns.
    k_range : range, optional
        Range of K values to evaluate (default range(3, 6)).
    random_state : int
        Random seed for K-Means (default 42).

    Returns
    -------
    ClusteringResult
        Contains cluster labels, selected K, silhouette score, inertia,
        and per-cluster SegmentProfile objects.

    Raises
    ------
    ValueError
        If df has insufficient data or no scaled columns.
    """
    if k_range is None:
        k_range = range(3, 6)

    # Check for scaled columns
    scaled_cols = [c for c in df.columns if c.endswith(_SCALED_SUFFIX)]
    if not scaled_cols:
        raise ValueError(
            "DataFrame has no scaled feature columns. "
            "Run build_features() first."
        )

    X = df[scaled_cols].values
    n_samples = len(X)

    if n_samples < k_range.start * 2:
        raise ValueError(
            f"Only {n_samples} customers but k_range starts at {k_range.start}. "
            "Need at least 2×k samples."
        )

    # Silhouette-guided K selection
    silhouettes = {}
    inertias = {}
    models = {}

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X)
        silhouettes[k] = silhouette_score(X, labels)
        inertias[k] = km.inertia_
        models[k] = km

    # Pick k with highest silhouette; tie-break toward larger k
    best_k = max(k_range, key=lambda k: (silhouettes[k], k))
    best_silhouette = silhouettes[best_k]
    best_inertia = inertias[best_k]
    best_labels = models[best_k].labels_

    # Profile each cluster
    df_labeled = df.copy()
    df_labeled["_cluster"] = best_labels

    profiles = []
    total = len(df_labeled)
    all_crops = df["crop_id"].unique().tolist() if "crop_id" in df.columns else ["N/A"]

    for cluster_id in range(best_k):
        sub = df_labeled[df_labeled["_cluster"] == cluster_id]
        size = len(sub)
        size_pct = size / total * 100

        avg_frequency = sub["purchase_frequency"].mean()
        avg_basket = sub["avg_basket_sgd"].mean()
        avg_kg = sub["avg_kg"].mean() if "avg_kg" in sub.columns else 0.0
        bulk_pct = sub["bulk_buyer"].mean() * 100
        live_share = sub["live_commerce_share"].mean()
        crop_div = sub["crop_diversity"].mean()
        organic_pct = sub["organic_certified"].mean() * 100 if "organic_certified" in sub.columns else 0.0

        # Dominant crop from orders — aggregate per cluster
        if "crop_id" in sub.columns:
            dominant_crop = sub["crop_id"].mode().iloc[0] if len(sub) > 0 else "N/A"
        else:
            dominant_crop = "N/A"

        profiles.append(
            SegmentProfile(
                cluster_id=cluster_id,
                size=size,
                size_pct=size_pct,
                avg_frequency=avg_frequency,
                avg_basket_sgd=avg_basket,
                avg_kg=avg_kg,
                bulk_buyer_pct=bulk_pct,
                live_commerce_share=live_share,
                crop_diversity=crop_div,
                dominant_crop=dominant_crop,
                organic_pct=organic_pct,
            )
        )

    return ClusteringResult(
        labels=best_labels,
        k=best_k,
        silhouette=best_silhouette,
        inertia=best_inertia,
        profiles=profiles,
    )


def name_segment(profile: SegmentProfile) -> tuple[str, str, str]:
    """Assign a behavioural name and recommended action to a segment profile.

    Parameters
    ----------
    profile : SegmentProfile

    Returns
    -------
    tuple[str, str, str]
        (segment_name, emoji, recommended_action)
    """
    # Decision tree based on dominant behavioural signals
    if profile.organic_pct > 60 and profile.avg_frequency >= 6:
        return (
            "Organic Subscribers",
            "\U0001f33f",
            "Push subscription box with monthly organic bundle",
        )
    elif profile.bulk_buyer_pct > 40 and profile.avg_kg > 4:
        return (
            "Bulk Contract Buyers",
            "\U0001f4e6",
            "Offer quarterly volume contract with 10% discount",
        )
    elif profile.live_commerce_share > 0.45:
        return (
            "Live Commerce Hunters",
            "\U0001f4f1",
            "Pre-notify before live streams; offer exclusive drops",
        )
    elif profile.avg_frequency < 4 and profile.avg_basket_sgd < 35:
        return (
            "Casual Top-up",
            "\U0001f6d2",
            "Retargeting campaigns; 'You're almost out of kale' nudge",
        )
    else:
        return (
            "Regular Buyers",
            "\U0001f6d2",
            "Loyalty rewards; seasonal crop previews",
        )
