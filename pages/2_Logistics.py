"""VRP Logistics page — Adopt a Kale Farm OS last-mile delivery routing."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from greenloop.layer2b.vrp_solver import solve_vrp
from greenloop.data.shared_data import load_farm_output

# ── Constants ────────────────────────────────────────────────────────────────
DEPOT_LAT = 1.3328
DEPOT_LNG = 103.7436
ROUTE_COLORS = {0: "red", 1: "blue", 2: "green", 3: "purple", 4: "orange"}


# ── Map helpers (defined before use) ────────────────────────────────────────
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
        popup="Adopt a Kale Farm — Jurong Innovation District Depot",
        icon=folium.Icon(color="blue", icon="home"),
    ).add_to(m)
    st_folium(m, width="100%", height=500)
    st.info("Press **Solve VRP** to compute delivery routes.")


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
        popup="Adopt a Kale Farm — Jurong Innovation District Depot",
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
            r = customers_df[customers_df["customer_id"] == cid].iloc[0]
            coords.append([r["lat"], r["lng"]])
        coords.append([DEPOT_LAT, DEPOT_LNG])  # return to depot
        folium.PolyLine(
            coords,
            color=ROUTE_COLORS.get(route_idx, "gray"),
            weight=3,
            opacity=0.7,
        ).add_to(m)

    st_folium(m, width="100%", height=500)
    st.caption("🟦 Depot  |  🔴 Route 1  |  🔵 Route 2  |  🟢 Route 3")


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Logistics — Adopt a Kale Farm OS",
    layout="wide",
)


# ── Load customer data ───────────────────────────────────────────────────────
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


# ── Sidebar controls ─────────────────────────────────────────────────────────
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

# ── Header ──────────────────────────────────────────────────────────────────
st.title("🚚 Last-Mile Delivery Routing")
st.caption(f"Depot: Jurong Innovation District ({DEPOT_LAT}, {DEPOT_LNG})")

# Load customers early (needed for delivery schedule + solve)
customers_df = load_customers()

# ── Today's Delivery Schedule (shared with Farm OS task list) ─────────────────
vrp_cached = st.session_state.get("vrp_result")
if vrp_cached:
    st.subheader("📦 Today's Delivery Schedule")
    n_routes = len([r for r in vrp_cached.get("routes", []) if r])
    route_cols = st.columns(max(n_routes, 1))
    total_stops = 0
    for ri, route in enumerate(vrp_cached.get("routes", [])):
        if not route:
            continue
        total_stops += len(route)
        with route_cols[ri % max(n_routes, 1)]:
            st.markdown(f"**Route {ri+1}** — {len(route)} stops")
            for cid in route:
                row = customers_df[customers_df["customer_id"] == cid]
                name = row["name"].values[0] if not row.empty else cid
                st.markdown(f"→ {name}")
    km = vrp_cached.get("total_km", 0)
    cost = vrp_cached.get("total_cost_sgd", 0)
    st.caption(f"🚚 {total_stops} deliveries · {km:.1f}km · ${cost:.0f} · Solved in {vrp_cached.get('solve_time_ms', 0):.0f}ms")
    st.divider()

# ── Today's Harvest (from Farm AI) ──────────────────────────────────────────
farm = load_farm_output()
if farm:
    st.subheader("🌾 Today's Harvest (from Farm AI)")

    rack_layout = farm.get("rack_layout", {})
    forecast = farm.get("forecast", {})

    crop_names = {
        "kai_lan": "Kai Lan", "baby_spinach": "Baby Spinach",
        "lettuce_mambo": "Lettuce", "chye_sim": "Chye Sim",
        "arugula": "Arugula", "pak_choi": "Pak Choi",
        "kale": "Kale", "basil_thai": "Thai Basil",
        "coriander": "Coriander", "mint": "Mint",
    }

    crop_colors = {
        "kai_lan": "#1abc9c", "baby_spinach": "#3498db",
        "lettuce_mambo": "#2c3e50", "chye_sim": "#e67e22",
        "arugula": "#2ecc71", "pak_choi": "#00bcd4",
        "kale": "#f1c40f", "basil_thai": "#9b59b6",
        "coriander": "#e74c3c", "mint": "#e91e63",
    }

    # Build per-crop harvest table
    crop_rows = []
    for tier_num in range(10):
        rack_id = f"tier_{tier_num}"
        crop_id = rack_layout.get(rack_id)
        if crop_id and crop_id in forecast:
            vals = forecast[crop_id]
            crop_rows.append({
                "Rack": f"Rack {tier_num}",
                "Crop": crop_names.get(crop_id, crop_id),
                "Predicted Harvest (kg)": round(vals.get("predicted_kg", 0), 1),
                "Lower CI": round(vals.get("lower_ci", 0), 1),
                "Upper CI": round(vals.get("upper_ci", 0), 1),
                "_color": crop_colors.get(crop_id, "#888888"),
            })

    if crop_rows:
        # Summary metric
        total_kg = sum(r["Predicted Harvest (kg)"] for r in crop_rows)
        m_h1, m_h2 = st.columns(2)
        m_h1.metric("Total Predicted Harvest", f"{total_kg:.1f} kg")
        m_h2.metric("Active Racks", f"{len(crop_rows)} / 10")

        # Per-rack cards
        cols = st.columns(min(len(crop_rows), 5))
        for i, r in enumerate(crop_rows):
            with cols[i % len(cols)]:
                color = r["_color"]
                st.markdown(
                    f"""
                    <div style="border:2px solid {color}; border-radius:6px;
                                padding:8px; text-align:center; margin-bottom:4px;">
                        <div style="font-size:0.75em; color:#888;">{r["Rack"]}</div>
                        <div style="font-size:0.9em; font-weight:bold; color:{color};">{r["Crop"]}</div>
                        <div style="font-size:1.1em; font-weight:bold;">{r["Predicted Harvest (kg)"]} kg</div>
                        <div style="font-size:0.7em; color:#aaa;">{r["Lower CI"]} – {r["Upper CI"]} kg</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No rack assignments yet — run Farm AI first.")

    cost = farm.get("cost_breakdown", {})
    if cost:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Farm Revenue", f"${cost.get('revenue', 0):.2f}")
        c2.metric("Energy Cost", f"${abs(cost.get('electricity', 0)):.2f}")
        c3.metric("Labour Cost", f"${abs(cost.get('labour', 0)):.2f}")
        profit = farm.get("objective_value_sgd", 0)
        c4.metric("Farm Profit", f"${profit:.2f}")

    st.caption(f"Source: Farm AI · Plan date: {farm.get('plan_date', 'unknown')}")
    st.divider()
else:
    st.info("🌾 Run **Farm AI** first to see today's harvest data here.")

# ── Solve ────────────────────────────────────────────────────────────────────
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

    # ── Metric cards ─────────────────────────────────────────────────────────
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

    # ── Folium map ───────────────────────────────────────────────────────────
    _render_map(result, customers_df)

    # ── Route table ──────────────────────────────────────────────────────────
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
