"""UMAP and PCA dimensionality reduction for segmentation visualization."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

try:
    import umap
except ImportError:  # pragma: no cover
    umap = None  # type: ignore

_FEATURE_COLS = [
    "purchase_frequency",
    "avg_basket_sgd",
    "bulk_buyer",
    "live_commerce_share",
    "crop_diversity",
]
_SCALED_SUFFIX = "_scaled"
_SCALED_COLS = [f"{c}{_SCALED_SUFFIX}" for c in _FEATURE_COLS]


def reduce_umap(df: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    """Reduce to 2D using UMAP for visualization.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain scaled feature columns from build_features().
    random_state : int

    Returns
    -------
    pd.DataFrame
        Columns: customer_id, umap_1, umap_2
    """
    if umap is None:
        raise ImportError(
            "umap-learn is required for UMAP visualization. "
            "Install with: pip install umap-learn"
        )

    scaled_cols = [c for c in df.columns if c.endswith(_SCALED_SUFFIX)]
    X = df[scaled_cols].values

    reducer = umap.UMAP(
        n_components=2,
        random_state=random_state,
        n_neighbors=15,
        min_dist=0.1,
    )
    X_umap = reducer.fit_transform(X)

    result = pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "umap_1": X_umap[:, 0],
        "umap_2": X_umap[:, 1],
    })
    return result


def reduce_pca(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce to 2D using PCA (deterministic) for pitch slides.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain scaled feature columns from build_features().

    Returns
    -------
    pd.DataFrame
        Columns: customer_id, pca_1, pca_2
    """
    scaled_cols = [c for c in df.columns if c.endswith(_SCALED_SUFFIX)]
    X = df[scaled_cols].values

    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    result = pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "pca_1": X_pca[:, 0],
        "pca_2": X_pca[:, 1],
    })
    return result
