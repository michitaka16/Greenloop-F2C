#!/usr/bin/env python3
"""Generate Phase 5 Implications Audit report.

Run from repo root:
    uv run python scripts/run_implications_audit.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure src/ is on path for local development
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from greenloop.governance.implications_audit import (
    ImpactSeverity,
    ImplicationCategory,
    get_all_implications,
    get_stakeholder_impacts,
    get_high_or_critical_implications,
    get_unmitigated_implications,
)


JOURNAL_DIR = Path(__file__).resolve().parents[1] / "journal"


def _severity_badge(severity: ImpactSeverity) -> str:
    return {
        ImpactSeverity.CRITICAL: "🔴 CRITICAL",
        ImpactSeverity.HIGH: "🟠 HIGH",
        ImpactSeverity.MEDIUM: "🟡 MEDIUM",
        ImpactSeverity.LOW: "🟢 LOW",
    }[severity]


def _category_label(category: ImplicationCategory) -> str:
    return {
        ImplicationCategory.DATA_BIAS: "Data Bias",
        ImplicationCategory.DECISION_BIAS: "Decision Bias",
        ImplicationCategory.STAKEHOLDER: "Stakeholder",
    }[category]


def main() -> int:
    implications = get_all_implications()
    stakeholders = get_stakeholder_impacts()
    high_crit = get_high_or_critical_implications()
    unmitigated = get_unmitigated_implications()

    # Severity breakdown
    by_severity = {s: [] for s in ImpactSeverity}
    for i in implications:
        by_severity[i.severity].append(i)

    # Stakeholder net scores
    stakeholder_scores = []
    for s in stakeholders:
        net = len(s.positive_effects) - len(s.negative_effects)
        stakeholder_scores.append((s.stakeholder, net, s))

    print("=" * 64)
    print("PHASE 5 IMPLICATIONS AUDIT — Greenloop F2C")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 64)

    print("\n── Severity breakdown ──")
    for sev in [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH,
                ImpactSeverity.MEDIUM, ImpactSeverity.LOW]:
        items = by_severity[sev]
        badge = _severity_badge(sev)
        blocking = " ← BLOCKS DEPLOYMENT" if sev == ImpactSeverity.CRITICAL and items else ""
        print(f"  {badge}: {len(items):2d}  {''.join(f'[{i.layer}]' for i in items)}{blocking}")

    print(f"\n  Total implications:   {len(implications)}")
    print(f"  HIGH/CRITICAL:         {len(high_crit)} (must be mitigated before Phase 1)")
    print(f"  Unmitigated H/C:      {len(unmitigated)} {'← BLOCKS GATE 4' if unmitigated else '✓'}")

    print(f"\n── Stakeholders ({len(stakeholders)}) ──")
    for name, net, s in sorted(stakeholder_scores, key=lambda x: -x[1]):
        icon = "✅" if net > 0 else "⚖️" if net == 0 else "⚠️"
        print(f"  {icon} {name}: {net:+d}  ({len(s.positive_effects)}+/ {len(s.negative_effects)}-)")

    print("\n── Detailed implications ──")
    for i in implications:
        print(f"\n  {_severity_badge(i.severity)} | {i.layer} | {_category_label(i.category)}")
        print(f"  {i.description[:120]}")
        print(f"  Mitigation: {i.mitigation[:120]}")
        print(f"  Evidence: {i.evidence}")
        if not i.is_mitigated:
            print("  ⚠️  NOT YET MITIGATED")

    print("\n── Stakeholder detail ──")
    for s in stakeholders:
        net = len(s.positive_effects) - len(s.negative_effects)
        icon = "✅" if net > 0 else "⚖️" if net == 0 else "⚠️"
        print(f"\n  {icon} {s.stakeholder} (net {net:+d})")
        for p in s.positive_effects:
            print(f"    + {p}")
        for n in s.negative_effects:
            print(f"    - {n}")
        print("    Actions: " + "; ".join(s.mitigation_actions))

    # Write JSON report
    report = {
        "audit_date": datetime.now().isoformat(),
        "total_implications": len(implications),
        "by_severity": {s.value: len(by_severity[s]) for s in ImpactSeverity},
        "high_or_critical_count": len(high_crit),
        "unmitigated_count": len(unmitigated),
        "gate4_pass": len(unmitigated) == 0,
        "stakeholders": [
            {
                "name": s.stakeholder,
                "net": len(s.positive_effects) - len(s.negative_effects),
                "positive": s.positive_effects,
                "negative": s.negative_effects,
                "mitigations": s.mitigation_actions,
            }
            for s in stakeholders
        ],
        "implications": [
            {
                "layer": i.layer,
                "category": i.category.value,
                "severity": i.severity.value,
                "description": i.description,
                "mitigation": i.mitigation,
                "evidence": i.evidence,
                "is_mitigated": i.is_mitigated,
            }
            for i in implications
        ],
    }

    json_path = JOURNAL_DIR / "phase5-implications-audit.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n📄 JSON report saved: {json_path}")

    # Write markdown summary
    md_lines = [
        "# Phase 5 Implications Audit — Summary",
        f"",
        f"**Generated:** {datetime.now().date()} | **Implications:** {len(implications)} | **Stakeholders:** {len(stakeholders)}",
        f"",
        f"## Severity",
        f"",
        f"| Severity | Count | Items |",
        f"|----------|-------|-------|",
    ]
    for sev in [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH, ImpactSeverity.MEDIUM, ImpactSeverity.LOW]:
        items = by_severity[sev]
        layers = ", ".join(f"`{i.layer}`" for i in items) or "—"
        md_lines.append(f"| {_severity_badge(sev)} | {len(items)} | {layers} |")

    md_lines.extend([
        "",
        f"## Gate 4 Criterion: Implications",
        "",
        f"| Criterion | Result |",
        f"|-----------|--------|",
        f"| CRITICAL count | {len(by_severity[ImpactSeverity.CRITICAL])} |",
        f"| HIGH count | {len(by_severity[ImpactSeverity.HIGH])} |",
        f"| Unmitigated H/C | {len(unmitigated)} |",
        f"| Gate 4 PASS | {'✅ YES' if len(unmitigated) == 0 else '❌ NO'} |",
    ])

    md_lines.extend([
        "",
        "## Stakeholder Net Impact",
        "",
        "| Stakeholder | Net | +/− |",
        "|-------------|-----|-----|",
    ])
    for name, net, s in sorted(stakeholder_scores, key=lambda x: -x[1]):
        md_lines.append(f"| {name} | {net:+d} | {len(s.positive_effects)}+/ {len(s.negative_effects)}− |")

    md_path = JOURNAL_DIR / "phase5-implications-audit.md"
    md_path.write_text("\n".join(md_lines))
    print(f"📄 Markdown summary saved: {md_path}")

    # Exit code: 0 if no unmitigated HIGH/CRITICAL
    sys.exit(0 if len(unmitigated) == 0 else 1)


if __name__ == "__main__":
    main()
