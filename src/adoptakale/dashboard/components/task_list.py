"""Today's Actions — farm-manager task list for Adopt a Kale.

Renders a concise action list from the MILP plan and CV diagnosis results,
framed from Amy Tan's perspective (Farm Manager, ACTF Farm #127).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

CROP_DISPLAY_NAMES: dict[str, str] = {
    "kai_lan": "Kai Lan",
    "baby_spinach": "Baby Spinach",
    "lettuce_mambo": "Lettuce",
    "chye_sim": "Chye Sim",
    "arugula": "Arugula",
    "pak_choi": "Pak Choi",
    "kale": "Kale",
    "basil_thai": "Thai Basil",
}

PEAK_HOURS = {17, 18, 19, 20, 21}  # 5–10pm peak tariff


def _priority_label(nutrition_status: str) -> str:
    """Return action verb for a nutrition diagnosis."""
    return {
        "nitrogen_low": "Add nitrogen",
        "water_stress": "Increase irrigation",
    }.get(nutrition_status, "Check crop")


def _harvest_time_for_tier(led_schedule: dict[str, list[int]], tier_name: str) -> int | None:
    """Return the hour (0-23) when LEDs first turn OFF for a tier, or None."""
    schedule = led_schedule.get(tier_name, [])
    if not schedule:
        return None
    for hour, is_on in enumerate(schedule):
        if is_on == 0 and hour > 5:  # Ignore early morning off-hours
            return hour
    return None


def _greeting() -> str:
    """Return a time-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning!"
    elif hour < 17:
        return "Good afternoon!"
    return "Good evening!"


def _build_priority_tasks(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Extract priority tasks from CV diagnosis results in the plan."""
    tasks = []
    cv_details = (
        plan.get("cv_diagnosis_summary", {})
        .get("details", {})
    )

    for rack_id, diag in cv_details.items():
        nutrition = diag.get("nutrition_status", "normal")
        if nutrition in ("nitrogen_low", "water_stress"):
            tier_num = rack_id.replace("tier_", "")
            crop_id = plan.get("rack_layout", {}).get(rack_id, "unknown")
            crop_name = CROP_DISPLAY_NAMES.get(crop_id, crop_id.replace("_", " ").title())
            tasks.append({
                "type": "priority",
                "rack": f"Rack {tier_num}",
                "crop": crop_name,
                "action": _priority_label(nutrition),
                "diagnosis": nutrition.replace("_", " ").replace("nitrogen low", "Nitrogen Low").replace("water stress", "Water Stress"),
            })
    return tasks


def _build_routine_tasks(plan: dict[str, Any], vrp_result: dict | None = None) -> list[dict[str, Any]]:
    """Extract routine tasks from MILP plan outputs."""
    tasks = []
    cv_details = (
        plan.get("cv_diagnosis_summary", {})
        .get("details", {})
    )
    led_schedule = plan.get("led_schedule", {})
    rack_layout = plan.get("rack_layout", {})

    # ── LED Switch on (start of photoperiod — from MILP schedule) ───────────
    # Find earliest tier that turns ON during morning hours (5-8am)
    led_on_hour = None
    for tier_name in sorted(led_schedule.keys()):
        schedule = led_schedule[tier_name]
        for hour in range(5, 9):  # 5am-8am window
            if hour < len(schedule) and schedule[hour] == 1:
                if led_on_hour is None or hour < led_on_hour:
                    led_on_hour = hour
                break
    if led_on_hour is not None:
        tasks.append({
            "type": "routine",
            "time": f"{led_on_hour:02d}:00",
            "action": "LED Switch on",
            "detail": "MILP photoperiod start",
            "role": "Farm Operations",
        })
    else:
        # Default to 6am if no clear schedule
        tasks.append({
            "type": "routine",
            "time": "06:00",
            "action": "LED Switch on",
            "detail": "MILP photoperiod start",
            "role": "Farm Operations",
        })

    # ── Pre-farm check (before photo walkabout) ────────────────────────────
    tasks.append({
        "type": "routine",
        "time": "06:00",
        "action": "Pre-farm check",
        "detail": "Irrigation, LED wiring, rack inspection",
        "role": "Farm Operations",
    })

    # ── Room temperature check ────────────────────────────────────────────────
    room_temp = plan.get("room_temp_target_c")
    if room_temp is not None:
        tasks.append({
            "type": "routine",
            "time": "06:30",
            "action": "Set room temp",
            "detail": f"MILP optimal: {room_temp}°C",
            "role": "Farm Operations",
        })

    # ── Priority tasks (Crop Health) — also shown in Routine ───────────────
    for rack_id, diag in cv_details.items():
        nutrition = diag.get("nutrition_status", "normal")
        if nutrition in ("nitrogen_low", "water_stress"):
            tier_num = rack_id.replace("tier_", "")
            crop_id = plan.get("rack_layout", {}).get(rack_id, "unknown")
            crop_name = CROP_DISPLAY_NAMES.get(crop_id, crop_id.replace("_", " ").title())
            tasks.append({
                "type": "routine",
                "time": "07:00",
                "action": _priority_label(nutrition),
                "detail": f"{crop_name} — Rack {tier_num}",
                "role": "Farm Operations",
                "is_priority": True,
                "rack_id": rack_id,
            })

    # ── Harvest tasks ────────────────────────────────────────────────────────
    for rack_id, diag in cv_details.items():
        if diag.get("growth_stage") == "harvest_ready":
            tier_num = rack_id.replace("tier_", "")
            crop_id = rack_layout.get(rack_id, "unknown")
            crop_name = CROP_DISPLAY_NAMES.get(crop_id, crop_id.replace("_", " ").title())
            tasks.append({
                "type": "routine",
                "time": "09:00",
                "action": f"Harvest Rack {tier_num}",
                "detail": f"{crop_name}",
                "role": "Farm Operations",
            })

    # ── Dispatch — from VRP result ─────────────────────────────────────────
    staff_shifts = plan.get("staff_shifts", [])
    has_morning = any(
        s.get("shift", "").lower() == "morning" and s.get("staff_count", 0) > 0
        for s in staff_shifts
    )
    if has_morning:
        if vrp_result and vrp_result.get("routes"):
            # Build rich route summary
            route_lines = []
            total_stops = 0
            for i, route in enumerate(vrp_result["routes"]):
                if route:
                    route_lines.append(f"Route {i+1}: {len(route)} stops")
                    total_stops += len(route)
            route_str = " / ".join(route_lines) if route_lines else "No routes"
            tasks.append({
                "type": "routine",
                "time": "10:00",
                "action": f"Dispatch ({total_stops} deliveries)",
                "detail": route_str,
                "role": "Logistics",
                "is_delivery": True,
                "vrp_result": vrp_result,
            })
        else:
            tasks.append({
                "type": "routine",
                "time": "10:00",
                "action": "Dispatch deliveries",
                "detail": "Run VRP in Logistics tab → routes appear here",
                "role": "Logistics",
                "is_delivery": True,
            })

    # ── LED off (peak tariff — from MILP schedule) ─────────────────────────
    led_off_hour = None
    for tier_name in sorted(led_schedule.keys()):
        schedule = led_schedule[tier_name]
        for hour in sorted(PEAK_HOURS):
            if hour < len(schedule) and schedule[hour] == 0:
                if led_off_hour is None or hour < led_off_hour:
                    led_off_hour = hour
                break

    if led_off_hour is not None:
        tasks.append({
            "type": "routine",
            "time": f"{led_off_hour:02d}:00",
            "action": "LED Switch off",
            "detail": "Peak tariff avoidance",
            "role": "Farm Operations",
        })
    else:
        tasks.append({
            "type": "routine",
            "time": "17:00",
            "action": "LED Switch off",
            "detail": "Peak tariff avoidance",
            "role": "Farm Operations",
        })

    # ── Review tomorrow's plan ──────────────────────────────────────────────
    tasks.append({
        "type": "routine",
        "time": "18:00",
        "action": "Review tomorrow's plan",
        "detail": "Check Layer 2 dashboard for updated forecast",
        "role": "Supervisor",
    })

    return tasks


def render_today_actions(plan: dict[str, Any] | None) -> None:
    """Render the Today's Actions panel at the top of the Farm OS page.

    Args:
        plan: The MILP plan dict returned by build_and_solve(). May be None.
    """
    import streamlit as st

    if plan is None:
        return

    # Read VRP result shared by Logistics page
    vrp_result = st.session_state.get("vrp_result")

    # ── Header ──────────────────────────────────────────────────────────────
    greeting = _greeting()
    now = datetime.now().strftime("%-I:%M%p").lower()
    container = st.container(border=True)

    with container:
        col_info, col_time = st.columns([3, 1])
        with col_info:
            st.markdown(
                "👩 **Amy Tan** · Farm Manager · ACTF Farm #127\n"
                f"{greeting} Here's your farm status."
            )
        with col_time:
            st.caption(f"Updated {now}")

        st.divider()

        # ── Priority tasks ──────────────────────────────────────────────────
        priority_tasks = _build_priority_tasks(plan)
        routine_tasks = _build_routine_tasks(plan, vrp_result=vrp_result)

        st.markdown("**📋 Today's Actions**")

        if not priority_tasks and not routine_tasks:
            st.info("No actions for today. Everything looks good!")
            return

        # Priority section — driven by Layer 1b Crop Health Diagnosis
        if priority_tasks:
            st.markdown("⚠️ **Priority — Crop Health Diagnosis** *(respond now)*")
            st.caption("Source: Layer 1b Transfer Learning · EfficientNet-B0 on rack leaf images · PlantVillage pre-trained")
            for task in priority_tasks:
                with st.container(border=True):
                    col_act, col_src = st.columns([3, 1])
                    with col_act:
                        st.checkbox(
                            f"**{task['action']}** — {task['rack']} · {task['crop']}",
                            value=False,
                            key=f"priority_task_{task['rack']}",
                        )
                    with col_src:
                        st.caption(f"🔬 {task['diagnosis']}")
            st.divider()

        # Routine section — driven by MILP Layer 2 optimization
        if routine_tasks:
            st.markdown("✓ **Routine**")
            st.caption("Source: Layer 2 MILP optimization · OR-Tools · LED tariff scheduling + staff shifts")
            for task in sorted(routine_tasks, key=lambda t: t["time"]):
                time_str = task["time"]
                action = task["action"]
                detail = task["detail"]
                role = task.get("role", "")
                is_priority = task.get("is_priority", False)
                is_delivery = task.get("is_delivery", False)
                vrp = task.get("vrp_result")
                prefix = "⚠️ " if is_priority else "□ "
                badge = "⚠️ Priority" if is_priority else ""
                role_badge = f"[{role}]" if role else ""
                label = f"{prefix}**{time_str}** — {action} {role_badge} ({detail}) {badge}"
                task_key = task.get("rack_id", "")
                key_str = f"routine_{time_str}_{action[:20]}_{task_key}" if task_key else f"routine_{time_str}_{action[:20]}"

                if is_delivery and vrp:
                    # Expanded delivery route card — synced with Logistics page
                    with st.container(border=True):
                        col_act, col_info2 = st.columns([3, 1])
                        with col_act:
                            st.checkbox(
                                f"**{time_str}** — {action}",
                                value=False,
                                key=key_str,
                            )
                        with col_info2:
                            total_km = vrp.get("total_km", 0)
                            total_cost = vrp.get("total_cost_sgd", 0)
                            st.caption(f"🚚 {total_km:.1f}km · ${total_cost:.0f}")
                        # Show each route inline
                        customers_df = None
                        try:
                            from adoptakale.data.loader import load_customers
                            customers_df = load_customers()
                        except Exception:
                            pass
                        route_cols = st.columns(len(vrp.get("routes", [])))
                        for ri, route in enumerate(vrp.get("routes", [])):
                            if not route:
                                continue
                            with route_cols[ri] if len(vrp["routes"]) <= 4 else st:
                                st.markdown(f"**Route {ri+1}**")
                                for cid in route:
                                    name = cid
                                    if customers_df is not None:
                                        row = customers_df[customers_df["customer_id"] == cid]
                                        if not row.empty:
                                            name = row["name"].values[0]
                                    st.markdown(f"  → {name}")
                else:
                    st.checkbox(
                        label,
                        value=False,
                        key=key_str,
                    )
