"""Design Decisions panel — surfaces Dimension A evidence in the dashboard.

During the VC pitch, judges want to see WHY each algorithmic choice was made.
Reading specs/decision-log.md live is friction; this panel renders the same
content inline, collapsed by default, expandable per decision.

Source of truth: specs/decision-log.md — the markdown is parsed into sections
at import time. If the spec changes, the panel reflects it automatically.
"""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

_DECISION_LOG = Path(__file__).resolve().parent.parent.parent.parent / "specs" / "decision-log.md"


def _load_decisions() -> list[tuple[str, str]]:
    """Parse decision-log.md into [(heading, body_markdown), ...].

    Returns an empty list if the spec is missing — the panel degrades silently
    rather than breaking the dashboard.
    """
    if not _DECISION_LOG.exists():
        return []
    text = _DECISION_LOG.read_text()
    # Split on '### Decision N:' headings; keep the heading as part of the body.
    pattern = re.compile(r"^### (Decision \d+:[^\n]+)\n", re.MULTILINE)
    matches = list(pattern.finditer(text))
    decisions: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        # Trim the separator '---' that precedes the next decision
        body = re.sub(r"\n---\s*$", "", body).strip()
        decisions.append((heading, body))
    return decisions


def render_design_decisions_panel() -> None:
    """Render the Design Decisions sidebar expander."""
    decisions = _load_decisions()
    if not decisions:
        return
    with st.sidebar.expander("Design Decisions (Dimension A)", expanded=False):
        st.caption(
            f"{len(decisions)} algorithmic choices, each with rationale and "
            "rejected alternative. Click to expand."
        )
        for heading, body in decisions:
            with st.expander(heading, expanded=False):
                st.markdown(body)
