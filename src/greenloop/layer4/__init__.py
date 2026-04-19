"""Layer 4: Retail AI — Customer Behavioural Segmentation."""

from greenloop.layer4.features import get_feature_cols, get_scaled_cols, load_features
from greenloop.layer4.segmentation import (
    ClusteringResult,
    SegmentProfile,
    cluster_customers,
)
from greenloop.layer4.visualization import reduce_pca, reduce_umap

__all__ = [
    "load_features",
    "get_feature_cols",
    "get_scaled_cols",
    "cluster_customers",
    "SegmentProfile",
    "ClusteringResult",
    "reduce_umap",
    "reduce_pca",
]
