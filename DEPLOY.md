# Deployment

Three supported targets. Pick one.

## 1. Streamlit Community Cloud (recommended for VC demos)

Free, public URL, auto-rebuilds on every push to `main`, ~3-minute setup.

### Steps

1. Open <https://share.streamlit.io/deploy> (sign in with GitHub).
2. Pick repo `michitaka16/Adopt-A-Kale`, branch `main`, main file path `streamlit_app.py`.
3. Click **Deploy**.

That's it. Streamlit Cloud reads `requirements.txt` (generated from `uv.lock`) and `.python-version` automatically.

### Behind the scenes

- `streamlit_app.py` at the repo root is Streamlit Cloud's conventional entrypoint. It imports and calls `adoptakale.dashboard.app.main`.
- `.python-version` pins Python 3.12.
- `requirements.txt` is the uv-exported lockfile.
- Trained models (`models/demand_q*.json`, `models/layer3/ppo_hydrofarm_final.zip`) are in-repo, so first-boot skips training.

### Troubleshooting

- **Build fails with `xgboost` import error** — Streamlit Cloud runs Linux, and Linux xgboost wheels need `libgomp1`. It's installed by default on Cloud; if you see this locally in Docker, check the Dockerfile includes `apt install libgomp1`.
- **"No module named adoptakale"** — confirm `streamlit_app.py` is at repo root (not inside `src/`). Streamlit Cloud runs the entry file in the repo root, which adds `src/` to the path via the installed `adopt-a-kale` package from `pyproject.toml`.

## 2. Fly.io / Render / Cloud Run (self-hosted container)

```bash
# Fly.io
fly launch --dockerfile Dockerfile --no-deploy
fly deploy

# Cloud Run
gcloud run deploy adoptakale \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 8501
```

The [`Dockerfile`](Dockerfile) is multi-stage, uses `uv` for resolution, and includes `libgomp1` for xgboost. Exposes 8501.

Test locally:

```bash
docker build -t adoptakale .
docker run --rm -p 8501:8501 adoptakale
open http://localhost:8501
```

## 3. Local (development)

```bash
uv sync --extra dev
uv run adoptakale dashboard
```

The CLI handles the macOS libomp redirect automatically.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push + PR:

1. `test` job — installs deps via uv, runs the 116-test suite.
2. `docker` job (depends on `test`) — builds the production image to catch Dockerfile regressions without publishing.

Add a deploy step by pushing to a registry after `docker`, or let Streamlit Cloud handle redeploys natively.
