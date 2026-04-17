---
type: DECISION
date: 2026-04-17
created_at: 2026-04-17T14:00:00Z
author: co-authored
session_id: 01358dfa-9027-4e11-a69e-056289852b5a
session_turn: 8
project: greenloop-f2c
topic: optimizer C1b crop-tier coverage and C5 LED enforcement
phase: implement
tags: [layer2, optimizer, ortools, constraints]
---

# Optimizer constraint improvements

## What changed

**C1b: Crop-tier coverage constraint** — Each crop must be assigned to at least 1 tier. Previously, the optimizer could stack all 3 tiers on the single most profitable crop, leaving other crops unassigned. This constraint forces diversification.

```python
for c in range(NUM_CROPS):
    model.add(sum(assign[c, t] for t in range(NUM_TIERS)) >= 1)
```

**C5: LED hours per tier enforcement** — Previously a soft incentive via revenue weighting. Now enforced as a hard constraint via `only_enforce_if`: if crop c is on tier t, the tier's LED-on hours must be at least 80% of the crop's daily requirement. The threshold was also bumped from 50% to 80%.

```python
for t in range(NUM_TIERS):
    total_led_t = sum(led[t, h] for h in range(NUM_HOURS))
    for c in range(NUM_CROPS):
        cid = CROP_IDS[c]
        min_hours = max(1, crop_led_hours[cid] * 4 // 5)  # 80%
        model.add(total_led_t >= min_hours).only_enforce_if(assign[c, t])
```

**Dashboard**: Forecast bar chart expanded from 5 to 10 crops with per-crop colors matching the established crop palette.

## Trade-off

Hard C5 constraints make the MILP harder — typhoon re-solve went from ~2s to ~3.4s. The typhoon integration test timeout was bumped from 3s to 4s to account for this. This is a deliberate tradeoff: the old soft incentive meant LED hours were frequently zeroed out, which would cause crop failures in production.

## Follow-up

- The 80% threshold is a guess. Real-world crop science data should validate or adjust it.
- C1b does not prevent a single crop from taking all tiers if NUM_TIERS > 1 but NUM_CROPS == 1. Edge case for future expansion.

## For Discussion

- **Counterfactual**: If C5 had remained a soft incentive (revenue penalty for LED deviation) instead of a hard constraint, how much would the optimizer have reduced LED hours under peak electricity pricing? Would any crop have received fewer than 4 hours?
- **Data reference**: The typhoon re-solve benchmark is at `tests/integration/test_pipeline.py::TestTyphoonScenario::test_typhoon_resolves_under_3_seconds`. After the C1b/C5 changes, the re-solve takes ~3.4s — is the 4s timeout acceptable, or should we add OR-Tools search heuristics (e.g., `set_num_search_workers`) to bring it under 3s?
- **Validation**: The 80% threshold for LED hours is an engineering guess. What crop science source would confirm or invalidate this? Is the constraint too loose (80% still allows meaningful energy savings) or too tight (does not allow deliberate LED reduction as a cost lever)?
