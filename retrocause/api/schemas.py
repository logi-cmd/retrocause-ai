from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    query: str
    model: str = "openrouter"
    api_key: Optional[str] = None
    explicit_model: Optional[str] = None
    scenario_override: Optional[str] = None


class ProviderPreflightRequest(BaseModel):
    model: str = "openrouter"
    api_key: Optional[str] = None
    explicit_model: Optional[str] = None


class UploadedEvidenceRequest(BaseModel):
    query: str
    content: str
    title: str = ""
    source_name: str = "uploaded evidence"
    domain: str = "general"
    time_scope: Optional[str] = None


class UploadedEvidenceResponse(BaseModel):
    evidence_id: str
    stored: bool
    source_tier: str
    extraction_method: str


class RunStepV2(BaseModel):
    id: str
    label: str
    status: str
    detail: str = ""


class UsageLedgerItemV2(BaseModel):
    category: str
    name: str
    quota_owner: str
    status: str
    count: int = 0
    detail: str = ""


class SavedRunSummaryV2(BaseModel):
    run_id: str
    query: str
    run_status: str
    analysis_mode: str
    created_at: str
    scenario_key: str = "general"


class SavedRunListResponse(BaseModel):
    runs: List[SavedRunSummaryV2] = []


class HarnessCheckV2(BaseModel):
    id: str
    label: str
    status: str
    detail: str = ""


class ProviderPreflightResponse(BaseModel):
    provider: str
    model_name: str
    status: str
    can_run_analysis: bool
    failure_code: Optional[str] = None
    diagnosis: str = ""
    user_action: str = ""
    checks: List[HarnessCheckV2] = []


class ProductHarnessReportV2(BaseModel):
    name: str = "result_value_harness"
    score: float = 0.0
    status: str = "unknown"
    user_value_summary: str = ""
    checks: List[HarnessCheckV2] = []
    next_actions: List[str] = []


class GraphNode(BaseModel):
    id: str
    title: str
    description: str
    probability: int


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class Evidence(BaseModel):
    id: str
    content: str
    source: str
    reliability: str


class EvidenceBindingV2(BaseModel):
    """Evidence record used inside V2 edge and hypothesis structures."""

    id: str
    content: str
    source: str
    reliability: str
    is_supporting: bool
    source_tier: str = "base"
    freshness: str = "unknown"
    timestamp: Optional[str] = None
    extraction_method: str = "manual"
    stance: str = "supporting"
    stance_basis: str = "legacy_or_manual"


class NodeEvidenceV2(BaseModel):
    """Evidence summaries attached to a node."""

    id: str
    content: str
    reliability: str


class UpstreamNodeV2(BaseModel):
    """A single upstream node referenced by another node's upstream_ids."""

    id: str
    label: str
    depth: int


class CitationSpanV2(BaseModel):
    evidence_id: str
    start_char: int
    end_char: int
    quoted_text: str
    relevance_score: float = 0.5


class UncertaintyAssessmentV2(BaseModel):
    uncertainty_types: List[str] = []
    overall_score: float = 0.0
    data_uncertainty: float = 0.0
    model_uncertainty: float = 0.0
    explanation: str = ""


class UncertaintyReportV2(BaseModel):
    per_node: dict = {}
    per_edge: dict = {}
    evidence_conflicts: dict = {}
    overall_uncertainty: float = 0.0
    dominant_uncertainty_type: Optional[str] = None
    summary: str = ""


class GraphNodeV2(BaseModel):
    """Chain-aware node with full provenance."""

    id: str
    label: str
    description: str
    probability: float
    type: str
    depth: int
    upstream_ids: List[str]
    supporting_evidence_ids: List[str]
    refuting_evidence_ids: List[str]
    uncertainty: Optional[UncertaintyAssessmentV2] = None


class GraphEdgeV2(BaseModel):
    """Edge with strength, typed relationship, and evidence bindings."""

    id: str
    source: str
    target: str
    strength: float
    type: str
    supporting_evidence_ids: List[str]
    refuting_evidence_ids: List[str]
    citation_spans: List[CitationSpanV2] = []
    evidence_conflict: str = "none"
    refutation_status: str = "not_checked"


class CounterfactualItemV2(BaseModel):
    """A single counterfactual what-if entry."""

    intervention: str
    original_outcome: str
    counterfactual_outcome: str
    strength: float


class CounterfactualSummaryV2(BaseModel):
    """Aggregated counterfactual analysis for a hypothesis chain."""

    items: List[CounterfactualItemV2]
    overall_confidence: float


class HypothesisChainV2(BaseModel):
    """One competing explanation chain."""

    chain_id: str
    label: str
    description: str
    probability: float
    nodes: List[GraphNodeV2]
    edges: List[GraphEdgeV2]
    supporting_evidence_ids: List[str]
    refuting_evidence_ids: List[str]
    refutation_status: str = "not_checked"
    counterfactual: CounterfactualSummaryV2
    depth: int


class UpstreamMapEntryV2(BaseModel):
    """A single entry in the upstream drill-down map."""

    node_id: str
    node_label: str
    upstream_node_ids: List[str]


class UpstreamMapV2(BaseModel):
    """Full upstream drill-down map for the query."""

    entries: List[UpstreamMapEntryV2]


class PipelineEvaluationV2(BaseModel):
    evidence_sufficiency: float
    probability_coherence: float
    chain_diversity: float
    overall_confidence: float
    weaknesses: List[str] = []
    recommended_actions: List[str] = []


class RetrievalTraceItemV2(BaseModel):
    source: str
    source_label: str = ""
    source_kind: str = "unknown"
    stability: str = "unknown"
    cache_policy: str = "no_cache_policy"
    query: str
    result_count: int
    cache_hit: bool = False
    error: Optional[str] = None
    status: str = "ok"
    retry_after_seconds: Optional[int] = None


class ChallengeCheckV2(BaseModel):
    edge_id: str
    source: str
    target: str
    query: str
    result_count: int = 0
    refuting_count: int = 0
    context_count: int = 0
    status: str = "not_checked"


class AnalysisBriefV2(BaseModel):
    answer: str
    confidence: float = 0.0
    top_reasons: List[str] = []
    challenge_summary: str = ""
    missing_evidence: List[str] = []
    source_coverage: str = ""


class ScenarioV2(BaseModel):
    key: str
    label: str
    confidence: float
    detection_method: str
    user_value: str


class ProductionBriefItemV2(BaseModel):
    title: str
    summary: str
    evidence_ids: List[str] = []
    confidence: float = 0.0


class ProductionBriefSectionV2(BaseModel):
    kind: str
    title: str
    items: List[ProductionBriefItemV2] = []


class ProductionBriefV2(BaseModel):
    title: str
    scenario_key: str
    executive_summary: str
    sections: List[ProductionBriefSectionV2] = []
    limits: List[str] = []
    next_verification_steps: List[str] = []


class ProductionHarnessCheckV2(BaseModel):
    name: str
    passed: bool
    severity: str
    message: str


class ProductionHarnessReportV2(BaseModel):
    status: str
    score: float
    scenario_key: str
    checks: List[ProductionHarnessCheckV2] = []
    next_actions: List[str] = []


class AnalyzeResponseV2(BaseModel):
    """Enriched top-level response for multi-hop causal tracing."""

    query: str
    run_id: Optional[str] = None
    run_status: str = "completed"
    run_steps: List[RunStepV2] = []
    usage_ledger: List[UsageLedgerItemV2] = []
    is_demo: bool = False
    demo_topic: Optional[str] = None
    analysis_mode: str = "live"
    freshness_status: str = "unknown"
    time_range: Optional[str] = None
    partial_live_reasons: List[str] = []
    recommended_chain_id: Optional[str]
    chains: List[HypothesisChainV2]
    evidences: List[EvidenceBindingV2]
    upstream_map: UpstreamMapV2
    evaluation: Optional[PipelineEvaluationV2] = None
    retrieval_trace: List[RetrievalTraceItemV2] = []
    challenge_checks: List[ChallengeCheckV2] = []
    analysis_brief: Optional[AnalysisBriefV2] = None
    markdown_brief: Optional[str] = None
    product_harness: Optional[ProductHarnessReportV2] = None
    scenario: Optional[ScenarioV2] = None
    production_brief: Optional[ProductionBriefV2] = None
    production_harness: Optional[ProductionHarnessReportV2] = None
    uncertainty_report: Optional[UncertaintyReportV2] = None
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    query: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    evidences: List[Evidence]
    is_demo: bool = False
    demo_topic: Optional[str] = None
    analysis_mode: str = "live"
    freshness_status: str = "unknown"
    time_range: Optional[str] = None
