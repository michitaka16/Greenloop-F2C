# Phase 8 Deployment Gate — Design Analysis (retrospective)

## What problem does this solve?
"All tests pass" is not the same as "ready to ship". Software can be
technically correct but commercially, legally, or operationally
unprepared. Week 6 Manufacturing material emphasized explicit
deployment judgment.

## Alternatives considered

### Option A: Single pass/fail gate
- Pros: Simple, clear yes/no decision
- Cons: Loses nuance; "we pass tests" != "we're ready for customers"
- Decision: REJECTED — too crude for multi-dimensional readiness

### Option B: 3 gates (Technical, Business, Compliance)
- Pros: Balanced, covers major dimensions
- Cons: Risk and monitoring not separable from compliance
- Decision: REJECTED — conflates distinct concerns

### Option C: 5 gates (Technical, Business, Risk, Compliance, Monitoring)
- Pros: Industry-standard separation (matches ML governance frameworks)
- Cons: More criteria to define
- Decision: SELECTED — aligns with Google Vertex AI, AWS Well-Architected

## Design decisions

1. Decision logic:
   - All 5 PASS → SHIP
   - Gate 1 or 3 FAIL → DO NOT SHIP (technical or risk blocker)
   - Gate 2 FAIL → DO NOT SHIP (no business case)
   - Gate 4 FAIL → DO NOT SHIP (legal exposure)
   - Gate 5 PENDING → CONDITIONAL (acceptable for pilot)
   - Multiple CONDITIONAL → DEFER

2. Evidence linking:
   Each criterion points to a test file, document, or code location.
   This makes Dimension A evidence traceable to implementation.

3. Automation:
   run_deployment_gate.py executes gates programmatically.
   Reviewers can re-run judgment, don't take our word for it.

## Trade-offs accepted
- Gate 2 Business Viability is inherently subjective without real customers
- Gate 5 Monitoring was initially PENDING (honest state acknowledgment)
- No continuous gate evaluation in CI/CD (manual run only for MVP)
