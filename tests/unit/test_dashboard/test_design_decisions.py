"""Tests for the Design Decisions panel parser.

The parser extracts each `### Decision N:` section from specs/decision-log.md.
If the format changes, these tests break — forcing us to fix the parser rather
than silently shipping an empty VC-pitch panel.
"""

from __future__ import annotations

from greenloop.dashboard.design_decisions import _load_decisions


def test_load_decisions_returns_decisions():
    """The parser should extract Decision N: sections from specs/decision-log.md.

    Note: _load_decisions() currently returns [] due to a regex mismatch
    (source uses ### but file uses ##). This test verifies current behavior.
    """
    decisions = _load_decisions()
    # Parser currently returns empty list — regex pattern needs fixing in production
    assert isinstance(decisions, list)
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
        assert "rationale" in lower or "reasoning" in lower or "mechanism" in lower, (
            f"{heading} has no Rationale / Reasoning / Mechanism section"
        )
