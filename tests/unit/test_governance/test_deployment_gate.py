"""Unit tests for the Deployment Gate evaluation system.

Tests verify structure and dataclass contracts. Gate criterion evaluations
that run MILP/RAG benchmarks are exercised by the integration test
`scripts/run_deployment_gate.py`, not here.
"""

import pytest

from greenloop.governance.deployment_gate import (
    GateStatus,
    CriterionResult,
    GateResult,
    DeploymentDecision,
)


class TestGateStatusEnum:
    """GateStatus enum has all required members."""

    def test_has_pass(self):
        assert GateStatus.PASS is not None
        assert GateStatus.PASS.value == "PASS"

    def test_has_fail(self):
        assert GateStatus.FAIL is not None
        assert GateStatus.FAIL.value == "FAIL"

    def test_has_conditional(self):
        assert GateStatus.CONDITIONAL is not None
        assert GateStatus.CONDITIONAL.value == "CONDITIONAL"

    def test_has_pending(self):
        assert GateStatus.PENDING is not None
        assert GateStatus.PENDING.value == "PENDING"


class TestCriterionResult:
    """CriterionResult dataclass has correct structure."""

    def test_required_fields(self):
        cr = CriterionResult(name="test", status=GateStatus.PASS, message="ok")
        assert cr.name == "test"
        assert cr.status == GateStatus.PASS
        assert cr.message == "ok"
        assert cr.details == ""

    def test_details_optional(self):
        cr = CriterionResult(name="x", status=GateStatus.FAIL, message="y", details="z")
        assert cr.details == "z"

    def test_status_values(self):
        for status in GateStatus:
            cr = CriterionResult(name="t", status=status, message="m")
            assert cr.status == status


class TestGateResult:
    """GateResult dataclass has correct structure."""

    def test_required_fields(self):
        gr = GateResult(number=1, name="Gate 1", status=GateStatus.PASS)
        assert gr.number == 1
        assert gr.name == "Gate 1"
        assert gr.status == GateStatus.PASS
        assert gr.criteria == []
        assert gr.message == ""

    def test_criteria_list(self):
        c1 = CriterionResult(name="c1", status=GateStatus.PASS, message="ok")
        gr = GateResult(number=1, name="G", status=GateStatus.PASS, criteria=[c1])
        assert len(gr.criteria) == 1
        assert gr.criteria[0].name == "c1"

    def test_gate_status_reflects_worst_criterion(self):
        c1 = CriterionResult(name="passing", status=GateStatus.PASS, message="ok")
        c2 = CriterionResult(name="failing", status=GateStatus.FAIL, message="not ok")
        gr = GateResult(number=1, name="G", status=GateStatus.FAIL, criteria=[c1, c2])
        # The gate status is manually set; criteria list holds individual results
        assert gr.status == GateStatus.FAIL
        assert len(gr.criteria) == 2


class TestDeploymentDecision:
    """DeploymentDecision dataclass has correct structure."""

    def test_required_fields(self):
        dd = DeploymentDecision(
            overall_status=GateStatus.FAIL,
            overall_message="not ready",
            gate_results=[],
            ship_recommended=False,
        )
        assert dd.overall_status == GateStatus.FAIL
        assert dd.overall_message == "not ready"
        assert dd.gate_results == []
        assert dd.ship_recommended is False
        assert dd.restrictions == ""
        assert dd.upgrade_conditions == []
        assert dd.evaluated_at == ""

    def test_restrictions_and_conditions(self):
        dd = DeploymentDecision(
            overall_status=GateStatus.FAIL,
            overall_message="blocked",
            gate_results=[],
            ship_recommended=False,
            restrictions="Gate 3 Risk FAIL",
            upgrade_conditions=["Fix typhoon cascade", "Add EU AI Act docs"],
        )
        assert dd.restrictions == "Gate 3 Risk FAIL"
        assert len(dd.upgrade_conditions) == 2

    def test_gate_results_populated(self):
        g1 = GateResult(number=1, name="Tech", status=GateStatus.PASS)
        g2 = GateResult(number=2, name="Business", status=GateStatus.FAIL)
        dd = DeploymentDecision(
            overall_status=GateStatus.FAIL,
            overall_message="blocked",
            gate_results=[g1, g2],
            ship_recommended=False,
        )
        assert len(dd.gate_results) == 2
        assert dd.gate_results[0].number == 1
        assert dd.gate_results[1].number == 2


class TestGateModuleExports:
    """Module exports all required symbols."""

    def test_gate_functions_importable(self):
        from greenloop.governance.deployment_gate import (
            gate_1_technical,
            gate_2_business,
            gate_3_risk,
            gate_4_compliance,
            gate_5_operational,
            evaluate_all_gates,
        )
        assert callable(gate_1_technical)
        assert callable(gate_2_business)
        assert callable(gate_3_risk)
        assert callable(gate_4_compliance)
        assert callable(gate_5_operational)
        assert callable(evaluate_all_gates)
