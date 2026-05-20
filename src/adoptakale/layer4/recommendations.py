"""Per-segment crop recommendations for Layer 4 Retail AI."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Bundle name templates per segment type
_BUNDLE_TEMPLATES = {
    "Organic Subscribers": "Weekly Organic Box: {crops}",
    "Bulk Buyers": "Monthly Farm Contract: {crops}",
    "Live Commerce Fans": "Exclusive Live Drop: {crops}",
    "Casual Shoppers": "Starter Pack: {crops}",
}


@dataclass
class CropRecommendation:
    """Recommendation for a single segment."""

    segment_name: str
    top_crops: list[str]
    bundle_name: str
    recommended_action: str


def get_segment_recommendations(
    df_features: pd.DataFrame,
    orders: pd.DataFrame,
    result,  # ClusteringResult
) -> list[CropRecommendation]:
    """Compute top-3 crop recommendations per segment.

    Parameters
    ----------
    df_features : pd.DataFrame
        Customer features with cluster labels attached (df["_cluster"] = result.labels).
    orders : pd.DataFrame
        Order-level data with crop_id, customer_id.
    result : ClusteringResult
        Output of cluster_customers().

    Returns
    -------
    list[CropRecommendation]
        One entry per segment, ordered by cluster_id.
    """
    df_lab = df_features.copy()
    df_lab["_cluster"] = result.labels

    recommendations = []
    segment_map = {p.cluster_id: p for p in result.profiles}

    for cluster_id in range(result.k):
        profile = segment_map[cluster_id]
        segment_name = profile.segment_name

        # Customers in this cluster
        cids = df_lab[df_lab["_cluster"] == cluster_id]["customer_id"].tolist()

        # Orders from these customers
        seg_orders = orders[orders["customer_id"].isin(cids)]

        # Top 3 crops by order count
        if len(seg_orders) > 0:
            crop_counts = seg_orders["crop_id"].value_counts()
            top_3 = crop_counts.head(3).index.tolist()
        else:
            top_3 = ["spinach", "kai_lan", "arugula"]  # fallback

        # Bundle name
        template = _BUNDLE_TEMPLATES.get(segment_name, "Seasonal Pack: {crops}")
        bundle_name = template.format(crops=" + ".join(top_3))

        recommendations.append(
            CropRecommendation(
                segment_name=segment_name,
                top_crops=top_3,
                bundle_name=bundle_name,
                recommended_action=profile.recommended_action,
            )
        )

    return recommendations
