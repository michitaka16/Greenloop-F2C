---
type: DISCOVERY
date: 2026-04-17
created_at: 2026-04-17T15:00:00Z
author: agent
session_id: 01358dfa-9027-4e11-a69e-056289852b5a
session_turn: 12
project: greenloop-f2c
topic: layer1b data scarcity 8 of 10 crops have zero public labeled data
phase: analyze
tags: [layer1b, computer-vision, transfer-learning, data-scarcity]
---

# Layer 1b CV diagnosis: data scarcity is the critical blocker

## Discovery

Adding dual-head transfer learning (EfficientNet-B0 + two classification heads) to GreenLoop Farm OS is technically sound as an architecture, but **8 of 10 Singapore crops have zero public labeled data** for any of the three tasks (growth stage, nutrition status, disease classification).

Only basil and kale have partial coverage:
- Basil: PlantDoc dataset (disease only, MIT license)
- Kale: Lichoro et al 2020 (nitrogen deficiency, East African kale)

All other crops — kai lan, baby spinach, lettuce, chye sim, arugula, pak choi, coriander, mint — have **zero** representation in PlantVillage (~54k images), PlantDoc, or any other public plant dataset.

## Implication

The MVP scope for Layer 1b must be explicitly scoped to basil + kale only. For the other 8 crops, the dashboard will show "Data pending." This is not a placeholder — it is the honest state of public data availability.

## Architecture decision confirmed

**Option A (shared EfficientNet-B0 backbone + dual classification heads) is the correct choice** over Option B (two separate models) and Option C (multi-task learning with hard parameter sharing):
- Single forward pass ~2× faster than Option B
- Task interference manageable via dropout; Option C requires solving multi-task loss weighting (GradNorm / uncertainty weighting) — a research problem
- Shared early features (edges, textures, color) are useful to both heads; later layers specialize

## Highest-risk component

**Wrong backbone features for LED-hydroponic domain** (DM-2, severity 5/5). EfficientNet-B0 pretrained on ImageNet extracts features optimized for natural light, outdoor/shade. Singapore vertical farms use 24-hour LED photoperiod. The domain gap may cause the backbone to extract features irrelevant to hydroponic LED growth (soil texture, natural shadows) that dominate the signal on real farm images.

**Mitigation**: UMAP/t-SNE validation on 10 real farm images before building heads. If cluster separation is poor → switch to CLIP ViT-B/32 frozen feature extractor (better zero-shot generalization to OOD domains).

## For Discussion

- **Counterfactual**: If PlantVillage had included kai lan and pak choi (as minor crops in a Southeast Asian greenhouse dataset), what would the MVP scope have been? Would 6 of 10 crops being covered have changed the architecture choice?
- **Data reference**: The 8-crop data gap is a specific, verifiable claim. Can the team confirm: (a) has anyone attempted to find labeled Singapore crop datasets? (b) is there any existing in-house photography of the farm's crops that could seed a proprietary dataset?
- **Risk calibration**: The cascading error scenario (LED panel change → backbone features drift → wrong growth stage → RL triggers early harvest → 40% yield loss) is severity 5/5. Is this scenario realistic enough to warrant a human-in-the-loop gate on harvest commands before Phase 2?
