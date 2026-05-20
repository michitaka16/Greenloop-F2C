"""VRP typhoon mode: 6-hour window may produce infeasible assignments."""
import pytest
import sys
from pathlib import Path

from adoptakale.layer2b.vrp_solver import solve_vrp


def test_vrp_typhoon_6h_window_returns_structured_result(customers_30):
    result = solve_vrp(
        customers=customers_30,
        trucks=3,
        truck_capacity_kg=200.0,
        depot_lat=1.3328,
        depot_lng=103.7436,
        time_window_hours=6,
        driver_wage_sgd_per_hour=15.0,
        fuel_cost_sgd_per_km=0.30,
    )
    assert "routes" in result
    assert "total_km" in result
    assert "total_cost_sgd" in result
    assert "solve_time_ms" in result
    assert result["solve_time_ms"] <= 3000
    # Feasible OR has unassigned customers
    assert result["infeasible"] is False or len(result["unassigned"]) > 0
