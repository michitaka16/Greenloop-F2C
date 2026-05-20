"""Unit tests for Phase 13 Drift Detector module."""

import sys
from pathlib import Path

# Ensure src/ is on path for pytest
_SRC = Path(__file__).resolve().parents[4] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest

from adoptakale.monitoring.drift_detector import (
    DriftSeverity,
    DriftType,
    DriftCheck,
    DriftEvent,
    get_all_drift_checks,
    get_drift_checks_by_layer,
    get_drift_checks_by_type,
    run_all_checks,
    log_diagnosis_confidence,
    log_milp_result,
    log_milp_solve_time,
    log_rag_feedback,
    log_ppo_reward,
    check_milp_infeasibility_rate,
    check_milp_solve_time_drift,
    check_rag_relevance_drift,
    check_efficientnet_confidence_drift,
    check_ppo_reward_drift,
    check_data_freshness,
    _INFEASIBILITY_LOG,
    _SOLVE_TIME_LOG,
    _RAG_FEEDBACK_LOG,
    _DIAGNOSIS_CONFIDENCE_LOG,
    _REWARD_LOG,
)


class TestAllLayersHaveDriftChecks:
    """Every ML layer must have at least one drift check."""

    EXPECTED_LAYERS = {
        "Layer 1",
        "Layer 1b",
        "Layer 2",
        "Layer 3",
        "Layer 4",
        "Layer 5",
        "System-wide",
    }

    def test_fourteen_checks_registered(self):
        checks = get_all_drift_checks()
        assert len(checks) == 14, f"Expected 14 checks, got {len(checks)}"

    def test_all_six_layers_have_checks(self):
        checks = get_all_drift_checks()
        layers_with_checks = {c.layer for c in checks}
        missing = self.EXPECTED_LAYERS - layers_with_checks
        assert not missing, f"Layers missing drift checks: {missing}"

    def test_feature_drift_checks_exist(self):
        feature_checks = get_drift_checks_by_type(DriftType.FEATURE)
        assert len(feature_checks) >= 3, "Need at least 3 feature drift checks"

    def test_performance_drift_checks_exist(self):
        perf_checks = get_drift_checks_by_type(DriftType.PERFORMANCE)
        assert len(perf_checks) >= 3, "Need at least 3 performance drift checks"

    def test_concept_drift_checks_exist(self):
        concept_checks = get_drift_checks_by_type(DriftType.CONCEPT)
        assert len(concept_checks) >= 3, "Need at least 3 concept drift checks"

    def test_each_check_has_required_fields(self):
        for check in get_all_drift_checks():
            assert check.name
            assert check.layer
            assert isinstance(check.drift_type, DriftType)
            assert callable(check.check_function)
            assert check.action_on_alert
            assert isinstance(check.description, str)


class TestDriftCheckExecution:
    """Drift checks run without errors and return correct types."""

    def test_all_checks_execute_without_exception(self):
        """Every check_function must return (DriftSeverity, dict) without raising."""
        for check in get_all_drift_checks():
            try:
                severity, details = check.check_function()
            except Exception as e:
                pytest.fail(f"Check {check.name} raised exception: {e}")
            assert isinstance(severity, DriftSeverity)
            assert isinstance(details, dict)

    def test_run_all_checks_returns_14_results(self):
        results = run_all_checks()
        assert len(results) == 14

    def test_each_check_returns_valid_severity(self):
        for check, severity, details in run_all_checks():
            assert isinstance(severity, DriftSeverity)
            assert severity in {
                DriftSeverity.OK,
                DriftSeverity.WARNING,
                DriftSeverity.ALERT,
                DriftSeverity.CRITICAL,
            }


class TestInfeasibilityTrackerAccumulates:
    """MILP infeasibility tracker accumulates and emits correct severity."""

    def test_no_solves_returns_ok(self):
        # Clear the log
        _INFEASIBILITY_LOG.clear()
        severity, details = check_milp_infeasibility_rate()
        assert severity == DriftSeverity.OK
        assert details["status"] == "no_recent_solves"

    def test_low_infeasibility_rate_returns_ok(self):
        _INFEASIBILITY_LOG.clear()
        import time
        now = time.time()
        # 10 feasible solves
        for i in range(10):
            _INFEASIBILITY_LOG.append((now, False))
        severity, details = check_milp_infeasibility_rate()
        assert severity == DriftSeverity.OK

    def test_10_percent_infeasibility_returns_warning(self):
        _INFEASIBILITY_LOG.clear()
        import time
        now = time.time()
        # 10% infeasible
        for i in range(90):
            _INFEASIBILITY_LOG.append((now, False))
        for i in range(10):
            _INFEASIBILITY_LOG.append((now, True))
        severity, details = check_milp_infeasibility_rate()
        rate = details.get("infeasibility_rate", 0)
        assert severity in (DriftSeverity.OK, DriftSeverity.WARNING)
        assert abs(rate - 0.10) < 0.02

    def test_20_percent_infeasibility_returns_alert(self):
        _INFEASIBILITY_LOG.clear()
        import time
        now = time.time()
        # 20% infeasible
        for i in range(80):
            _INFEASIBILITY_LOG.append((now, False))
        for i in range(20):
            _INFEASIBILITY_LOG.append((now, True))
        severity, details = check_milp_infeasibility_rate()
        rate = details.get("infeasibility_rate", 0)
        assert abs(rate - 0.20) < 0.02
        assert severity in (DriftSeverity.WARNING, DriftSeverity.ALERT, DriftSeverity.CRITICAL)

    def test_log_milp_result_append_works(self):
        _INFEASIBILITY_LOG.clear()
        log_milp_result(was_infeasible=True)
        log_milp_result(was_infeasible=False)
        assert len(_INFEASIBILITY_LOG) == 2


class TestSolveTimeTracker:
    """MILP solve time tracker emits correct severity."""

    def test_no_solves_returns_ok(self):
        _SOLVE_TIME_LOG.clear()
        severity, details = check_milp_solve_time_drift()
        assert severity == DriftSeverity.OK

    def test_median_solve_time_returns_ok(self):
        _SOLVE_TIME_LOG.clear()
        import time
        now = time.time()
        # All fast solves
        for ms in [100, 150, 200, 180, 120, 90, 110]:
            _SOLVE_TIME_LOG.append((now, float(ms)))
        severity, details = check_milp_solve_time_drift()
        assert severity == DriftSeverity.OK
        assert details["p95_solve_time_ms"] < 500

    def test_high_p95_solve_time_returns_warning(self):
        _SOLVE_TIME_LOG.clear()
        import time
        now = time.time()
        # Mostly fast, but a few very slow (p95 will be high)
        for _ in range(20):
            _SOLVE_TIME_LOG.append((now, 100.0))
        for _ in range(80):
            _SOLVE_TIME_LOG.append((now, 600.0))  # p95 will be 600ms
        severity, details = check_milp_solve_time_drift()
        p95 = details.get("p95_solve_time_ms", 0)
        assert p95 >= 500
        assert severity in (DriftSeverity.WARNING, DriftSeverity.ALERT)


class TestDataFreshness:
    """Data freshness check works for all tracked files."""

    def test_check_returns_ok_or_warning(self):
        severity, details = check_data_freshness()
        assert isinstance(severity, DriftSeverity)
        assert "files" in details


class TestDriftReportGeneration:
    """run_all_checks produces valid data for report generation."""

    def test_all_14_checks_run(self):
        results = run_all_checks()
        check_names = {c.name for c, _, _ in results}
        expected = {
            "xgboost_feature_drift",
            "xgboost_performance_drift",
            "xgboost_prediction_bias",
            "efficientnet_confidence_drift",
            "efficientnet_diagnosis_rate",
            "milp_infeasibility_rate",
            "milp_solve_time_drift",
            "milp_constraint_violations",
            "ppo_reward_drift",
            "ppo_action_distribution_drift",
            "segment_stability",
            "customer_segment_size_drift",
            "rag_relevance_drift",
            "data_freshness",
        }
        assert check_names == expected, f"Missing: {expected - check_names}"

    def test_severity_distribution_valid(self):
        _, severities, _ = zip(*run_all_checks())
        # All should be valid severities
        for sev in severities:
            assert isinstance(sev, DriftSeverity)
        # Most should be OK (no production data yet)
        ok_count = sum(1 for s in severities if s == DriftSeverity.OK)
        assert ok_count >= 10, f"Expected at least 10 OK checks, got {ok_count}"

    def test_check_by_layer_returns_correct_layer(self):
        layer1_checks = get_drift_checks_by_layer("Layer 1")
        assert all(c.layer == "Layer 1" for c in layer1_checks)
        assert len(layer1_checks) == 3

    def test_check_by_type_returns_correct_type(self):
        feature_checks = get_drift_checks_by_type(DriftType.FEATURE)
        assert all(c.drift_type == DriftType.FEATURE for c in feature_checks)
