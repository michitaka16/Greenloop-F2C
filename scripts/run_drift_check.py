#!/usr/bin/env python3
"""Run all Phase 13 drift checks and output a formatted report.

Run from repo root:
    uv run python scripts/run_drift_check.py
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

from adoptakale.monitoring.drift_detector import (
    DriftSeverity,
    DriftType,
    get_all_drift_checks,
    run_all_checks,
)


JOURNAL_DIR = Path(__file__).resolve().parents[1] / "journal"


def _severity_icon(severity: DriftSeverity) -> str:
    return {
        DriftSeverity.OK: "✅",
        DriftSeverity.WARNING: "⚠️",
        DriftSeverity.ALERT: "🔔",
        DriftSeverity.CRITICAL: "🚨",
    }[severity]


def _severity_label(severity: DriftSeverity) -> str:
    return severity.value.upper()


def main() -> int:
    checks = get_all_drift_checks()
    results = run_all_checks()

    counts = {s: 0 for s in DriftSeverity}
    rows: list[dict] = []

    print("=" * 66)
    print("PHASE 13 DRIFT MONITORING REPORT — Adopt a Kale")
    print(f"Generated: {datetime.now().isoformat()}")
    print(f"Checks: {len(checks)}")
    print("=" * 66)

    for check, severity, details in results:
        counts[severity] += 1
        icon = _severity_icon(severity)

        print(f"\n{icon} [{severity.value:8s}] {check.name}")
        print(f"    Layer: {check.layer} | Type: {check.drift_type.value}")
        print(f"    Action: {check.action_on_alert}")
        status = details.get("status", "ok")
        if status != "ok":
            msg = details.get("message", details.get("error", status))
            print(f"    Status: {status} — {msg}")

        rows.append({
            "check_name": check.name,
            "layer": check.layer,
            "drift_type": check.drift_type.value,
            "severity": severity.value,
            "status": details.get("status", "ok"),
            "details": details,
            "action_on_alert": check.action_on_alert,
        })

    print("\n" + "─" * 66)
    print("Summary:")
    print(f"  ✅ OK:        {counts[DriftSeverity.OK]}")
    print(f"  ⚠️  WARNING:  {counts[DriftSeverity.WARNING]}")
    print(f"  🔔 ALERT:    {counts[DriftSeverity.ALERT]}")
    print(f"  🚨 CRITICAL: {counts[DriftSeverity.CRITICAL]}")

    non_ok = (
        counts[DriftSeverity.WARNING]
        + counts[DriftSeverity.ALERT]
        + counts[DriftSeverity.CRITICAL]
    )
    if non_ok == 0:
        print("\nAll checks nominal — no drift detected.")
    else:
        print(f"\n{non_ok} check(s) require attention.")

    # Write JSON report
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_checks": len(checks),
        "summary": {
            "ok": counts[DriftSeverity.OK],
            "warning": counts[DriftSeverity.WARNING],
            "alert": counts[DriftSeverity.ALERT],
            "critical": counts[DriftSeverity.CRITICAL],
        },
        "checks": rows,
    }

    json_path = JOURNAL_DIR / "phase13-drift-report.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n📄 JSON report: {json_path}")

    # Write markdown report
    md_lines = [
        "# Phase 13 Drift Monitoring Report",
        "",
        f"**Generated:** {datetime.now().date()} | **Checks:** {len(checks)}",
        "",
        "## Severity Summary",
        "",
        f"| Status | Count |",
        f"|--------|------:|",
        f"| ✅ OK | {counts[DriftSeverity.OK]} |",
        f"| ⚠️ WARNING | {counts[DriftSeverity.WARNING]} |",
        f"| 🔔 ALERT | {counts[DriftSeverity.ALERT]} |",
        f"| 🚨 CRITICAL | {counts[DriftSeverity.CRITICAL]} |",
        "",
        "## Check Results",
        "",
        "| Check | Layer | Type | Severity | Action |",
        "|-------|-------|------|----------|--------|",
    ]

    for check, severity, details in results:
        status = details.get("status", "—")
        md_lines.append(
            f"| `{check.name}` | {check.layer} | "
            f"{check.drift_type.value} | {severity.value} | "
            f"{check.action_on_alert} |"
        )

    md_path = JOURNAL_DIR / "phase13-drift-report.md"
    md_path.write_text("\n".join(md_lines))
    print(f"📄 Markdown report: {md_path}")

    # Exit code: 1 if any ALERT or CRITICAL
    sys.exit(1 if counts[DriftSeverity.ALERT] + counts[DriftSeverity.CRITICAL] > 0 else 0)


if __name__ == "__main__":
    main()
