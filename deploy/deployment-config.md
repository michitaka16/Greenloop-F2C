# Deployment Configuration

```yaml
type: application
name: adopt-a-kale
description: >
  Streamlit dashboard for a 3-layer AI farm-operations pipeline
  (XGBoost forecast → OR-Tools MILP → PPO RL). Shipped as a single
  Docker container on port 8501.

# ─── Deployment targets ────────────────────────────────────────────────
# Primary target for the VC-pitch window is local Docker — runs on the
# presenter's laptop, no internet dependency. Public URL via Streamlit
# Community Cloud is secondary (blocked on GitHub SSH auth at time of
# onboarding).
targets:
  local-docker:
    primary: true
    platform: docker
    image: adopt-a-kale:latest
    container_name: adoptakale
    port: 8501
    live_url: http://localhost:8501

  streamlit-cloud:
    primary: false
    platform: streamlit-community-cloud
    repo: michitaka16/Adopt-A-Kale
    branch: main
    entrypoint: streamlit_app.py
    # Public URL is assigned by Streamlit Cloud after first deploy.
    # Update once known.
    live_url: null

# ─── Production paths ──────────────────────────────────────────────────
# Files that, when changed, require a redeploy.
production_paths:
  - src/adoptakale/
  - streamlit_app.py
  - Dockerfile
  - pyproject.toml
  - uv.lock
  - requirements.txt
  - data/
  - models/

# ─── Pre-deploy gates ──────────────────────────────────────────────────
# Why each gate: see rules/deploy-hygiene.md Rule 8.
gates:
  - name: tests
    command: uv run pytest -q
    why: 116 tests guard Layer 1/2/3, dashboard helpers, CLI. Non-zero
         exit blocks deploy because a red suite means the feature under
         test does not behave as specified.
  - name: docker-build
    command: docker build -t adopt-a-kale:latest .
    why: Confirms the runtime image builds reproducibly from HEAD. Catches
         Dockerfile drift (missing libgomp1, wrong Python version) before
         the container is swapped in production.

# ─── Deploy command (local-docker target) ──────────────────────────────
# --env-file .env injects LLM_PROVIDER / {PROVIDER}_API_KEY / {PROVIDER}_MODEL
# into the container so the AI narrative expander works without baking
# secrets into the image. The .env stays gitignored.
deploy_command: |
  docker rm -f adoptakale 2>/dev/null || true
  docker run -d --name adoptakale --restart unless-stopped \
    --env-file .env \
    -p 8501:8501 adopt-a-kale:latest

# ─── Post-deploy verification ──────────────────────────────────────────
deploy_check_command: |
  docker inspect --format='{{.Config.Image}} {{.State.Status}}' adoptakale

user_visible_check: |
  curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8501/

smoke_test_command: |
  curl -fsSL http://localhost:8501/ | grep -q "Streamlit" && echo "ok"

# Streamlit Cloud handles its own cache / CDN. Local Docker has none.
cache_invalidation_command: null

# ─── State tracking ────────────────────────────────────────────────────
deploy_state_file: deploy/.last-deployed
deploy_log_dir: deploy/deployments/
```

## Streamlit Cloud public deploy

Blocked on one credential step (SSH key paste → GitHub). Once `git push origin main` succeeds:

1. Open <https://share.streamlit.io/deploy>
2. Repo: `michitaka16/Adopt-A-Kale`, branch `main`, main file: `streamlit_app.py`
3. Click **Deploy**. Copy the assigned URL into the `streamlit-cloud.live_url` field above.

## Changelog

- **2026-04-14** — Onboarded. First recorded deploy to local-docker target.
