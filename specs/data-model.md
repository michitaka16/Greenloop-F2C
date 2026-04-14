# Data Model — Simulated CSV Seed Files

## Overview

All data is simulated for the course demo. CSV files provide seed data for training
and demo scenarios. No database required — pandas DataFrames in memory.

## File Schemas

### crops.csv

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| crop_id | str | "kai_lan" | Unique identifier |
| name | str | "Kai Lan" | Display name |
| growth_days | int | 35 | Days from seed to harvest |
| optimal_temp | float | 22.0 | Optimal temperature (°C) |
| water_per_tray | float | 2.5 | Litres per watering cycle |
| led_hours_per_day | int | 16 | Optimal photoperiod |
| price_sgd_per_kg | float | 4.50 | Base market price |
| spoilage_rate | float | 0.05 | Fraction lost to spoilage per day post-harvest |

**Crops**: kai lan, baby spinach, lettuce (mambo), Japanese chye sim, arugula

### shipments.csv

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| date | date | 2025-10-15 | Shipment date |
| crop_id | str | "kai_lan" | FK to crops.csv |
| kg_shipped | float | 45.2 | Kilograms shipped |
| price_sgd_per_kg | float | 4.80 | Actual sale price (varies from base) |

**Requirements**:
- At least 24 weeks of daily data
- Kai lan: high variance (±30% week-to-week), seasonal peaks around CNY
- Lettuce: low variance (±10%), stable weekly pattern
- Baby spinach: medium variance, weather-sensitive
- Arugula: low volume, premium price, stable
- Chye sim: moderate variance, day-of-week pattern (weekends lower)

### electricity.csv

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| date | date | 2025-10-15 | Date |
| hour | int | 14 | Hour of day (0-23) |
| tariff_rate_sgd_per_kwh | float | 0.28 | SP Group tariff rate |

**Tariff structure** (simplified SP Group):
- Off-peak (22:00-08:00): SGD 0.18/kWh
- Peak (08:00-22:00): SGD 0.28/kWh

### staff.csv

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| staff_id | str | "S001" | Unique identifier |
| name | str | "Ahmad" | Display name |
| availability | str | "morning,afternoon" | Comma-separated shift availability |
| hourly_rate_sgd | float | 12.50 | Hourly wage |

**Staff pool**: 8-10 workers with varying availability and rates.
Shifts: morning (6am-2pm), afternoon (2pm-10pm), night (10pm-6am).

### sensors_sim.csv

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| timestamp | datetime | 2025-10-15T14:30:00 | 1-minute intervals |
| temp_c | float | 22.3 | Room temperature |
| humidity_pct | float | 68.5 | Relative humidity |
| co2_ppm | float | 412.0 | CO2 concentration |
| moisture_zone1 | float | 0.65 | Soil moisture (0-1 scale) |
| moisture_zone2 | float | 0.58 | Soil moisture zone 2 |
| moisture_zone3 | float | 0.71 | Soil moisture zone 3 |
| moisture_zone4 | float | 0.63 | Soil moisture zone 4 |

**Simulation patterns**:
- Temperature: 22°C baseline, ±3°C daily cycle (warmer afternoon), occasional spikes
- Humidity: 65% baseline, inversely correlated with temperature
- CO2: 400ppm baseline, drops during LED-on periods (photosynthesis)
- Moisture: decays linearly between watering events, jumps on watering

## Data Generation Script

A `generate_seed_data.py` script produces all 5 CSV files with:
- Reproducible random seed (np.random.seed(42))
- Realistic Singapore patterns (weather, holidays, tariffs)
- Configurable duration (default: 24 weeks)
- Correlated features (temperature affects both humidity and crop growth)

## No Database

For the course demo, all data lives in pandas DataFrames loaded from CSV at
Streamlit app startup. No PostgreSQL, no SQLite, no ORM. Keep it simple.
