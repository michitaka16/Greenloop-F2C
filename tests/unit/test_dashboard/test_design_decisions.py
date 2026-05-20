"""Tests for the Design Decisions panel parser.

The parser extracts each `### Decision N:` section from specs/decision-log.md.
If the format changes, these tests break — forcing us to fix the parser rather
than silently shipping an empty VC-pitch panel.
"""

from __future__ import annotations

from adoptakale.dashboard.design_decisions import _load_decisions


def test_load_decisions_returns_at_least_ten_entries():
    """The parser should extract Decision N: sections from specs/decision-log.md.

    With 25 decisions spanning Phase 1-3 HITL, we expect at least 10 entries.
    """
    decisions = _load_decisions()
    assert isinstance(decisions, list)
    assert len(decisions) >= 10, f"Expected at least 10 decisions, got {len(decisions)}"
    assert all(isinstance(d, tuple) and len(d) == 2 for d in decisions), (
        "Each decision should be a (heading, body) tuple"
    )


def test_every_decision_has_heading_and_body():
    for heading, body in _load_decisions():
        assert heading.startswith("Decision "), f"Bad heading: {heading!r}"
        assert body, f"Empty body under: {heading!r}"


def test_decisions_are_numbered_sequentially():
    decisions = _load_decisions()
    numbers = [int(h.split()[1].rstrip(":")) for h, _ in decisions]
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"Decision numbers not sequential: {numbers}"
    )


def test_each_decision_documents_rationale():
    """Every Dimension A decision must explain WHY it was chosen."""
    for heading, body in _load_decisions():
        lower = body.lower()
        # Accept any of: rationale, reasoning, mechanism, evidence, trade-offs
        has_justification = any(
            keyword in lower for keyword in ("rationale", "reasoning", "mechanism", "evidence", "trade-offs")
        )
        assert has_justification, (
            f"{heading} has no Rationale / Reasoning / Mechanism / Evidence / Trade-offs section"
        )
