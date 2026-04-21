"""Tests for the MILP diversity constraint (max 30% racks per crop).

C7: No single crop may be assigned to more than MAX_RACKS_PER_CROP tiers.
With 10 tiers and 0.3 cap, that's at most 3 racks per crop.
"""

import pandas as pd
import pytest

from greenloop.layer2.optimizer import build_and_solve
from greenloop.utils.config import CROP_IDS


@pytest.fixture
def crops_df():
    from greenloop.data.loader import load_crops

    return load_crops()


@pytest.fixture
def electricity_df():
    rows = []
    for hour in range(24):
        rate = 0.28 if 8 <= hour < 22 else 0.18
        rows.append({"date": "2025-10-15", "hour": hour, "tariff_rate_sgd_per_kwh": rate})
    return pd.DataFrame(rows)


@pytest.fixture
def staff_df():
    return pd.DataFrame({
        "staff_id": [f"S{i:03d}" for i in range(1, 9)],
        "name": ["Ahmad", "Wei Lin", "Priya", "Jun Hao", "Siti", "Ravi", "Mei Ying", "Ismail"],
        "availability": [
            "morning,afternoon", "morning,afternoon", "morning",
            "afternoon,night", "morning,afternoon,night", "night",
            "morning,afternoon", "afternoon,night",
        ],
        "hourly_rate_sgd": [12.5, 13.0, 14.0, 12.0, 15.0, 16.0, 11.5, 13.5],
    })


@pytest.fixture
def forecast():
    return {
        cid: {"predicted_kg": 80.0, "lower_ci": 65.0, "upper_ci": 100.0}
        for cid in CROP_IDS
    }


class TestDiversityConstraint:
    """Verify C7 diversity constraint is enforced by the MILP."""

    def test_no_crop_exceeds_30_percent_by_default(self, forecast, crops_df, electricity_df, staff_df):
        """With 10 tiers and 30% cap, no crop should exceed 3 rack assignments."""
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        layout = result["rack_layout"]

        from collections import Counter
        crop_counts = Counter(layout.values())
        max_allowed = int(0.3 * len(layout))

        for crop_id, count in crop_counts.items():
            assert count <= max_allowed, (
                f"Crop {crop_id} assigned to {count} racks, exceeds 30% cap ({max_allowed})"
            )

    def test_plan_has_at_least_4_different_crops(self, forecast, crops_df, electricity_df, staff_df):
        """A realistic farm plan should use at least 4 distinct crops across 10 racks."""
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)
        layout = result["rack_layout"]

        unique_crops = set(layout.values())
        assert len(unique_crops) >= 4, (
            f"Plan uses only {len(unique_crops)} crops: {unique_crops}. "
            "Expected at least 4 for a diverse farm portfolio."
        )

    def test_diversity_constraint_does_not_cause_infeasibility(self, forecast, crops_df, electricity_df, staff_df):
        """Diversity cap should not make the problem infeasible with 10 tiers and 10 crops."""
        result = build_and_solve(forecast, crops_df, electricity_df, staff_df)

        # Solver should return a valid plan dict, not None (which signals infeasibility)
        assert result is not None, "Diversity constraint may have made the problem infeasible"
        assert "rack_layout" in result
        assert len(result["rack_layout"]) == 10
