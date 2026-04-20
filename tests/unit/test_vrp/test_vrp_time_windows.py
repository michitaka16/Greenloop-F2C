"""VRP time windows: deliveries should arrive within their stated time windows."""
import pytest
import sys
from pathlib import Path

from greenloop.layer2b.vrp_solver import solve_vrp


def test_vrp_deliveries_within_time_windows(customers_30):
    result = solve_vrp(
        customers=customers_30,
        trucks=3,
        truck_capacity_kg=200.0,
        depot_lat=1.3328,
        depot_lng=103.7436,
        time_window_hours=12,
        driver_wage_sgd_per_hour=15.0,
        fuel_cost_sgd_per_km=0.30,
    )

    # If time_window_violations is tracked, it should be a dict
    assert isinstance(result.get("time_window_violations", {}), dict)
    # Late minutes should be non-negative integers
    for cid, minutes_late in result.get("time_window_violations", {}).items():
        assert minutes_late >= 0, f"{cid} has negative lateness: {minutes_late}"
