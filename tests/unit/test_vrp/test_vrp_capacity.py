"""VRP capacity: no route should exceed truck capacity."""
import pytest
import sys
from pathlib import Path

from greenloop.layer2b.vrp_solver import solve_vrp


def test_vrp_capacity_constraints_honored(customers_30):
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

    customer_map = {c["customer_id"]: c for c in customers_30}
    for route in result["routes"]:
        route_kg = sum(
            customer_map[cid]["weekly_kg"]
            for cid in route
        )
        assert route_kg <= 200.0 + 1e-6, f"Route exceeds 200kg capacity: {route_kg}kg"
