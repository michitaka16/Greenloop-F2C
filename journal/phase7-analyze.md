# Phase 7 Red-Team — Design Analysis (retrospective)

## What problem does this solve?
Traditional unit tests verify the system works on expected inputs.
But MGMT655 Week 4 red-teaming methodology requires testing HOSTILE
inputs — what an adversary or malicious user would do to break the system.

## Alternatives considered

### Option A: Skip red-teaming (use only unit tests)
- Pros: Less work, standard industry practice for MVPs
- Cons: No evidence of resilience; gives false confidence
- Decision: REJECTED — Hong's Dimension A requires hostile-input evidence

### Option B: Sparse red-teaming (3-5 scenarios)
- Pros: Demonstrates awareness, minimal effort
- Cons: Insufficient coverage of 6 ML layers
- Decision: REJECTED — coverage gap too large for credibility

### Option C: Systematic red-team across all 6 layers + system-wide
- Pros: Complete coverage, demonstrates rigor
- Cons: 38 tests is significant effort
- Decision: SELECTED — evidence strength justifies cost

## Design decisions

1. 5 test categories per layer:
   - Adversarial inputs (malformed, hostile)
   - Data poisoning (corrupted training data)
   - Constraint stress (boundary conditions)
   - Reward hacking (RL-specific exploitation)
   - Prompt injection (LLM-specific)
   Plus system-wide cascade tests (seed supply, customer churn).

2. Pass criteria per test:
   - Graceful degradation (no crash)
   - Clear error message
   - No silent data corruption
   - Security boundary preserved

3. Test location: tests/adversarial/ (separate from tests/unit/)
   Rationale: adversarial tests are slower and more expensive;
   shouldn't block fast feedback loop in normal development.

## Trade-offs accepted
- No automated fuzzing (would require LibFuzzer-style infrastructure)
- No adversarial ML attacks (FGSM, PGD) on the CV model
- Phase 1 pilot will surface real-world adversarial patterns we
  can't anticipate
