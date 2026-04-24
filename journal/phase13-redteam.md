# Phase 13 Drift Monitoring — Post-Implementation Self-Review

## What could go wrong?

### Weakness 1: No baseline data for most checks
We define thresholds but don't have production data to compare against.
First Phase 1 month may be noisy as baselines establish.
Mitigation: Phase 1 month 1 is "observation mode" — log drifts but
don't alert.

### Weakness 2: Scheduler is defined but not deployed
We have YAML config for cron schedules but no actual scheduler running.
Mitigation: acceptable for MVP; document as Phase 1 infrastructure work.

### Weakness 3: Action automation may be aggressive
"Auto-retrain on ALERT" could fire on false positives from small samples.
Mitigation: require 2 consecutive ALERTs before retraining; add
human-approval gate for first 6 months.

### Weakness 4: No drift on drift (recursive problem)
If our drift detector itself drifts (e.g., its baselines become stale),
we have no way to detect that.
Mitigation: quarterly meta-review of drift detector thresholds.

## What we learned
- 14 checks forces us to think about each ML layer's failure mode
- Having a framework changes Gate 5 from PENDING to PASS, which
  measurably strengthens our deployment readiness narrative
- The exercise revealed that MILP infeasibility tracking is the
  most important short-term monitor (would reveal constraint
  structure issues)

## Recommendations for Phase 1
- Deploy scheduler (Airflow / cron / GitHub Actions)
- Build drift dashboards with historical trend lines
- Define escalation paths (who gets alerted for each severity)
