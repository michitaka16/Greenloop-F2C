"""OR-Tools CVRPTW solver for Adopt a Kale last-mile delivery routing.

Depot: Jurong Innovation District (1.3328°N, 103.7436°E)
"""
from __future__ import annotations

import math
import time
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# Average vehicle speed in km/h → converted to km/min for the callback
AVG_SPEED_KMH = 30.0
AVG_SPEED_KM_PER_MIN = AVG_SPEED_KMH / 60.0  # 0.5 km/min
SERVICE_MINUTES = 10  # minutes per stop


def solve_vrp(
    customers: list[dict],
    trucks: int = 3,
    truck_capacity_kg: float = 200.0,
    depot_lat: float = 1.3328,
    depot_lng: float = 103.7436,
    time_window_hours: int = 12,
    driver_wage_sgd_per_hour: float = 15.0,
    fuel_cost_sgd_per_km: float = 0.30,
    max_time_seconds: float = 2.0,
) -> dict:
    """Solve Capacitated VRP with Time Windows using OR-Tools.

    Args:
        customers: list of dicts with keys:
            customer_id, lat, lng, weekly_kg,
            time_window_start (HH:MM), time_window_end (HH:MM)
        trucks: number of vehicles (default 3)
        truck_capacity_kg: capacity per truck (default 200.0)
        depot_lat, depot_lng: depot coordinates
        time_window_hours: delivery window width in hours (6 = typhoon, 12 = normal)
        driver_wage_sgd_per_hour: driver hourly wage
        fuel_cost_sgd_per_km: fuel cost per km
        max_time_seconds: solver time limit

    Returns:
        dict with keys: routes, total_km, total_cost_sgd, solve_time_ms,
                        infeasible, unassigned, time_window_violations,
                        vehicle_assignments
    """
    n = len(customers)
    if n == 0:
        return _empty_result()

    # ── Distance matrix ─────────────────────────────────────────────────────
    # Index 0 = depot, 1..n = customers
    all_lats = [depot_lat] + [float(c["lat"]) for c in customers]
    all_lngs = [depot_lng] + [float(c["lng"]) for c in customers]
    dist_km = [[0.0] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        d = haversine(depot_lat, depot_lng, all_lats[i], all_lngs[i])
        dist_km[0][i] = d
        dist_km[i][0] = d
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                dist_km[i][j] = haversine(all_lats[i], all_lngs[i], all_lats[j], all_lngs[j])

    # ── Demand ──────────────────────────────────────────────────────────────
    demands = [0] + [int(float(c["weekly_kg"])) for c in customers]

    # ── Time windows in minutes from depot departure at 06:00 ───────────────
    BASE_HOUR = 6
    time_windows = [(0, int(time_window_hours) * 60)]  # depot: 0..720 min (12h)
    for c in customers:
        tw_start = _hhmm_to_min(c.get("time_window_start", "06:00"), BASE_HOUR)
        tw_end = _hhmm_to_min(c.get("time_window_end", f"{BASE_HOUR + time_window_hours:02d}:00"), BASE_HOUR)
        time_windows.append((tw_start, tw_end))

    # ── OR-Tools model ─────────────────────────────────────────────────────
    manager = pywrapcp.RoutingIndexManager(n + 1, trucks, 0)
    routing = pywrapcp.RoutingModel(manager)

    def dist_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return int(dist_km[from_node][to_node] * 1000)  # km → m for arc cost

    def time_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        travel_min = dist_km[from_node][to_node] / AVG_SPEED_KM_PER_MIN  # km / (km/min) = min
        return int(travel_min + SERVICE_MINUTES)

    dist_idx = routing.RegisterTransitCallback(dist_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(dist_idx)

    demand_idx = routing.RegisterUnaryTransitCallback(
        lambda i: demands[manager.IndexToNode(i)]
    )
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [int(truck_capacity_kg)] * trucks, True, "Capacity"
    )

    time_idx = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_idx,
        0,  # no slack
        int(time_window_hours) * 60,  # max route duration
        False,  # don't fix start cumul to zero
        "Time",
    )
    time_dim = routing.GetDimensionOrDie("Time")

    # ── Soft time windows ─────────────────────────────────────────────────
    for node_idx in range(1, n + 1):
        tw_open, tw_close = time_windows[node_idx]
        # Soft upper bound: penalty for late arrivals
        time_dim.SetCumulVarSoftUpperBound(node_idx, tw_close, 1000)
        # Soft lower bound: penalty for early arrivals
        time_dim.SetCumulVarSoftLowerBound(node_idx, tw_open, 100)

    # ── Solve ─────────────────────────────────────────────────────────────
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.seconds = int(max_time_seconds)
    params.log_search = False

    start_ms = int(time.time() * 1000)
    solution = routing.SolveWithParameters(params)
    elapsed_ms = int(time.time() * 1000 - start_ms)

    if not solution:
        return _no_solution_result(customers, elapsed_ms, trucks)

    # ── Extract results ────────────────────────────────────────────────────
    routes: list[list[str]] = [[] for _ in range(trucks)]
    vehicle_assignments: dict[str, str] = {}
    total_km = 0.0
    assigned: set[str] = set()

    for v in range(trucks):
        idx = routing.Start(v)
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node != 0:
                cid = customers[node - 1]["customer_id"]
                routes[v].append(cid)
                vehicle_assignments[cid] = f"V{v + 1:03d}"
                assigned.add(cid)
            nxt = solution.Value(routing.NextVar(idx))
            if not routing.IsEnd(nxt):
                total_km += dist_km[node][manager.IndexToNode(nxt)]
            idx = nxt

    unassigned = [c["customer_id"] for c in customers if c["customer_id"] not in assigned]

    # ── Time window violations ─────────────────────────────────────────────
    violations: dict[str, int] = {}
    for node_idx in range(1, n + 1):
        arr_min = solution.Value(time_dim.CumulVar(node_idx))
        _, tw_close = time_windows[node_idx]
        if arr_min > tw_close:
            cid = customers[node_idx - 1]["customer_id"]
            violations[cid] = arr_min - tw_close

    infeasible = len(unassigned) > 0

    # ── Cost ───────────────────────────────────────────────────────────────
    total_driver_min = 0.0
    for v in range(trucks):
        idx = routing.Start(v)
        while not routing.IsEnd(idx):
            nxt = solution.Value(routing.NextVar(idx))
            if not routing.IsEnd(nxt):
                total_driver_min += time_callback(idx, nxt)
            idx = nxt
    total_driver_hours = total_driver_min / 60.0
    total_cost = total_km * fuel_cost_sgd_per_km + total_driver_hours * driver_wage_sgd_per_hour

    return {
        "routes": routes,
        "total_km": round(total_km, 1),
        "total_cost_sgd": round(total_cost, 2),
        "solve_time_ms": elapsed_ms,
        "infeasible": infeasible,
        "unassigned": unassigned,
        "time_window_violations": violations,
        "vehicle_assignments": vehicle_assignments,
    }


def _hhmm_to_min(hhmm: str, base_hour: int) -> int:
    """HH:MM → minutes from base_hour:00."""
    parts = hhmm.split(":")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    return (h - base_hour) * 60 + m


def _empty_result() -> dict:
    return dict(
        routes=[], total_km=0.0, total_cost_sgd=0.0,
        solve_time_ms=0, infeasible=False, unassigned=[],
        time_window_violations={}, vehicle_assignments={},
    )


def _no_solution_result(customers: list[dict], elapsed_ms: int, trucks: int) -> dict:
    return dict(
        routes=[[] for _ in range(trucks)],
        total_km=0.0, total_cost_sgd=0.0,
        solve_time_ms=elapsed_ms, infeasible=True,
        unassigned=[c["customer_id"] for c in customers],
        time_window_violations={}, vehicle_assignments={},
    )
