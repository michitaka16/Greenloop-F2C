"""Tests for forecast_band.py — profit CI band computation."""

import pytest

from greenloop.layer2.forecast_band import compute_profit_band, ProfitBand


class TestComputeProfitBand:
    """Profit band from Layer 1 CI propagation."""

    @pytest.fixture
    def base_fixture(self):
        forecast = {
            "kai_lan": {"predicted_kg": 80.0, "lower_ci": 65.0, "upper_ci": 100.0},
            "baby_spinach": {"predicted_kg": 60.0, "lower_ci": 48.0, "upper_ci": 75.0},
            "lettuce_mambo": {"predicted_kg": 55.0, "lower_ci": 40.0, "upper_ci": 68.0},
        }
        cost_breakdown = {
            "revenue": 0.0,  # not used in band calc
            "electricity": 120.0,
            "labour": 180.0,
            "waste_penalty": 30.0,
            "nutrient_adjustment": 15.0,
        }
        crop_prices = {
            "kai_lan": 4.50,
            "baby_spinach": 5.20,
            "lettuce_mambo": 3.80,
        }
        crop_spoilage = {
            "kai_lan": 0.08,
            "baby_spinach": 0.10,
            "lettuce_mambo": 0.06,
        }
        return forecast, cost_breakdown, crop_prices, crop_spoilage

    def test_profit_band_is_profit_band_dataclass(self, base_fixture):
        forecast, cost_breakdown, crop_prices, crop_spoilage = base_fixture
        rack_assignment = {
            "tier_0": "kai_lan",
            "tier_1": "baby_spinach",
            "tier_2": "lettuce_mambo",
        }
        band = compute_profit_band(
            forecast, cost_breakdown, crop_prices, crop_spoilage, rack_assignment
        )
        assert isinstance(band, ProfitBand)
        assert hasattr(band, "profit_expected")
        assert hasattr(band, "profit_low")
        assert hasattr(band, "profit_high")
        assert hasattr(band, "ci_width_pct")

    def test_profit_low_lte_expected_lte_profit_high(self, base_fixture):
        forecast, cost_breakdown, crop_prices, crop_spoilage = base_fixture
        rack_assignment = {
            "tier_0": "kai_lan",
            "tier_1": "baby_spinach",
            "tier_2": "lettuce_mambo",
        }
        band = compute_profit_band(
            forecast, cost_breakdown, crop_prices, crop_spoilage, rack_assignment
        )
        assert band.profit_low <= band.profit_expected <= band.profit_high

    def test_profit_expected_uses_upper_ci(self, base_fixture):
        """Expected profit is computed with upper_ci revenue minus fixed costs."""
        forecast, cost_breakdown, crop_prices, crop_spoilage = base_fixture
        rack_assignment = {"tier_0": "kai_lan"}
        band = compute_profit_band(
            forecast, cost_breakdown, crop_prices, crop_spoilage, rack_assignment
        )
        # Revenue = upper_ci * price * (1 - spoilage) / num_tiers
        # upper_ci = 100.0, price = 4.50, spoilage = 0.08, num_tiers = 10
        expected_rev = 100.0 * 4.50 * (1 - 0.08) / 10  # = 414.0
        total_cost = 120.0 + 180.0 + 30.0 + 15.0  # = 345.0
        assert round(band.profit_expected, 2) == round(expected_rev - total_cost, 2)

    def test_ci_width_pct_is_nonzero_when_lower_ne_upper(self, base_fixture):
        """CI width is positive when lower_ci != upper_ci."""
        forecast, cost_breakdown, crop_prices, crop_spoilage = base_fixture
        rack_assignment = {"tier_0": "kai_lan"}
        band = compute_profit_band(
            forecast, cost_breakdown, crop_prices, crop_spoilage, rack_assignment
        )
        # lower_ci=65, upper_ci=100 → CI width should be > 0
        assert band.ci_width_pct > 0.0

    def test_zero_rack_assignment_returns_negative_profit(self, base_fixture):
        """Empty rack assignment means zero revenue → profit = -total_cost."""
        forecast, cost_breakdown, crop_prices, crop_spoilage = base_fixture
        rack_assignment = {}
        band = compute_profit_band(
            forecast, cost_breakdown, crop_prices, crop_spoilage, rack_assignment
        )
        total_cost = 120.0 + 180.0 + 30.0 + 15.0  # = 345.0
        assert band.profit_expected == -total_cost
        assert band.profit_low == -total_cost
        assert band.profit_high == -total_cost
        assert band.ci_width_pct == 0.0
