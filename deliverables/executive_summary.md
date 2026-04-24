% GreenLoop Farm-to-Consumer Vertical Hydroponics OS
% MGMT 655 — AI & Machine Learning | Week 8 Submission
% 2026-04-24

---

# GreenLoop F2C — Executive Summary

## 1. The Opportunity

Singapore imports over 90% of its food. The COVID-19 pandemic and 2022 egg shortage caused price spikes lasting months. The government commits SGD 70M through the ACTF fund to shorten supply chains. Swiss vertical-farm competitor Greenphyto AG raised CHF 12M in January 2025 citing Singapore as their APAC entry point. GreenLoop is first to build the AI-native operating system for hydroponics — competitors plan farms by hand.

## 2. The Product

GreenLoop F2C is a 5-layer AI platform managing a vertical-hydroponic farm from seed to delivery. Layer 1 (XGBoost quantile regression) predicts demand with confidence intervals using 9 indoor-farm-appropriate features: lag shipments (7/14/28d), rolling 28d mean/std, cyclical week encoding, day-of-week, Singapore holiday flags, consumer rainy-day signal (simulated by monsoon month), indoor climate readings (temperature, humidity, CO2 deviation from 800 ppm optimal), electricity tariff tiers, and cross-crop market density. Layer 2 (OR-Tools MILP) generates the profit-maximising daily operating plan in **< 50 ms** — enabling real-time re-planning when conditions change. Layer 3 (PPO RL via Gymnasium) autonomously controls climate. Layer 4 (K-Means k=4 + UMAP) segments customers. Layer 5 (RAG with ChromaDB + Claude) answers investor questions live.

**Key differentiators:**

- **30/30 customers served** by OR-Tools CVRPTW in 6-hour compressed window (nearest-neighbor fails 20-40% of time windows)
- **Silhouette 0.765** at k=4 — beats k=3 (0.698) and k=5 (0.742) for customer segmentation
- **Typhoon scenario (v2)**: live dashboard button cuts delivery window 12 h to 6 h; 30% probability of power outage triggers 4-hour UPS countdown with emergency harvest protocol; demand surge +20% from panic buying; MILP re-solves and shows profit delta in milliseconds

![Kailan — Healthy](data/demo_images/demo_kailan_healthy.jpg){width=180}
![Lettuce — Wilted](data/demo_images/demo_lettuce_wilt.jpg){width=180}
![Spinach — Nitrogen Deficient](data/demo_images/demo_spinach_nitrogen.jpg){width=180}

*Figure 1: Computer vision diagnosis from EfficientNet-B0 dual-head transfer learning — detecting growth stage and nutrition status from rack photography.*

## 3. How It Works

**6 ML Techniques Across 4 Course Domains**

| # | Technique | MGMT 655 Week |
|---|-----------|---------------|
| 1 | XGBoost quantile regression (q=0.05/0.50/0.95) | Week 2-3 |
| 2 | OR-Tools MILP (CP-SAT) — 10 tiers, 24h LED, tariff-aware | Week 4 |
| 3 | K-Means k=4 clustering + UMAP visualization | Week 5 |
| 4 | EfficientNet-B0 dual-head CNN (growth + nutrition) | Week 6-7 |
| 5 | PPO reinforcement learning — Gymnasium simulation | Week 7 |
| 6 | RAG (ChromaDB + sentence-transformers + Claude) | Week 5-6 |

**Daily flow:** 05:00 Layer 1 demand forecast (q=0.95 upper CI) to 06:00 Layer 2 MILP plan (< 50 ms) plus Layer 2b VRP routes (30 customers) to 06:00-22:00 Layer 3 PPO RL controls climate to 08:00-18:00 deliveries to daily Layer 4 re-segmentation to on-demand Layer 5 RAG.

**Typhoon proof:** The Typhoon button triggers a full resilience cascade — not a delivery delay simulator. A 6-hour delivery window compression triggers 30% probability of power outage. If the grid fails, a 4-hour UPS countdown begins with a live red-banner timer in the dashboard. The PPO RL agent forces LEDs off and takes a −500 reward penalty per step on battery. Layer 2 MILP simultaneously re-solves in emergency harvest mode: 12 crops harvested early to prevent total loss if power does not return, cold storage switches activated for unsold produce. Meanwhile, rainy weather keeps consumers indoors — Layer 1 applies a +20% demand surge to tomorrow's plan. Every layer responds autonomously. MILP re-solves in under 50 ms — proving the farm re-plans itself under multi-variable stress without human intervention.

## 4. Governance & Production Readiness

Our system is not just a working demo — it is evaluated against production-readiness criteria:

**Technical validation** (Phase 7 Red-Team)
- 38 adversarial tests across all 6 ML layers
- Covers data poisoning, prompt injection, constraint stress, reward hacking, system-wide cascade
- 100% passing; honest limitations documented in `journal/phase7-redteam.md`

**Ship decision** (Phase 8 Deployment Gate)
- 5 gates, 25 criteria, automated evaluation via `run_deployment_gate.py`
- Technical / Business / Risk / Compliance / Monitoring dimensions
- Current judgment: **CONDITIONAL SHIP** for Phase 1 Pilot
- Gate 2 Business Viability CONDITIONAL — pilot data required

**Ethical analysis** (Phase 5 Implications Audit)
- 6 layers × 3 categories: data bias, decision bias, stakeholder impact
- 1 HIGH severity identified (PlantVillage dataset bias → Asian crop misclassification)
- 6 stakeholders mapped: net positive for 5, neutral for 1 (workers)
- Integrated with Gate 4 Compliance — unmitigated HIGH/CRITICAL blocks deployment

**Operational monitoring** (Phase 13 Drift Monitoring)
- 14 checks across 6 layers + system-wide
- Feature drift: KS test on XGBoost inputs (weekly)
- Performance drift: MILP infeasibility rate (hourly), EfficientNet confidence (daily), PPO reward ratio (weekly)
- Concept drift: XGBoost prediction bias, PPO action distribution, segment stability, customer segment size, MILP constraint violations
- YAML-scheduled execution from hourly to weekly

Together, 13 of 14 MGMT 655 phases completed. Retrospective documentation (analyze + redteam per phase in `journal/`) ensures transparency even where the COC workflow was compressed.

## 5. Business Model

| Stream | Model | Year 1 ARR |
|--------|-------|------------|
| B2B SaaS — Farm OS license | SGD 8K/rack/year | SGD 480 K |
| B2C subscription boxes | 15% GMV commission | SGD 180 K |
| AI model licensing | One-time + support | SGD 60 K |
| **Total** | | **SGD 720 K** |

**Unit economics:** ACV SGD 8,000/rack/year; 20-rack farm; 82% gross margin; CAC/LTV ratio 0.15; payback 11 months. **GTM:** Phase 1 — 1 anchor farm, Jurong Innovation District, 3 paying accounts. Phase 2 — 10 farms (SG + Malaysia), B2C subscription, SGD 500 K ARR. Phase 3 — APAC AI model licensing, SFA national monitoring partnership.

## 6. Evidence & Validation

**Live Dashboard Metrics (typical run)**

| Metric | Value |
|--------|-------|
| Revenue | ~SGD 1,000-1,200 / day |
| Profit | ~SGD 350-450 / day |
| MILP solve time | **< 50 ms** |
| Optimality gap | 0% (proven optimal) |

**VRP — 30 Singapore customers, Jurong depot**

| Metric | Value |
|--------|-------|
| Customers served | **30 / 30** |
| Total route | **147.1 km** |
| Logistics cost | **SGD 188.87** |

**Sustainability** (live-computed by Layer 2 plan): **95% less water** vs. conventional farming (2 L/kg vs. 20 L/kg; source: AVA Singapore 2019). **87% less CO2** (0.3 vs. 2.5 kg-CO2/kg; source: SFA 2023 lifecycle analysis).

**Test suite:** 434 tests — all governance, monitoring, adversarial, and unit tests passing. See `tests/` for full breakdown.

## 7. Team

| Member | Focus |
|--------|-------|
| Takahide Kawabe | Farm OS, MILP, VRP, RL, full-stack integration |
| QN | Business model, segmentation, sustainability |
| Claude (AI agent) | RAG pipeline, CC/CO knowledge extraction, testing |

**4-page dashboard fully functional:** Farm OS (Layer 1-2 + Sustainability + Typhoon) | Logistics (CVRPTW map, 30/30 routes) | Retail AI (K-Means + UMAP, silhouette 0.765) | Media AI (RAG chatbot + demo mode).

## 8. The Ask

**Phase 1 Pilot — SGD 80,000 for 20% equity**

| | |
|-|-|
| Amount | SGD 80,000 |
| Equity | 20% |
| Duration | 12 weeks |
| Farms | 3 pilot farms (Jurong, Lim Chu Kang, Woodlands) |

**Use of funds:** Hardware sensors (SGD 25K) · Singapore training data collection (SGD 20K) · Monitoring infrastructure (SGD 15K) · Pilot operations (SGD 12K) · Contingency (SGD 8K).

**What happens next:** Week 2 — install sensors on 3 pilot farms. Week 6 — first Singapore-specific model retraining with Phase 1 data. Week 12 — governance review and Phase 2 decision gate.

*Submitted: 2026-04-24 | Greenloop-F2C | main | 434 tests passing | 13 of 14 phases complete*
