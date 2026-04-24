# Phase 5 Implications — Design Analysis (retrospective)

## What problem does this solve?
Technical excellence ≠ ethical responsibility. Week 4-7 materials
across Finance, Manufacturing, and Media all stressed stakeholder
impact analysis. Without this, our system could unintentionally harm
workers, bias against demographic groups, or lock small farms out.

## Alternatives considered

### Option A: Generic "AI ethics" statement
- Pros: Minimal effort
- Cons: Not layer-specific, not evidence-based
- Decision: REJECTED — boilerplate doesn't demonstrate thinking

### Option B: Bias testing only (technical dimension)
- Pros: Concrete, testable
- Cons: Misses stakeholder impact (labor, equity, power dynamics)
- Decision: REJECTED — too narrow

### Option C: 3-category audit (data bias + decision bias + stakeholder)
- Pros: Matches AI Verify framework, comprehensive
- Cons: Subjective categories
- Decision: SELECTED — comprehensive, defensible framework

## Design decisions

1. Layer-by-layer audit:
   Each of 6 ML layers examined for bias risks.
   This avoids generic statements; each finding is concrete.

2. Severity scoring:
   CRITICAL (block deployment) / HIGH / MEDIUM / LOW
   Uses the same severity scale as Gate risk assessment.

3. Stakeholder mapping:
   6 stakeholders chosen: farm managers, workers, owners, consumers,
   Greenphyto, AVA. Covers direct users, affected parties, competitors,
   regulators.

4. Gate 4 integration:
   If any HIGH/CRITICAL implication is unmitigated → Gate 4 fails.
   This creates a feedback loop: ethics audit has deployment consequences.

## Trade-offs accepted
- No quantitative bias metrics (statistical parity, equal opportunity)
  — acceptable without production data
- Stakeholder analysis is desk research, not interviews
- Implications may reveal more issues during Phase 1 pilot
