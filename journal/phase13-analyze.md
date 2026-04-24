# Phase 13 Drift Monitoring — Design Analysis (retrospective)

## What problem does this solve?
ML models degrade over time as the world changes. Week 8 Capstone
material explicitly requires drift detection design. Without this,
our Week 8 demo numbers become stale within weeks of deployment.

## Alternatives considered

### Option A: No monitoring (retrain on schedule only)
- Pros: Simple
- Cons: Blind to gradual degradation; wastes compute on unnecessary retrains
- Decision: REJECTED — not production-viable

### Option B: Single metric per model (accuracy drift only)
- Pros: Clear, one threshold per model
- Cons: Misses feature drift (input changes) and concept drift (relationship changes)
- Decision: REJECTED — incomplete

### Option C: 3-type framework (Feature + Performance + Concept) × 6 layers
- Pros: Comprehensive; matches academic drift taxonomy (Gama et al.)
- Cons: 14 checks to maintain
- Decision: SELECTED — state of the art, future-proof

## Design decisions

1. Statistical tests per drift type:
   - Feature: Kolmogorov-Smirnov (non-parametric, sensitive)
   - Performance: RMSE / accuracy delta from baseline
   - Concept: Jaccard similarity for clusters, reward for RL

2. Severity mapping:
   OK / WARNING / ALERT / CRITICAL
   Each severity has a defined automated action:
   - WARNING: log only
   - ALERT: notify manager + optional retrain
   - CRITICAL: halt decisions + emergency retrain

3. Schedule via YAML config:
   Hourly for fast-moving (MILP infeasibility)
   Daily for slow (customer feedback)
   Weekly for ML retraining cycles

4. Integration with Gate 5:
   Framework presence → Gate 5 PASS
   Active production data with no critical drifts → Gate 5 maintained

## Trade-offs accepted
- Drift thresholds are initial estimates, will tune in Phase 1
- Some checks are "framework present" not "running on real data"
- No backfill drift detection for historical retrospective
