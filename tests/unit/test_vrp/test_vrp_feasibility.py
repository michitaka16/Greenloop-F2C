"""VRP normal mode: 12-hour window should always be feasible with 30 customers."""
import pytest
import sys
from pathlib import Path

from greenloop.layer2b.vrp_solver import solve_vrp


def test_vrp_normal_12h_window_succeeds(customers_30):
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
    assert result["solve_time_ms"] <= 3000
    total_assigned = sum(len(route) for route in result["routes"])
    assert total_assigned > 0, "No customers assigned — solver may have timed out"
