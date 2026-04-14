"""Layer 2 scenario modifiers — Typhoon and plan comparison utilities."""

import copy


def apply_typhoon(base_plan_kwargs: dict) -> dict:
    """Modify kwargs for Typhoon scenario: delivery_hours=6, re-solve.

    Returns a new dict with delivery_hours set to 6. Does NOT mutate
    the original base_plan_kwargs.

    Parameters
    ----------
    base_plan_kwargs : dict
        Keyword arguments suitable for ``build_and_solve(**kwargs)``.

    Returns
    -------
    dict
        Modified kwargs with ``delivery_hours=6``.
    """
    modified = copy.deepcopy(base_plan_kwargs)
    modified["delivery_hours"] = 6
    return modified


def compare_plans(plan_before: dict, plan_after: dict) -> dict:
    """Return a structured before/after comparison of two plans.

    Parameters
    ----------
    plan_before : dict
        The baseline plan (e.g. normal conditions).
    plan_after : dict
        The modified plan (e.g. typhoon scenario).

    Returns
    -------
    dict
        ``{"before": {...}, "after": {...}, "delta": {...}}``
        where ``delta`` contains the numeric differences for key metrics.
    """
    before_breakdown = plan_before.get("cost_breakdown", {})
    after_breakdown = plan_after.get("cost_breakdown", {})

    delta: dict = {
        "objective_value_sgd": round(
            plan_after.get("objective_value_sgd", 0)
            - plan_before.get("objective_value_sgd", 0),
            2,
        ),
    }

    # Add per-component deltas from cost_breakdown.
    for key in ("revenue", "electricity", "labour", "waste_penalty"):
        delta[key] = round(
            after_breakdown.get(key, 0) - before_breakdown.get(key, 0), 2
        )

    # Staff shift deltas.
    before_staff = {s["shift"]: s["staff_count"] for s in plan_before.get("staff_shifts", [])}
    after_staff = {s["shift"]: s["staff_count"] for s in plan_after.get("staff_shifts", [])}
    staff_delta = {}
    for shift_name in ("morning", "afternoon", "night"):
        staff_delta[shift_name] = after_staff.get(shift_name, 0) - before_staff.get(shift_name, 0)
    delta["staff_shifts"] = staff_delta

    # Temperature delta.
    delta["room_temp_target_c"] = (
        plan_after.get("room_temp_target_c", 0)
        - plan_before.get("room_temp_target_c", 0)
    )

    return {
        "before": {
            "objective_value_sgd": plan_before.get("objective_value_sgd"),
            "cost_breakdown": before_breakdown,
            "room_temp_target_c": plan_before.get("room_temp_target_c"),
        },
        "after": {
            "objective_value_sgd": plan_after.get("objective_value_sgd"),
            "cost_breakdown": after_breakdown,
            "room_temp_target_c": plan_after.get("room_temp_target_c"),
        },
        "delta": delta,
    }
