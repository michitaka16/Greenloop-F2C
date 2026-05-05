"""Today's Actions — farm-manager task list for GreenLoop Farm OS.

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


def _build_routine_tasks(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract routine tasks from MILP plan outputs."""
    tasks = []
    cv_details = (
        plan.get("cv_diagnosis_summary", {})
        .get("details", {})
    )
    led_schedule = plan.get("led_schedule", {})
    rack_layout = plan.get("rack_layout", {})

    # ── LED on (start of photoperiod — from MILP schedule) ───────────────
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
            "action": "LED panels on",
            "detail": "MILP photoperiod start",
            "role": "Farm Operations",
        })
    else:
        # Default to 6am if no clear schedule
        tasks.append({
            "type": "routine",
            "time": "06:00",
            "action": "LED panels on",
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

    # ── Dispatch ────────────────────────────────────────────────────────────
    staff_shifts = plan.get("staff_shifts", [])
    has_morning = any(
        s.get("shift", "").lower() == "morning" and s.get("staff_count", 0) > 0
        for s in staff_shifts
    )
    if has_morning:
        tasks.append({
            "type": "routine",
            "time": "10:00",
            "action": "Dispatch deliveries",
            "detail": "Morning dispatch — check VRP routes in Logistics tab",
            "role": "Logistics",
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
            "action": "LED panels off",
            "detail": "Peak tariff avoidance",
            "role": "Farm Operations",
        })
    else:
        tasks.append({
            "type": "routine",
            "time": "17:00",
            "action": "LED panels off",
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
        routine_tasks = _build_routine_tasks(plan)

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
                            key=f"priority_{task['rack']}_{task['action']}",
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
                role_badge = f"[{role}]" if role else ""
                st.checkbox(
                    f"□ **{time_str}** — {action} {role_badge} ({detail})",
                    value=False,
                    key=f"routine_{time_str}_{action[:20]}",
                )
