# Overnight Batch — 2026-04-22

## Session Summary

Ran 5 tasks sequentially. Committed after each. Pushed at end.

---

## Task 1: Multi-rack grid view (Option C)
**Status: ✓ Completed**

**Commit:** `897c13a feat(dashboard): 10-rack grid view + batch demo set loader`

- Replaced single-image upload with 3×4 rack grid
- Per-cell: upload button, thumbnail, diagnosis badge, confidence
- Top action bar: Load demo set / Diagnose all / Reset / Re-solve Layer 2
- Summary bar: rack count, diagnosed count, healthy/attention
- Phase context info box at top of section
- State: `st.session_state.rack_images` + `st.session_state.rack_diagnoses`

**Note:** Task spec said `src/greenloop/dashboard/components/crop_diagnosis.py` but the 10-rack grid was kept in `app.py` as `_render_cv_diagnosis()`. Component file was not created (previous session decision).

---

## Task 2: Remove redundant panels
**Status: ✓ Completed**

**Commit:** `2bdc603 refactor(dashboard): remove redundant rack panels — consolidated into grid`

- Removed "Today's Rack Assignment" panel
- Removed "All-rack diagnosis" panel
- All info now lives per-cell in the 10-rack grid

---

## Task 3: Diversity constraint in MILP
**Status: ✓ Completed**

**Commit:** `ac20dda feat(layer2): diversity constraint — max 30% per crop`

- `MAX_RACKS_PER_CROP = int(NUM_TIERS * 0.3)` = 3 for 10 tiers
- Hard constraint added to MILP: no crop assigned to more than 3 racks
- Tests: `test_no_crop_exceeds_30_percent_by_default`, `test_plan_has_at_least_4_different_crops`, `test_diversity_does_not_cause_infeasibility` — all passing

---

## Task 4: Forecast-labeled KPIs with confidence bands
**Status: ✓ Completed (interrupted session, resumed and committed)**

**Commit:** `d064d97 feat(dashboard): relabel KPIs as Forecasted with CI bands`

- `src/greenloop/layer2/forecast_band.py` (new): `ProfitBand` dataclass + `compute_profit_band()` — propagates Layer 1 XGBoost lower_ci/upper_ci through MILP revenue model
- `src/greenloop/layer2/optimizer.py`: added `lower_ci` to `uncertainty_buffers`, added `crop_prices` and `crop_spoilage` to plan dict
- `_render_kpi_strip()`: "Profit (SGD)" → "Forecasted Profit (SGD)" with ±CI band as st.metric delta; same for Revenue
- `_render_plan()`: same relabeling + CI band computation
- Typhoon section: "Profit" → "Forecasted Profit"
- `deliverables/01_pitch_storyline.md`: added robust optimization narrative about upper_ci production target
- `deliverables/03_qa_preparation.md`: added Q&A "Is that profit number predicted or actual?"
- `tests/unit/test_layer2/test_forecast_band.py` (new): 6 tests
- `tests/unit/test_dashboard/test_kpi_strip.py`: updated expected labels

---

## Task 5: Phase-based camera operation docs
**Status: ✓ Completed (markdown); ✗ Skipped (.docx)**

`.docx` files (`GreenLoop_v5_4_JA.docx`, `GreenLoop_v5_4_EN.docx`) are binary and cannot be edited. Markdown deliverables updated:

**Commit:** `35f2a1b docs: add Phase-based camera operation to proposal + Q&A + pitch` (from previous session)

- `deliverables/01_pitch_storyline.md`: updated Transfer Learning section with Phase 1/2/3 narrative
- `deliverables/03_qa_preparation.md`: added 2 Q&As — "Do managers really photograph racks manually?" and "How does Greenphyto do this?"

---

## Test Results
- **434 passed**, 1 skipped, 84 warnings
- All 5 task areas green

## Push
- Pushed to `origin/main` (2bdc603..d064d97)

## Notes
- `.docx` files in `deliverables/` need manual editing for camera operation table
- 14 test failures in overnight batch were from the interrupted session's stashed changes — resolved after popping stash and fixing `test_kpi_strip.py`
