#!/usr/bin/env python3
"""VRP feasibility check — run before demo to verify solver works."""
import sys
sys.path.insert(0, "src")

import csv
from greenloop.layer2b.vrp_solver import solve_vrp

def main():
    with open("data/customers_geo.csv") as f:
        customers = list(csv.DictReader(f))

    print(f"Loaded {len(customers)} customers, demand: {sum(int(c['weekly_kg']) for c in customers)}kg")
    print(f"Depot: Jurong Innovation District (1.3328, 103.7436)")
    print()

    # Normal mode: 12h window
    print("=== Normal Mode (12h window) ===")
    result = solve_vrp(
        customers=customers, trucks=3, truck_capacity_kg=200.0,
        depot_lat=1.3328, depot_lng=103.7436, time_window_hours=12,
        driver_wage_sgd_per_hour=15.0, fuel_cost_sgd_per_km=0.30,
    )
    print(f"  Solve time: {result['solve_time_ms']}ms")
    print(f"  Total km: {result['total_km']} km")
    print(f"  Total cost: ${result['total_cost_sgd']}")
    print(f"  Assigned: {sum(len(r) for r in result['routes'])}/{len(customers)}")
    print(f"  Infeasible: {result['infeasible']}")
    assert result["solve_time_ms"] <= 3000, f"Solve took {result['solve_time_ms']}ms (budget: 3000ms)"
    assert sum(len(r) for r in result["routes"]) >= 25, "Too few customers assigned in normal mode"
    print("  ✓ Normal mode OK")
    print()

    # Typhoon mode: 6h window
    print("=== Typhoon Mode (6h window) ===")
    result2 = solve_vrp(
        customers=customers, trucks=3, truck_capacity_kg=200.0,
        depot_lat=1.3328, depot_lng=103.7436, time_window_hours=6,
        driver_wage_sgd_per_hour=15.0, fuel_cost_sgd_per_km=0.30,
    )
    print(f"  Solve time: {result2['solve_time_ms']}ms")
    print(f"  Total km: {result2['total_km']} km")
    print(f"  Assigned: {sum(len(r) for r in result2['routes'])}/{len(customers)}")
    print(f"  Infeasible: {result2['infeasible']}")
    print(f"  Unassigned: {result2['unassigned']}")
    print(f"  TW violations: {result2['time_window_violations']}")
    assert result2["solve_time_ms"] <= 3000, f"Solve took {result2['solve_time_ms']}ms (budget: 3000ms)"
    print("  ✓ Typhoon mode OK (returns structured result)")
    print()

    print("All checks passed ✓")

if __name__ == "__main__":
    main()
