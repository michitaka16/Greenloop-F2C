"""Tests for the KPI header strip renderer.

The strip renders Streamlit widgets, so we stub `st.columns` / `st.metric`
to capture the labels + values without pulling in a full Streamlit runtime.
This keeps the test as a Tier-1 unit test.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch


def _install_stub_streamlit():
    """Return (stub_st, captured_metrics) where captured_metrics is a list of
    (label, value) tuples in the order st.metric was called."""
    captured: list[tuple[str, Any]] = []

    col = MagicMock()
    col.metric = lambda label, value, **kwargs: captured.append((label, value))

    stub = MagicMock()
    stub.columns.return_value = (col, col, col, col, col)
    return stub, captured


def test_kpi_strip_with_full_plan():
    stub_st, captured = _install_stub_streamlit()
    plan = {
        "objective_value_sgd": 153.98,
        "solve_time_ms": 40.5,
        "cost_breakdown": {
            "revenue": 412.50,
            "electricity": 120.10,
            "labour": 138.42,
            "waste_penalty": 0.0,
        },
    }
    with patch("greenloop.dashboard.app.st", stub_st):
        from greenloop.dashboard.app import _render_kpi_strip

        _render_kpi_strip(plan)

    labels = [c[0] for c in captured]
    values = [c[1] for c in captured]
    assert labels == [
        "Profit (SGD)",
        "Revenue (SGD)",
        "Energy cost (SGD)",
        "Labour cost (SGD)",
        "Solve time",
    ]
    # Profit and revenue rendered with $ and thousands separator + 2 dp
    assert values[0] == "$153.98"
    assert values[1] == "$412.50"
    assert values[4] == "40 ms"


def test_kpi_strip_with_none_plan_shows_placeholders():
    """When MILP is infeasible the KPI strip must still render — dashboard
    should never crash into a blank page on a bad solve."""
    stub_st, captured = _install_stub_streamlit()
    with patch("greenloop.dashboard.app.st", stub_st):
        from greenloop.dashboard.app import _render_kpi_strip

        _render_kpi_strip(None)
    values = [c[1] for c in captured]
    assert values == ["—", "—", "—", "—", "—"]


def test_kpi_strip_missing_cost_breakdown_defaults_to_zero():
    """Zero-tolerance: missing keys must not raise — they show $0.00."""
    stub_st, captured = _install_stub_streamlit()
    with patch("greenloop.dashboard.app.st", stub_st):
        from greenloop.dashboard.app import _render_kpi_strip

        _render_kpi_strip({"objective_value_sgd": 0, "solve_time_ms": 0})
    values = [c[1] for c in captured]
    assert values[0] == "$0.00"
    assert values[2] == "$0.00"  # energy defaults to 0
