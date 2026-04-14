"""GreenLoop CLI entrypoint.

Single command to launch the dashboard for the VC demo. Handles the macOS
libomp dylib lookup that xgboost needs so the user doesn't see a cryptic
"libomp.dylib not found" traceback.

Usage:
    greenloop dashboard         # launch Streamlit dashboard
    greenloop solve             # run a one-shot Layer 2 solve and print the plan
    greenloop forecast          # print Layer 1 forecast for every crop
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _ensure_libomp_visible() -> None:
    """On macOS, xgboost's libxgboost.dylib hardcodes `/opt/homebrew/opt/libomp/lib`.

    When the user does not have Homebrew installed but has scikit-learn in the
    venv (which bundles libomp.dylib in its .dylibs folder), we prepend the
    sklearn bundle to DYLD_FALLBACK_LIBRARY_PATH so xgboost's dynamic loader
    finds it. Does nothing on non-macOS or if the bundled copy is missing.
    """
    if sys.platform != "darwin":
        return
    try:
        import sklearn
    except ImportError:
        return
    candidate = Path(sklearn.__file__).parent / ".dylibs"
    if not (candidate / "libomp.dylib").exists():
        return
    current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    if str(candidate) in current:
        return
    parts = [str(candidate)] + ([current] if current else [])
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(parts)


def cmd_dashboard(args: argparse.Namespace) -> int:
    _ensure_libomp_visible()
    app_path = Path(__file__).parent / "dashboard" / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.port),
        "--server.headless",
        "true",
    ]
    return subprocess.call(cmd)


def cmd_solve(args: argparse.Namespace) -> int:
    _ensure_libomp_visible()
    from greenloop.data.loader import load_crops, load_electricity, load_staff
    from greenloop.layer2.optimizer import build_and_solve

    # Reasonable default forecast for a smoke demo — the dashboard uses live
    # Layer 1 output. This command exists so integrators can sanity-check
    # Layer 2 in isolation.
    forecast = {
        "kai_lan": {"predicted_kg": 48.2, "lower_ci": 34.5, "upper_ci": 68.3},
        "baby_spinach": {"predicted_kg": 31.5, "lower_ci": 24.0, "upper_ci": 39.1},
        "lettuce_mambo": {"predicted_kg": 56.8, "lower_ci": 51.2, "upper_ci": 62.4},
        "chye_sim": {"predicted_kg": 36.1, "lower_ci": 28.0, "upper_ci": 44.2},
        "arugula": {"predicted_kg": 12.8, "lower_ci": 10.5, "upper_ci": 15.1},
    }
    plan = build_and_solve(
        forecast,
        load_crops(),
        load_electricity(),
        load_staff(),
        available_headcount=args.headcount,
    )
    print(f"Profit:      ${plan['objective_value_sgd']:.2f} SGD")
    print(f"Solve time:  {plan['solve_time_ms']} ms")
    print(f"Rack layout: {plan['rack_layout']}")
    return 0


def cmd_forecast(args: argparse.Namespace) -> int:
    _ensure_libomp_visible()
    from greenloop.data.loader import load_shipments
    from greenloop.layer1.features import build_features
    from greenloop.layer1.model import load_models, train_models
    from greenloop.layer1.predict import predict_demand

    shipments = load_shipments()
    features = build_features(shipments)
    models_dir = _REPO_ROOT / "models"
    try:
        models = load_models(models_dir)
    except FileNotFoundError:
        print("Training demand models (first run)...", file=sys.stderr)
        models = train_models(features, models_dir)
    forecast = predict_demand(models, features)
    print(f"{'Crop':<16}{'Median (kg)':>14}{'Lower CI':>12}{'Upper CI':>12}")
    print("-" * 54)
    for crop, f in forecast.items():
        print(f"{crop:<16}{f['predicted_kg']:>14.1f}{f['lower_ci']:>12.1f}{f['upper_ci']:>12.1f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="greenloop",
        description="GreenLoop Farm OS — 3-layer AI pipeline for hydroponic farming",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_dash = sub.add_parser("dashboard", help="Launch the Streamlit dashboard")
    p_dash.add_argument("--port", type=int, default=8501)
    p_dash.set_defaults(func=cmd_dashboard)

    p_solve = sub.add_parser("solve", help="Run a one-shot Layer 2 solve")
    p_solve.add_argument("--headcount", type=int, default=6)
    p_solve.set_defaults(func=cmd_solve)

    p_fc = sub.add_parser("forecast", help="Print Layer 1 demand forecast")
    p_fc.set_defaults(func=cmd_forecast)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
