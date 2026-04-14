# GreenLoop Farm OS

3-layer AI pipeline for Singapore vertical hydroponic farming (farm-to-consumer).

| Layer | Responsibility | Tech |
|---|---|---|
| **Layer 1** | Weekly crop demand forecast with 90 % confidence intervals | XGBoost quantile regression (q=0.05 / 0.50 / 0.95), SHAP explainability |
| **Layer 2** | Daily operating plan: LED schedule, staff shifts, rack layout, climate targets | Mixed-Integer Linear Programming via Google OR-Tools |
| **Layer 3** | Real-time climate control (temperature, humidity, CO₂, moisture) | PPO reinforcement learning (`stable-baselines3`) + pre-action safety envelope |
| **Dashboard** | Single-screen VC demo integrating all layers + Typhoon scenario re-optimization | Streamlit + Plotly |

The upper CI from Layer 1 feeds the production target of Layer 2, so volatile crops automatically get larger buffers. Full rationale lives in [`specs/decision-log.md`](specs/decision-log.md) (7 Dimension A design decisions) and is surfaced in the dashboard sidebar.

## Quick Start

Requirements: `uv`, Python 3.11–3.13 (3.14 is not yet supported by `shap`/`llvmlite`).

```bash
uv sync --extra dev
uv run greenloop dashboard    # launches on http://localhost:8501
```

Other CLI commands:

```bash
uv run greenloop forecast     # print Layer 1 demand forecast per crop
uv run greenloop solve        # run a one-shot Layer 2 MILP solve
```

### macOS — libomp

`xgboost` on Apple Silicon expects `libomp.dylib` at `/opt/homebrew/opt/libomp/lib/`. If you don't have Homebrew, the `greenloop` CLI transparently redirects the dynamic linker to the copy bundled with `scikit-learn` inside the venv — no extra setup needed.

If you run `streamlit run` or import `xgboost` manually instead of through the CLI and see `Library not loaded: @rpath/libomp.dylib`:

```bash
brew install libomp               # preferred
# or symlink the sklearn-bundled copy into the Python lib dir:
ln -sf "$PWD/.venv/lib/python3.12/site-packages/sklearn/.dylibs/libomp.dylib" \
  "$(uv run python -c 'import sys,pathlib; print(pathlib.Path(sys.prefix).parent/"lib"/"libomp.dylib")')"
```

## Testing

```bash
uv run pytest                 # 113 tests across unit + integration
```

The 3-tier layout:

```
tests/
├── unit/             Tier 1 — fast, isolated, mocking allowed
│   ├── test_cli.py                  CLI smoke tests
│   ├── test_dashboard/              Design-decision parser
│   ├── test_data/                   CSV loaders
│   ├── test_layer1/                 XGBoost quantile forecast
│   ├── test_layer2/                 MILP constraints + scenarios
│   └── test_layer3/                 Gym environment
├── integration/      Tier 2 — real pipeline (no mocks)
└── sdk/              Standalone Kailash-SDK validator (not pytest)
```

## Repository Layout

```
src/greenloop/
  layer1/   features.py, model.py (train/load), predict.py, explain.py
  layer2/   optimizer.py (MILP), scenarios.py (typhoon re-opt), exceptions.py
  layer3/   environment.py (gym), train.py (PPO), inference.py (escalation)
  dashboard/ app.py (Streamlit), design_decisions.py (VC-pitch panel)
  data/     loader.py, generate_seed_data.py
  cli.py    CLI entrypoint (dashboard / solve / forecast)

specs/      Domain truth (demand-forecasting, resource-optimization, climate-control,
            data-model, dashboard, decision-log)
data/       Seed CSVs (crops, shipments, electricity, staff, sensors_sim)
models/     Trained artifacts (demand_q05/q50/q95.json, layer3/ppo_hydrofarm_final.zip)
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
