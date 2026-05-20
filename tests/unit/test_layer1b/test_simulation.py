"""Tests for Layer 1b simulation module."""

import numpy as np
import pytest

from adoptakale.layer1b.architecture import GROWTH_LABELS, NUTRITION_LABELS, DiagnosisResult
from adoptakale.layer1b.simulation import (
    GROWTH_BADGES,
    NUTRITION_BADGES,
    RACK_SCENARIOS,
    diagnose_all_racks_simulated,
    generate_impacts,
    mock_diagnose,
    mock_diagnose_from_image,
)


class TestMockDiagnose:
    """Tests for mock_diagnose()."""

    def test_returns_diagnosis_result(self):
        result = mock_diagnose("tier_0")
        assert isinstance(result, DiagnosisResult)

    def test_rack_id_preserved(self):
        result = mock_diagnose("tier_3")
        assert result.rack_id == "tier_3"

    def test_growth_stage_valid(self):
        result = mock_diagnose("tier_0")
        assert result.growth_stage in GROWTH_LABELS

    def test_nutrition_status_valid(self):
        result = mock_diagnose("tier_0")
        assert result.nutrition_status in NUTRITION_LABELS

    def test_confidence_range(self):
        result = mock_diagnose("tier_0")
        assert 0.5 <= result.growth_confidence <= 0.99
        assert 0.5 <= result.nutrition_confidence <= 0.99

    def test_probs_sum_to_one(self):
        result = mock_diagnose("tier_0")
        assert abs(sum(result.growth_probs) - 1.0) < 0.01
        assert abs(sum(result.nutrition_probs) - 1.0) < 0.01

    def test_probs_length(self):
        result = mock_diagnose("tier_0")
        assert len(result.growth_probs) == len(GROWTH_LABELS)
        assert len(result.nutrition_probs) == len(NUTRITION_LABELS)

    def test_is_simulated_flag(self):
        result = mock_diagnose("tier_0")
        assert result.is_simulated is True

    def test_unknown_rack_gets_default(self):
        result = mock_diagnose("tier_99")
        assert result.growth_stage in GROWTH_LABELS
        assert result.nutrition_status in NUTRITION_LABELS

    def test_deterministic_scenario_lookup(self):
        """Same rack_id always returns same growth/nutrition combo."""
        # Run multiple times — scenario is fixed, only confidence noise varies
        results = [mock_diagnose("tier_3") for _ in range(5)]
        assert all(r.growth_stage == results[0].growth_stage for r in results)
        assert all(r.nutrition_status == results[0].nutrition_status for r in results)


class TestMockDiagnoseFromImage:
    """Tests for mock_diagnose_from_image()."""

    def test_deterministic_from_same_image(self):
        img = b"fake image bytes for testing"
        r1 = mock_diagnose_from_image(img, "tier_0")
        r2 = mock_diagnose_from_image(img, "tier_0")
        assert r1.growth_stage == r2.growth_stage
        assert r1.nutrition_status == r2.nutrition_status

    def test_different_images_may_differ(self):
        img1 = b"image content A"
        img2 = b"image content B"
        r1 = mock_diagnose_from_image(img1, "tier_0")
        r2 = mock_diagnose_from_image(img2, "tier_0")
        # Not guaranteed to differ, but at least both are valid
        assert r1.growth_stage in GROWTH_LABELS
        assert r2.growth_stage in GROWTH_LABELS

    def test_returns_diagnosis_result(self):
        result = mock_diagnose_from_image(b"test", "tier_5")
        assert isinstance(result, DiagnosisResult)
        assert result.rack_id == "tier_5"
        assert result.is_simulated is True


class TestDiagnoseAllRacks:
    """Tests for diagnose_all_racks_simulated()."""

    def test_returns_all_10_tiers(self):
        results = diagnose_all_racks_simulated()
        assert len(results) == 10
        for i in range(10):
            assert f"tier_{i}" in results

    def test_all_results_are_diagnosis(self):
        results = diagnose_all_racks_simulated()
        for rack_id, result in results.items():
            assert isinstance(result, DiagnosisResult)
            assert result.rack_id == rack_id


class TestRackScenarios:
    """Tests for RACK_SCENARIOS data."""

    def test_has_10_entries(self):
        assert len(RACK_SCENARIOS) == 10

    def test_all_tiers_present(self):
        for i in range(10):
            assert f"tier_{i}" in RACK_SCENARIOS

    def test_all_growth_stages_valid(self):
        for rack_id, scenario in RACK_SCENARIOS.items():
            assert scenario["growth_stage"] in GROWTH_LABELS, f"{rack_id}: invalid growth"

    def test_all_nutrition_valid(self):
        for rack_id, scenario in RACK_SCENARIOS.items():
            assert scenario["nutrition"] in NUTRITION_LABELS, f"{rack_id}: invalid nutrition"


class TestGenerateImpacts:
    """Tests for generate_impacts()."""

    def test_harvest_ready_normal(self):
        diag = DiagnosisResult(
            rack_id="tier_0", growth_stage="harvest_ready",
            growth_confidence=0.9, growth_probs=[0.1, 0.0, 0.9],
            nutrition_status="normal", nutrition_confidence=0.9,
            nutrition_probs=[0.05, 0.05, 0.9],
        )
        impacts = generate_impacts(diag, "Arugula")
        assert any("harvest schedule" in i for i in impacts)
        assert any("normal" in i.lower() for i in impacts)

    def test_nitrogen_low(self):
        diag = DiagnosisResult(
            rack_id="tier_3", growth_stage="mid",
            growth_confidence=0.85, growth_probs=[0.1, 0.85, 0.05],
            nutrition_status="nitrogen_low", nutrition_confidence=0.8,
            nutrition_probs=[0.8, 0.1, 0.1],
        )
        impacts = generate_impacts(diag, "Kai Lan")
        assert any("nitrogen" in i.lower() for i in impacts)
        assert any("Layer 3" in i for i in impacts)

    def test_water_stress(self):
        diag = DiagnosisResult(
            rack_id="tier_4", growth_stage="early",
            growth_confidence=0.9, growth_probs=[0.9, 0.05, 0.05],
            nutrition_status="water_stress", nutrition_confidence=0.8,
            nutrition_probs=[0.1, 0.8, 0.1],
        )
        impacts = generate_impacts(diag, "Kale")
        assert any("irrigation" in i.lower() or "moisture" in i.lower() for i in impacts)
        assert any("80%" in i for i in impacts)

    def test_early_stage_shows_days_estimate(self):
        diag = DiagnosisResult(
            rack_id="tier_2", growth_stage="early",
            growth_confidence=0.9, growth_probs=[0.9, 0.05, 0.05],
            nutrition_status="normal", nutrition_confidence=0.9,
            nutrition_probs=[0.05, 0.05, 0.9],
        )
        impacts = generate_impacts(diag, "Lettuce")
        assert any("14 days" in i for i in impacts)


class TestBadges:
    """Tests for badge mappings."""

    def test_all_growth_stages_have_badges(self):
        for label in GROWTH_LABELS:
            assert label in GROWTH_BADGES

    def test_all_nutrition_have_badges(self):
        for label in NUTRITION_LABELS:
            assert label in NUTRITION_BADGES
