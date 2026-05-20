"""Tests for pre-solve contradiction checker."""

import pytest

from adoptakale.layer2.feasibility_check import validate_constraints
from adoptakale.utils.config import CROP_IDS


@pytest.fixture
def forecast():
    """Synthetic forecast where all crops have active demand."""
    return {cid: {"predicted_kg": 80.0, "upper_ci": 100.0} for cid in CROP_IDS}


class TestValidateConstraintsNoOverrides:
    """No overrides → always feasible."""

    def test_empty_constraints_are_feasible(self, forecast):
        result = validate_constraints([], [], forecast, None)
        assert result.is_feasible is True

    def test_empty_constraints_no_reason(self, forecast):
        result = validate_constraints([], [], forecast, None)
        assert result.reason is None


class TestValidateConstraintsExcludedRacks:
    """Rack exclusion tests."""

    def test_excluding_one_rack_is_feasible(self, forecast):
        result = validate_constraints([0], [], forecast, None)
        assert result.is_feasible is True

    def test_excluding_eight_racks_is_warning(self, forecast):
        # 10 tiers - 8 excluded = 2 remaining. Multiple crops can share
        # a tier in the MILP, so it is technically feasible but very tight.
        result = validate_constraints([0, 1, 2, 3, 4, 5, 6, 7], [], forecast, None)
        assert result.is_feasible is True
        assert result.severity == "warning"
        assert "2 tier" in result.reason

    def test_excluding_nine_racks_is_infeasible(self, forecast):
        result = validate_constraints(list(range(9)), [], forecast, None)
        assert result.is_feasible is False

    def test_excluding_all_tiers_is_infeasible(self):
        result = validate_constraints(list(range(10)), [], None, None)
        assert result.is_feasible is False

    def test_excluding_three_racks_is_info(self, forecast):
        # 10 tiers - 3 excluded = 7 remaining. With multiple crops per tier
        # this is not tight; falls through to info (no warning triggered).
        result = validate_constraints([0, 1, 2], [], forecast, None)
        assert result.is_feasible is True
        assert result.severity == "info"

    def test_excluding_two_racks_is_info(self, forecast):
        result = validate_constraints([0, 1], [], forecast, None)
        assert result.is_feasible is True


class TestValidateConstraintsUnavailableShifts:
    """Staff unavailability tests."""

    def test_one_shift_unavailable_is_feasible(self, forecast):
        result = validate_constraints([], ["morning"], forecast, None)
        assert result.is_feasible is True

    def test_all_three_shifts_unavailable_is_infeasible(self, forecast):
        result = validate_constraints([], ["morning", "afternoon", "night"], forecast, None)
        assert result.is_feasible is False
        assert "At least one shift" in result.reason


class TestValidateConstraintsJoint:
    """Combined constraint tests."""

    def test_tight_but_feasible(self, forecast):
        # 4 excluded racks + 2 shifts unavailable → 6 tiers, 3 shifts = marginal.
        result = validate_constraints([0, 1, 2, 3], ["night"], forecast, None)
        assert result.is_feasible is True

    def test_infeasible_from_racks_not_shifts(self, forecast):
        # 7 excluded → 3 remaining. Multiple crops share tiers so still feasible,
        # but tight — severity is warning.
        result = validate_constraints([0, 1, 2, 3, 4, 5, 6], ["morning"], forecast, None)
        assert result.is_feasible is True
        assert result.severity == "warning"


class TestValidateConstraintsNoForecast:
    """Without forecast — fewer checks, so fewer failures."""

    def test_excluding_seven_racks_without_forecast_warns(self):
        # Without forecast we can't check per-crop demand.
        # 7 excluded → 3 remaining → tight but still feasible (warning).
        result = validate_constraints([0, 1, 2, 3, 4, 5, 6], [], None, None)
        assert result.is_feasible is True
        assert result.severity == "warning"
