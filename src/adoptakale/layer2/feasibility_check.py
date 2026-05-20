"""Pre-solve contradiction checker for Layer 2 HITL manual constraints.

Validates that user-added hard constraints (rack exclusions, staff
unavailability) do not make the MILP problem infeasible before wasting
compute time on a solve that will inevitably fail.
"""

from __future__ import annotations

from dataclasses import dataclass

from adoptakale.utils.config import CROP_IDS, NUM_CROPS, NUM_TIERS, SHIFTS


@dataclass
class ValidationResult:
    """Result of a pre-solve feasibility check."""

    is_feasible: bool
    reason: str | None = None
    severity: str = "error"  # "error" | "warning" | "info"

    def __bool__(self) -> bool:
        return self.is_feasible


def validate_constraints(
    excluded_racks: list[int],
    unavailable_shifts: list[str],
    forecast: dict | None = None,
    crops_df=None,
) -> ValidationResult:
    """Validate that HITL manual constraints are jointly feasible.

    Checks performed
    ---------------
    1. Excluding N racks leaves at least 2 tiers free (minimum for
       meaningful assignment with NUM_CROPS crops).
    2. At least one shift must remain available (delivery requires staff).
    3. Excluded racks must not eliminate all tiers assigned to a crop
       that has non-zero demand (checked if forecast is provided).

    Parameters
    ----------
    excluded_racks : list[int]
        Tier numbers to exclude today (0-indexed).
    unavailable_shifts : list[str]
        Shift names with no staff (e.g. ["morning", "afternoon"]).
    forecast : dict | None
        Layer 1 forecast: {crop_id: {predicted_kg, upper_ci}}.
        If provided, enables the per-crop tier-count check.
    crops_df : pd.DataFrame | None
        Crop master data. Required if forecast is provided.

    Returns
    -------
    ValidationResult
        is_feasible=True if all checks pass.
        is_feasible=False with severity="error" if a hard contradiction exists.
        is_feasible=True with severity="warning" if checks pass but
        constraints are tight (near-infeasible).
    """
    # ---- Check 1: Too many racks excluded ----
    remaining_tiers = NUM_TIERS - len(excluded_racks)
    if remaining_tiers < 2:
        return ValidationResult(
            is_feasible=False,
            severity="error",
            reason=(
                f"Excluding {len(excluded_racks)} racks leaves only "
                f"{remaining_tiers} active tier(s). Minimum 2 tiers required "
                f"to assign {NUM_CROPS} crops (each crop needs ≥1 tier)."
            ),
        )

    # Warn if nearly all tiers are excluded (tight but not infeasible)
    if remaining_tiers <= 3:
        return ValidationResult(
            is_feasible=True,
            severity="warning",
            reason=(
                f"Only {remaining_tiers} tier(s) active. "
                f"Solver may struggle to assign all {NUM_CROPS} crops meaningfully."
            ),
        )

    # ---- Check 2: No shifts available ----
    all_shift_names = list(SHIFTS.keys())
    available_shifts = [s for s in all_shift_names if s not in unavailable_shifts]
    if not available_shifts:
        return ValidationResult(
            is_feasible=False,
            severity="error",
            reason=(
                "All shifts are marked unavailable. "
                "At least one shift must have staff to run the farm."
            ),
        )

    # ---- Check 3: Per-crop tier coverage with forecast ----
    if forecast is not None and crops_df is not None:
        excluded_tiers_set = set(excluded_racks)

        # Build a simple map: crop → how many tiers it could use
        # We don't know the actual assignment, but we can check:
        # if forecast[cid]["upper_ci"] > 0, that crop has active demand
        # and needs at least 1 tier. With N excluded racks, it's possible
        # (but not guaranteed) that the remaining tiers cover all crops.
        crops_with_demand = [
            cid for cid in CROP_IDS
            if cid in forecast and forecast[cid].get("upper_ci", 0) > 0
        ]

        # If we have N crops and M remaining tiers, we need M >= N
        # for a feasible assignment (each crop >= 1 tier).
        if remaining_tiers < len(crops_with_demand):
            return ValidationResult(
                is_feasible=False,
                severity="error",
                reason=(
                    f"Only {remaining_tiers} tier(s) active but "
                    f"{len(crops_with_demand)} crops have active demand. "
                    "Each crop needs at least 1 tier. "
                    "Exclude fewer racks or reduce crop targets."
                ),
            )

    return ValidationResult(is_feasible=True, severity="info", reason=None)
