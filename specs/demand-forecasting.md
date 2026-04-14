# Layer 1 — Demand Forecasting (XGBoost)

## Goal

Predict next-week production targets per crop with 90% confidence intervals.
CI values feed directly into Layer 2 as robust optimisation buffers.

## Model Architecture

### XGBoost Quantile Regression (3 models)

| Model | Quantile | Output | Purpose |
|-------|----------|--------|---------|
| Lower | 0.05 | lower_ci | Floor for Layer 2 minimum production |
| Median | 0.50 | predicted_kg | Point estimate for dashboard display |
| Upper | 0.95 | upper_ci | Ceiling for Layer 2 robust buffer |

Train 3 separate XGBRegressor instances with `objective='reg:quantile'` and
`quantile_alpha` set to 0.05, 0.50, 0.95 respectively.

### Why Not +/-1 Std (Dimension A Decision #2)

Standard deviation assumes symmetric, normal distribution of errors. Crop demand
is often skewed (kai lan has high variance, lettuce is stable). Quantile regression:
- Makes no distributional assumption
- Produces asymmetric intervals when data is asymmetric
- Directly answers "what's the 95th percentile demand?" without assuming normality
- High-variance crops automatically get wider buffers in the MILP

## Input Features

From simulated CSV seed files:

| Feature | Source | Type |
|---------|--------|------|
| Historical shipment volume (past 12 weeks, per crop) | shipments.csv | Lag features |
| Seasonality index (week-of-year) | Derived | Cyclical (sin/cos encoding) |
| Day-of-week pattern | Derived | Categorical / one-hot |
| Weather proxy (temperature, humidity) | sensors_sim.csv or generated | Continuous |
| Spot market price per crop | shipments.csv (price_sgd_per_kg) | Continuous |
| Public holiday flag (Singapore calendar) | Hardcoded list | Binary |

### Feature Engineering

```python
# Lag features (per crop)
for lag in [1, 2, 4, 8, 12]:  # weeks
    df[f'shipment_lag_{lag}w'] = df.groupby('crop_id')['kg_shipped'].shift(lag)

# Rolling statistics
df['shipment_rolling_4w_mean'] = df.groupby('crop_id')['kg_shipped'].transform(
    lambda x: x.rolling(4).mean()
)
df['shipment_rolling_4w_std'] = df.groupby('crop_id')['kg_shipped'].transform(
    lambda x: x.rolling(4).std()
)

# Cyclical encoding for week-of-year
df['week_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
df['week_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)
```

### Why XGBoost Over Linear Regression (Dimension A Decision #1)

- Handles nonlinear interactions (e.g., price x season effects) without explicit feature crosses
- Robust to outliers and missing values in simulated data
- Built-in feature importance for interpretability
- Native quantile regression support
- Linear regression assumes additive, linear feature effects — crop demand patterns are not linear

## Output Contract

```python
{
    "crop_id": "kai_lan",
    "predicted_kg": 120.5,
    "lower_ci": 85.2,      # 5th percentile
    "upper_ci": 168.3,     # 95th percentile
    "interval_width": 83.1, # upper - lower (buffer size for Layer 2)
    "feature_importance": {
        "shipment_lag_1w": 0.35,
        "price_sgd_per_kg": 0.22,
        "week_sin": 0.15,
        ...
    }
}
```

## Training Pipeline

1. Load shipments.csv, join with crops.csv for metadata
2. Generate lag features, rolling stats, calendar features
3. TimeSeriesSplit cross-validation (no data leakage — never train on future data)
4. Train 3 XGBRegressor models (q=0.05, 0.50, 0.95)
5. Evaluate: check that lower_ci < predicted_kg < upper_ci for all predictions
6. Check empirical coverage: ~90% of actuals should fall within [lower_ci, upper_ci]
7. Save models as pickled objects or XGBoost native format

## Simulated Data Requirements

shipments.csv must contain:
- At least 24 weeks of daily data (12 weeks for lag features + 12 for training)
- 5 crops: kai lan, baby spinach, lettuce (mambo), Japanese chye sim, arugula
- Realistic patterns: kai lan high variance, lettuce stable, seasonal trends
- Price variation: ±15% around mean per crop

## Edge Cases

- Quantile crossing: if lower_ci > predicted_kg (can happen with quantile regression),
  sort the outputs: lower_ci = min(q05, q50), predicted_kg = median(q05, q50, q95)
- Missing lag features for early weeks: fill with crop-level mean from available data
- All-zero shipment weeks (crop not in season): model should predict near-zero with
  narrow intervals
