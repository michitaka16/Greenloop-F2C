"""ObjectiveWeights dataclass and mode presets for Layer 2 HITL control."""

from __future__ import annotations

from dataclasses import dataclass, field

from adoptakale.utils.config import CROP_IDS


@dataclass
class ObjectiveWeights:
    """Explicit objective function weights for HITL control.

    Weights multiply each term in the MILP objective function.
    Defaults (balanced mode) are all 1.0 — no change to existing behavior.

    Attributes
    ----------
    revenue : float
        Multiplier on the revenue term. Higher = optimizer prioritises revenue.
    electricity : float
        Multiplier on the electricity cost term. Higher = optimizer minimises energy.
    labour : float
        Multiplier on the labour cost term. Higher = optimizer minimises staffing.
    waste : float
        Multiplier on the waste penalty term. Higher = optimizer minimises spoilage.
    balance : float
        Multiplier on the workload-balance penalty term. Higher = optimizer
        prefers even shift distribution.
    sustainability : float
        Bonus applied for off-peak energy usage (added to objective, not multiplied).
        Higher = stronger preference for nighttime LED operation.
    crop_weights : dict[str, float]
        Per-crop revenue multiplier. Key = crop_id, value = weight [0.0, 2.0].

    Examples
    --------
    >>> weights = ObjectiveWeights.from_mode("profit")
    >>> weights = ObjectiveWeights(revenue=1.5, electricity=0.8, sustainability=0.5)
    """

    revenue: float = 1.0
    electricity: float = 1.0
    labour: float = 1.0
    waste: float = 1.0
    balance: float = 1.0
    sustainability: float = 0.0
    crop_weights: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.crop_weights:
            self.crop_weights = {cid: 1.0 for cid in CROP_IDS}

    @classmethod
    def from_mode(cls, mode: str) -> "ObjectiveWeights":
        """Factory for the three preset HITL modes.

        Parameters
        ----------
        mode : str
            One of "profit", "sustainability", or "balanced".

        Returns
        -------
        ObjectiveWeights
            Pre-configured weight set for the given mode.
        """
        presets = {
            "profit": cls(
                revenue=1.5,
                electricity=1.0,
                labour=1.0,
                waste=0.8,
                balance=0.5,
                sustainability=0.3,
            ),
            "sustainability": cls(
                revenue=1.0,
                electricity=0.5,
                labour=0.8,
                waste=1.5,
                balance=1.5,
                sustainability=2.0,
            ),
            "balanced": cls(
                revenue=1.0,
                electricity=1.0,
                labour=1.0,
                waste=1.0,
                balance=1.0,
                sustainability=1.0,
            ),
        }
        return presets.get(mode, presets["balanced"])


#: Convenience reference for dashboard wiring.
MODE_OPTIONS = ["profit", "sustainability", "balanced"]
MODE_LABELS = {
    "profit": "Profit",
    "sustainability": "Sustainability",
    "balanced": "Balanced",
}
