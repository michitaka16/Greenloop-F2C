# syntax=docker/dockerfile:1.7

# ─── Build stage ────────────────────────────────────────────────────────────
# We install into a venv under /app/.venv so the runtime stage can copy a
# self-contained tree. Uses uv for resolution speed + lockfile reproducibility.
FROM python:3.12-slim-bookworm AS builder

# libgomp1 ships libgomp.so which xgboost's Linux wheel links against.
# Without it, `import xgboost` fails with the same libomp error we saw on mac.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# uv: 50x faster than pip for this dep graph. Pinned for reproducibility.
# Bump deliberately and verify the local+CI builds still pass.
COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /uvx /bin/

WORKDIR /app

# Copy only resolution inputs first so the dep layer caches independently
# of source changes.
COPY pyproject.toml uv.lock README.md ./

# Install production deps into /app/.venv. --no-install-project keeps the
# project itself out until source is copied.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Now copy source and install the project itself
COPY src/ ./src/
COPY data/ ./data/
COPY models/ ./models/
COPY specs/ ./specs/
COPY streamlit_app.py ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ─── Runtime stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

# Same OpenMP runtime the wheels need
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

# Fly.io / Render / Cloud Run / generic Docker entrypoint
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
