"""Shared data manager — Farm AI writes outputs, other pages read them.

All 4 pages share data through data/farm_output.json.
Farm AI writes after solving; Logistics, Retail AI, and Media AI read on load.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from greenloop.utils.config import DATA_DIR

logger = logging.getLogger(__name__)
OUTPUT_FILE = DATA_DIR / "farm_output.json"


def save_farm_output(plan: dict, forecast: dict) -> None:
    """Write Farm AI outputs to data/farm_output.json for sharing with other pages."""
    try:
        payload = {
            "plan_date": str(date.today()),
            "rack_layout": plan.get("rack_layout", {}),
            "forecast": forecast,
            "led_schedule": plan.get("led_schedule", {}),
            "staff_shifts": plan.get("staff_shifts", []),
            "cv_diagnosis_summary": plan.get("cv_diagnosis_summary"),
            "cost_breakdown": plan.get("cost_breakdown", {}),
            "objective_value_sgd": plan.get("objective_value_sgd"),
            "solve_time_ms": plan.get("solve_time_ms"),
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Farm output saved to {OUTPUT_FILE}")
    except Exception as exc:
        logger.warning(f"Could not save farm output: {exc}")


def load_farm_output() -> dict | None:
    """Read Farm AI outputs from data/farm_output.json. Returns None if missing."""
    try:
        if not OUTPUT_FILE.exists():
            return None
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    except Exception as exc:
        logger.warning(f"Could not load farm output: {exc}")
        return None
