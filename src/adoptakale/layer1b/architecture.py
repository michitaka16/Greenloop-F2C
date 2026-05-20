"""Dual-head EfficientNet-B0 classifier for crop diagnosis.

Architecture: EfficientNet-B0 backbone + shared GAP + Dropout → two Dense heads
- Head A: growth_stage ∈ {early, mid, harvest_ready}
- Head B: nutrition_status ∈ {nitrogen_low, water_stress, normal}
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import torch
import torch.nn as nn
import timm


GROWTH_LABELS = ["early", "mid", "harvest_ready"]
NUTRITION_LABELS = ["nitrogen_low", "water_stress", "normal"]


@dataclass
class DiagnosisResult:
    """Result of a rack diagnosis from the dual-head classifier."""

    rack_id: str
    growth_stage: Literal["early", "mid", "harvest_ready"]
    growth_confidence: float
    growth_probs: list[float]
    nutrition_status: Literal["nitrogen_low", "water_stress", "normal"]
    nutrition_confidence: float
    nutrition_probs: list[float]
    is_simulated: bool = False
    is_ood: bool = False  # Out-of-distribution: non-plant image detected

    def to_milp_dict(self) -> dict:
        """Convert to dict for MILP integration."""
        return {
            "rack_id": self.rack_id,
            "growth_stage": self.growth_stage,
            "growth_confidence": self.growth_confidence,
            "growth_probs": self.growth_probs,
            "nutrition_status": self.nutrition_status,
            "nutrition_confidence": self.nutrition_confidence,
            "nutrition_probs": self.nutrition_probs,
        }


class DualHeadClassifier(nn.Module):
    """EfficientNet-B0 backbone with two classification heads.

    Shared feature extraction with independent task heads for:
    - growth_stage: 3-class classification
    - nutrition_status: 3-class classification
    """

    def __init__(
        self,
        *,
        num_classes_growth: int = 3,
        num_classes_nutrition: int = 3,
        pretrained: bool = True,
    ) -> None:
        super().__init__()
        # Load EfficientNet-B0 backbone (feature extractor only — no classifier head)
        self.backbone = timm.create_model(
            "efficientnet_b0",
            pretrained=pretrained,
            num_classes=0,  # Remove classifier — we add our own heads
            global_pool="avg",
        )
        backbone_out = self.backbone.num_features  # 1280 for EfficientNet-B0

        # Shared head: GAP → Dropout → Dense(256) → ReLU → Dropout(0.2)
        self.shared = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(backbone_out, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
        )

        # Task-specific heads
        self.head_growth = nn.Linear(256, num_classes_growth)
        self.head_nutrition = nn.Linear(256, num_classes_nutrition)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.

        Args:
            x: Input tensor of shape (B, 3, 224, 224)

        Returns:
            Tuple of (growth_logits, nutrition_logits, growth_probs, nutrition_probs)
        """
        features = self.backbone(x)  # (B, 1280)
        shared = self.shared(features)  # (B, 256)

        growth_logits = self.head_growth(shared)  # (B, 3)
        nutrition_logits = self.head_nutrition(shared)  # (B, 3)

        growth_probs = torch.softmax(growth_logits, dim=-1)
        nutrition_probs = torch.softmax(nutrition_logits, dim=-1)

        return growth_logits, nutrition_logits, growth_probs, nutrition_probs

    @torch.no_grad()
    def predict(self, x: torch.Tensor) -> DiagnosisResult:
        """Single-image prediction returning a DiagnosisResult dataclass.

        Args:
            x: Input tensor of shape (1, 3, 224, 224)

        Returns:
            DiagnosisResult with predicted labels, confidences, and full distributions
        """
        growth_logits, nutrition_logits, growth_probs, nutrition_probs = self(x)

        growth_idx = growth_probs.argmax(dim=-1).item()
        nutrition_idx = nutrition_probs.argmax(dim=-1).item()

        return DiagnosisResult(
            rack_id="unknown",
            growth_stage=GROWTH_LABELS[growth_idx],
            growth_confidence=growth_probs[0, growth_idx].item(),
            growth_probs=growth_probs[0].tolist(),
            nutrition_status=NUTRITION_LABELS[nutrition_idx],
            nutrition_confidence=nutrition_probs[0, nutrition_idx].item(),
            nutrition_probs=nutrition_probs[0].tolist(),
        )


def build_dual_head_model(pretrained: bool = True) -> DualHeadClassifier:
    """Factory function to build a DualHeadClassifier."""
    return DualHeadClassifier(pretrained=pretrained)


# ---------------------------------------------------------------------------
# Out-of-distribution (OOD) detection via feature-norm heuristic
# ---------------------------------------------------------------------------

# ImageNet feature norm statistics (approximate per-class mean + std)
# A crop rack image under LED lights has different norm than ImageNet photos.
OOD_FEATURE_NORM_THRESHOLD = 8.0  # Empirical: real ImageNet images have mean norm ~10-15


def compute_feature_norm(img_tensor: torch.Tensor, pretrained: bool = True) -> float:
    """Compute L2 norm of the GAP feature vector.

    Used as a simple OOD heuristic: ImageNet pretrained features on
    non-plant images (e.g., faces, text) tend to have different magnitude.
    """
    backbone = timm.create_model("efficientnet_b0", pretrained=pretrained, num_classes=0, global_pool="avg")
    backbone.eval()
    with torch.no_grad():
        features = backbone(img_tensor)  # (1, 1280)
    return float(features.norm(dim=-1).item())


def is_ood_by_feature_norm(img_tensor: torch.Tensor, threshold: float = OOD_FEATURE_NORM_THRESHOLD) -> bool:
    """Heuristic OOD detection based on feature norm.

    Returns True if the image's feature norm is below threshold,
    suggesting it may be out-of-distribution (non-plant image).
    """
    norm = compute_feature_norm(img_tensor)
    return norm < threshold
