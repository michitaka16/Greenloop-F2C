"""Unit tests for Layer 2 sustainability KPI computation."""

import pandas as pd
import pytest

from adoptakale.layer2.sustainability import (
    compute_sustainability_kpis,
    compute_weekly_sustainability,
)
from adoptakale.utils.config import CROP_IDS, PEAK_HOURS


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def crops_df():
    """Minimal crops DataFrame covering the crops referenced in plan fixtures."""
    return pd.DataFrame({
        "crop_id": CROP_IDS,
        "water_per_tray": [2.0] * len(CROP_IDS),
        "spoilage_rate": [0.05] * len(CROP_IDS),
    })


@pytest.fixture
def plan_full(crops_df):
    """A plan with known LED schedule, rack layout, and watering."""
    rack_layout = {f"tier_{i}": CROP_IDS[i % len(CROP_IDS)] for i in range(10)}
    led_schedule = {}
    for tier in rack_layout:
        schedule = [0] * 24
        # LEDs on from 6am-10pm (6..21)
        for h in range(6, 22):
            schedule[h] = 1
        led_schedule[tier] = schedule
    watering_schedule = {cid: 2 for cid in CROP_IDS}
    return {
        "led_schedule": led_schedule,
        "rack_layout": rack_layout,
        "watering_schedule": watering_schedule,
        "plan_date": "2025-10-15",
    }


@pytest.fixture
def forecast():
    """Synthetic forecast for every crop in CROP_IDS."""
    return {
        cid: {"predicted_kg": 80.0, "lower_ci": 65.0, "upper_ci": 100.0}
        for cid in CROP_IDS
    }


# ─── Water Savings ───────────────────────────────────────────────────────────

def test_water_savings_formula(plan_full, forecast, crops_df):
    """Hydroponics uses 95% less water than conventional — formula: total * (20/2 - 1)."""
    kpis = compute_sustainability_kpis(plan_full, forecast, crops_df)

    # Compute expected: total_water_used * (20/2 - 1) = total_water_used * 9
    rack_layout = plan_full["rack_layout"]
    watering_schedule = plan_full["watering_schedule"]
    expected_total = sum(
        crops_df.set_index("crop_id").loc[crop_id, "water_per_tray"]
        * watering_schedule.get(crop_id, 2)
        for crop_id in rack_layout.values()
    )
    expected_saved = expected_total * (20 / 2 - 1)  # 9x multiplier

    assert kpis["water_saved_l"] == pytest.approx(round(expected_saved, 1))


# ─── CO2 Reduction ───────────────────────────────────────────────────────────

def test_co2_reduction_formula(plan_full, forecast, crops_df):
    """CO2 avoided = total_kg_produced * (2.5 - 0.3) = total_kg * 2.2."""
    kpis = compute_sustainability_kpis(plan_full, forecast, crops_df)

    # Compute expected total_kg_produced
    tiers_per_crop = {}
    for crop_id in plan_full["rack_layout"].values():
        tiers_per_crop[crop_id] = tiers_per_crop.get(crop_id, 0) + 1

    expected_kg = sum(
        forecast[crop_id]["upper_ci"]
        * (num_tiers / len(CROP_IDS))
        * (1.0 - crops_df.set_index("crop_id").loc[crop_id, "spoilage_rate"])
        for crop_id, num_tiers in tiers_per_crop.items()
    )
    expected_co2 = expected_kg * (2.5 - 0.3)

    assert kpis["co2_avoided_kg"] == pytest.approx(round(expected_co2, 1))


# ─── Food Waste ───────────────────────────────────────────────────────────────

def test_food_waste_prevented_formula(plan_full, forecast, crops_df):
    """Food waste = upper_ci_sum - actual_production (negative = perfect fit)."""
    kpis = compute_sustainability_kpis(plan_full, forecast, crops_df)

    total_upper_ci = sum(v["upper_ci"] for v in forecast.values())

    # Production calculation matches the function
    tiers_per_crop = {}
    for crop_id in plan_full["rack_layout"].values():
        tiers_per_crop[crop_id] = tiers_per_crop.get(crop_id, 0) + 1

    total_produced = sum(
        forecast[crop_id]["upper_ci"]
        * (num_tiers / len(CROP_IDS))
        * (1.0 - crops_df.set_index("crop_id").loc[crop_id, "spoilage_rate"])
        for crop_id, num_tiers in tiers_per_crop.items()
    )

    expected_waste = total_upper_ci - total_produced
    assert kpis["food_waste_prevented_kg"] == pytest.approx(round(expected_waste, 1))


# ─── Energy Efficiency ────────────────────────────────────────────────────────

def test_energy_efficiency_kwh_per_kg(plan_full, forecast, crops_df):
    """Energy efficiency = total_kwh / total_kg_produced."""
    kpis = compute_sustainability_kpis(plan_full, forecast, crops_df)

    # LED is on 16 hours (6am-10pm), 10 tiers, 0.5 kWh/tier/hour
    # = 10 * 16 * 0.5 = 80 kWh
    led_kwh = sum(
        sum(schedule) * 0.5
        for schedule in plan_full["led_schedule"].values()
    )

    tiers_per_crop = {}
    for crop_id in plan_full["rack_layout"].values():
        tiers_per_crop[crop_id] = tiers_per_crop.get(crop_id, 0) + 1

    total_produced = sum(
        forecast[crop_id]["upper_ci"]
        * (num_tiers / len(CROP_IDS))
        * (1.0 - crops_df.set_index("crop_id").loc[crop_id, "spoilage_rate"])
        for crop_id, num_tiers in tiers_per_crop.items()
    )

    expected_eff = led_kwh / total_produced if total_produced > 0 else 0.0
    assert kpis["energy_efficiency_kwh_per_kg"] == pytest.approx(round(expected_eff, 2))


# ─── Off-Peak Energy Ratio ───────────────────────────────────────────────────

def test_off_peak_energy_ratio(plan_full, forecast, crops_df):
    """Off-peak ratio = off_peak_kwh / total_kwh * 100."""
    kpis = compute_sustainability_kpis(plan_full, forecast, crops_df)

    total_kwh = sum(sum(s) * 0.5 for s in plan_full["led_schedule"].values())
    # Off-peak hours: 0-7 and 22-23 (8 hours off-peak, 16 hours peak for this schedule)
    off_peak_kwh = sum(
        sum(1 for h, on in enumerate(s) if on and h not in PEAK_HOURS) * 0.5
        for s in plan_full["led_schedule"].values()
    )

    expected_ratio = (off_peak_kwh / total_kwh * 100) if total_kwh > 0 else 0.0
    assert kpis["off_peak_energy_ratio_pct"] == pytest.approx(round(expected_ratio, 1))


# ─── Edge Case: Zero Production ─────────────────────────────────────────────

def test_zero_production_edge_case(forecast, crops_df):
    """Division by zero must not raise — zero production yields zero savings."""
    plan_zero = {
        "led_schedule": {},       # No LEDs = no energy
        "rack_layout": {},        # No tiers = no production
        "watering_schedule": {},
        "plan_date": "2025-10-15",
    }

    kpis = compute_sustainability_kpis(plan_zero, forecast, crops_df)

    assert kpis["water_saved_l"] == 0.0
    assert kpis["co2_avoided_kg"] == 0.0
    assert kpis["food_waste_prevented_kg"] == pytest.approx(
        sum(v["upper_ci"] for v in forecast.values())
    )
    assert kpis["energy_efficiency_kwh_per_kg"] == 0.0
    assert kpis["off_peak_energy_ratio_pct"] == 0.0


# ─── Weekly Aggregation ───────────────────────────────────────────────────────

def test_compute_weekly_sustainability(plan_full, forecast, crops_df):
    """Weekly aggregation returns one row per (plan, forecast) pair."""
    plans = [plan_full, plan_full]
    forecasts = [forecast, forecast]

    result = compute_weekly_sustainability(plans, forecasts, crops_df)

    assert len(result) == 2
    assert set(result.columns) == {"date", "water_saved_l", "co2_avoided_kg", "total_kwh", "off_peak_pct"}
    assert result["date"].iloc[0] == "2025-10-15"
