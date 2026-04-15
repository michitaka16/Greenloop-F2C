# DEPLOY — 2026-04-15 (refresh)

## What shipped

Nothing new on the production surface — this was a refresh deploy to resync `.last-deployed` (was `088660f`) with HEAD (`a1a46c3`). The only commit in between touched deployment metadata, not production code.

## Why we ran it anyway

`/deploy` was explicitly invoked. Running the checklist end-to-end:

- Proved the container is actually serving what it claims.
- Updated `.last-deployed` → `a1a46c3` so the next `/deploy --check` doesn't incorrectly report drift against a deployment-only commit.

## Gates + checks

- pytest: **132 passed** in 40.97 s
- docker build: cache hit (no prod-path changes)
- HTTP 200 @ <http://localhost:8501> in 2.55 ms, Streamlit markers present
- `/_stcore/health` → 200

## Cache invalidation

None — local Docker has no CDN.

## Follow-up

- Public URL via Streamlit Cloud is still the one outstanding deploy target (<https://share.streamlit.io/deploy>). The commit being deployed here (`a1a46c3`) is on `origin/main` and would be picked up automatically once Streamlit Cloud is connected.
