"""VRP Logistics page — GreenLoop Farm OS last-mile delivery routing."""
from __future__ import annotations

import pandas as pd
import streamlit as st

# Lazy imports — folium and streamlit_folium loaded only when page renders
from greenloop.layer2b.vrp_solver import solve_vrp

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Logistics — GreenLoop Farm OS",
    layout="wide",
)

DEPOT_LAT = 1.3328
DEPOT_LNG = 103.7436

# ── Load customer data ─────────────────────────────────────────────────────
@st.cache_data
def load_customers() -> pd.DataFrame:
    return pd.read_csv("data/customers_geo.csv")


def _default_params() -> dict:
    return dict(
        num_trucks=3,
        driver_wage=15.0,
        fuel_cost=0.30,
        truck_capacity=200.0,
    )


# ── Sidebar controls ───────────────────────────────────────────────────────
st.sidebar.title("VRP Parameters")

num_trucks = st.sidebar.number_input(
    "Trucks", min_value=1, max_value=5, value=3, key="num_trucks",
)
driver_wage = st.sidebar.number_input(
    "Driver wage (SGD/h)", min_value=5.0, max_value=100.0, value=15.0, key="driver_wage",
)
fuel_cost = st.sidebar.number_input(
    "Fuel cost (SGD/km)", min_value=0.01, max_value=5.0, value=0.30, key="fuel_cost",
)
truck_capacity = st.sidebar.number_input(
    "Truck capacity (kg)", min_value=50.0, max_value=500.0, value=200.0, key="truck_capacity",
)

# ── Typhoon mode ────────────────────────────────────────────────────────────
is_typhoon = st.session_state.get("typhoon_active", False)
time_window_hours = 6 if is_typhoon else 12

if is_typhoon:
    st.warning("⚠️ Typhoon active — delivery window reduced to 6 hours")

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🚚 Last-Mile Delivery Routing")
st.caption(f"Depot: Jurong Innovation District ({DEPOT_LAT}, {DEPOT_LNG})")

# ── Solve ──────────────────────────────────────────────────────────────────
customers_df = load_customers()

solve_clicked = st.button("🚚 Solve VRP", type="primary")

if solve_clicked or "vrp_result" in st.session_state:
    if solve_clicked:
        result = solve_vrp(
            customers=customers_df.to_dict("records"),
            trucks=num_trucks,
            truck_capacity_kg=truck_capacity,
            depot_lat=DEPOT_LAT,
            depot_lng=DEPOT_LNG,
            time_window_hours=time_window_hours,
            driver_wage_sgd_per_hour=driver_wage,
            fuel_cost_sgd_per_km=fuel_cost,
        )
        st.session_state.vrp_result = result
        st.session_state.vrp_params = {
            "time_window_hours": time_window_hours,
            "num_trucks": num_trucks,
        }
    else:
        result = st.session_state.vrp_result

    # ── Metric cards ────────────────────────────────────────────────────────
    total_delivered = sum(len(route) for route in result["routes"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Distance", f"{result['total_km']:.1f} km")
    m2.metric("Total Cost", f"${result['total_cost_sgd']:.2f}")
    m3.metric(
        "Deliveries Served",
        f"{total_delivered}/{len(customers_df)}",
    )
    m4.metric("Solve Time", f"{result['solve_time_ms']:.0f} ms")

    if result["infeasible"] and result["unassigned"]:
        st.error(
            f"❌ {len(result['unassigned'])} deliveries cannot be served "
            f"in {time_window_hours}h window:"
        )
        for cid in result["unassigned"]:
            row = customers_df[customers_df["customer_id"] == cid].iloc[0]
            st.markdown(
                f"  - **{row['name']}** "
                f"({row['time_window_start']}–{row['time_window_end']})"
            )
    elif not result["infeasible"]:
        st.success(f"✅ All {total_delivered} deliveries served in {time_window_hours}h window")

    # ── Folium map ──────────────────────────────────────────────────────────
    _render_map(result, customers_df)

    # ── Route table ─────────────────────────────────────────────────────────
    st.subheader("Routes")
    for i, route in enumerate(result["routes"]):
        if route:
            route_names = [
                customers_df[customers_df["customer_id"] == cid]["name"].values[0]
                for cid in route
            ]
            st.markdown(f"**Route {i+1} ({len(route)} stops):** {' → '.join(route_names)}")

    # ── Clear typhoon ───────────────────────────────────────────────────────
    if is_typhoon:
        if st.sidebar.button("Clear Typhoon Scenario"):
            for key in ["vrp_result", "vrp_params"]:
                st.session_state.pop(key, None)
            st.session_state.typhoon_active = False
            st.rerun()
else:
    _render_map_empty()


# ── Map helpers ─────────────────────────────────────────────────────────────

ROUTE_COLORS = {0: "red", 1: "blue", 2: "green", 3: "purple", 4: "orange"}


def _render_map(result: dict, customers_df: pd.DataFrame) -> None:
    """Render the Folium map with depot, customer markers, and route polylines."""
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.error("Map libraries not installed. Run: uv add folium streamlit-folium")
        return

    m = folium.Map(
        location=[DEPOT_LAT, DEPOT_LNG],
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    # Depot marker
    folium.Marker(
        [DEPOT_LAT, DEPOT_LNG],
        popup="GreenLoop Farm — Jurong Innovation District Depot",
        icon=folium.Icon(color="blue", icon="home"),
    ).add_to(m)

    # Build assignment lookup: customer_id → route index
    assignment: dict[str, int] = {}
    for route_idx, route in enumerate(result["routes"]):
        for cid in route:
            assignment[cid] = route_idx

    # Customer markers colored by route
    for _, row in customers_df.iterrows():
        cid = row["customer_id"]
        route_idx = assignment.get(cid, -1)
        color = ROUTE_COLORS.get(route_idx, "gray")
        folium.CircleMarker(
            [row["lat"], row["lng"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=(
                f"<b>{row['name']}</b><br>"
                f"ID: {cid}<br>"
                f"Window: {row['time_window_start']}–{row['time_window_end']}<br>"
                f"{row['weekly_kg']} kg/week"
            ),
        ).add_to(m)

    # Route polylines: depot → customers → depot
    for route_idx, route in enumerate(result["routes"]):
        if not route:
            continue
        coords = [[DEPOT_LAT, DEPOT_LNG]]
        for cid in route:
            row = customers_df[customers_df["customer_id"] == cid].iloc[0]
            coords.append([row["lat"], row["lng"]])
        coords.append([DEPOT_LAT, DEPOT_LNG])  # return to depot
        folium.PolyLine(
            coords,
            color=ROUTE_COLORS.get(route_idx, "gray"),
            weight=3,
            opacity=0.7,
        ).add_to(m)

    st_folium(m, width="100%", height=500)
    st.caption("🟦 Depot  |  🔴 Route 1  |  🔵 Route 2  |  🟢 Route 3")


def _render_map_empty() -> None:
    """Render an empty map when no VRP result is available yet."""
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("Map libraries not installed.")
        return

    m = folium.Map(
        location=[DEPOT_LAT, DEPOT_LNG],
        zoom_start=12,
        tiles="OpenStreetMap",
    )
    folium.Marker(
        [DEPOT_LAT, DEPOT_LNG],
        popup="GreenLoop Farm — Jurong Innovation District Depot",
        icon=folium.Icon(color="blue", icon="home"),
    ).add_to(m)
    st_folium(m, width="100%", height=500)
    st.info("Press **Solve VRP** to compute delivery routes.")
