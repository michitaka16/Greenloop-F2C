"""Layer 1b: Computer Vision Crop Diagnosis.

Dual-head EfficientNet-B0 transfer learning for:
- Growth stage: early / mid / harvest_ready
- Nutrition status: nitrogen_low / water_stress / normal

Modules:
- architecture: DualHeadClassifier model definition + DiagnosisResult dataclass
- inference: diagnose_rack() — real model inference with OOD detection + simulation fallback
- simulation: mock_diagnose() + RACK_SCENARIOS for demo mode
- data_pipeline: SyntheticCVDataset + generate_training_data() for training data generation
- train: End-to-end training script for the dual-head model
"""

from greenloop.layer1b.architecture import DiagnosisResult, DualHeadClassifier
from greenloop.layer1b.data_pipeline import (
    SyntheticCVDataset,
    generate_training_data,
    load_training_data,
)
from greenloop.layer1b.inference import check_ood, diagnose_all_racks, diagnose_rack, load_cv_model
from greenloop.layer1b.simulation import (
    GROWTH_BADGES,
    NUTRITION_BADGES,
    diagnose_all_racks_simulated,
    generate_impacts,
    is_simulated_mode,
    mock_diagnose,
    mock_diagnose_from_image,
    RACK_SCENARIOS,
)

__all__ = [
    # Architecture
    "DiagnosisResult",
    "DualHeadClassifier",
    # Inference
    "check_ood",
    "diagnose_all_racks",
    "diagnose_rack",
    "load_cv_model",
    # Simulation
    "GROWTH_BADGES",
    "NUTRITION_BADGES",
    "diagnose_all_racks_simulated",
    "generate_impacts",
    "is_simulated_mode",
    "mock_diagnose",
    "mock_diagnose_from_image",
    "RACK_SCENARIOS",
    # Data pipeline
    "SyntheticCVDataset",
    "generate_training_data",
    "load_training_data",
]
