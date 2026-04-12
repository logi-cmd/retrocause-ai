"""数据模型 — Evidence, CausalVariable, CausalEdge, HypothesisChain, AnalysisResult"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from retrocause.evaluation import PipelineEvaluation


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


class UncertaintyType(str, Enum):
    """不确定性来源分类"""

    EPISTEMIC = "epistemic"
    DATA = "data"
    MODEL = "model"
    THIN_EVIDENCE = "thin_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    LOW_CONFIDENCE_REASONING = "low_confidence_reasoning"


class EvidenceConflictType(str, Enum):
    """证据冲突分类"""

    NONE = "none"  # 无冲突
    PARTIAL = "partial"  # 部分冲突
    DIRECT = "direct"  # 直接矛盾
    TEMPORAL = "temporal"  # 时间线冲突


@dataclass
class CitationSpan:
    """证据中的引用跨度 — 标记证据中与特定因果断言相关的片段"""

    evidence_id: str
    start_char: int  # 证据文本中的起始字符位置（近似）
    end_char: int  # 证据文本中的结束字符位置（近似）
    quoted_text: str  # 被引用的原文片段
    relevance_score: float = 0.5  # 该片段与因果断言的相关度 0-1


@dataclass
class UncertaintyAssessment:
    """单个节点或边的不确定性评估"""

    uncertainty_types: list[UncertaintyType] = field(default_factory=list)
    overall_score: float = 0.0  # 0 = 完全确定, 1 = 完全不确定
    data_uncertainty: float = 0.0  # 数据层面的不确定性
    model_uncertainty: float = 0.0  # 模型/知识层面的不确定性
    explanation: str = ""  # 不确定性的自然语言解释


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
    source_tier: str = "base"
    freshness: str = "unknown"
    captured_at: Optional[str] = None
    extraction_method: str = "manual"


@dataclass
class CausalVariable:
    name: str
    description: str
    evidence_ids: list[str] = field(default_factory=list)
    posterior_support: float = 0.5
    uncertainty_contribution: float = 0.0
    uncertainty: Optional[UncertaintyAssessment] = None


@dataclass
class CausalEdge:
    source: str
    target: str
    conditional_prob: float
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    refuting_evidence_ids: list[str] = field(default_factory=list)
    citation_spans: list[CitationSpan] = field(default_factory=list)
    uncertainty: Optional[UncertaintyAssessment] = None
    evidence_conflict: EvidenceConflictType = EvidenceConflictType.NONE


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
class UncertaintyReport:
    """全 pipeline 不确定性汇总"""

    per_node: dict[str, UncertaintyAssessment] = field(default_factory=dict)
    per_edge: dict[str, UncertaintyAssessment] = field(default_factory=dict)
    evidence_conflicts: dict[str, EvidenceConflictType] = field(default_factory=dict)
    overall_uncertainty: float = 0.0
    dominant_uncertainty_type: Optional[UncertaintyType] = None
    summary: str = ""


@dataclass
class AnalysisResult:
    query: str
    domain: str
    variables: list[CausalVariable]
    edges: list[CausalEdge]
    hypotheses: list[HypothesisChain]
    evidences: list[Evidence] = field(default_factory=list)
    total_evidence_count: int = 0
    total_uncertainty: float = 0.0
    recommended_next_steps: list[str] = field(default_factory=list)
    is_demo: bool = False
    demo_topic: Optional[str] = None
    evaluation: PipelineEvaluation | None = None
    uncertainty_report: Optional[UncertaintyReport] = None
    analysis_mode: str = "live"
    freshness_status: str = "unknown"
