# Adopt a Kale — Current State Report

**Generated:** 2026-05-19
**Repository:** `Greenloop-F2C` (legacy slug) · `main` branch
**Brand:** Adopt a Kale (formerly GreenLoop F2C)

---

## 1. Repository Overview

Adopt a Kale is a 5-layer AI platform (6 ML techniques) for Singapore vertical hydroponic farming. It is built as a multi-page Streamlit application: a B2B Farm OS dashboard with 4 pages (Farm AI, Logistics, Retail AI, Media AI) and a B2C consumer app (`consumer_app/`) with 9 pages branded *Adopt a Kale*. Both share a common data layer. The project is a Python 3.11–3.13 application.

### Project Metadata

| Field | Value |
|-------|-------|
| Name | `adopt-a-kale` |
| Version | `0.1.0` |
| Python | `>=3.11,<3.14` |
| License | Not declared (add to pyproject.toml) |
| CI/CD | Not configured |

### Dependency Stack

**Layer 1 — Demand Forecasting:**
- `xgboost>=2.0` — gradient-boosted demand forecasting with quantile regression (q=0.05, 0.5, 0.95)
- `scikit-learn>=1.4` — clustering, PCA, metrics
- `shap>=0.45` — feature attribution on demand model

**Layer 2 — Constraint Optimization:**
- `ortools>=9.9` — MILP solver (Google OR-Tools) for rack assignment + harvest scheduling

**Layer 3 — RL Environment Control:**
- `stable-baselines3>=2.3` — PPO agent for LED/temperature/CO₂ control
- `gymnasium>=1.0` — environment interface

**Layer 4 — Retail Segmentation:**
- `umap-learn>=0.5` — dimensionality reduction for customer visualization

**Layer 5 — RAG Chatbot:**
- `chromadb>=0.4` — vector store
- `sentence-transformers>=3.0` — embedding model

**Frontend:**
- `streamlit>=1.38` — multi-page app
- `plotly>=5.22` — charts
- `folium>=0.20.0` + `streamlit-folium>=0.27.1` — VRP map

**ML Runtime:**
- `torch>=2.10.0`, `torchvision>=0.25.0`, `timm>=1.0.26` — EfficientNet-B0 for crop health diagnosis
- `opencv-python-headless>=4.13` — image preprocessing

**LLM Clients:**
- `openai>=1.50` — OpenAI SDK (talks to OpenAI + Z.ai OpenAI-compatible endpoint)
- `anthropic>=0.40` — Anthropic SDK (talks to MiniMax via Anthropic-compatible endpoint)

---

## 2. Directory Structure

```
src/adoptakale/
├── __init__.py
├── cli.py                  # CLI entry point (adoptakale CLI)
├── dashboard/
│   ├── app.py             # Main Streamlit app (Farm AI — Layer 0–2)
│   ├── components/
│   │   └── task_list.py   # Routine task renderer with role badges
│   ├── design_decisions.py
│   └── pages/
│       ├── 2_Logistics.py   # VRP — Layer 3
│       ├── 3_Retail_AI.py   # K-Means segmentation — Layer 4
│       └── 4_Media_AI.py     # RAG chatbot — Layer 5
├── data/
│   ├── ema.py             # Live electricity API (data.gov.sg EMA)
│   ├── generate_seed_data.py
│   ├── loader.py           # CSV loaders (customers, orders, crops, staff, shipments)
│   └── shared_data.py      # SharedDataManager (data/farm_output.json r/w)
├── governance/
│   └── deployment_gate.py  # PACT governance deployment gate
├── layer1/
│   ├── explain.py          # SHAP-based model explanation
│   ├── features.py         # Feature engineering for demand forecasting
│   ├── model.py            # XGBoost model training + loading
│   └── predict.py          # Quantile regression demand prediction
├── layer1b/
│   ├── architecture.py     # EfficientNet-B0 crop health model architecture
│   ├── data_pipeline.py    # PlantVillage dataset pipeline
│   ├── inference.py        # Live crop health inference
│   ├── simulation.py       # Simulation mode (mock diagnoses)
│   └── train.py            # Model training script
├── layer2/
│   ├── exceptions.py       # InfeasibleError
│   ├── feasibility_check.py
│   ├── forecast_band.py    # Profit band computation
│   ├── objective.py        # ObjectiveWeights, MODE_LABELS
│   ├── optimizer.py        # build_and_solve (MILP via OR-Tools)
│   ├── scenarios.py        # TyphoonScenarioInput, apply_typhoon, compare_plans
│   └── sustainability.py   # compute_sustainability_kpis, compute_weekly_sustainability
├── layer2b/
│   └── vrp_solver.py       # Capacitated VRP with time windows (OR-Tools)
├── layer3/
│   ├── agent.py            # PPO RL agent (stable-baselines3)
│   ├── autonomy_gate.py    # AutonomyGate, AutonomyMode
│   ├── environment.py      # HydroFarmEnv (gymnasium)
│   ├── inference.py        # RL inference
│   └── train.py            # RL training script
├── layer4/
│   ├── features.py         # Customer feature engineering
│   ├── recommendations.py  # Segment action recommendations
│   ├── segmentation.py     # K-Means clustering + profiling
│   └── visualization.py     # PCA/UMAP dimensionality reduction
├── layer5/                # (consolidated into layer4/ and rag/)
├── llm/
│   └── (llm.py)           # LLM integration (explain_plan, llm_is_configured)
├── monitoring/
│   └── (monitoring.py)
├── rag/
│   ├── agent.py            # RAGAgent (ChromaDB + sentence-transformers)
│   └── hitl.py            # Human-in-the-loop for RAG
└── utils/
    └── config.py           # DATA_DIR, ASSETS_DIR paths

pages/
├── 1_Farm.py              # (Farm AI — same as dashboard/app.py via streamlit_app.py)
├── 2_Logistics.py         # VRP
├── 3_Retail_AI.py         # K-Means segmentation
└── 4_Media_AI.py          # RAG chatbot

streamlit_app.py            # Entry point: runs src/adoptakale/dashboard/app.py
scripts/
└── (scripts/)
data/
├── farm_output.json        # Shared cross-page data (written by Farm AI, read by others)
├── electricity.csv         # EMA historical electricity data
├── customers_geo.csv       # VRP customer locations
├── customers.csv           # Retail AI customer data
├── orders.csv              # Retail AI order data
├── crops.csv
├── shipments.csv
├── staff.csv               # 8 workers: 5 Farm Ops, 2 Logistics, 1 Supervisor
└── rag_knowledge/         # RAG knowledge base

tests/
├── e2e/                   # Playwright E2E tests
├── integration/            # Integration tests
├── sdk/                    # Standalone SDK validator script
└── unit/                   # Unit tests
```

---

## 3. Architecture

### 3.1 Pages (Streamlit Multi-Page App)

**`streamlit_app.py`** is the entry point that imports and runs `src/adoptakale/dashboard/app.py`.

| Page | File | Role |
|------|------|------|
| Farm AI | `app.py` | Main dashboard — Layer 0 (electricity), Layer 1 (demand forecast + MILP), Layer 2 (PPO RL control) |
| Logistics | `pages/2_Logistics.py` | VRP solver for last-mile delivery |
| Retail AI | `pages/3_Retail_AI.py` | K-Means customer segmentation + demand forecast annotation |
| Media AI | `pages/4_Media_AI.py` | RAG chatbot with farm status context |

### 3.2 Cross-Page Data Sharing

**`src/adoptakale/data/shared_data.py`** implements the shared data manager:

```
data/farm_output.json (written by Farm AI after solve)
       ↓
  load_farm_output() read by Logistics, Retail AI, Media AI
```

Fields shared: `rack_layout`, `forecast`, `led_schedule`, `staff_shifts`, `cv_diagnosis_summary`, `cost_breakdown`, `objective_value_sgd`, `plan_date`

### 3.3 Layer 1 — Demand Forecasting + MILP Optimization

```
build_features()          → feature engineering from historical data
load_models() / train_models()
predict_demand()         → XGBoost quantile regression (q=0.05, 0.5, 0.95)
validate_constraints()   → check feasibility before MILP
build_and_solve()        → OR-Tools MILP: rack assignment + harvest scheduling
compute_profit_band()    → Monte Carlo profit envelope
```

### 3.4 Layer 1b — Crop Health Diagnosis

```
EfficientNet-B0 (timm pretrained)
    ↓ (transfer learning on PlantVillage)
mock_diagnose_from_image()   # Simulation mode
diagnose_all_racks_simulated()  # Batch simulation
```

### 3.5 Layer 2 — RL Environment Control

```
HydroFarmEnv (gymnasium)   → PPO agent (stable-baselines3)
AutonomyGate              → autonomy level (ADVISORY, SEMI_AUTONOMOUS, FULLY_AUTONOMOUS)
```

### 3.6 Layer 2b — VRP (Logistics)

```
solve_vrp()  → OR-Tools Capacitated VRP with Time Windows
  - Depot: Jurong Innovation District (1.3328, 103.7436)
  - Default: 3 trucks, 200kg capacity, 12h window
  - Typhoon mode: 6h window
```

### 3.7 Layer 4 — Customer Segmentation (Retail AI)

```
load_features()      → customer features (basket size, frequency, bulk buyer, live commerce)
cluster_customers()  → K-Means (silhouette-evaluated)
name_segment()       → label segments (e.g. "💡 High-Value Bulk")
reduce_pca() / reduce_umap()  → 2D visualization
```

### 3.8 Layer 5 — RAG Chatbot (Media AI)

```
RAGAgent  → ChromaDB vector store + sentence-transformers embeddings
  - Fallback: demo cache when no API key
  - Freshness scoring (days since update)
  - Latency tracking + target <500ms
```

### 3.9 Live Data Integration

**Electricity:** `load_live_electricity()` in `ema.py` fetches from `data.gov.sg` EMA API, falls back to `electricity.csv`.

---

## 4. Git State

**Branch:** `main`
**Last commit:** `56aa831` — `docs: executive summary final v1 — updated test count, Ask, date`

**Uncommitted changes:**
- `journal/phase5-implications-audit.json` — modified
- `journal/overnight-batch-2026-04-22.md` — new untracked
- `journal/phase13-drift-report.json` — new untracked
- `journal/phase13-drift-report.md` — new untracked

**Recent commits (last 5):**
```
56aa831 docs: executive summary final v1 — updated test count, Ask, date
d239196 feat(pitch): deck v3 with governance framework slide
d8ab902 docs(decision-log): add top-level Dimension A summary
5361156 docs(summary): add Section 4 Governance & Production Readiness
9ca4b45 docs(pitch): add 02_role_allocation with governance Q&A ownership
```

---

## 5. Tests

**Test locations:** `tests/unit/`, `tests/integration/`, `tests/e2e/`

**Test configuration** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests/unit", "tests/integration"]
pythonpath = ["src"]
filterwarnings = ["ignore::DeprecationWarning"]
```

**Dev dependencies:** `pytest>=7.2.0`, `pytest-cov>=4.0`, `ruff>=0.1.0`

**No test results** are available in the current session (tests not run).

---

## 6. Implementation Gaps

### 6.1 Missing License Declaration

`pyproject.toml` has no `license` field. Add:
```toml
license = {text = "Apache-2.0"}
```

### 6.2 No CI/CD Configuration

No GitHub Actions, no `.github/workflows/`. All deployment is manual.

### 6.3 Governance / Deployment Gate

`src/adoptakale/governance/deployment_gate.py` exists but has no tests and is not wired into the app execution path (only imported).

### 6.4 RAG Knowledge Base

`data/rag_knowledge/` directory referenced but contents unknown. The RAG agent falls back to demo cache when ChromaDB is not populated.

### 6.5 Layer 1b — No Real Training Pipeline

`layer1b/train.py` and `data_pipeline.py` exist but:
- Training requires PlantVillage dataset (not included)
- Simulation mode (`mock_diagnose_from_image`) is the only available path
- No pre-trained model checkpoint committed

### 6.6 Layer 3 — RL Agent Not Wired to Dashboard

The PPO agent (`layer3/agent.py`) is defined and the `HydroFarmEnv` exists, but:
- No UI control to trigger RL training or live inference in the dashboard
- The dashboard does not call `layer3/inference.py`
- RL autonomy level (`AutonomyGate`) is not rendered in the UI

### 6.7 No End-to-End Test

No Playwright or any E2E test exists that navigates the full Streamlit app flow (Farm AI solve → Logistics VRP → Retail AI → Media AI).

### 6.8 Staff CSV — Role Assignment Inferred from Role Field

The staff CSV (`data/staff.csv`) has a `role` column (Farm Operations, Logistics, Supervisor) that is the source of truth for role assignment. The `task_list.py` component reads this directly rather than having an explicit mapping. This works but is a fragile coupling.

### 6.9 `CURRENT_STATE_REPORT.md` Not in `.gitignore`

This report (if committed) will be a large blob in git history. Consider adding to `.gitignore` if it should remain a local-only analysis artifact.

---

## 7. Summary

| Area | Status |
|------|--------|
| Farm AI (Layer 0–2) | ✅ Working — demand forecast, MILP optimization, live electricity |
| Logistics (Layer 3) | ✅ Working — VRP solver with Folium map |
| Retail AI (Layer 4) | ✅ Working — K-Means segmentation + demand annotation |
| Media AI (Layer 5) | ✅ Working — RAG chatbot with farm status context |
| Cross-page wiring | ✅ Working — `data/farm_output.json` shared layer |
| Crop health (Layer 1b) | ⚠️ Simulation only — no real model |
| RL control (Layer 3) | ⚠️ Defined but not wired to dashboard UI |
| Tests | ⚠️ Structure exists, no recent results |
| CI/CD | ❌ Not configured |
| License | ❌ Not declared |
