# GreenLoop Farm OS — User Guide

**Version:** 1.0 | **Last updated:** April 2026

---

## What is GreenLoop Farm OS?

GreenLoop Farm OS is an AI-powered vertical farm management dashboard that runs a 3-layer intelligent system to maximize profit while keeping crops healthy and operations within real-world constraints.

Think of it as a **copilot for your farm manager** — it looks at tomorrow's likely demand, works out the cheapest way to fulfil it, checks the health of your crops, and adjusts the climate controls automatically.

---

## The 3-Layer Architecture

Every time you load the dashboard, three AI systems run in sequence:

| Layer | What it does | Technology |
|---|---|---|
| **Layer 1** | Forecasts tomorrow's demand for each crop | XGBoost quantile regression |
| **Layer 2** | Builds the cheapest feasible daily plan | OR-Tools MILP optimizer |
| **Layer 1b** | Diagnoses crop health from rack photos | EfficientNet-B0 transfer learning |
| **Layer 3** | Adjusts temperature, humidity, CO₂ in real time | PPO reinforcement learning |

---

## Sidebar Controls

Before anything runs, you can configure two parameters:

### Electricity Tariff Date

Select which day's electricity prices to use. The optimizer needs to know when electricity is cheap vs expensive to decide when to run LEDs and pumps. Older dates are useful for replaying historical scenarios.

**Default:** most recent available date.

### Available Staff

How many workers are on shift tomorrow? The optimizer treats this as a hard constraint — if you say 3 staff, it will not produce a plan requiring 5.

**Range:** 1–10 workers. **Default:** 6.

---

## Layer 1 — Demand Forecast

The first thing the dashboard computes is a demand forecast for each of the 10 crops.

### What you see

- **Forecast table** (left column): each crop with predicted demand in kg, a lower and upper 90% confidence interval, and a buffer percentage
- **Bar chart with error bars**: the same data visualised with confidence intervals

### What the numbers mean

- **Predicted (kg)** — the most likely demand tomorrow, in kilograms
- **Lower CI / Upper CI** — the range the model is 90% confident the true demand falls within
- **Buffer ±%** — how much uncertainty the model sees; a wider range means the forecast is less certain

### Why it matters for Layer 2

The optimizer treats the **upper confidence interval** as the safe production target — it plans to grow enough to cover the upper bound, then absorbs any over-production as waste cost if demand turns out lower. Growing to the point estimate would leave you short 5% of the time.

---

## Layer 2 — Optimal Daily Plan

The heart of the system. Every time you load the page (or change the sidebar), Layer 2 runs a Mixed-Integer Linear Program (MILP) using Google OR-Tools to find the profit-maximising plan.

### What it decides

The optimizer makes all of the following decisions simultaneously:

| Decision | What it means |
|---|---|
| **Which crop goes in which rack** | Assignment of all 10 racks to crops |
| **When to run LEDs** | 24-hour binary on/off schedule per rack |
| **How much to water each crop** | Irrigation frequency (1–6 times/day) |
| **How many staff per shift** | Morning / afternoon / night shift allocation |
| **Room temperature target** | Single target °C for the day |
| **Harvest quantity** | How many kg to actually harvest per crop |

### What it balances

The optimizer maximises:

```
Revenue − Electricity cost − Labour cost − Waste cost
```

It respects hard constraints:
- **Staff headcount** — cannot exceed available workers
- **Delivery window** — 12 hours per day (reduced to 6h in Typhoon scenario)
- **Tank capacity** — total water demand cannot exceed the reservoir
- **Crop LED hours** — each crop needs a minimum number of LED hours per day
- **Labour per shift** — maximum 8 hours per worker per shift

### What you see

**KPI strip (top of page):**
- Profit (SGD) — the headline number
- Revenue (SGD)
- Energy cost (SGD)
- Labour cost (SGD)
- Solve time (ms) — how long the MILP took to solve

**Optimal Plan section:**
- Revenue and Profit metrics
- Temperature target
- LED schedule chart (24-hour bar chart, top 5 racks shown)
- Staff shift table
- Cost breakdown caption

**CV Diagnosis impact expander** (inside the Plan section):
- Number of racks diagnosed
- Count of nitrogen-low racks (+15% nutrient cost each)
- Count of water-stressed racks (+1× irrigation each)
- Count of low-confidence diagnoses (±50% wider uncertainty band)
- Per-rack detail table with growth stage, nutrition, yield multiplier, and nutrient impact

---

## Layer 1b — Crop Health Diagnosis

This panel diagnoses each rack's crop health using a computer vision model — without you needing to do anything. It runs automatically every time the plan is solved.

### What it detects

The model inspects a rack photo (or uses a simulated diagnosis in demo mode) and reports two things:

**Growth stage** (one of):
- 🌱 **Early** — crop just planted; yield multiplier ×0.60
- 🌿 **Mid** — growing well; yield multiplier ×0.90
- ✅ **Harvest Ready** — confirmed ready; yield multiplier ×1.00

**Nutrition status** (one of):
- ✅ **Normal** — healthy; no adjustments
- ⚠️ **Nitrogen Low** — leaves yellowing; optimizer adds +15% nutrient cost
- 💧 **Water Stress** — bronzing or wilt; optimizer increases irrigation frequency

### Upload your own rack photo

1. Scroll to the **Crop Health & Growth Diagnosis** panel
2. Click **Upload rack photo** and select a JPG or PNG
3. Choose which rack tier the photo corresponds to
4. The diagnosis card updates to show your specific crop's result

The diagnosis updates the plan in real time — if you mark a rack as nitrogen-low, the optimizer immediately factors in the extra nutrient cost.

### Confidence scores

Each diagnosis comes with a confidence percentage (e.g. 87%). If confidence drops below 70%, the optimizer widens the uncertainty band by 50% — it becomes more conservative rather than over-committing to a uncertain reading.

> **Note:** In demo mode (the default), diagnoses are simulated from realistic scenario tables. To use the real computer vision model, a model trained on real plant images (PlantVillage or PlantDoc dataset) needs to be placed at `models/layer1b_efficientnet_b0.pt`.

### What happens to the plan

Each diagnosis feeds directly into Layer 2 as adjustments:

| Diagnosis | Effect on the plan |
|---|---|
| Early growth | Yield estimate reduced to 60% |
| Mid growth | Yield estimate reduced to 90% |
| Harvest Ready | Full yield |
| Nitrogen Low | +15% nutrient cost added |
| Water Stress | +1 additional irrigation frequency |
| Low confidence (<70%) | Uncertainty band widened 50% |

---

## Layer 3 — RL Climate Control

The bottom-left panel shows live reinforcement learning inference. It is not connected to the plan by default — it simulates a PPO agent adjusting the farm's climate in real time.

### What it controls

The RL agent sets targets for:
- **Temperature** (°C)
- **Humidity** (%)
- **CO₂** (ppm)
- **Soil moisture**

### How to use it

Click **▶ Run 10 steps** to simulate 10 timesteps of the agent acting on the environment. The step counter, current sensor readings, and cumulative reward update live.

The **Temperature** and **Humidity** metrics show both the current value and the deviation from the target set by the agent.

### Agent types

- **PPO** — a trained agent, if `models/layer3_ppo_agent.pt` exists
- **Random** — random action fallback, if no trained agent is found

Both run against the same `HydroFarmEnv` gymnasium environment, so the comparison is fair.

---

## Scenario Testing — Typhoon Button

The **⚡ Typhoon Warning** button in the bottom-right panel re-runs Layer 2 under a disrupted scenario.

### What changes

When you press the button, the optimizer receives:
- **Delivery window reduced** from 12 hours → 6 hours
- **Electricity tariff adjusted** to reflect emergency grid pricing

The new plan is re-optimised from scratch and compared against the current plan side-by-side.

### What to look for

After pressing the button, look for:
- **Profit Change** — how much the typhoon costs the farm per day
- **Delivery Window** — should show 6 hours (down from 12h)
- **Solve Time** — should still be sub-second if the farm is well-configured

If the plan becomes **infeasible**, the dashboard will show an error explaining which constraint is blocking the plan (e.g. "Not enough staff to harvest in 6 hours").

---

## AI Narrative Brief

At the top of the right column, the **AI narrative brief** expander asks a configured language model to explain today's plan in plain English.

**Example output:**

> "Today the farm should focus on kale and baby spinach, which have the highest demand and the shortest growth windows. The optimizer is scheduling LED hours for racks 3–7 during off-peak night hours to minimise electricity cost. Thai basil shows low confidence in the demand forecast (±28%), so the plan carries a larger waste buffer for that crop."

### Setup

To enable this feature, add to your `.env` file:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

Supported providers: `openai`, `zai`, `minimax`. Any OpenAI-compatible endpoint works.

If no LLM is configured, the expander shows a setup hint instead of generating text.

---

## Design Decisions Panel

The sidebar includes a collapsible **Design Decisions** panel that surfaces the rationale behind every algorithmic choice made in the dashboard. This is included for VC pitch preparation — it gives judges direct evidence of *why* the system works the way it does, without needing to read the source code.

Each decision is expandable and covers:
- What was chosen and why
- What alternatives were rejected
- What trade-offs were made

---

## Understanding the Output Numbers

### Why does the plan sometimes show negative profit?

Negative profit means the optimizer has determined it is **cheaper to not produce** than to produce at a loss. This typically happens when:
- Electricity tariffs are very high
- Demand forecast is very low (not enough revenue to cover costs)
- Too few staff to operate efficiently

The optimizer will not produce a plan that loses money unless there is no feasible alternative (e.g. contractual obligations). If you see a negative-profit plan, try:
1. Increasing the staff headcount (more workers → more efficient harvesting)
2. Selecting a different electricity tariff date (cheaper off-peak day)
3. Reducing the demand buffer (lower upper CI → less over-production → less waste)

### What does solve time mean?

Solve time is how long the MILP solver took to find the optimal plan, measured in milliseconds. Sub-second solve times mean the optimizer can respond to changing conditions (like a typhoon warning) in real time. Solve times above 5 seconds may indicate the problem is approaching infeasibility.

### What is the waste penalty?

When the optimizer produces more of a crop than demand requires, the surplus is penalised in the objective function. The waste penalty is not a real cost — it signals to the optimizer that over-production hurts profit. The optimizer tries to produce as close to the upper confidence interval as possible without exceeding it.

---

## Troubleshooting

### Dashboard shows "No feasible plan"

This means Layer 2 could not find any plan that satisfies all constraints simultaneously.

**Try:**
1. Increase staff headcount (the most common cause)
2. Check if the electricity CSV has data for the selected date
3. Reduce the demand buffer by selecting a day with higher predicted demand
4. Read the binding constraint suggestion shown below the error message

### Typhoon button shows infeasible

The farm physically cannot operate within a 6-hour delivery window with current staffing. Options:
1. Increase staff headcount significantly before re-trying
2. Accept that typhoon scenarios require pre-positioning (a real operations decision, not a software one)

### CV diagnosis shows all "normal" in demo mode

This is expected — demo mode uses `RACK_SCENARIOS`, a fixed table that assigns realistic diagnoses to each tier. In a real deployment, diagnoses are produced by the EfficientNet model from actual rack photos.

### LLM narrative shows an error

If the AI narrative expander shows a red error:
- Check your `.env` has the correct `LLM_PROVIDER` and API key
- Make sure your API key has credits / is active
- Try `OPENAI_API_KEY=sk-test-...` format (some providers use different prefixes)

### Solve times are very long (>10 seconds)

This can happen when the optimizer explores many branch-and-bound nodes. Try:
1. Reducing the number of crops by using a filtered `crops.csv`
2. Restarting the dashboard (solver state can accumulate)

---

## File Reference

The dashboard reads from these files at startup:

| File | Purpose |
|---|---|
| `data/crops.csv` | Crop definitions (growth days, water, LED hours, price, spoilage) |
| `data/electricity.csv` | Hourly tariff rates by date |
| `data/staff.csv` | Worker availability, hourly rates |
| `data/shipments.csv` | Historical delivery data used for demand forecasting |
| `data/cv_training/manifest.json` | Image manifest for CV model training |
| `models/layer1b_efficientnet_b0.pt` | Trained CV diagnosis model (optional) |
| `models/xgboost/Models.json` | Trained XGBoost demand forecasting models |
| `.env` | API keys and provider configuration |
