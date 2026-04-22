"""Profit confidence interval band computation.

Propagates Layer 1 XGBoost lower_ci/upper_ci quantile regression bounds
through the Layer 2 MILP revenue model to produce a profit range.

All three values use the same cost structure (electricity, labour, waste,
nutrient adjustment) — only the revenue side varies with the CI bound.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProfitBand:
    """Profit confidence interval band."""

    profit_expected: float  # midpoint / nominal plan (uses upper_ci)
    profit_low: float  # pessimistic bound (uses lower_ci)
    profit_high: float  # optimistic bound (uses upper_ci, same as expected)
    ci_width_pct: float  # (profit_high - profit_low) / abs(profit_expected) * 100


def compute_profit_band(
    forecast: dict[str, dict],
    cost_breakdown: dict[str, float],
    crop_prices: dict[str, float],
    crop_spoilage: dict[str, float],
    rack_assignment: dict[str, str],
    num_tiers: int = 10,
) -> ProfitBand:
    """Compute profit CI band from Layer 1 forecast CIs.

    Args:
        forecast: Layer 1 output {crop_id: {predicted_kg, lower_ci, upper_ci}}.
        cost_breakdown: MILP cost_breakdown dict with keys:
            revenue, electricity, labour, waste_penalty, nutrient_adjustment.
        crop_prices: {crop_id: price_sgd_per_kg}.
        crop_spoilage: {crop_id: spoilage_rate (0-1)}.
        rack_assignment: {rack_id: crop_id} MILP rack layout.
        num_tiers: Total number of racks (default 10).

    Returns:
        ProfitBand with expected / low / high profit estimates.
    """
    # Costs are fixed regardless of CI bound
    electricity = cost_breakdown.get("electricity", 0.0)
    labour = cost_breakdown.get("labour", 0.0)
    waste_penalty = cost_breakdown.get("waste_penalty", 0.0)
    nutrient_adj = cost_breakdown.get("nutrient_adjustment", 0.0)
    total_cost = electricity + labour + waste_penalty + nutrient_adj

    def revenue_for_ci(ci_key: str) -> float:
        """Sum revenue across racks using either lower_ci or upper_ci."""
        total = 0.0
        for rack_id, crop_id in rack_assignment.items():
            ci_val = forecast.get(crop_id, {}).get(ci_key, 0.0)
            price = crop_prices.get(crop_id, 0.0)
            spoilage = crop_spoilage.get(crop_id, 0.0)
            # Revenue per tier: ci * price * (1 - spoilage) * (1 / num_tiers)
            # Simplified: ci_val * price * (1 - spoilage) / num_tiers
            rev_per_rack = ci_val * price * (1.0 - spoilage) / num_tiers
            total += rev_per_rack
        return round(total, 2)

    rev_expected = revenue_for_ci("upper_ci")
    rev_low = revenue_for_ci("lower_ci")
    # Upper CI is the optimistic bound (more produce → more revenue)
    rev_high = rev_expected

    profit_expected = round(rev_expected - total_cost, 2)
    profit_low = round(rev_low - total_cost, 2)
    profit_high = round(rev_high - total_cost, 2)

    # CI width as percentage of expected profit
    if profit_expected != 0:
        ci_width_pct = round(abs(profit_high - profit_low) / abs(profit_expected) * 100, 1)
    else:
        ci_width_pct = 0.0

    return ProfitBand(
        profit_expected=profit_expected,
        profit_low=profit_low,
        profit_high=profit_high,
        ci_width_pct=ci_width_pct,
    )
