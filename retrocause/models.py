"""数据模型 — Evidence, CausalVariable, CausalEdge, HypothesisChain, AnalysisResult"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EvidenceType(str, Enum):
    LITERATURE = "literature"
    NEWS = "news"
    DATA = "data"
    ARCHIVE = "archive"
    SCIENTIFIC = "scientific"
    SOCIAL = "social"
    TESTIMONY = "testimony"


class HypothesisStatus(str, Enum):
    ACTIVE = "active"
    DEBATING = "debating"
    REFINED = "refined"
    REFUTED = "refuted"
    COLLAPSED = "collapsed"


@dataclass
class Evidence:
    id: str
    content: str
    source_type: EvidenceType
    source_url: Optional[str] = None
    timestamp: Optional[str] = None
    prior_reliability: float = 0.5
    posterior_reliability: float = 0.5
    linked_variables: list[str] = field(default_factory=list)


@dataclass
class CausalVariable:
    name: str
    description: str
    evidence_ids: list[str] = field(default_factory=list)
    posterior_support: float = 0.5
    uncertainty_contribution: float = 0.0


@dataclass
class CausalEdge:
    source: str
    target: str
    conditional_prob: float
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    refuting_evidence_ids: list[str] = field(default_factory=list)


@dataclass
class HypothesisChain:
    id: str
    name: str
    description: str
    variables: list[CausalVariable] = field(default_factory=list)
    edges: list[CausalEdge] = field(default_factory=list)
    path_probability: float = 0.0
    posterior_probability: float = 0.0
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    debate_rounds: list[dict] = field(default_factory=list)
    evidence_coverage: float = 0.0
    unanchored_edges: list[str] = field(default_factory=list)
    counterfactual_results: list[CounterfactualResult] = field(default_factory=list)
    counterfactual_score: float = 0.0


@dataclass
class CounterfactualResult:
    """反事实验证结果"""

    hypothesis_id: str
    intervention_var: str
    original_path_prob: float
    intervened_path_prob: float
    probability_delta: float
    still_reachable: bool
    sensitivity_lower: float
    sensitivity_upper: float
    counterfactual_score: float


@dataclass
class FactorIntervention:
    variable_name: str
    original_value: float
    new_value: float
    intervention_type: str = "probability"


@dataclass
class ImpactResult:
    intervention: FactorIntervention
    affected_hypotheses: list[str] = field(default_factory=list)
    original_result_probs: dict[str, float] = field(default_factory=dict)
    new_result_probs: dict[str, float] = field(default_factory=dict)
    probability_deltas: dict[str, float] = field(default_factory=dict)
    affected_variables: list[str] = field(default_factory=list)
    cascade_detail: list[dict] = field(default_factory=list)


@dataclass
class SensitivityPoint:
    variable_name: str
    tested_value: float
    hypothesis_probs: dict[str, float] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    query: str
    domain: str
    variables: list[CausalVariable]
    edges: list[CausalEdge]
    hypotheses: list[HypothesisChain]
    total_evidence_count: int = 0
    total_uncertainty: float = 0.0
    recommended_next_steps: list[str] = field(default_factory=list)
    is_demo: bool = False
    demo_topic: Optional[str] = None
