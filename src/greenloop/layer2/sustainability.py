"""Layer 2 — Sustainability KPI computation.

Computes environmental impact KPIs from the Layer 2 optimizer plan output:
water savings, CO2 reduction, food waste prevention, energy efficiency,
and off-peak energy ratio.
"""

from __future__ import annotations

import pandas as pd

from greenloop.utils.config import CROP_IDS, PEAK_HOURS

# Must match optimizer.py LED_KWH_PER_TIER_HOUR
_LED_KWH_PER_TIER_HOUR = 0.5

# Conventional farming benchmarks (per kg of produce)
_CONVENTIONAL_WATER_L_PER_KG = 20.0  # Singapore soil farming average
HYDROPONIC_WATER_L_PER_KG = 2.0  # GreenLoop hydroponics
_CONVENTIONAL_CO2_KG_PER_KG = 2.5  # vs conventional farming baseline


def compute_sustainability_kpis(
    plan: dict,
    forecast: dict,
    crops_df: pd.DataFrame,
) -> dict:
    """Compute sustainability KPIs from a Layer 2 optimizer plan.

    Parameters
    ----------
    plan : dict
        Output of ``build_and_solve()``.
    forecast : dict
        Layer 1 output: {crop_id: {predicted_kg, lower_ci, upper_ci}}.
    crops_df : pd.DataFrame
        Crop master data (must include water_per_tray, spoilage_rate columns).

    Returns
    -------
    dict
        Keys: water_saved_l, co2_avoided_kg, food_waste_prevented_kg,
        energy_efficiency_kwh_per_kg, off_peak_energy_ratio_pct,
        total_water_used_l, total_kwh, total_kg_produced,
        off_peak_kwh, peak_kwh.
    """
    led_schedule: dict[str, list[int]] = plan.get("led_schedule", {})
    rack_layout: dict[str, str] = plan.get("rack_layout", {})
    watering_schedule: dict[str, int] = plan.get("watering_schedule", {})

    # ── Water ───────────────────────────────────────────────────────────────
    total_water_used_l = _compute_water_used(rack_layout, watering_schedule, crops_df)
    conventional_water_l = total_water_used_l * (_CONVENTIONAL_WATER_L_PER_KG / HYDROPONIC_WATER_L_PER_KG)
    water_saved_l = conventional_water_l - total_water_used_l

    # ── CO2 ────────────────────────────────────────────────────────────────
    total_kg_produced = _compute_total_kg_produced(rack_layout, forecast, crops_df)
    co2_avoided_kg = total_kg_produced * (_CONVENTIONAL_CO2_KG_PER_KG - 0.3)

    # ── Food waste ─────────────────────────────────────────────────────────
    total_upper_ci = sum(v["upper_ci"] for v in forecast.values())
    food_waste_prevented_kg = total_upper_ci - total_kg_produced

    # ── Energy ─────────────────────────────────────────────────────────────
    total_kwh, off_peak_kwh, peak_kwh = _compute_energy_kwh(led_schedule)

    # Energy efficiency: kWh per kg produced
    energy_efficiency_kwh_per_kg = (
        total_kwh / total_kg_produced if total_kg_produced > 0 else 0.0
    )

    # Off-peak ratio
    off_peak_energy_ratio_pct = (
        (off_peak_kwh / total_kwh * 100) if total_kwh > 0 else 0.0
    )

    return {
        "water_saved_l": round(water_saved_l, 1),
        "co2_avoided_kg": round(co2_avoided_kg, 1),
        "food_waste_prevented_kg": round(food_waste_prevented_kg, 1),
        "energy_efficiency_kwh_per_kg": round(energy_efficiency_kwh_per_kg, 2),
        "off_peak_energy_ratio_pct": round(off_peak_energy_ratio_pct, 1),
        # Raw intermediates (used for weekly chart)
        "total_water_used_l": round(total_water_used_l, 1),
        "total_kwh": round(total_kwh, 2),
        "total_kg_produced": round(total_kg_produced, 1),
        "off_peak_kwh": round(off_peak_kwh, 2),
        "peak_kwh": round(peak_kwh, 2),
    }


def _compute_water_used(
    rack_layout: dict[str, str],
    watering_schedule: dict[str, int],
    crops_df: pd.DataFrame,
) -> float:
    """Total litres of nutrient solution used today."""
    water_lookup: dict[str, float] = dict(
        zip(crops_df["crop_id"], crops_df["water_per_tray"])
    )
    total = 0.0
    for tier_name, crop_id in rack_layout.items():
        water_per_tray = water_lookup.get(crop_id, 2.0)
        freq = watering_schedule.get(crop_id, 2)
        total += water_per_tray * freq
    return total


def _compute_total_kg_produced(
    rack_layout: dict[str, str],
    forecast: dict,
    crops_df: pd.DataFrame,
) -> float:
    """Total kg of produce planned (after spoilage)."""
    spoilage_lookup: dict[str, float] = dict(
        zip(crops_df["crop_id"], crops_df["spoilage_rate"])
    )
    # Count tiers per crop
    tiers_per_crop: dict[str, int] = {}
    for crop_id in rack_layout.values():
        tiers_per_crop[crop_id] = tiers_per_crop.get(crop_id, 0) + 1

    total = 0.0
    for crop_id, num_tiers in tiers_per_crop.items():
        upper_ci = forecast.get(crop_id, {}).get("upper_ci", 0.0)
        spoilage = spoilage_lookup.get(crop_id, 0.0)
        # Production = upper_ci * tiers_assigned / NUM_TIERS * (1 - spoilage)
        produced = upper_ci * (num_tiers / len(CROP_IDS)) * (1.0 - spoilage)
        total += produced
    return total


def _compute_energy_kwh(led_schedule: dict[str, list[int]]) -> tuple[float, float, float]:
    """Total, off-peak, and peak LED kWh from the LED schedule.

    Returns (total_kwh, off_peak_kwh, peak_kwh).
    """
    total_kwh = 0.0
    off_peak_kwh = 0.0
    peak_kwh = 0.0

    for schedule in led_schedule.values():
        for hour, led_on in enumerate(schedule):
            if led_on:
                kwh = _LED_KWH_PER_TIER_HOUR
                total_kwh += kwh
                if hour in PEAK_HOURS:
                    peak_kwh += kwh
                else:
                    off_peak_kwh += kwh

    return total_kwh, off_peak_kwh, peak_kwh


def compute_weekly_sustainability(
    plans: list[dict],
    forecasts: list[dict],
    crops_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute sustainability KPIs for each day in a list of (plan, forecast) pairs.

    Returns a DataFrame with one row per day and columns:
    date, water_saved_l, co2_avoided_kg, total_kwh, off_peak_pct.
    """
    rows = []
    for plan, forecast in zip(plans, forecasts, strict=True):
        kpis = compute_sustainability_kpis(plan, forecast, crops_df)
        rows.append({
            "date": plan.get("plan_date", "unknown"),
            "water_saved_l": kpis["water_saved_l"],
            "co2_avoided_kg": kpis["co2_avoided_kg"],
            "total_kwh": kpis["total_kwh"],
            "off_peak_pct": kpis["off_peak_energy_ratio_pct"],
        })
    return pd.DataFrame(rows)
