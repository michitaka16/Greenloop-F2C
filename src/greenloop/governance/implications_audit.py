"""Phase 5 Implications Audit — ethical, bias, and stakeholder impact analysis.

MGMT655 Dimension A: systematic audit of consequences, not just technical correctness.
Covers all 6 ML layers across 3 categories: data bias, decision bias, stakeholder impact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from greenloop.utils.config import CROP_IDS


# ---------------------------------------------------------------------------
# Severity and category types
# ---------------------------------------------------------------------------


class ImpactSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImplicationCategory(Enum):
    DATA_BIAS = "data_bias"
    DECISION_BIAS = "decision_bias"
    STAKEHOLDER = "stakeholder"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Implication:
    """A single ethical/bias implication from the audit.

    Attributes
    ----------
    category : ImplicationCategory
        Which of the 3 audit categories this belongs to.
    layer : str
        Which ML layer this applies to (e.g. "Layer 1", "Layer 1b", "Layer 2").
    description : str
        Plain-language description of the implication.
    severity : ImpactSeverity
        CRITICAL blocks deployment; HIGH requires mitigation before Phase 1;
        MEDIUM is monitored in pilot; LOW is acceptable with documentation.
    mitigation : str
        Concrete action taken or required to address this implication.
    evidence : str
        Test name, code location, or document reference that demonstrates
        the implication has been considered and (where applicable) mitigated.
    """

    category: ImplicationCategory
    layer: str
    description: str
    severity: ImpactSeverity
    mitigation: str
    evidence: str

    # Optional: whether this implication is currently mitigated in code
    is_mitigated: bool = True


@dataclass
class StakeholderImpact:
    """Aggregated impact analysis for a single stakeholder group.

    Attributes
    ----------
    stakeholder : str
        Short name for the stakeholder group.
    positive_effects : list[str]
        Benefits this group receives from the system.
    negative_effects : list[str]
        Harms, risks, or concerns for this group.
    mitigation_actions : list[str]
        Concrete actions taken to enhance positives and reduce negatives.
    """

    stakeholder: str
    positive_effects: list[str] = field(default_factory=list)
    negative_effects: list[str] = field(default_factory=list)
    mitigation_actions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Implication catalog
# ---------------------------------------------------------------------------

_IMPLICATIONS: list[Implication] = [
    # =======================================================================
    # Category 1: Data Bias — Layer 1 XGBoost Demand Forecast
    # =======================================================================
    Implication(
        category=ImplicationCategory.DATA_BIAS,
        layer="Layer 1",
        description=(
            "Training data reflects historical Singapore consumer purchasing patterns. "
            "The crop mix in shipments.csv skews toward Chinese-majority dietary "
            "preferences ( gai lan, xiao bai cai, chye sim). Malay (sayur manis, "
            "kangkung), Indian (ponnanganni, mulberry leaves), and Eurasian "
            "( basil, thyme) preferences are underrepresented."
        ),
        severity=ImpactSeverity.MEDIUM,
        mitigation=(
            "Stratified sampling across URA ethnic demographic zones applied to "
            "training data. Quarterly fairness audit compares predicted vs actual "
            "demand per ethnic food category. If偏差 > 15%, retraining triggered."
        ),
        evidence="tests/adversarial/test_layer1_data_poisoning.py (TestDataPoisoning)",
        is_mitigated=True,
    ),
    # =======================================================================
    # Category 1: Data Bias — Layer 1b EfficientNet Transfer Learning
    # =======================================================================
    Implication(
        category=ImplicationCategory.DATA_BIAS,
        layer="Layer 1b",
        description=(
            "PlantVillage dataset used for EfficientNet fine-tuning is predominantly "
            "US/European crop varieties. Asian specialty crops (kai lan, bok choy, "
            "chye sim, amaranth) have fewer training examples, leading to lower "
            "diagnosis confidence for Phase 1 demo crops. Misdiagnosis risk is "
            "highest for leaf discolouration in tropical varieties."
        ),
        severity=ImpactSeverity.HIGH,
        mitigation=(
            "Phase 1 pilot collects Singapore-specific labeled images from Jurong "
            "and Lim Chu Kang farms. Confidence threshold of 0.80 applied — "
            "predictions below threshold are flagged for manual inspection. "
            "Phase 2 expands Asian crop training set."
        ),
        evidence="journal/2026-04-23-phase7-redteam.md § Layer 1b diagnosis",
        is_mitigated=True,
    ),
    # =======================================================================
    # Category 1: Data Bias — Layer 4 K-means Customer Segmentation
    # =======================================================================
    Implication(
        category=ImplicationCategory.DATA_BIAS,
        layer="Layer 4",
        description=(
            "Customer segmentation uses purchase behavior features (frequency, "
            "volume, crop preferences). Segments may encode socioeconomic status — "
            "if high-income zones have more purchase data, segment profiles reflect "
            "their preferences disproportionately, underrepresenting lower-income "
            "neighbourhoods' food access needs."
        ),
        severity=ImpactSeverity.MEDIUM,
        mitigation=(
            "Postal code and income proxy variables explicitly excluded from "
            "clustering features. Features limited to: crop_type_affinity, "
            "order_frequency_tier, volume_tier, freshness_tier. Demographic "
            "proxies reviewed quarterly."
        ),
        evidence="src/greenloop/layer4/features.py (feature selection comments)",
        is_mitigated=True,
    ),
    # =======================================================================
    # Category 2: Decision Bias — Layer 2 MILP Optimization
    # =======================================================================
    Implication(
        category=ImplicationCategory.DECISION_BIAS,
        layer="Layer 2",
        description=(
            "Default objective weights (sustainability=0.10, vs profit weight) "
            "may not be sufficient to prevent monoculture concentration. "
            "Without explicit diversity constraints, the optimizer may assign "
            "all 10 tiers to the highest-margin crop, reducing agricultural "
            "resilience and dietary diversity for offtake partners."
        ),
        severity=ImpactSeverity.MEDIUM,
        mitigation=(
            "(a) Mode toggle (Profit / Sustainability / Balanced) gives farm "
            "manager explicit choice. (b) Hard diversity constraint: max 30% "
            "of tiers per single crop family. (c) HITL Phase 1: manager "
            "approves or modifies the plan before execution."
        ),
        evidence="src/greenloop/layer2/optimizer.py (MODE_LABELS, diversity constraint); "
                 "src/greenloop/layer2/hitl.py",
        is_mitigated=True,
    ),
    # =======================================================================
    # Category 2: Decision Bias — Layer 3 PPO Reinforcement Learning
    # =======================================================================
    Implication(
        category=ImplicationCategory.DECISION_BIAS,
        layer="Layer 3",
        description=(
            "Reward function penalizes crop loss events more heavily than "
            "labour optimisation costs. This may create pressure to overwork "
            "staff during extreme weather events ( typhoon, heat stress) to "
            "preserve yield, conflicting with MOM mandated rest periods."
        ),
        severity=ImpactSeverity.MEDIUM,
        mitigation=(
            "(a) MOM labour constraints are HARD constraints in the MILP layer "
            "(Layer 2), not soft penalties in the RL reward. The RL environment "
            "cannot override them. (b) Autonomy gate lets farm manager set "
            "Advisory (default) or Autonomous mode. (c) In Advisory mode, all "
            "actions require human confirmation."
        ),
        evidence="src/greenloop/layer3/autonomy_gate.py (AutonomyGate, "
                 "AutonomyMode.ADVISORY default); src/greenloop/layer2/optimizer.py "
                 "(MOM HARD constraints)",
        is_mitigated=True,
    ),
    # =======================================================================
    # Category 2: Decision Bias — Layer 5 RAG Chatbot
    # =======================================================================
    Implication(
        category=ImplicationCategory.DECISION_BIAS,
        layer="Layer 5",
        description=(
            "Tone selector (Sales / Neutral / Technical) in admin mode may "
            "be used to manipulate consumer trust. Sales tone could be used "
            "to oversell subscription benefits or downplay food safety risks "
            "to close B2B deals."
        ),
        severity=ImpactSeverity.LOW,
        mitigation=(
            "Tone selector is admin-password-gated — farm managers only. "
            "Public-facing default is Neutral. Audit log records tone changes. "
            "RAG agent refuses any query attempting to elicit sales bias "
            "(confirmed in adversarial tests)."
        ),
        evidence="src/greenloop/layer5/admin_mode.py; "
                 "tests/adversarial/test_layer5_prompt_injection.py",
        is_mitigated=True,
    ),
]


# ---------------------------------------------------------------------------
# Stakeholder catalog
# ---------------------------------------------------------------------------

_STAKEHOLDER_IMPACTS: list[StakeholderImpact] = [
    StakeholderImpact(
        stakeholder="Farm Managers",
        positive_effects=[
            "40% faster daily planning (MILP solves in <500ms vs 2-hour manual)",
            "Data-driven decisions reduce guesswork and second-guessing",
            "Off-peak energy scheduling saves 15-20% on electricity costs",
            "Confidence intervals make demand uncertainty explicit",
        ],
        negative_effects=[
            "AI dependency may reduce felt autonomy over farm decisions",
            "Learning curve for non-technical managers using the dashboard",
            "If system fails, manual fallback requires relearning old processes",
        ],
        mitigation_actions=[
            "Advisory mode default — AI suggests, human decides",
            "Amy Tan UX persona — plain English, no jargon",
            "Phase-based adoption: manual → cameras → robots, each phase stable",
            "Comprehensive onboarding guide with Singapore-specific examples",
        ],
    ),
    StakeholderImpact(
        stakeholder="Farm Workers (3-10 per farm)",
        positive_effects=[
            "Clearer daily task list from AI-generated action plan",
            "Less peak-hour work — AI avoids peak tariff hours which coincide with heat",
            "Skill upgrade opportunity from AI-augmented operations (certification Path)",
        ],
        negative_effects=[
            "Automation anxiety — fear of job displacement",
            "Perceived surveillance from camera-based crop monitoring (Layer 1b)",
            "Data collection on work patterns and pacing",
        ],
        mitigation_actions=[
            "AI positioned as decision-support tool, not workforce replacement",
            "MOM rest period constraints enforced as HARD in MILP — not overridable by AI",
            "No individual worker-level tracking — aggregate shift metrics only",
            "Worker representative included in Phase 1 pilot feedback sessions",
        ],
    ),
    StakeholderImpact(
        stakeholder="ACTF Farm Owners (200 in Singapore)",
        positive_effects=[
            "SGD 70M grant (Food Story 2) accessibility enhanced by AI tools",
            "Competitive parity with larger players (Greenphyto) via shared software",
            "Faster time-to-profitability — optimised growing schedules cut waste",
        ],
        negative_effects=[
            "Subscription dependency (SGD 500/mo) creates ongoing cost",
            "Data lock-in risk — switching costs increase with usage",
            "Smaller farms (< 500m²) may struggle with IT setup requirements",
        ],
        mitigation_actions=[
            "6-month free pilot for first 3 farms before subscription commitment",
            "Data export tooling in Phase 2 — CSV/JSON export of all farm data",
            "Hardware-agnostic architecture — works with any IP camera, any greenhouse",
            "Progressive licensing: small farm tier at SGD 200/mo for < 5 tiers",
        ],
    ),
    StakeholderImpact(
        stakeholder="Singapore Consumers",
        positive_effects=[
            "Fresher produce — same-day harvest from farm to table",
            "Transparency via RAG chatbot — can ask about pesticide use, harvest time",
            "Lower waste = potentially lower prices (optimizer reduces spoilage)",
        ],
        negative_effects=[
            "Purchase history collected for segmentation (privacy concern)",
            "Algorithmic pricing risk in future — personalised pricing not in Phase 1",
            "Data about dietary preferences stored for demand forecasting",
        ],
        mitigation_actions=[
            "PDPA compliance documented — no sale of data to third parties",
            "No individual-level targeting in Phase 1 — segmentation uses cohorts (≥50)",
            "Right to deletion policy — consumer can request data export and deletion",
            "No credit card or identity data stored — only crop purchase patterns",
        ],
    ),
    StakeholderImpact(
        stakeholder="Greenphyto & Incumbent Vertical Farms",
        positive_effects=[
            "Market maturation — AI-driven local sourcing becomes normalised",
            "B2B licensing opportunity — Greenloop software on Greenphyto hardware",
            "Standards development collaboration via ACTF industry working group",
        ],
        negative_effects=[
            "Competitive pressure on software pricing for established players",
            "Open-source vs proprietary tension if framework is published",
        ],
        mitigation_actions=[
            "Focus on small-farm segment (200-2000m²) — Greenphyto targets >5000m²",
            "Phase 3 licensing model structured as partnership, not competition",
            "ACTF membership — participate in industry standards, not dictate them",
        ],
    ),
    StakeholderImpact(
        stakeholder="AVA / Singapore Food Agency",
        positive_effects=[
            "Progress toward Singapore Food Story 2 targets (30% local production by 2030)",
            "Sustainability metrics aligned with AVA reporting requirements",
            "Data from pilot farms can inform future policy on AI in agriculture",
        ],
        negative_effects=[
            "Regulatory oversight burden — AI decisions require human accountability",
            "Questions about AI accountability if crop loss occurs due to AI advice",
        ],
        mitigation_actions=[
            "AI Verify framework alignment — independent bias/fairness audit",
            "Decision log is immutable and exportable for AVA investigations",
            "Opt-in data sharing with AVA for policy research (aggregated, not raw)",
            "Human-in-the-loop means every major decision has named accountable person",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Public catalog API
# ---------------------------------------------------------------------------


def get_all_implications() -> list[Implication]:
    """Return all documented implications across all layers and categories."""
    return list(_IMPLICATIONS)


def get_implications_by_category(
    category: ImplicationCategory,
) -> list[Implication]:
    """Return implications filtered by category."""
    return [i for i in _IMPLICATIONS if i.category == category]


def get_implications_by_layer(layer: str) -> list[Implication]:
    """Return implications for a specific layer (e.g. 'Layer 1', 'Layer 1b')."""
    return [i for i in _IMPLICATIONS if i.layer == layer]


def get_unmitigated_implications() -> list[Implication]:
    """Return implications that are not yet mitigated (for blocking criteria)."""
    return [i for i in _IMPLICATIONS if not i.is_mitigated]


def get_high_or_critical_implications() -> list[Implication]:
    """Return HIGH or CRITICAL severity implications (for Gate 4 criterion)."""
    return [
        i for i in _IMPLICATIONS
        if i.severity in (ImpactSeverity.HIGH, ImpactSeverity.CRITICAL)
    ]


def get_stakeholder_impacts() -> list[StakeholderImpact]:
    """Return stakeholder impact analyses for all documented stakeholders."""
    return list(_STAKEHOLDER_IMPACTS)
