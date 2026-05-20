# Adopt a Kale

**Farm-to-Consumer Vertical Hydroponics OS for Singapore.** Formerly known as **GreenLoop F2C**.

A 5-layer AI platform (6 ML techniques) that runs Singapore vertical-hydroponic farms end-to-end — seed to delivery — and powers the consumer-facing *Adopt a Kale* subscription that lets Singapore residents adopt a named hydroponic plot and receive weekly harvests at home. The same six AI techniques drive both the B2B Farm OS dashboard and the B2C consumer app.

> **Brand note:** Python package is `adoptakale`; GitHub repo is `Adopt-A-Kale`. The legacy `Greenloop-F2C` repo URL 301-redirects to the new slug for backward compatibility.

| Layer | Responsibility | Tech |
|---|---|---|
| **Layer 1** | Weekly crop demand forecast with 90 % confidence intervals | XGBoost quantile regression (q = 0.05 / 0.50 / 0.95) · SHAP explainability |
| **Layer 1b** | Crop health diagnosis (growth stage + nutrition) from rack photography | EfficientNet-B0 dual-head CNN (transfer learning, PlantVillage) — simulation mode |
| **Layer 2** | Daily operating plan: LED schedule, staff shifts, rack layout, climate targets | Mixed-Integer Linear Programming via Google OR-Tools (< 50 ms solve) |
| **Layer 2b** | Last-mile delivery routes | Capacitated VRP with Time Windows (OR-Tools) — 30 / 30 Singapore customers, 147.1 km |
| **Layer 3** | Real-time climate control (temperature, humidity, CO₂, moisture) | PPO reinforcement learning (`stable-baselines3`) + AutonomyGate (MANUAL / ADVISORY / AUTONOMOUS) |
| **Layer 4** | Customer segmentation for B2C omakase pairing | K-Means k = 4 (silhouette 0.765) + UMAP visualisation |
| **Layer 5** | Investor / consumer AI chat | RAG (ChromaDB + sentence-transformers + Claude) |
| **Dashboards** | B2B *Farm OS* (4 pages) + B2C *Adopt a Kale* (9 pages) | Streamlit + Plotly |

The upper CI from Layer 1 feeds the production target of Layer 2, so volatile crops automatically get larger buffers. Full rationale lives in [`specs/decision-log.md`](specs/decision-log.md) and [`journal/decision-log.md`](journal/decision-log.md), and is surfaced in the dashboard sidebar.

## Quick Start

Requirements: `uv`, Python 3.11–3.13 (3.14 is not yet supported by `shap` / `llvmlite`).

```bash
uv sync --extra dev
uv run adoptakale dashboard    # B2B Farm OS — launches on http://localhost:8501

# Consumer-facing Adopt a Kale app:
cd consumer_app
streamlit run Home.py         # B2C Adopt a Kale — http://localhost:8501
```

Other CLI commands:

```bash
uv run adoptakale forecast     # print Layer 1 demand forecast per crop
uv run adoptakale solve        # run a one-shot Layer 2 MILP solve
```

### macOS — libomp

`xgboost` on Apple Silicon expects `libomp.dylib` at `/opt/homebrew/opt/libomp/lib/`. If you don't have Homebrew, the `adoptakale` CLI transparently redirects the dynamic linker to the copy bundled with `scikit-learn` inside the venv — no extra setup needed.

If you run `streamlit run` or import `xgboost` manually instead of through the CLI and see `Library not loaded: @rpath/libomp.dylib`:

```bash
brew install libomp               # preferred
# or symlink the sklearn-bundled copy into the Python lib dir:
ln -sf "$PWD/.venv/lib/python3.12/site-packages/sklearn/.dylibs/libomp.dylib" \
  "$(uv run python -c 'import sys,pathlib; print(pathlib.Path(sys.prefix).parent/"lib"/"libomp.dylib")')"
```

## Testing

```bash
uv run pytest                 # 494 tests — unit · integration · adversarial · e2e
```

Test layout:

```
tests/
├── unit/             Tier 1 — fast, isolated, mocking allowed
│   ├── test_cli.py                  CLI smoke tests
│   ├── test_dashboard/              Design-decision parser
│   ├── test_data/                   CSV loaders
│   ├── test_layer1/                 XGBoost quantile forecast
│   ├── test_layer1b/                EfficientNet adversarial
│   ├── test_layer2/                 MILP constraints + scenarios
│   ├── test_layer3/                 Gym environment
│   ├── test_layer4/                 K-Means segmentation
│   ├── test_layer5/                 RAG + HITL
│   ├── test_vrp/                    CVRPTW capacity / time-windows / typhoon
│   ├── test_governance/             Deployment gate + implications audit
│   └── test_monitoring/             Drift detector
├── adversarial/      Tier 2 — 38 red-team tests across all layers
├── integration/      Tier 3 — real pipeline (no mocks)
├── e2e/              Tier 4 — Playwright end-to-end
└── sdk/              Standalone Kailash-SDK validator (not pytest)
```

## Repository Layout

```
src/adoptakale/                # Python package (legacy name retained)
  layer1/   features.py, model.py (train/load), predict.py, explain.py
  layer1b/  architecture.py (EfficientNet-B0), inference.py, simulation.py
  layer2/   optimizer.py (MILP), scenarios.py (typhoon re-opt), exceptions.py
  layer2b/  vrp_solver.py (CVRPTW)
  layer3/   environment.py (gym), train.py (PPO), inference.py, autonomy_gate.py
  layer4/   segmentation.py (K-Means), recommendations.py, visualization.py
  rag/      agent.py (ChromaDB + Claude), hitl.py
  governance/ deployment_gate.py, implications_audit.py
  monitoring/ drift_detector.py
  dashboard/ app.py (Streamlit Farm OS), design_decisions.py
  data/     loader.py, generate_seed_data.py, ema.py (live electricity API)
  cli.py    CLI entrypoint (dashboard / solve / forecast)

consumer_app/                 # B2C Adopt a Kale Streamlit app (9 pages)
  Home.py                     Landing — tier comparison
  pages/                      Start · My Plot · Chat · Schedule · Account ·
                              Plant Camera · Celebration · Alerts
  lib/                        styles.py, mock_data.py
  assets/                     Kale leaf PNGs

specs/      Domain truth (demand-forecasting, resource-optimization, climate-control,
            data-model, dashboard, decision-log)
data/       Seed CSVs + farm_output.json (cross-page shared state)
models/     Trained artifacts (demand_q05/q50/q95.json, layer3/ppo_hydrofarm_final.zip)
journal/    COC decision log + phase reports (phase 5/7/8/13 audit trail)
deliverables/ MGMT 655 submission — executive summary + pitch decks
pitch/      VC pitch deck source
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
