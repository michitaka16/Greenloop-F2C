"""Streamlit Cloud entrypoint.

Streamlit Community Cloud looks for a top-level `streamlit_app.py` by
convention. This file just re-exports the main dashboard so Cloud and the
`greenloop dashboard` CLI share a single source of truth.

Linux wheels of xgboost bundle OpenMP via libgomp — no libomp dance needed
on Streamlit Cloud / Docker. The CLI's macOS libomp redirect is only
triggered on darwin, so importing the dashboard here is safe everywhere.
"""

from greenloop.dashboard.app import main

main()
