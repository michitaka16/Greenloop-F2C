"""Generate simulated CSV seed files for GreenLoop Farm OS.

Produces 5 CSV files with realistic Singapore hydroponic farm patterns.
Reproducible via np.random.seed(42).
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
WEEKS = 30  # ~210 days ending ~2026-04-29
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def generate_crops() -> pd.DataFrame:
    """Generate crops.csv with 10 Singapore hydroponic crops.

    All 10 are commercially grown by SFA-licensed vertical farms in
    Singapore (Sustenir, SG Veg Farm, Archisen, VertiVegies, Sky Greens):
    5 leafy-green staples + 2 premium leafy + 3 herbs. All fit the
    21-35 day growth envelope, standard NFT/DWC racks, and require no
    pollination. Prices reflect wholesale SGD/kg in 2025-2026.
    """
    return pd.DataFrame([
        {
            "crop_id": "kai_lan",
            "name": "Kai Lan",
            "growth_days": 35,
            "optimal_temp": 22.0,
            "water_per_tray": 2.5,
            "led_hours_per_day": 16,
            "price_sgd_per_kg": 4.50,
            "spoilage_rate": 0.06,
        },
        {
            "crop_id": "baby_spinach",
            "name": "Baby Spinach",
            "growth_days": 25,
            "optimal_temp": 20.0,
            "water_per_tray": 2.0,
            "led_hours_per_day": 14,
            "price_sgd_per_kg": 6.00,
            "spoilage_rate": 0.08,
        },
        {
            "crop_id": "lettuce_mambo",
            "name": "Lettuce (Mambo)",
            "growth_days": 30,
            "optimal_temp": 21.0,
            "water_per_tray": 2.2,
            "led_hours_per_day": 14,
            "price_sgd_per_kg": 3.80,
            "spoilage_rate": 0.07,
        },
        {
            "crop_id": "chye_sim",
            "name": "Japanese Chye Sim",
            "growth_days": 28,
            "optimal_temp": 22.0,
            "water_per_tray": 2.3,
            "led_hours_per_day": 15,
            "price_sgd_per_kg": 4.00,
            "spoilage_rate": 0.05,
        },
        {
            "crop_id": "arugula",
            "name": "Arugula",
            "growth_days": 21,
            "optimal_temp": 19.0,
            "water_per_tray": 1.8,
            "led_hours_per_day": 12,
            "price_sgd_per_kg": 8.00,
            "spoilage_rate": 0.04,
        },
        # ── New: 2025-10 additions ────────────────────────────────
        {
            "crop_id": "pak_choi",
            "name": "Pak Choi",
            "growth_days": 25,
            "optimal_temp": 21.0,
            "water_per_tray": 2.1,
            "led_hours_per_day": 14,
            "price_sgd_per_kg": 3.50,
            "spoilage_rate": 0.07,
        },
        {
            "crop_id": "kale",
            "name": "Kale (Curly)",
            "growth_days": 35,
            "optimal_temp": 20.0,
            "water_per_tray": 2.0,
            "led_hours_per_day": 14,
            "price_sgd_per_kg": 9.50,
            "spoilage_rate": 0.05,
        },
        {
            "crop_id": "basil_thai",
            "name": "Thai Basil",
            "growth_days": 28,
            "optimal_temp": 24.0,
            "water_per_tray": 1.8,
            "led_hours_per_day": 14,
            "price_sgd_per_kg": 15.00,
            "spoilage_rate": 0.04,
        },
        {
            "crop_id": "coriander",
            "name": "Coriander",
            "growth_days": 28,
            "optimal_temp": 21.0,
            "water_per_tray": 1.9,
            "led_hours_per_day": 13,
            "price_sgd_per_kg": 12.00,
            "spoilage_rate": 0.06,
        },
        {
            "crop_id": "mint",
            "name": "Mint",
            "growth_days": 30,
            "optimal_temp": 22.0,
            "water_per_tray": 2.0,
            "led_hours_per_day": 13,
            "price_sgd_per_kg": 14.00,
            "spoilage_rate": 0.05,
        },
    ])


def generate_shipments(rng: np.random.Generator) -> pd.DataFrame:
    """Generate shipments.csv: 24 weeks of daily data per crop.

    Patterns:
    - Kai lan: high variance (±30%), seasonal peaks
    - Lettuce: low variance (±10%), stable weekly pattern
    - Baby spinach: medium variance, weather-sensitive
    - Arugula: low volume, premium price, stable
    - Chye sim: moderate variance, weekend dip
    """
    dates = pd.date_range("2025-10-01", periods=WEEKS * 7, freq="D")
    rows = []

    crop_params = {
        "kai_lan": {
            "base_kg": 45.0,
            "noise_std": 13.5,  # ±30%
            "price_base": 4.50,
            "price_noise": 0.70,
            "weekend_factor": 0.85,
            "seasonal_amp": 15.0,  # CNY-like peak around week 16-18
            "seasonal_peak_week": 17,
        },
        "baby_spinach": {
            "base_kg": 30.0,
            "noise_std": 7.5,  # ±25%
            "price_base": 6.00,
            "price_noise": 0.90,
            "weekend_factor": 0.90,
            "seasonal_amp": 5.0,
            "seasonal_peak_week": 10,
        },
        "lettuce_mambo": {
            "base_kg": 55.0,
            "noise_std": 5.5,  # ±10%
            "price_base": 3.80,
            "price_noise": 0.40,
            "weekend_factor": 0.95,
            "seasonal_amp": 3.0,
            "seasonal_peak_week": 12,
        },
        "chye_sim": {
            "base_kg": 35.0,
            "noise_std": 8.0,  # ±23%
            "price_base": 4.00,
            "price_noise": 0.50,
            "weekend_factor": 0.75,  # Strong weekend dip
            "seasonal_amp": 4.0,
            "seasonal_peak_week": 17,
        },
        "arugula": {
            "base_kg": 12.0,
            "noise_std": 2.0,  # ±17%
            "price_base": 8.00,
            "price_noise": 0.80,
            "weekend_factor": 0.92,
            "seasonal_amp": 1.5,
            "seasonal_peak_week": 8,
        },
        # ── New crops ─────────────────────────────────────────────────
        # pak_choi — highest-volume Chinese staple green. Price-sensitive,
        # moderate weekend dip (wet-market crowd on weekends offsets
        # supermarket dip).
        "pak_choi": {
            "base_kg": 60.0,
            "noise_std": 6.0,   # ±10%
            "price_base": 3.50,
            "price_noise": 0.35,
            "weekend_factor": 0.93,
            "seasonal_amp": 4.0,
            "seasonal_peak_week": 14,
        },
        # kale — premium, Sustenir's signature. Low volume, stable,
        # slight weekend bump (brunch cafes).
        "kale": {
            "base_kg": 18.0,
            "noise_std": 3.0,   # ±17%
            "price_base": 9.50,
            "price_noise": 0.90,
            "weekend_factor": 1.04,
            "seasonal_amp": 2.0,
            "seasonal_peak_week": 11,
        },
        # basil_thai — hawker + restaurant demand. Weekend demand higher
        # (dine-out volume). Very high margin.
        "basil_thai": {
            "base_kg": 10.0,
            "noise_std": 2.0,   # ±20%
            "price_base": 15.00,
            "price_noise": 1.40,
            "weekend_factor": 1.12,
            "seasonal_amp": 1.5,
            "seasonal_peak_week": 15,
        },
        # coriander — massive Singapore home-cooking + laksa/curry demand.
        # Mid-week supply peak to catch weekend cook-at-home prep.
        "coriander": {
            "base_kg": 14.0,
            "noise_std": 2.5,   # ±18%
            "price_base": 12.00,
            "price_noise": 1.10,
            "weekend_factor": 1.05,
            "seasonal_amp": 2.5,
            "seasonal_peak_week": 13,
        },
        # mint — drinks + dessert demand. Weekend bump (hawker drinks,
        # home mojitos). Seasonal peak in hot months.
        "mint": {
            "base_kg": 8.0,
            "noise_std": 1.6,   # ±20%
            "price_base": 14.00,
            "price_noise": 1.20,
            "weekend_factor": 1.08,
            "seasonal_amp": 2.0,
            "seasonal_peak_week": 6,
        },
    }

    for date in dates:
        day_of_week = date.dayofweek  # 0=Mon, 6=Sun
        week_num = (date - dates[0]).days // 7 + 1
        is_weekend = day_of_week >= 5

        for crop_id, params in crop_params.items():
            # Base demand + seasonal + noise
            seasonal = params["seasonal_amp"] * np.exp(
                -0.5 * ((week_num - params["seasonal_peak_week"]) / 3) ** 2
            )
            base = params["base_kg"] + seasonal
            noise = rng.normal(0, params["noise_std"])
            weekend_adj = params["weekend_factor"] if is_weekend else 1.0

            # Day-of-week pattern: slight mid-week peak
            dow_factor = 1.0 + 0.05 * np.sin(2 * np.pi * day_of_week / 7)

            kg_shipped = max(0.5, base * weekend_adj * dow_factor + noise)

            # Price with noise
            price = max(
                params["price_base"] * 0.7,
                params["price_base"] + rng.normal(0, params["price_noise"]),
            )

            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "crop_id": crop_id,
                "kg_shipped": round(kg_shipped, 1),
                "price_sgd_per_kg": round(price, 2),
            })

    return pd.DataFrame(rows)


def generate_electricity() -> pd.DataFrame:
    """Generate electricity.csv: 24 weeks of hourly SP Group tariffs."""
    dates = pd.date_range("2025-10-01", periods=WEEKS * 7, freq="D")
    rows = []

    for date in dates:
        for hour in range(24):
            # SP Group simplified: peak 8am-10pm, off-peak 10pm-8am
            is_peak = 8 <= hour < 22
            tariff = 0.28 if is_peak else 0.18
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "hour": hour,
                "tariff_rate_sgd_per_kwh": tariff,
            })

    return pd.DataFrame(rows)


def generate_staff() -> pd.DataFrame:
    """Generate staff.csv: 8 workers with varying availability, rates and roles."""
    return pd.DataFrame([
        {"staff_id": "S001", "name": "Ahmad",      "role": "Farm Operations", "availability": "morning,afternoon", "hourly_rate_sgd": 12.50},
        {"staff_id": "S002", "name": "Wei Lin",    "role": "Farm Operations", "availability": "morning,afternoon", "hourly_rate_sgd": 13.00},
        {"staff_id": "S003", "name": "Priya",      "role": "Farm Operations", "availability": "morning",       "hourly_rate_sgd": 14.00},
        {"staff_id": "S004", "name": "Jun Hao",    "role": "Supervisor",    "availability": "afternoon,night", "hourly_rate_sgd": 12.00},
        {"staff_id": "S005", "name": "Siti",       "role": "Logistics",     "availability": "morning,afternoon,night", "hourly_rate_sgd": 15.00},
        {"staff_id": "S006", "name": "Ravi",       "role": "Farm Operations", "availability": "night",        "hourly_rate_sgd": 16.00},
        {"staff_id": "S007", "name": "Mei Ying",   "role": "Farm Operations", "availability": "morning,afternoon", "hourly_rate_sgd": 11.50},
        {"staff_id": "S008", "name": "Ismail",     "role": "Logistics",     "availability": "afternoon,night", "hourly_rate_sgd": 13.50},
    ])


def generate_sensors(rng: np.random.Generator) -> pd.DataFrame:
    """Generate sensors_sim.csv: 1 day of minute-by-minute sensor readings.

    Patterns:
    - Temperature: 22°C baseline with daily cycle and noise
    - Humidity: 65% baseline, inversely correlated with temperature
    - CO2: 400ppm baseline, drops during LED-on hours (photosynthesis)
    - Moisture zones: decay between watering events, jump on watering
    """
    minutes = 1440  # 24 hours
    timestamps = pd.date_range("2025-10-15", periods=minutes, freq="min")

    # Temperature: 22°C ± 3°C daily cycle (peaks at 2pm = minute 840)
    hours = np.arange(minutes) / 60.0
    temp_cycle = 3.0 * np.sin(2 * np.pi * (hours - 6) / 24)  # Peak at 2pm
    temp = 22.0 + temp_cycle + rng.normal(0, 0.3, minutes)

    # Add occasional spikes (e.g., door opening)
    spike_times = rng.choice(minutes, size=3, replace=False)
    for t in spike_times:
        duration = min(15, minutes - t)
        temp[t : t + duration] += rng.uniform(2, 4)

    # Humidity: inversely correlated with temperature
    humidity = 65.0 - 2.0 * (temp - 22.0) + rng.normal(0, 1.5, minutes)
    humidity = np.clip(humidity, 40, 95)

    # CO2: drops during LED-on hours (6am-10pm = hours 6-22)
    co2 = np.full(minutes, 400.0)
    for i in range(minutes):
        hour = i / 60.0
        if 6 <= hour < 22:  # LED on → photosynthesis → CO2 drops
            co2[i] -= 80 * np.sin(np.pi * (hour - 6) / 16)
        co2[i] += rng.normal(0, 8)
    co2 = np.clip(co2, 250, 600)

    # Moisture zones: decay linearly, jump when watered
    watering_hours = [7, 12, 17, 21]  # 4x daily watering
    moisture_zones = []
    for _zone in range(1, 5):
        moisture = np.zeros(minutes)
        moisture[0] = 0.65 + rng.uniform(-0.05, 0.05)
        for i in range(1, minutes):
            hour = i / 60.0
            # Evaporation decay
            moisture[i] = moisture[i - 1] - 0.0003 + rng.normal(0, 0.002)
            # Watering events
            for wh in watering_hours:
                if abs(hour - wh) < 0.02:  # Within ~1 minute of watering
                    moisture[i] += 0.15 + rng.uniform(-0.02, 0.02)
            moisture[i] = np.clip(moisture[i], 0.1, 0.95)
        moisture_zones.append(np.round(moisture, 3))

    return pd.DataFrame({
        "timestamp": timestamps.strftime("%Y-%m-%dT%H:%M:%S"),
        "temp_c": np.round(temp, 1),
        "humidity_pct": np.round(humidity, 1),
        "co2_ppm": np.round(co2, 0).astype(int),
        "moisture_zone1": moisture_zones[0],
        "moisture_zone2": moisture_zones[1],
        "moisture_zone3": moisture_zones[2],
        "moisture_zone4": moisture_zones[3],
    })


def main():
    """Generate all seed data files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    crops = generate_crops()
    crops.to_csv(DATA_DIR / "crops.csv", index=False)
    print(f"crops.csv: {len(crops)} rows")

    shipments = generate_shipments(rng)
    shipments.to_csv(DATA_DIR / "shipments.csv", index=False)
    print(f"shipments.csv: {len(shipments)} rows")

    electricity = generate_electricity()
    electricity.to_csv(DATA_DIR / "electricity.csv", index=False)
    print(f"electricity.csv: {len(electricity)} rows")

    staff = generate_staff()
    staff.to_csv(DATA_DIR / "staff.csv", index=False)
    print(f"staff.csv: {len(staff)} rows")

    sensors = generate_sensors(rng)
    sensors.to_csv(DATA_DIR / "sensors_sim.csv", index=False)
    print(f"sensors_sim.csv: {len(sensors)} rows")

    print(f"\nAll files written to {DATA_DIR}/")


if __name__ == "__main__":
    main()
