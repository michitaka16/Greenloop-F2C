"""Unit tests for Phase 5 Implications Audit module."""

import sys
from pathlib import Path

# Ensure src/ is on path for pytest
_SRC = Path(__file__).resolve().parents[3] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest

from adoptakale.governance.implications_audit import (
    ImpactSeverity,
    ImplicationCategory,
    Implication,
    StakeholderImpact,
    get_all_implications,
    get_implications_by_category,
    get_implications_by_layer,
    get_high_or_critical_implications,
    get_unmitigated_implications,
    get_stakeholder_impacts,
)


class TestAllLayersHaveBiasAnalysis:
    """Every ML layer must have at least one documented implication."""

    EXPECTED_LAYERS = {"Layer 1", "Layer 1b", "Layer 2", "Layer 3", "Layer 4", "Layer 5"}

    def test_all_six_layers_have_implications(self):
        implications = get_all_implications()
        layers_with_implications = {i.layer for i in implications}
        missing = self.EXPECTED_LAYERS - layers_with_implications
        assert not missing, f"Layers missing implications: {missing}"

    def test_all_three_categories_represented(self):
        implications = get_all_implications()
        categories = {i.category for i in implications}
        assert ImplicationCategory.DATA_BIAS in categories
        assert ImplicationCategory.DECISION_BIAS in categories

    def test_layers_have_data_bias_analysis(self):
        """Layer 1, 1b, and 4 must have Data Bias implications."""
        data_bias = get_implications_by_category(ImplicationCategory.DATA_BIAS)
        layers = {i.layer for i in data_bias}
        assert "Layer 1" in layers, "Layer 1 must have Data Bias analysis"
        assert "Layer 1b" in layers, "Layer 1b must have Data Bias analysis"
        assert "Layer 4" in layers, "Layer 4 must have Data Bias analysis"

    def test_layers_have_decision_bias_analysis(self):
        """Layer 2, 3, and 5 must have Decision Bias implications."""
        decision_bias = get_implications_by_category(ImplicationCategory.DECISION_BIAS)
        layers = {i.layer for i in decision_bias}
        assert "Layer 2" in layers, "Layer 2 must have Decision Bias analysis"
        assert "Layer 3" in layers, "Layer 3 must have Decision Bias analysis"
        assert "Layer 5" in layers, "Layer 5 must have Decision Bias analysis"


class TestNoCriticalImplicationsUnmitigated:
    """CRITICAL implications must always be mitigated — blocks deployment."""

    def test_zero_critical_implications(self):
        implications = get_all_implications()
        critical = [i for i in implications if i.severity == ImpactSeverity.CRITICAL]
        assert len(critical) == 0, (
            f"Found {len(critical)} CRITICAL implications — deployment must be blocked. "
            f"Details: {[i.description[:80] for i in critical]}"
        )

    def test_high_implications_are_mitigated(self):
        implications = get_all_implications()
        high = [i for i in implications if i.severity == ImpactSeverity.HIGH]
        unmitigated = [i for i in high if not i.is_mitigated]
        assert len(unmitigated) == 0, (
            f"Found unmitigated HIGH implications: "
            f"{[i.layer for i in unmitigated]}. "
            f"All HIGH implications must be mitigated before Phase 1."
        )

    def test_no_unmitigated_high_or_critical(self):
        """Gate 4 criterion: zero unmitigated HIGH/CRITICAL."""
        unmitigated = get_unmitigated_implications()
        high_crit = [i for i in unmitigated
                     if i.severity in (ImpactSeverity.HIGH, ImpactSeverity.CRITICAL)]
        assert len(high_crit) == 0, (
            f"Gate 4 FAIL — {len(high_crit)} unmitigated HIGH/CRITICAL implications: "
            f"{[(i.layer, i.severity.value) for i in high_crit]}"
        )


class TestStakeholderCountMatchesDocumented:
    """All documented stakeholders must be present in the catalog."""

    def test_six_stakeholders_analysed(self):
        stakeholders = get_stakeholder_impacts()
        assert len(stakeholders) == 6, (
            f"Expected 6 stakeholders, got {len(stakeholders)}"
        )

    def test_expected_stakeholders_present(self):
        stakeholders = get_stakeholder_impacts()
        names = {s.stakeholder for s in stakeholders}
        expected = {
            "Farm Managers",
            "Farm Workers (3-10 per farm)",
            "ACTF Farm Owners (200 in Singapore)",
            "Singapore Consumers",
            "Greenphyto & Incumbent Vertical Farms",
            "AVA / Singapore Food Agency",
        }
        missing = expected - names
        assert not missing, f"Missing stakeholders: {missing}"

    def test_all_stakeholders_have_positive_and_negative_effects(self):
        stakeholders = get_stakeholder_impacts()
        for s in stakeholders:
            assert len(s.positive_effects) > 0, (
                f"Stakeholder '{s.stakeholder}' has no positive effects documented"
            )
            assert len(s.negative_effects) > 0, (
                f"Stakeholder '{s.stakeholder}' has no negative effects documented"
            )
            assert len(s.mitigation_actions) > 0, (
                f"Stakeholder '{s.stakeholder}' has no mitigation actions"
            )


class TestReportGenerationWorks:
    """The catalog API must produce valid, usable data for report generation."""

    def test_get_all_implications_returns_list(self):
        result = get_all_implications()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_each_implication_has_required_fields(self):
        for i in get_all_implications():
            assert i.layer
            assert i.description
            assert isinstance(i.severity, ImpactSeverity)
            assert i.mitigation
            assert i.evidence
            assert isinstance(i.is_mitigated, bool)

    def test_get_implications_by_layer(self):
        layer1_imps = get_implications_by_layer("Layer 1")
        assert len(layer1_imps) >= 1
        assert all(i.layer == "Layer 1" for i in layer1_imps)

    def test_get_implications_by_category(self):
        db = get_implications_by_category(ImplicationCategory.DATA_BIAS)
        assert len(db) >= 3  # Layer 1, 1b, 4
        assert all(i.category == ImplicationCategory.DATA_BIAS for i in db)

    def test_high_or_critical_count_matches_expected(self):
        """Expected: 1 HIGH (Layer 1b), 0 CRITICAL."""
        hc = get_high_or_critical_implications()
        severities = {i.severity for i in hc}
        assert ImpactSeverity.CRITICAL not in severities
        high_layers = {i.layer for i in hc}
        assert high_layers == {"Layer 1b"}, f"Expected Layer 1b as only HIGH, got {high_layers}"

    def test_severity_distribution_matches_expected(self):
        implications = get_all_implications()
        by_sev = {s: 0 for s in ImpactSeverity}
        for i in implications:
            by_sev[i.severity] += 1
        # Expected: 0 CRITICAL, 1 HIGH, 4 MEDIUM, 1 LOW
        assert by_sev[ImpactSeverity.CRITICAL] == 0
        assert by_sev[ImpactSeverity.HIGH] == 1
        assert by_sev[ImpactSeverity.MEDIUM] == 4
        assert by_sev[ImpactSeverity.LOW] == 1

    def test_gate4_criterion_pass(self):
        """Gate 4 implications criterion should PASS (0 unmitigated H/C)."""
        unmitigated = get_unmitigated_implications()
        high_crit_unmitigated = [
            i for i in unmitigated
            if i.severity in (ImpactSeverity.HIGH, ImpactSeverity.CRITICAL)
        ]
        assert len(high_crit_unmitigated) == 0, (
            f"Gate 4 criterion FAIL: {len(high_crit_unmitigated)} "
            f"unmitigated HIGH/CRITICAL implications"
        )
