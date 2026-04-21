# GreenLoop F2C — Q&A Preparation

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
