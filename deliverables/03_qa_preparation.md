# Adopt a Kale — Q&A Preparation

## Anticipated Questions

---

### Q: Why simulate power outage? Isn't Singapore's grid reliable?

**Primary:** Architect (Member 1)

Singapore's grid is reliable 99.95% of the time. But for a vertical farm, 0.05% downtime is existential. LEDs stop, crops die in hours. Greenphyto lost 40K SGD in one outage in 2023. Building for rare events is how you protect against catastrophic loss.

**Backup:** We consume SP Power's live alert API in production. The demo uses historical SP Power data showing severe typhoons cause localized outages at roughly 30% probability — that's our scenario trigger.

---

### Q: How did you model the 30% probability?

**Primary:** HR Specialist (Member 2)

Historical SP Power data shows severe typhoons cause localized outages with roughly 30% probability. We use this as a demo scenario threshold — in production, we'd consume SP Power's live alert API.

**Backup:** The 30% figure is a conservative estimate from SP Power's publicly reported outage incidents during Northeast Monsoon seasons 2019–2023. It represents a severe typhoon directly affecting the Jurong industrial area.

---

### Q: What about Singapore's weather — temperature, humidity? Why is it not in your model?

**Primary:** Architect (Member 1)

Because our target customers are indoor vertical farms. Temperature, humidity, and rainfall don't affect crop growth in a climate-controlled environment. What DOES matter is consumer behavior in rain — people stay home, order food online more. We model that separately as a demand signal, not a growth signal.

**Backup:** Indoor farms control their own climate. Our Layer 3 PPO RL agent manages LED, CO2, temperature, and humidity set-points autonomously. External weather is irrelevant to the growing environment — it only matters insofar as it affects consumer purchasing behavior.

---

### Q: How does the UPS countdown work in practice?

**Primary:** Architect (Member 1)

When a power outage is triggered (simulated or via SP Power alert), the Layer 3 RL environment enters emergency mode: LEDs forced off, PPO agent receives a large negative reward (-500) per step while on UPS battery. The UPS countdown decrements each simulation step. At zero, if power hasn't returned, the emergency harvest protocol activates — Layer 2 MILP re-solves with yield_multiplier=0 for affected crops.

---

### Q: What's the ROI of the UPS investment?

**Primary:** QN (Business)

A commercial UPS for a 20-rack vertical farm costs roughly 15–25K SGD. One prevented crop loss event (which can exceed 40K SGD based on competitor incidents) pays for the UPS many times over. The resilience cascade — UPS → early harvest → cold storage → demand surge response — is fully automated, so there's no manual intervention cost.

---

### Q: How does emergency harvest work in the MILP?

**Primary:** Architect (Member 1)

When `seed_supply_delayed=True` OR `power_outage=True`, the MILP adds a hard constraint: `max_new_tiers = seed_stock_kg[cid] / growth_days[cid]`. This limits new planting to only what can be supported by available seed stock, preventing the farm from over-committing to growth cycles that can't be completed. In power outage mode, `yield_multiplier=0.0` forces the optimizer to harvest existing crops immediately rather than waiting for a growth cycle that may not complete.

---

### Q: Is that profit number predicted or actual?

**Primary:** QN (Business)

Forecasted — not actual. We use Layer 1 XGBoost quantile regression (q=0.95 upper bound) as our production target in the MILP, which means we're planning for the optimistic case. The confidence interval shown on every plan comes from the lower bound (q=0.05) propagated through the same cost structure. "Profit $401 with 85% confidence between $360 and $440" means: in 85% of scenarios, actual profit will fall in that band — assuming the farm executes the plan and weather behaves as modelled. Actual profit depends on real growing conditions, harvest efficiency, and market prices at time of sale.

---

### Q: What happens if an attacker uploads malicious images?

**Primary:** Architect (Member 1)

Phase 7 Red-Team tested 15 adversarial scenarios covering all 6 ML layers. Disease images can't be misclassified as healthy due to confidence thresholds — the model outputs a confidence score and rejects below 0.75. Corrupt files are rejected gracefully with a clear error, not a silent fallback. See `tests/adversarial/` — 38 tests, 100% passing.

**Backup:** Our EfficientNet model uses dual-head architecture (growth stage + nutrition status). An image that tricks one head would need to simultaneously satisfy both classification criteria to pass as healthy.

---

### Q: Are you ready to ship this?

**Primary:** HR Specialist (Member 2)

Phase 8 Deployment Gate: 5 gates evaluated across 25 criteria. Gates 1, 3, 4, 5 PASS. Gate 2 Business Viability is CONDITIONAL pending real customer data — which is precisely what our Phase 1 pilot is designed for. Our judgment: conditional ship for 3-farm pilot, not general availability.

**Backup:** The automated `run_deployment_gate.py` script produces a machine-readable judgment in under 5 seconds. Anyone can re-run it. The criteria are documented with point-of-contact evidence (test files, journal entries).

---

### Q: How do you know you're not biased?

**Primary:** Finance (Member 3)

Phase 5 Implications Audit, 6 layers × 3 categories (data bias, decision bias, stakeholder impact). We identified 1 HIGH severity bias — EfficientNet trained on PlantVillage (US/EU crops) may misclassify Asian varieties like kai lan and xiao bai cai. Mitigation is in Gate 4 Compliance: Phase 1 pilot collects Singapore-specific training data before general availability.

**Backup:** Full implications audit at `journal/phase5-implications-report.md`. We count 6 stakeholders — managers, workers, owners, consumers, Greenphyto, AVA. Net positive for 5, neutral for 1 (workers: automation anxiety is real, mitigated by Advisory mode).

---

### Q: How will you know if the model degrades over time?

**Primary:** Architect (Member 1)

Phase 13 Drift Monitoring. 14 checks across all 6 layers: XGBoost feature drift via Kolmogorov-Smirnov test (weekly), MILP infeasibility rate (hourly), PPO reward drift (weekly), RAG relevance (daily). Each alert has an automated action — retrain, rollback, or halt. Scheduled via YAML cron. See `config/drift_monitoring_schedule.yaml`.

**Backup:** Until production data flows in, checks return OK with `requires_production_data` status. The framework is in place — activation is automatic as Phase 1 data becomes available.

---

### Q: What's your ethical framework?

**Primary:** Finance (Member 3)

We audit 3 categories per layer: Data bias (demographic representation in training data), Decision bias (MILP optimization weights, RL reward balance), and Stakeholder impact (6 groups — managers, workers, owners, consumers, competitors, regulators). Net positive for 3, neutral for 3. Honest accounting: we don't claim workers are net受益 when they face genuine trade-offs.

**Backup:** The implications audit is integrated with Gate 4 — if any unmitigated HIGH/CRITICAL implication exists, deployment is blocked. Currently: 0 CRITICAL, 1 HIGH (mitigated), 4 MEDIUM, 1 LOW.

---

### Q: What could still go wrong?

**Primary:** HR Specialist (Member 2)

Our redteam self-review documents acknowledge 4 weaknesses per phase. Phase 13 self-review: no baseline data yet, scheduler not deployed, action automation may be aggressive (2 consecutive ALERTs required before retrain), no drift-on-drift detection. We know our limits and document them explicitly.

**Backup:** Full weaknesses and mitigations in `journal/phase7-redteam.md`, `phase8-redteam.md`, `phase5-redteam.md`, `phase13-redteam.md`.

---

### Q: Isn't this over-engineered for an MVP?

**Primary:** Architect (Member 1)

Fair question. The governance framework IS heavy. But MGMT 655 asked for Dimension A — decision quality, not just implementation. Every framework choice is documented: 5 gates not 3, 3 drift categories not 1, 6 stakeholders not 3. Alternatives considered, reasons given. That's the deliverable.

**Backup:** The Decision Log has 25 entries, each with alternatives rejected and rationale. See `journal/decision-log.md`.

---

### Q: Did you actually follow your own methodology?

**Primary:** Finance (Member 3)

Partially. Our Decision Log has a candid entry: Phase 5/7/8/13 were compressed — we ran `/implement` without separate `/analyze` and `/redteam` steps. We recovered with retrospective documentation — 8 analyze+redteam docs added after the fact. We quantified the gap: 10 hours actual vs 17 hours ideal. Phase 1 will use the full workflow. Transparency over perfection.

**Backup:** The 8 retrospective documents (analyze + redteam for each of 4 phases) are at `journal/phase7-analyze.md`, `journal/phase7-redteam.md`, `journal/phase8-analyze.md`, `journal/phase8-redteam.md`, `journal/phase5-analyze.md`, `journal/phase5-redteam.md`, `journal/phase13-analyze.md`, `journal/phase13-redteam.md`.
