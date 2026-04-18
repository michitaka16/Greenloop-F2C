# Layer 1b: Computer Vision Crop Diagnosis

## Domain: ML / Computer Vision
## Phase: Proposed addition to GreenLoop Farm OS

---

## 1. Overview

Layer 1b adds Computer Vision diagnosis to the GreenLoop Farm OS pipeline. From a single crop rack image, a dual-head neural network classifies:

1. **Growth stage** (3-class): `early` / `mid` / `harvest-ready`
2. **Nutrition status** (3-class): `nitrogen-low` / `water-stress` / `normal`

Both outputs feed into Layer 2 (MILP) and Layer 3 (RL) to adjust harvest timing, fertilizer targets, and control parameters.

**This spec covers**: model architecture, training pipeline, inference deployment, confidence reporting, and the MVP simulation strategy for the VC demo.

---

## 2. Model Architecture

### 2.1 Design Decision: Shared Backbone + Dual Heads (Option A)

**Chosen architecture**: EfficientNet-B0 backbone + two independent classification heads.

**Why Option A over Option B (two separate models)**:
- Single backbone pass is ~2× faster than two serial passes
- Shared feature extraction amortizes data scarcity across both tasks
- Task interference is manageable via dropout regularization
- Option B doubles inference cost without accuracy benefit for MVP scope

**Why Option A over Option C (hard parameter sharing with prefixes)**:
- Option C requires multi-task loss balancing (uncertainty weighting or GradNorm) — a research-level problem
- Option A with shared GAP + dropout before task heads achieves similar feature sharing without MTL complexity

### 2.2 Architecture Specification

```
Input: rack image (224×224×3, RGB)
    ↓
EfficientNet-B0 (pretrained on ImageNet, frozen for MVP)
    ↓ [1280-dim feature vector after Global Average Pooling]
Shared Dropout (p=0.3)
    ↓
Shared Dense (256 units, ReLU activation)
    ↓
Shared Dropout (p=0.2)
    ↓
    ├──→ Head 1: Dense(3, softmax) → growth_stage ∈ {early, mid, harvest_ready}
    │
    └──→ Head 2: Dense(3, softmax) → nutrition_status ∈ {nitrogen_low, water_stress, normal}

Total parameters: ~5.3M (backbone) + ~131K (heads)
Model size: ~21MB (FP32), ~5.5MB (INT8 quantized)
```

### 2.3 Task Labels

**Growth stage** — based on weeks-from-planting and visual morphological cues:

| Label | Morphological Cue | Typical Days Post-Planting |
|-------|-------------------|---------------------------|
| `early` | Seedling < 10cm, cotyledons visible, no true leaves | 0–10 days |
| `mid` | True leaves > 3 per plant, canopy forming, no flowering | 11–20 days |
| `harvest_ready` | Full canopy, leaves at commercial size, no senescence | 21–28 days |

**Nutrition status** — based on visual symptoms under LED grow lights:

| Label | Visual Symptom | LED Lighting Cue |
|-------|---------------|-----------------|
| `nitrogen_low` | General chlorosis (yellowing) starting from older leaves, reduced leaf size | Pale green / yellow-green under blue-dominant LED |
| `water_stress` | Leaf curl, wilting despite adequate nutrients, dry substrate surface | Slight bronzing under red-heavy LED |
| `normal` | Uniform green color, turgid leaves, active new growth | Rich green under full-spectrum LED |

**Class balance requirement**: Training data must have ≥ 15% minority class representation per head. Use class-weighted loss if imbalance exceeds 3:1 ratio.

### 2.4 Loss Function

```
L_total = L_growth_stage + λ * L_nutrition_status

Where:
- L_* = CrossEntropy(logits, labels)
- λ = 1.0 for MVP (equal weight; task weighting can be tuned in Phase 2)
```

---

## 3. Data Requirements

### 3.1 MVP Scope: 2-Crop Limitation

**Critical constraint**: Public datasets cover only 2 of 10 Singapore crops:

| Crop | Public Dataset | Coverage |
|------|---------------|----------|
| Basil | PlantDoc | Disease classification only |
| Kale | Lichoro et al 2020 | Nitrogen deficiency only |

**For MVP**: Layer 1b operates on basil and kale only. Other 8 crops display "Data pending" with no classification output.

**Phase 1 data collection target**: 200 labeled images per crop across all 3 growth stages × 3 nutrition statuses = 1,800 images per crop × 8 pending crops. This is a farm operation milestone, not an engineering deliverable.

### 3.2 Training Data Pipeline

```
Public Dataset Images (PlantVillage/PlantDoc)
    ↓
LED-Spectrum Augmentation (domain adaptation for hydroponic LED)
    ├── Blue channel × 1.10
    ├── Red channel × 1.05
    └── Green channel × 0.85
    ↓
Resize to 224×224
    ↓
Standard ImageNet normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ↓
HorizontalFlip (p=0.5)
RandomRotation (±15°)
ColorJitter (brightness=0.2, contrast=0.2, saturation=0.2)
    ↓
Training: Frozen backbone → Linear probe → Full fine-tune last 2 blocks
```

### 3.3 Data Format

Images stored at `data/cv_training/{crop}/{growth_stage}/{nutrition_status}/{image_id}.jpg`

Example:
```
data/cv_training/
  basil/
    early/
      normal/basil_001.jpg
      nitrogen_low/basil_002.jpg
    mid/normal/basil_003.jpg
    harvest_ready/water_stress/basil_004.jpg
  kale/
    ...
```

---

## 4. Inference Pipeline

### 4.1 Rack-Level Inference

**Trigger**: Every 30 minutes (configurable), or on-demand from dashboard button.

**Per-rack pipeline**:
```python
def diagnose_rack(rack_image: np.ndarray) -> DiagnosisResult:
    # Preprocess
    img = cv2.resize(rack_image, (224, 224))
    img = preprocess_imagenet(img)

    # Inference
    logits_growth, logits_nutrition = model.predict(img)  # Shape: (3,), (3,)

    # Softmax + confidence
    growth_probs = softmax(logits_growth)
    nutrition_probs = softmax(logits_nutrition)

    growth_stage = GROWTH_LABELS[growth_probs.argmax()]
    nutrition = NUTRITION_LABELS[nutrition_probs.argmax()]

    growth_confidence = growth_probs.max()
    nutrition_confidence = nutrition_probs.max()

    return DiagnosisResult(
        rack_id=rack_id,
        growth_stage=growth_stage,
        growth_confidence=growth_confidence,
        growth_probs=growth_probs.tolist(),  # Full distribution for Layer 2
        nutrition_status=nutrition,
        nutrition_confidence=nutrition_confidence,
        nutrition_probs=nutrition_probs.tolist(),  # Full distribution for Layer 2
        timestamp=datetime.now(),
    )
```

### 4.2 Model Loading

```python
# Load once at dashboard startup, keep in memory
@st.cache_resource
def load_cv_model():
    model_path = Path(__file__).resolve().parent.parent.parent / "models" / "layer1b_efficientnet_b0.pt"
    model = torchvision.models.efficientnet_b0(weights=MobileNet_V3_Large_Weights.DEFAULT)
    # Replace classifier with dual-head architecture
    model.classifier = DualHeadClassifier(in_features=1280, num_classes_growth=3, num_classes_nutrition=3)
    state_dict = torch.load(model_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model
```

### 4.3 Fallback Behavior

| Failure Mode | Behavior |
|---|---|
| Model file not found | Display "CV model not loaded — Layer 1b inactive" in dashboard; Layer 2/3 run without CV input |
| Image load error (corrupt frame) | Skip rack, log warning, retry next interval |
| Inference timeout (>5s) | Return `unknown` with confidence=0.0; dashboard shows yellow warning |
| CUDA OOM | Fall back to CPU inference; log GPU memory warning |

---

## 5. Dashboard Integration

### 5.1 CV Diagnosis Panel (New Section)

Add below the existing Layer 1 forecast table in `app.py`:

```
┌─────────────────────────────────────────────────────┐
│  Crop Diagnosis (Layer 1b)                          │
│  [Camera feed thumbnail]  [Diagnose All Racks ▶]    │
├──────────────┬───────────────┬──────────────────────┤
│ Crop         │ Growth Stage  │ Nutrition Status      │
├──────────────┼───────────────┼──────────────────────┤
│ Basil (Rack A)│ mid (87%)    │ normal ✓ (91%)       │
│ Kale (Rack B) │ harvest (72%)| nitrogen_low ⚠ (68%)│
│ Pak Choi      │ Data pending │ Data pending          │
└──────────────┴───────────────┴──────────────────────┘
```

- Growth stage colored: early=blue, mid=yellow, harvest-ready=green
- Nutrition status: normal=green, nitrogen_low=yellow, water_stress=orange
- Confidence shown in parentheses
- Confidence < 70% → yellow warning icon
- Confidence < 50% → red warning icon + "Verify manually"

### 5.2 Confidence Reporting

Every Layer 1b output in the dashboard MUST display:
- Class prediction with label
- Confidence score (0–100%)
- Full probability distribution available on hover/expand

```
⚠ nitrogen_low (68%) — Verify manually
  early: 4% | mid: 28% | harvest_ready: 68%
```

**Why**: Showing only the argmax prediction hides model uncertainty. A farmer who sees "nitrogen_low — 68%" vs "nitrogen_low — 99%" should apply very different confidence to the diagnosis.

---

## 6. Layer 2 Integration

### 6.1 Data Contract: Layer 1b → Layer 2

Layer 1b outputs are passed to Layer 2 MILP as adjustments to production targets:

```python
# In dashboard app.py — _solve_plan call
cv_diagnosis = get_cv_diagnosis()  # Returns dict {rack_id: DiagnosisResult}

plan = build_and_solve(
    forecast=layer1a_forecast,
    crops_df=crops,
    electricity_df=electricity,
    staff_df=staff,
    available_headcount=headcount,
    # Layer 1b inputs:
    cv_diagnosis=cv_diagnosis,  # New parameter
)
```

### 6.2 MILP Adjustment Rules

When `cv_diagnosis` is provided, Layer 2 applies these adjustments:

| CV Output | MILP Adjustment |
|---|---|
| `growth_stage=early` | Extend harvest window by +3 days; reduce expected yield by 40% |
| `growth_stage=mid` | No change to harvest window; reduce expected yield by 10% |
| `growth_stage=harvest_ready` | Confirm harvest window; no yield adjustment |
| `nutrition_status=normal` | No fertilizer adjustment |
| `nutrition_status=nitrogen_low` | Increase fertilizer cost budget by 15% |
| `nutrition_status=water_stress` | Increase water/irrigation frequency by 1× |
| `confidence < 0.70` | Apply ±50% wider uncertainty band (act on distribution tails) |

### 6.3 Probability Distribution as Constraint Input

Instead of passing point estimates, pass the full softmax distribution to allow robust optimization:

```python
# MILP receives full probability vector instead of argmax
cv_diagnosis[rack_id] = {
    "growth_stage_probs": [0.04, 0.28, 0.68],  # [early, mid, harvest_ready]
    "nutrition_probs": [0.68, 0.12, 0.20],       # [nitrogen_low, water_stress, normal]
}
# MILP can now compute expected yield as weighted sum across growth stages
```

---

## 7. Layer 3 Integration

### 7.1 Data Contract: Layer 1b → Layer 3

Layer 1b updates the RL agent's control targets via `rl_env.update_targets()`:

```python
# After CV diagnosis runs
if cv_diagnosis:
    for rack_id, diag in cv_diagnosis.items():
        if diag.growth_stage == "harvest_ready":
            # Signal RL to prepare for harvest: reduce nutrients, lower temperature slightly
            rl_targets[rack_id] = {
                "temp_target_c": 18.0,  # Slightly cooler to slow growth
                "nutrient_target": 0.6,  # Reduce to 60% of standard
                "harvest_imminent": True,
            }
        elif diag.nutrition_status == "nitrogen_low":
            # Boost nitrogen in nutrient solution
            rl_targets[rack_id] = {
                "nutrient_target": 1.2,  # 20% above standard
            }
```

### 7.2 Harvest Escalation Gate

**Critical**: Layer 3 must not act on a single `harvest_ready` reading.

```python
HARVEST_CONFIRMATION_THRESHOLD = 3  # Consecutive readings
HARVEST_CONSECUTIVE_INTERVAL_MINUTES = 30

# Track harvest readings per rack
harvest_readings = defaultdict(list)  # {rack_id: [(timestamp, confidence), ...]}

def on_diagnosis(diag: DiagnosisResult):
    if diag.growth_stage == "harvest_ready" and diag.growth_confidence > 0.75:
        harvest_readings[diag.rack_id].append((diag.timestamp, diag.growth_confidence))

    # Prune old readings
    cutoff = datetime.now() - timedelta(minutes=HARVEST_CONSECUTIVE_INTERVAL_MINUTES * HARVEST_CONFIRMATION_THRESHOLD)
    harvest_readings[diag.rack_id] = [
        r for r in harvest_readings[diag.rack_id] if r[0] > cutoff
    ]

    # Escalate only if threshold met
    if len(harvest_readings[diag.rack_id]) >= HARVEST_CONFIRMATION_THRESHOLD:
        rl_env.update_targets({"harvest_imminent": True})
        st.warning(f"Rack {diag.rack_id}: Harvest confirmed by CV ({len(harvest_readings[diag.rack_id])} consistent readings)")
```

---

## 8. MVP Simulation Strategy (VC Demo)

### 8.1 What to Simulate

| Component | Keep Real? | Reason |
|---|---|---|
| EfficientNet-B0 backbone | **Yes** | Real ImageNet features provide visual authenticity |
| Feature maps visualization | **Yes** | Shows "what the AI sees" — compelling for VC demo |
| Dual-head classification | **No (simulate)** | Real classification on 8/10 crops would be random-guess accuracy |
| Confidence scores | **Yes** | Add Gaussian noise to simulated labels to produce realistic confidence distribution |

### 8.2 Simulation Implementation

```python
# SimulatedLayer1bOutput: generates realistic-looking outputs for demo
RACK_SCENARIOS = {
    "basil_A": {"growth_stage": "mid", "nutrition": "normal", "confidence": 0.87},
    "basil_B": {"growth_stage": "harvest_ready", "nutrition": "nitrogen_low", "confidence": 0.72},
    "kale_C": {"growth_stage": "early", "nutrition": "normal", "confidence": 0.91},
    "lettuce_D": {"growth_stage": "mid", "nutrition": "water_stress", "confidence": 0.65},
}

def simulate_diagnosis(rack_id: str) -> DiagnosisResult:
    scenario = RACK_SCENARIOS.get(rack_id, {"growth_stage": "mid", "nutrition": "normal", "confidence": 0.80})

    # Add controlled noise to confidence
    noisy_confidence = scenario["confidence"] + np.random.normal(0, 0.05)
    noisy_confidence = np.clip(noisy_confidence, 0.50, 0.97)

    # Generate realistic probability distribution
    probs = np.array([0.0, 0.0, 0.0])
    probs[GROWTH_LABELS.index(scenario["growth_stage"])] = noisy_confidence
    remaining = 1.0 - noisy_confidence
    other_indices = [i for i in range(3) if i != probs.argmax()]
    probs[other_indices[0]] = remaining * np.random.dirichlet([1.0, 0.5])[0]
    probs[other_indices[1]] = remaining * np.random.dirichlet([1.0, 0.5])[1]

    return DiagnosisResult(
        rack_id=rack_id,
        growth_stage=scenario["growth_stage"],
        growth_confidence=noisy_confidence,
        nutrition_status=scenario["nutrition"],
        nutrition_confidence=noisy_confidence - 0.05,
        timestamp=datetime.now(),
    )
```

### 8.3 Demo UI Toggle

```python
USE_SIMULATED_CV = os.environ.get("GREENLOOP_CV_MODE", "simulated")  # "real" or "simulated"

@st.cache_resource
def get_cv_model():
    if USE_SIMULATED_CV == "real":
        return load_real_efficientnet_model()
    return None

def diagnose_all_racks():
    if USE_SIMULATED_CV == "simulated":
        return {rack_id: simulate_diagnosis(rack_id) for rack_id in RACK_IDS}
    return run_real_inference(get_cv_model())
```

---

## 9. Non-Functional Requirements

| Requirement | Target | Measurement |
|---|---|---|
| Inference latency (per rack) | < 100ms on CPU | `time.perf_counter()` on `model.predict()` |
| Memory footprint | < 200MB (including model + input buffers) | `tracemalloc` during inference |
| Model file size | < 25MB (INT8 quantized) | `os.path.getsize(model_path)` |
| Dashboard CV panel load time | < 2s | Streamlit profiler |
| Minimum confidence for auto-action | 70% | Config flag, fail-safe default |

---

## 10. File Locations

```
src/greenloop/
  layer1b/                      # NEW — CV module
    __init__.py
    architecture.py              # DualHeadClassifier model definition
    inference.py                # diagnose_rack(), load_model()
    simulation.py               # RACK_SCENARIOS, simulate_diagnosis()
    augmentation.py             # LED-spectrum color transforms
    data_pipeline.py            # Dataset loader, ImageNet normalization

models/
  layer1b_efficientnet_b0.pt    # Trained model weights (committed to repo)
  layer1b_efficientnet_b0_int8.pt  # Quantized model (optional)

data/cv_training/              # Training data (gitignored, not committed)
  {crop}/{growth_stage}/{nutrition_status}/*.jpg

tests/
  unit/test_layer1b_inference.py  # Model loading, inference shape tests
  integration/test_layer1b_wiring.py  # Full pipeline test
```

---

## 11. Open Decisions

| Decision | Options | Status |
|---|---|---|
| Backbone choice | EfficientNet-B0 vs MobileNetV3-Large vs CLIP ViT-B/32 | **Open** — depends on UMAP validation on real farm images |
| Nutrition status granularity | 3-class (N-low/water/normal) vs 9-class (N/P/K × low/mid/high) | **Open** — 3-class MVP, 9-class Phase 2 |
| Camera placement | Top-down (overhead) vs side-view vs RGB-D depth camera | **Open** — affects classification signal significantly |
| Real data collection | In-house farm photography vs crowdsourced annotation vs third-party dataset | **Open** — farm operation milestone |
| Training compute | CPU fine-tuning (hours) vs GPU (20min) vs cloud ML (cost) | **Open** — depends on available hardware |
