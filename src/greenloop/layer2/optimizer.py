"""Layer 2 — MILP constraint optimization using OR-Tools CP-SAT solver.

Builds and solves a mixed-integer linear program that maximizes profit
(Revenue - Electricity - Labour - Waste) for a single-day farm plan.

CP-SAT requires all variables and expressions to be integers. Continuous
values (SGD costs, temperatures) are scaled by COST_SCALE=100 so that
$18.42 is represented as 1842.
"""

import logging
import time
from collections import defaultdict
from datetime import date

import pandas as pd
from ortools.sat.python import cp_model

from greenloop.layer2.exceptions import InfeasibleError
from greenloop.layer2.objective import ObjectiveWeights
from greenloop.utils.config import (
    CROP_IDS,
    MAX_SHIFT_HOURS,
    OFF_PEAK_RATE_SGD,
    PEAK_HOURS,
    PEAK_RATE_SGD,
    SHIFTS,
)

logger = logging.getLogger(__name__)

# Scaling factor: multiply SGD floats by this to get integers for CP-SAT.
COST_SCALE = 100

NUM_TIERS = 10
NUM_HOURS = 24
NUM_CROPS = len(CROP_IDS)
TANK_CAPACITY_L = 10.0
# Water scale: multiply litres by this so the constraint is integer.
WATER_SCALE = 10

# LED power draw per tier per hour (kWh). Simplified: 1 tier on for 1 hour = 0.5 kWh.
LED_KWH_PER_TIER_HOUR = 0.5

# Workload balance penalty weight (scaled).
BALANCE_PENALTY_WEIGHT = 50

# Peak multiplier for LED cost during peak hours.
PEAK_LED_MULTIPLIER = 1.5

SHIFT_NAMES = list(SHIFTS.keys())  # ["morning", "afternoon", "night"]


def _shift_hours(shift_name: str) -> int:
    """Return the number of hours in a shift (always MAX_SHIFT_HOURS=8)."""
    return MAX_SHIFT_HOURS


def _get_new_planting_crops(crops_df: pd.DataFrame) -> list[str]:
    """Return crop_ids that are in early growth stage (new plantings).

    For demo: uses crops with growth_days > 25 as "new planting".
    In production this would be driven by CV diagnosis.
    """
    new_planting = []
    for _, row in crops_df.iterrows():
        growth_days_val = row.get("growth_days", 0)
        if growth_days_val > 25:
            new_planting.append(row["crop_id"])
    return new_planting


def _available_for_shift(staff_df: pd.DataFrame, shift_name: str) -> int:
    """Count how many staff members list *shift_name* in their availability."""
    count = 0
    for avail in staff_df["availability"]:
        if shift_name in str(avail).split(","):
            count += 1
    return count


def _avg_hourly_rate_scaled(staff_df: pd.DataFrame) -> int:
    """Average hourly rate in scaled-integer cents."""
    avg = staff_df["hourly_rate_sgd"].mean()
    return int(round(avg * COST_SCALE))


def build_and_solve(
    forecast: dict,
    crops_df: pd.DataFrame,
    electricity_df: pd.DataFrame,
    staff_df: pd.DataFrame,
    delivery_hours: int = 12,
    available_headcount: int = 6,
    tariff_rate: float | None = None,
    cv_diagnosis: dict | None = None,
    seed_supply_delayed: bool = False,
    seed_stock_kg: dict | None = None,
    growth_days: dict | None = None,
    power_outage: bool = False,
    # --- HITL parameters ---
    excluded_racks: list[int] | None = None,
    unavailable_shifts: list[str] | None = None,
    objective_weights: ObjectiveWeights | None = None,
) -> dict:
    """Build and solve the MILP model.

    Parameters
    ----------
    forecast : dict
        Layer 1 output: {crop_id: {predicted_kg, lower_ci, upper_ci}}.
    crops_df : pd.DataFrame
        Crop master data.
    electricity_df : pd.DataFrame
        Hourly tariff data.
    staff_df : pd.DataFrame
        Staff roster.
    delivery_hours : int
        Hours available for delivery (default 12; Typhoon sets to 6).
    available_headcount : int
        Max staff on any single shift.
    tariff_rate : float | None
        If set, overrides the per-hour tariff from electricity_df.
    cv_diagnosis : dict | None
        Layer 1b CV diagnosis results: {rack_id: DiagnosisResult}.
        When provided, applies the following MILP adjustments:
        - growth_stage=early: reduce expected_yield by 40%
        - growth_stage=mid: reduce expected_yield by 10%
        - nutrition_status=nitrogen_low: increase nutrient cost by 15%
        - nutrition_status=water_stress: increase irrigation frequency by 1x
        - confidence < 0.70: apply 50% wider uncertainty band
    seed_supply_delayed : bool
        If True, applies a constraint limiting new tier assignments per crop
        based on available seed stock and growth cycle (seed_stock_kg / growth_days).
        Logs a warning when active.
    seed_stock_kg : dict | None
        Per-crop seed stock in kg. Required when seed_supply_delayed=True.
        Format: {crop_id: seed_stock_kg}
    growth_days : dict | None
        Per-crop growth days. Required when seed_supply_delayed=True.
        Format: {crop_id: growth_days}
    power_outage : bool
        If True, LEDs fail, yield_multiplier=0.0 for all crops (growth stopped),
        emergency harvest mode activated. Logs a warning when active.
    excluded_racks : list[int] | None
        Tier numbers (0-indexed) to exclude from today's plan.
        Adds a hard constraint: no crop can be assigned to these tiers.
    unavailable_shifts : list[str] | None
        Shift names (e.g. ["morning"]) with no staff available today.
        Sets staff_count to 0 for those shifts.
    objective_weights : ObjectiveWeights | None
        Explicit weight multipliers for the objective function terms.
        Supports HITL mode toggle (profit/sustainability/balanced).
        Defaults to all-1.0 (equivalent to previous implicit weights).

    Returns
    -------
    dict
        Optimized daily plan.

    Raises
    ------
    InfeasibleError
        When no feasible solution exists (e.g. available_headcount=0).
    """
    # --- Power outage handling ---
    if power_outage:
        logger.warning("optimizer.power_outage.active")
        # Emergency harvest mode: set yield_multiplier=0.0 for all crops
        # by pre-populating _cv_yield_mult with zeros
        if not hasattr(build_and_solve, "_power_outage_yield_mult"):
            build_and_solve._power_outage_yield_mult = {}  # type: ignore[attr-defined]
        for cid in CROP_IDS:
            build_and_solve._power_outage_yield_mult[cid] = 0.0  # type: ignore[attr-defined]

    logger.info(
        "optimizer.build_and_solve.start",
        extra={
            "delivery_hours": delivery_hours,
            "available_headcount": available_headcount,
            "tariff_override": tariff_rate is not None,
            "power_outage": power_outage,
        },
    )
    t0 = time.monotonic()

    model = cp_model.CpModel()

    # ---------------------------------------------------------------
    # Build per-hour tariff lookup (scaled integer cents).
    # ---------------------------------------------------------------
    hourly_tariff_scaled: list[int] = []
    if tariff_rate is not None:
        hourly_tariff_scaled = [int(round(tariff_rate * COST_SCALE))] * NUM_HOURS
    else:
        tariff_by_hour: dict[int, float] = {}
        for _, row in electricity_df.iterrows():
            h = int(row["hour"])
            tariff_by_hour[h] = float(row["tariff_rate_sgd_per_kwh"])
        for h in range(NUM_HOURS):
            rate = tariff_by_hour.get(h, PEAK_RATE_SGD if h in PEAK_HOURS else OFF_PEAK_RATE_SGD)
            hourly_tariff_scaled.append(int(round(rate * COST_SCALE)))

    # ---------------------------------------------------------------
    # Index helpers
    # ---------------------------------------------------------------
    crop_price_scaled = {}
    crop_spoilage_scaled = {}
    crop_water_per_tray_scaled = {}
    crop_led_hours = {}

    crop_prices: dict[str, float] = {}
    crop_spoilage: dict[str, float] = {}
    for _, row in crops_df.iterrows():
        cid = row["crop_id"]
        crop_price_scaled[cid] = int(round(float(row["price_sgd_per_kg"]) * COST_SCALE))
        crop_spoilage_scaled[cid] = int(round(float(row["spoilage_rate"]) * COST_SCALE))
        crop_water_per_tray_scaled[cid] = int(round(float(row["water_per_tray"]) * WATER_SCALE))
        crop_led_hours[cid] = int(row["led_hours_per_day"])
        # Non-scaled versions for dashboard profit-band computation
        crop_prices[cid] = float(row["price_sgd_per_kg"])
        crop_spoilage[cid] = float(row["spoilage_rate"])

    avg_rate_scaled = _avg_hourly_rate_scaled(staff_df)

    # ---------------------------------------------------------------
    # Layer 1b CV Diagnosis: apply adjustments to crop parameters
    # ---------------------------------------------------------------
    # Track nutrient cost adjustment across all diagnosed racks.
    # If all racks report nitrogen_low, the nutrient budget may be exceeded.
    # We track this as a cost term so the solver can balance trade-offs.
    nutrient_cost_adjustment: float = 0.0
    water_freq_boost: dict[int, int] = {}  # crop_idx → additional water freq boost

    if cv_diagnosis is not None:
        # Map rack_id → DiagnosisResult using positional mapping.
        # rack_id format: "tier_N" where N is 0-9.
        # tier_N maps to CROP_IDS[N] (tier_0 → kai_lan, tier_9 → mint).
        crop_diagnosis: dict[str, object] = {}
        for rack_id, diag in cv_diagnosis.items():
            parts = rack_id.split("_")
            if len(parts) == 2 and parts[0] == "tier":
                try:
                    tier_num = int(parts[1])
                    if 0 <= tier_num < NUM_CROPS:
                        cid = CROP_IDS[tier_num]
                        crop_diagnosis[cid] = diag
                except ValueError:
                    pass
            else:
                # Legacy support: "crop_name_RACKID" format (e.g. "basil_A")
                crop_name = parts[0].lower()
                for cid in CROP_IDS:
                    if cid.replace("_", " ").startswith(crop_name) or crop_name in cid:
                        crop_diagnosis[cid] = diag
                        break

        for cid, diag in crop_diagnosis.items():
            # Find crop index
            try:
                c_idx = CROP_IDS.index(cid)
            except ValueError:
                continue

            # --- Growth stage yield adjustment ---
            # Adjust upper_ci used in revenue/waste calculations.
            # We store an adjustment factor applied later in the revenue calc.
            yield_multiplier = 1.0
            if diag.growth_stage == "early":
                yield_multiplier = 0.60  # 40% reduction
            elif diag.growth_stage == "mid":
                yield_multiplier = 0.90  # 10% reduction
            elif diag.growth_stage == "harvest_ready":
                yield_multiplier = 1.0  # confirmed

            # Store multiplier in a lookup for use in revenue/waste calculation
            if not hasattr(build_and_solve, "_cv_yield_mult"):
                build_and_solve._cv_yield_mult = {}  # type: ignore[attr-defined]
            build_and_solve._cv_yield_mult[cid] = yield_multiplier  # type: ignore[attr-defined]

            # --- Nutrition adjustment ---
            if diag.nutrition_status == "nitrogen_low":
                # Increase nutrient cost: +15% per diagnosed rack
                # We track this as a cost addition (proxied via labour cost increase)
                nutrient_cost_adjustment += 0.15
                logger.info(
                    "optimizer.cv.nitrogen_low",
                    extra={"rack": getattr(diag, "rack_id", "?"), "cid": cid},
                )
            elif diag.nutrition_status == "water_stress":
                # Increase irrigation frequency by 1x for water-stress racks
                if c_idx not in water_freq_boost:
                    water_freq_boost[c_idx] = 0
                water_freq_boost[c_idx] += 1
                logger.info(
                    "optimizer.cv.water_stress",
                    extra={"rack": getattr(diag, "rack_id", "?"), "cid": cid},
                )

            # --- Low confidence: widen uncertainty band ---
            if diag.growth_confidence < 0.70:
                # Apply 50% wider uncertainty band — reduce effective yield by extra 20%
                if hasattr(build_and_solve, "_cv_yield_mult"):
                    build_and_solve._cv_yield_mult[cid] = (
                        build_and_solve._cv_yield_mult.get(cid, 1.0) * 0.80  # type: ignore[index]
                    )
                logger.warning(
                    "optimizer.cv.low_confidence",
                    extra={
                        "rack": getattr(diag, "rack_id", "?"),
                        "confidence": diag.growth_confidence,
                    },
                )

    # ---------------------------------------------------------------
    # Decision variables
    # ---------------------------------------------------------------

    # 1. LED on/off per tier per hour — binary (10 x 24)
    led = {}
    for t in range(NUM_TIERS):
        for h in range(NUM_HOURS):
            led[t, h] = model.new_bool_var(f"led_t{t}_h{h}")

    # 2. Staff count per shift — integer [0, available_headcount]
    unavailable_shifts = unavailable_shifts or []
    staff_count = {}
    for s_idx, s_name in enumerate(SHIFT_NAMES):
        if s_name in unavailable_shifts:
            # Hard constraint: no staff for this shift today.
            staff_count[s_idx] = model.new_int_var(0, 0, f"staff_{s_name}")
            logger.info("optimizer.constraint.shift_unavailable", shift=s_name)
        else:
            cap = min(available_headcount, _available_for_shift(staff_df, s_name))
            staff_count[s_idx] = model.new_int_var(0, cap, f"staff_{s_name}")

    # 3. Crop-to-tier assignment — binary (5 x 10)
    assign = {}
    for c in range(NUM_CROPS):
        for t in range(NUM_TIERS):
            assign[c, t] = model.new_bool_var(f"assign_c{c}_t{t}")

    # 4. Room temperature target — integer [18, 26]
    room_temp = model.new_int_var(18, 26, "room_temp")

    # 5. Watering frequency per crop — integer [1 + boost, 4 + boost]
    # Boost applied if crop diagnosed as water_stress (from CV diagnosis).
    water_freq = {}
    for c in range(NUM_CROPS):
        boost = water_freq_boost.get(c, 0)
        water_freq[c] = model.new_int_var(
            1 + boost,
            min(4 + boost, 6),
            f"water_freq_c{c}",
        )

    # ---------------------------------------------------------------
    # Hard constraints
    # ---------------------------------------------------------------

    # C1: Each active tier grows at least 1 crop (LED panel serves multiple crops).
    #     Excluded tiers are handled by C1c (0 assignment).
    excluded_racks = excluded_racks or []
    active_tiers = [t for t in range(NUM_TIERS) if t not in excluded_racks]
    for t in active_tiers:
        model.add(sum(assign[c, t] for c in range(NUM_CROPS)) >= 1)

    # C1b: Each crop gets at least 1 tier — prevents the optimizer from
    #      putting all tiers on the single most profitable crop.
    for c in range(NUM_CROPS):
        model.add(sum(assign[c, t] for t in range(NUM_TIERS)) >= 1)

    # C1c: HITL — excluded racks cannot be assigned to any crop.
    if excluded_racks:
        for t in excluded_racks:
            for c in range(NUM_CROPS):
                model.add(assign[c, t] == 0)
        logger.info("optimizer.constraint.racks_excluded", excluded_racks=excluded_racks)

    # C2: MOM — each shift <= MAX_SHIFT_HOURS (structurally guaranteed
    #     because _shift_hours returns 8, and we use that as the hours value).

    # C3: Harvest window — at least 1 shift must have staff > 0.
    model.add(sum(staff_count[s] for s in range(len(SHIFT_NAMES))) >= 1)

    # C4: Water constraint — freq * water_per_tray <= TANK_CAPACITY for each crop.
    #     Scaled: freq * water_scaled <= TANK_CAPACITY * WATER_SCALE.
    tank_scaled = int(TANK_CAPACITY_L * WATER_SCALE)
    for c in range(NUM_CROPS):
        cid = CROP_IDS[c]
        # water_freq[c] * water_per_tray_scaled <= tank_scaled
        model.add(water_freq[c] * crop_water_per_tray_scaled[cid] <= tank_scaled)

    # C5: LED hours per tier must respect the assigned crop's requirement.
    #     If crop c is on tier t, the tier's LED-on hours must be at least
    #     80% of the crop's daily requirement. This links LED decisions to
    #     crop assignments and prevents the optimizer from turning all LEDs off.
    for t in range(NUM_TIERS):
        total_led_t = sum(led[t, h] for h in range(NUM_HOURS))
        for c in range(NUM_CROPS):
            cid = CROP_IDS[c]
            min_hours = max(1, crop_led_hours[cid] * 4 // 5)  # 80%
            model.add(total_led_t >= min_hours).only_enforce_if(assign[c, t])

    # ---------------------------------------------------------------
    # C6: Seed supply delay constraint — limit new tier assignments
    #      based on seed stock availability and growth cycle.
    # ---------------------------------------------------------------
    if seed_supply_delayed:
        logger.warning(
            "optimizer.seed_supply_delayed.active",
            extra={"cid": "all"},
        )
        # Default seed_stock_kg and growth_days to 1.0 if not provided
        # (avoids division by zero; effectively no constraint if stock is ample)
        seed_stock = defaultdict(lambda: 1.0, seed_stock_kg or {})
        growth = defaultdict(lambda: 1.0, growth_days or {})

        new_planting_cids = _get_new_planting_crops(crops_df)

        for c in range(NUM_CROPS):
            cid = CROP_IDS[c]
            # Only apply constraint to crops flagged as new planting
            if cid not in new_planting_cids:
                continue
            max_new_tiers = seed_stock[cid] / growth[cid]
            if max_new_tiers < 1:
                # Cannot assign any new tiers if seed stock is insufficient
                model.add(sum(assign[c, t] for t in range(NUM_TIERS)) <= 0)
            else:
                model.add(
                    sum(assign[c, t] for t in range(NUM_TIERS)) <= int(max_new_tiers)
                )

    # ---------------------------------------------------------------
    # C7: Diversity — no single crop occupies more than 30% of racks.
    # Real Singapore vertical farms (e.g. Greenphyto) run 8+ varieties
    # simultaneously to satisfy restaurant/premium-buyer contracts.
    # ---------------------------------------------------------------
    MAX_RACKS_PER_CROP = int(NUM_TIERS * 0.3)  # = 3 for 10 tiers

    for c in range(NUM_CROPS):
        model.add(
            sum(assign[c, t] for t in range(NUM_TIERS)) <= MAX_RACKS_PER_CROP
        )

    # ---------------------------------------------------------------
    # Objective components (all in scaled-integer cents)
    # ---------------------------------------------------------------

    # --- Revenue ---
    # Revenue = sum over crops of (upper_ci * price * (1 - spoilage_rate) * tiers_assigned)
    # We use upper_ci as the production target per the spec (uncertainty propagation).
    # Tiers assigned to a crop is sum(assign[c, t] for t).
    # Revenue is divided across tiers: upper_ci applies per-crop total, but we scale
    # per tier as upper_ci / NUM_TIERS * tiers * price * (1 - spoilage).
    # Simplified: revenue per crop = upper_ci * price * (1 - spoilage) * (tiers / NUM_TIERS)
    # To keep it integer: precompute revenue_per_tier_scaled for each crop.

    revenue_terms: list = []
    for c in range(NUM_CROPS):
        cid = CROP_IDS[c]
        upper_ci = forecast[cid]["upper_ci"]
        price = crop_price_scaled[cid]  # already scaled
        spoilage = float(crops_df.loc[crops_df["crop_id"] == cid, "spoilage_rate"].iloc[0])

        # Apply CV diagnosis yield multiplier (from Layer 1b growth stage assessment).
        # If cv_diagnosis is None, _cv_yield_mult is not set → default to 1.0.
        # Power outage overrides to 0.0 (emergency harvest mode).
        yield_mult = 1.0
        if hasattr(build_and_solve, "_power_outage_yield_mult"):
            yield_mult = build_and_solve._power_outage_yield_mult.get(cid, 1.0)  # type: ignore[attr-defined]
        elif hasattr(build_and_solve, "_cv_yield_mult"):
            yield_mult = build_and_solve._cv_yield_mult.get(cid, 1.0)  # type: ignore[attr-defined]

        # revenue per tier for this crop (scaled):
        # upper_ci * price_scaled * (1 - spoilage) / NUM_TIERS * yield_mult
        rev_per_tier = int(round(upper_ci * price * (1.0 - spoilage) / NUM_TIERS * yield_mult))
        tiers_assigned = sum(assign[c, t] for t in range(NUM_TIERS))
        revenue_terms.append(rev_per_tier * tiers_assigned)

    total_revenue = sum(revenue_terms)

    # --- Electricity cost ---
    # For each tier and hour where the LED is on, cost = tariff * LED_KWH * multiplier.
    # Peak hours get 1.5x multiplier (soft penalty).
    led_kwh_scaled = int(round(LED_KWH_PER_TIER_HOUR * COST_SCALE))
    electricity_terms: list = []
    for t in range(NUM_TIERS):
        for h in range(NUM_HOURS):
            tariff = hourly_tariff_scaled[h]
            if h in PEAK_HOURS:
                # peak multiplier 1.5x — scale: tariff * 15 / 10
                cost_per_unit = tariff * led_kwh_scaled * 15 // (10 * COST_SCALE)
            else:
                cost_per_unit = tariff * led_kwh_scaled // COST_SCALE
            electricity_terms.append(cost_per_unit * led[t, h])

    total_electricity = sum(electricity_terms)

    # --- Labour cost ---
    # For each shift: staff_count * shift_hours * avg_hourly_rate_scaled.
    labour_terms: list = []
    for s_idx in range(len(SHIFT_NAMES)):
        hours = _shift_hours(SHIFT_NAMES[s_idx])
        labour_terms.append(staff_count[s_idx] * hours * avg_rate_scaled)

    total_labour = sum(labour_terms)

    # --- Waste penalty ---
    # Waste = sum over crops of (spoilage_rate * upper_ci * price * yield_mult * tiers / NUM_TIERS)
    # Yield multiplier from CV diagnosis is applied here too (reduces waste if yield is lower).
    # Power outage sets yield_mult=0.0, so waste is also zero (nothing growing to spoil).
    waste_terms: list = []
    for c in range(NUM_CROPS):
        cid = CROP_IDS[c]
        upper_ci = forecast[cid]["upper_ci"]
        price = crop_price_scaled[cid]
        spoilage = float(crops_df.loc[crops_df["crop_id"] == cid, "spoilage_rate"].iloc[0])
        yield_mult = 1.0
        if hasattr(build_and_solve, "_power_outage_yield_mult"):
            yield_mult = build_and_solve._power_outage_yield_mult.get(cid, 1.0)  # type: ignore[attr-defined]
        elif hasattr(build_and_solve, "_cv_yield_mult"):
            yield_mult = build_and_solve._cv_yield_mult.get(cid, 1.0)  # type: ignore[attr-defined]
        waste_per_tier = int(round(upper_ci * price * spoilage / NUM_TIERS * yield_mult))
        tiers_assigned = sum(assign[c, t] for t in range(NUM_TIERS))
        waste_terms.append(waste_per_tier * tiers_assigned)

    total_waste = sum(waste_terms)

    # --- Workload balance penalty ---
    # Penalize if any shift exceeds 120% of average staff.
    # avg_staff_approx = total_staff / 3. We introduce an auxiliary variable.
    total_staff = sum(staff_count[s] for s in range(len(SHIFT_NAMES)))
    # balance_excess[s] >= staff_count[s] * 3 - total_staff * 12 // 10
    # but we simplify: penalty if staff_count[s] * 10 > total_staff * 4 (i.e. > 120% of avg)
    # We use a penalty term instead of hard constraint.
    balance_penalties: list = []
    for s_idx in range(len(SHIFT_NAMES)):
        excess = model.new_int_var(0, available_headcount * 10, f"balance_excess_{s_idx}")
        # excess >= staff_count[s] * 30 - total_staff * 12  (scaled by 10 to avoid fractions)
        # staff_count * 30 means staff_count * 3 * 10
        # total_staff * 12 means total_staff * 1.2 * 10
        model.add(excess >= staff_count[s_idx] * 30 - total_staff * 12)
        balance_penalties.append(excess * BALANCE_PENALTY_WEIGHT)

    total_balance_penalty = sum(balance_penalties)

    # --- Nutrient cost adjustment (from CV diagnosis: nitrogen_low → +15% nutrient cost) ---
    # This is a fixed cost term — it reduces the objective by a known amount per affected rack.
    # Represented as a scaled integer deduction from revenue.
    nutrient_cost_scaled = int(round(nutrient_cost_adjustment * 100))  # 0.15 → 15 (in scaled cents)

    # --- Objective: Maximize Revenue - Electricity - Labour - Waste - Balance - Nutrient ---
    # Apply HITL objective weights (default: all 1.0).
    weights = objective_weights or ObjectiveWeights()

    # Sustainability bonus: additional reward for off-peak LED usage.
    off_peak_bonus = sum(
        led[t, h]
        for t in range(NUM_TIERS)
        for h in range(NUM_HOURS)
        if h not in PEAK_HOURS
    )

    model.maximize(
        int(weights.revenue) * total_revenue
        - int(weights.electricity) * total_electricity
        - int(weights.labour) * total_labour
        - int(weights.waste) * total_waste
        - int(weights.balance) * total_balance_penalty
        + int(weights.sustainability) * off_peak_bonus
        - nutrient_cost_scaled
    )

    # ---------------------------------------------------------------
    # Solve
    # ---------------------------------------------------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.solve(model)

    solve_time_ms = round((time.monotonic() - t0) * 1000, 1)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        binding = _detect_binding_constraint(available_headcount)
        logger.warning(
            "optimizer.infeasible",
            extra={"status": status, "binding_constraint": binding},
        )
        raise InfeasibleError(
            f"MILP solver returned status {status} — no feasible plan found. "
            f"Check constraints (headcount={available_headcount}, delivery_hours={delivery_hours}).",
            binding_constraint=binding,
        )

    logger.info(
        "optimizer.build_and_solve.ok",
        extra={"status": status, "solve_time_ms": solve_time_ms},
    )

    # ---------------------------------------------------------------
    # Extract solution
    # ---------------------------------------------------------------
    led_schedule: dict[str, list[int]] = {}
    for t in range(NUM_TIERS):
        led_schedule[f"tier_{t}"] = [solver.value(led[t, h]) for h in range(NUM_HOURS)]

    staff_shifts: list[dict] = []
    for s_idx, s_name in enumerate(SHIFT_NAMES):
        staff_shifts.append(
            {
                "shift": s_name,
                "staff_count": solver.value(staff_count[s_idx]),
                "hours": _shift_hours(s_name),
            }
        )

    rack_layout: dict[str, str] = {}
    for t in range(NUM_TIERS):
        for c in range(NUM_CROPS):
            if solver.value(assign[c, t]):
                rack_layout[f"tier_{t}"] = CROP_IDS[c]
                break

    room_temp_val = solver.value(room_temp)

    watering_schedule: dict[str, int] = {}
    for c in range(NUM_CROPS):
        watering_schedule[CROP_IDS[c]] = solver.value(water_freq[c])

    # Cost breakdown — descale from integer cents to SGD floats.
    rev_val = solver.value(total_revenue) / COST_SCALE
    elec_val = solver.value(total_electricity) / COST_SCALE
    lab_val = solver.value(total_labour) / COST_SCALE
    waste_val = solver.value(total_waste) / COST_SCALE
    obj_val = solver.objective_value / COST_SCALE

    cost_breakdown = {
        "revenue": round(rev_val, 2),
        "electricity": round(-elec_val, 2),
        "labour": round(-lab_val, 2),
        "waste_penalty": round(-waste_val, 2),
        "nutrient_adjustment": round(nutrient_cost_adjustment, 2),
    }

    # Uncertainty buffers
    uncertainty_buffers: dict[str, dict] = {}
    for cid in CROP_IDS:
        predicted = forecast[cid]["predicted_kg"]
        upper = forecast[cid]["upper_ci"]
        lower = forecast[cid].get("lower_ci", predicted)
        buffer_pct = round((upper - predicted) / predicted * 100, 1) if predicted > 0 else 0.0
        uncertainty_buffers[cid] = {
            "upper_ci": upper,
            "lower_ci": lower,
            "buffer_pct": buffer_pct,
        }

    # --- CV Diagnosis summary for dashboard before/after comparison ---
    cv_summary: dict | None = None
    if cv_diagnosis is not None:
        cv_summary = {
            "num_diagnosed": len(cv_diagnosis),
            "nitrogen_low_count": sum(
                1 for d in cv_diagnosis.values() if d.nutrition_status == "nitrogen_low"
            ),
            "water_stress_count": sum(
                1 for d in cv_diagnosis.values() if d.nutrition_status == "water_stress"
            ),
            "low_confidence_count": sum(
                1 for d in cv_diagnosis.values() if d.growth_confidence < 0.70
            ),
            "details": {rack_id: d.to_milp_dict() for rack_id, d in cv_diagnosis.items()},
        }

    plan = {
        "plan_date": str(date.today()),
        "objective_value_sgd": round(obj_val, 2),
        "solve_time_ms": solve_time_ms,
        "led_schedule": led_schedule,
        "staff_shifts": staff_shifts,
        "rack_layout": rack_layout,
        "room_temp_target_c": room_temp_val,
        "watering_schedule": watering_schedule,
        "cost_breakdown": cost_breakdown,
        "uncertainty_buffers": uncertainty_buffers,
        "cv_diagnosis_summary": cv_summary,
        "power_outage": power_outage,
        "excluded_racks": excluded_racks or [],
        "unavailable_shifts": unavailable_shifts or [],
        "objective_mode": (
            _infer_mode(weights) if objective_weights is None else _weights_to_mode(weights)
        ),
        # Crop metadata for dashboard profit-band CI computation
        "crop_prices": crop_prices,
        "crop_spoilage": crop_spoilage,
    }

    return plan


def _weights_to_mode(weights: ObjectiveWeights) -> str:
    """Infer which preset mode best matches the given weights (for display)."""
    PRESETS = {
        "profit": ObjectiveWeights.from_mode("profit"),
        "sustainability": ObjectiveWeights.from_mode("sustainability"),
        "balanced": ObjectiveWeights.from_mode("balanced"),
    }
    best_mode = "balanced"
    best_dist = float("inf")
    for mode_name, preset in PRESETS.items():
        dist = abs(weights.revenue - preset.revenue) + abs(
            weights.electricity - preset.electricity
        )
        if dist < best_dist:
            best_dist = dist
            best_mode = mode_name
    return best_mode


def _infer_mode(weights: ObjectiveWeights) -> str:
    """Alias for _weights_to_mode for backward compatibility."""
    return _weights_to_mode(weights)


def _detect_binding_constraint(available_headcount: int) -> str:
    """Heuristic to identify the most likely binding constraint causing infeasibility."""
    if available_headcount <= 0:
        return "harvest_window_requires_staff"
    return "unknown"
