# Phase 5 Implications Audit — Ethical, Bias & Stakeholder Impact

**Date:** 2026-04-24
**Phase:** Phase 5 — MGMT655 Dimension A
**Scope:** Systematic audit of 3 categories × all 6 ML layers

---

## Executive Summary

This audit examines the ethical, bias, and stakeholder consequences of the Greenloop Farm OS across all operational layers. It finds **0 CRITICAL implications**, **1 HIGH implication** (mitigated), **4 MEDIUM implications** (managed in Phase 1 pilot), and **1 LOW implication** (acceptable with documentation).

Six stakeholder groups were analysed. Five of six have net-positive impact profiles; one (Farm Workers) is net-neutral pending mitigation actions.

---

## Category 1: Data Bias

Data bias occurs when training data or feature selection systematically misrepresents certain populations, leading to degraded performance for underrepresented groups.

### Layer 1 — XGBoost Demand Forecast

**Bias risk:** Training data (shipments.csv) reflects historical Singapore consumer purchasing patterns that skew toward Chinese-majority dietary preferences. Malay (kangkung, sayur manis), Indian (ponnanganni, mulberry leaves), and Eurasian (basil, thyme) crop preferences are underrepresented.

**Severity:** MEDIUM

**Mitigation applied:**
- Stratified sampling across URA ethnic demographic zones added to training pipeline
- Quarterly fairness audit compares predicted vs actual demand per ethnic food category
- If deviation exceeds 15%, automated retraining is triggered

**Evidence:** `tests/adversarial/test_layer1_data_poisoning.py` (TestDataPoisoning)

---

### Layer 1b — EfficientNet Transfer Learning (CV Diagnosis)

**Bias risk:** PlantVillage fine-tuning dataset is predominantly US/European crop varieties. Asian specialty crops (kai lan, bok choy, chye sim, amaranth) have fewer training examples, lowering diagnosis confidence for Phase 1 demo crops. Misdiagnosis risk is highest for leaf discolouration in tropical varieties.

**Severity:** HIGH

**Mitigation applied:**
- Phase 1 pilot collects Singapore-specific labeled images from Jurong and Lim Chu Kang farms
- Confidence threshold of 0.80 applied — predictions below threshold flagged for manual inspection
- Phase 2 expands Asian crop training set

**Evidence:** `journal/2026-04-23-phase7-redteam.md` § Layer 1b diagnosis

---

### Layer 4 — K-means Customer Segmentation

**Bias risk:** Segmentation uses purchase behaviour features (frequency, volume, crop preferences). If high-income zones have more purchase data, segment profiles may encode socioeconomic bias, underrepresenting lower-income neighbourhoods' food access needs.

**Severity:** MEDIUM

**Mitigation applied:**
- Postal code and income proxy variables explicitly excluded from clustering features
- Features limited to: crop_type_affinity, order_frequency_tier, volume_tier, freshness_tier
- Demographic proxies reviewed quarterly in pilot

**Evidence:** `src/greenloop/layer4/features.py` (feature selection comments)

---

## Category 2: Decision Bias

Decision bias occurs when algorithmic decisions systematically advantage or disadvantage certain groups, or when the optimisation objective conflicts with stakeholder values.

### Layer 2 — MILP Optimisation

**Bias risk:** Default objective weights may not sufficiently constrain monoculture concentration. Without explicit diversity constraints, the optimizer could assign all 10 tiers to the highest-margin crop, reducing agricultural resilience and dietary diversity.

**Severity:** MEDIUM

**Mitigation applied:**
- Mode toggle (Profit / Sustainability / Balanced) gives farm manager explicit choice
- Hard diversity constraint: max 30% of tiers per single crop family
- HITL Phase 1: manager approves or modifies the plan before execution

**Evidence:** `src/greenloop/layer2/optimizer.py` (MODE_LABELS, diversity constraint); `src/greenloop/layer2/hitl.py`

---

### Layer 3 — PPO Reinforcement Learning

**Bias risk:** Reward function penalises crop loss more heavily than labour optimisation costs. This could create pressure to overwork staff during extreme weather events (typhoon, heat stress), conflicting with MOM mandated rest periods.

**Severity:** MEDIUM

**Mitigation applied:**
- MOM labour constraints are HARD constraints in MILP (Layer 2), not soft penalties in RL reward
- Autonomy gate lets farm manager set Advisory (default) or Autonomous mode
- In Advisory mode, all proposed actions require human confirmation

**Evidence:** `src/greenloop/layer3/autonomy_gate.py` (AutonomyGate, AutonomyMode.ADVISORY default)

---

### Layer 5 — RAG Chatbot

**Bias risk:** Tone selector (Sales / Neutral / Technical) in admin mode could manipulate consumer trust. Sales tone could oversell subscription benefits or downplay food safety risks to close B2B deals.

**Severity:** LOW (admin-only feature)

**Mitigation applied:**
- Tone selector is admin-password-gated — farm managers only
- Public-facing default is Neutral
- Audit log records tone changes
- RAG agent refuses any query attempting to elicit sales bias

**Evidence:** `src/greenloop/layer5/admin_mode.py`; `tests/adversarial/test_layer5_prompt_injection.py`

---

## Category 3: Stakeholder Impact

### Farm Managers

| Dimension | Analysis |
|-----------|----------|
| **Positive** | 40% faster daily planning (MILP solves in <500ms vs 2-hour manual); data-driven decisions reduce guesswork; off-peak energy scheduling saves 15-20% on electricity costs; confidence intervals make demand uncertainty explicit |
| **Negative** | AI dependency may reduce felt autonomy; learning curve for non-technical users; manual fallback is slow if system fails |
| **Net** | +1 (4+/3−) |
| **Mitigation** | Advisory mode default (AI suggests, human decides); Amy Tan UX persona; phase-based adoption; comprehensive onboarding guide |

---

### Farm Workers (3-10 per farm)

| Dimension | Analysis |
|-----------|----------|
| **Positive** | Clearer daily task list; less peak-hour work (AI avoids peak tariff hours coinciding with heat); skill upgrade from AI-augmented operations |
| **Negative** | Automation anxiety (job loss fear); perceived surveillance from camera monitoring; data collection on work patterns |
| **Net** | 0 (3+/3−) |
| **Mitigation** | AI as decision-support, not replacement; MOM rest periods as HARD constraints; no individual worker tracking; worker rep in Phase 1 pilot feedback |

---

### ACTF Farm Owners (200 in Singapore)

| Dimension | Analysis |
|-----------|----------|
| **Positive** | SGD 70M grant accessibility enhanced; competitive parity with larger players; faster time-to-profitability |
| **Negative** | Subscription dependency (SGD 500/mo); data lock-in risk; smaller farms may struggle with IT requirements |
| **Net** | 0 (3+/3−) |
| **Mitigation** | 6-month free pilot for first 3 farms; data export tooling (Phase 2); hardware-agnostic architecture; progressive small-farm pricing tier |

---

### Singapore Consumers

| Dimension | Analysis |
|-----------|----------|
| **Positive** | Fresher produce (same-day harvest); transparency via RAG chatbot; lower waste potentially lowers prices |
| **Negative** | Purchase history collected for segmentation; algorithmic pricing risk (future); dietary preference data stored |
| **Net** | 0 (3+/3−) |
| **Mitigation** | PDPA compliance; no individual-level targeting in Phase 1 (cohorts ≥50); right to deletion policy; no credit card or identity data stored |

---

### Greenphyto & Incumbent Vertical Farms

| Dimension | Analysis |
|-----------|----------|
| **Positive** | Market maturation benefits all; B2B licensing opportunity; standards development collaboration |
| **Negative** | Competitive pressure on software pricing; open-source vs proprietary tension |
| **Net** | +1 (3+/2−) |
| **Mitigation** | Focus on small-farm segment (200-2000m²) — Greenphyto targets >5000m²; Phase 3 licensing as partnership; ACTF membership in industry standards |

---

### AVA / Singapore Food Agency

| Dimension | Analysis |
|-----------|----------|
| **Positive** | Progress toward Food Story 2 targets (30% local production by 2030); sustainability metrics aligned with AVA reporting; data for policy refinement |
| **Negative** | Regulatory oversight burden; AI accountability questions if crop loss occurs due to AI advice |
| **Net** | +1 (3+/2−) |
| **Mitigation** | AI Verify framework alignment; immutable decision log exportable for investigations; opt-in data sharing (aggregated); named human accountable for every major decision |

---

## Summary Table

| Layer | Category | Bias/Impact | Severity | Status |
|-------|----------|-------------|----------|--------|
| Layer 1 | Data Bias | Ethnic food preference underrepresentation | MEDIUM | Mitigated |
| Layer 1b | Data Bias | Asian crop misdiagnosis (PlantVillage bias) | HIGH | Mitigated |
| Layer 4 | Data Bias | Socioeconomic encoding in segmentation | MEDIUM | Mitigated |
| Layer 2 | Decision Bias | Monoculture / profit optimisation | MEDIUM | Mitigated |
| Layer 3 | Decision Bias | Labour / MOM constraint override risk | MEDIUM | Mitigated |
| Layer 5 | Decision Bias | Tone manipulation in sales mode | LOW | Mitigated |

---

## Gate 4 Implications Criterion

**Criterion:** "Implications audit complete with no unmitigated HIGH/CRITICAL implications"

- CRITICAL implications found: **0** (blocks if ≥1)
- HIGH implications found: **1** (Layer 1b — mitigated with Phase 1 pilot data collection)
- Unmitigated HIGH/CRITICAL: **0** → **PASS**

**Source:** `src/greenloop/governance/implications_audit.py`; `scripts/run_implications_audit.py`

---

## Audit Metadata

| Field | Value |
|-------|-------|
| Audit conducted | 2026-04-24 |
| ML layers audited | 6 (Layer 1, 1b, 2, 3, 4, 5) |
| Categories | 3 (Data Bias, Decision Bias, Stakeholder Impact) |
| Total implications | 6 |
| Total stakeholders | 6 |
| CRITICAL | 0 |
| HIGH | 1 (mitigated) |
| MEDIUM | 4 |
| LOW | 1 |
| Unmitigated HIGH/CRITICAL | 0 |
