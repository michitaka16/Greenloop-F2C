# GreenLoop F2C — Pitch Storyline

## Act 1 — The Problem (0:00–3:00)

**0:00 — Hook**
"Singapore imports over 90% of its food."
→ Show: dependency statistic, COVID/Egg shortage price spike timeline.

**0:30 — Market**
"Every month of shortage costs families and governments millions."
→ Show: ACTF SGD 70M fund commitment, Greenphyto AG CHF 12M raise (Jan 2025).

**1:00 — The Gap**
"Competitors plan farms by hand. GreenLoop plans by AI."
→ Show: manual planning vs. AI planning contrast.

**1:30 — Introduce GreenLoop F2C**
"Five-layer AI platform. Seed to delivery. Every decision optimized."
→ Show: Layer 1 → Layer 2 → Layer 3 → Layer 4 → Layer 5 overview.

---

## Act 2 — The Demo (3:00–5:30)

**3:00 — Layer 1: Demand Forecasting**
"Dubbel's Kailan, Xin Market's Lettuce — what sells tomorrow?"
→ Show: real prediction output, confidence intervals.
"XGBoost quantile regression. q=0.05 / 0.50 / 0.95. 18 indoor-farm features."
→ Confidence interval visualization.

**3:45 — Layer 2: Farm Optimization**
"MILP. Profit-maximizing plan in under 50 milliseconds."
→ Show: 10-tier LED schedule, tariff optimization.
"Electricity: peak vs off-peak LED. Every dollar tracked."
"Revenue and profit are forecasted — not actual. We use XGBoost upper-ci as our production target. The 85% confidence interval for profit is shown on every plan."

**4:30 — Logistics (VRP)**
"30 customers. Jurong depot. 6-hour window."
→ Show: CVRPTW route map. 30/30 customers served.
"147 km total. SGD 188.87 logistics cost."

**5:00 — Typhoon Cascade** *(compressed: 5:00–6:00)*
"Press the Typhoon Warning button.
 Watch — delivery window compresses 12h to 6h.
 Now the real risk: 30% power outage probability during severe typhoon.
 UPS backup: 4 hours remaining. Red banner in the dashboard.
 Layer 2 MILP re-optimizes in emergency harvest mode.
 12 crops harvested early to avoid loss if power doesn't return.
 Cold storage switch activated for unsold produce.
 And — rainy weather at home means consumers order online more.
 Demand surge +20% auto-applied to tomorrow's plan.
 This isn't a delivery delay simulator. This is a full resilience cascade."
→ Show: Typhoon v2 UI with red danger banner, UPS countdown, power outage metrics.

---

## Act 2.5 — The Governance Moment (6:00–6:30)

**6:00 — Before we leave the farm side, one more thing.**
"Every AI startup pitches live demos. Few can answer: what happens when things go wrong AFTER deployment?"

→ Show: Deployment Gate panel in Farm OS

"Phase 8 Deployment Gate. 5 gates, 25 criteria.
Gate 1 Technical: PASS. Gate 3 Risk: PASS after 38 adversarial tests.
Gate 4 Compliance: PASS. Gate 5 Monitoring: PASS with 14 drift checks."

→ Show: Implications Audit panel

"Phase 5 Implications. 6 stakeholders analyzed.
Farm workers face automation anxiety — we mitigate with Advisory mode.
PlantVillage dataset bias may misclassify Asian crops — we flag as HIGH
severity, Phase 1 pilot collects Singapore data."

→ Show: Drift Monitoring panel

"Phase 13 Drift. 14 checks across 6 layers.
XGBoost feature drift weekly. MILP infeasibility rate hourly.
PPO reward drift weekly. RAG relevance daily. Scheduled via YAML."

"This is not a demo. This is a production-ready governance framework."

---

## Act 3 — The Business (6:30–8:00)

**6:30 — Business Model**
"B2B SaaS: SGD 8K/rack/year. 20 racks. 82% gross margin."
→ Show: unit economics table.
"11-month payback. CAC/LTV ratio 0.15."

**7:00 — Go-to-Market**
"Phase 1: 1 anchor farm, Jurong Innovation District."
"Phase 2: 10 farms, B2C subscription."
"Phase 3: APAC AI model licensing."

**7:30 — Why Now**
"Swiss competitor entered Singapore Jan 2025. ACTF fund is open."
"First-mover advantage in AI-native farm OS."

---

## Act 4 — The Ask (8:00–9:00)

**8:00 — Traction**
"259 tests passing. Live dashboard running."
"Silhouette 0.765. 30/30 customers served. 48ms MILP solve."

**8:30 — The Ask**
"[Amount] for [purpose]."
"[What happens next with the investment]."
