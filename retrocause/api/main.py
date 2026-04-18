from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
import threading
import json
import logging
import os
import queue
from uuid import uuid4

from retrocause.app.demo_data import (
    PROVIDERS,
    detect_demo_topic,
    topic_aware_demo_result,
)
from retrocause.evidence_access import describe_source_name
from retrocause.evidence_store import EvidenceStore
from retrocause.api.runtime import TimeoutError, run_with_timeout
from retrocause.models import AnalysisResult

logger = logging.getLogger(__name__)

app = FastAPI(title="RetroCause API", description="Backend API for RetroCause Engine")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# ─────────────────────────────────────────────────────────────────────────────
# V2 — Multi-hop causal tracing schema
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceBindingV2(BaseModel):
    """Evidence record used inside V2 edge and hypothesis structures."""

    id: str
    content: str
    source: str
    reliability: str
    is_supporting: bool  # True → supporting, False → refuting
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
    depth: int  # distance from the root of the chain


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
    """
    Chain-aware node with full provenance.
    Covers: id / label / description / probability / type / depth / upstream ids
    """

    id: str
    label: str
    description: str
    probability: float  # 0.0–1.0
    type: str  # e.g. "cause", "effect", "mediator", "confounder"
    depth: int  # position in the causal chain (0 = root cause)
    upstream_ids: List[str]  # ids of direct upstream (parent) nodes
    supporting_evidence_ids: List[str]
    refuting_evidence_ids: List[str]
    uncertainty: Optional[UncertaintyAssessmentV2] = None


class GraphEdgeV2(BaseModel):
    """
    Edge with strength, typed relationship, and evidence bindings.
    Covers: source / target / strength / type / supporting evidence ids / refuting evidence ids
    """

    id: str
    source: str
    target: str
    strength: float  # 0.0–1.0
    type: str  # e.g. "causes", "prevents", "mediates"
    supporting_evidence_ids: List[str]
    refuting_evidence_ids: List[str]
    citation_spans: List[CitationSpanV2] = []
    evidence_conflict: str = "none"
    refutation_status: str = "not_checked"


class CounterfactualItemV2(BaseModel):
    """A single counterfactual what-if entry."""

    intervention: str  # what was hypothetically changed
    original_outcome: str  # what the data says happened
    counterfactual_outcome: str  # what would have happened under intervention
    strength: float  # 0.0–1.0 confidence in this counterfactual


class CounterfactualSummaryV2(BaseModel):
    """Aggregated counterfactual analysis for a hypothesis chain."""

    items: List[CounterfactualItemV2]
    overall_confidence: float  # 0.0–1.0


class HypothesisChainV2(BaseModel):
    """
    One competing explanation chain.
    Covers: chain id / label / probability / nodes / edges / evidence / counterfactuals
    """

    chain_id: str
    label: str
    description: str
    probability: float  # 0.0–1.0
    nodes: List[GraphNodeV2]
    edges: List[GraphEdgeV2]
    supporting_evidence_ids: List[str]
    refuting_evidence_ids: List[str]
    refutation_status: str = "not_checked"
    counterfactual: CounterfactualSummaryV2
    depth: int  # max depth of this chain (for sorting/filtering)


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
    """
    Enriched top-level response for multi-hop causal tracing.
    Preserves query field and adds chain-aware structures.
    """

    query: str
    run_id: Optional[str] = None
    run_status: str = "completed"
    run_steps: List[RunStepV2] = []
    usage_ledger: List[UsageLedgerItemV2] = []
    # True when the engine could not run real analysis and demo data was returned
    is_demo: bool = False
    demo_topic: Optional[str] = None
    analysis_mode: str = "live"
    freshness_status: str = "unknown"
    time_range: Optional[str] = None
    partial_live_reasons: List[str] = []
    # Recommended chain to display by default (None if no chains qualify)
    recommended_chain_id: Optional[str]
    # All competing hypothesis chains
    chains: List[HypothesisChainV2]
    # Evidence pool referenced by chains
    evidences: List[EvidenceBindingV2]
    # Upstream drill-down map
    upstream_map: UpstreamMapV2
    # Pipeline quality evaluation (absent for demo results)
    evaluation: Optional[PipelineEvaluationV2] = None
    # Source-level retrieval trace for UI transparency.
    retrieval_trace: List[RetrievalTraceItemV2] = []
    # Targeted attempts to find counter-evidence or alternative explanations.
    challenge_checks: List[ChallengeCheckV2] = []
    # User-facing synthesis of the current result.
    analysis_brief: Optional[AnalysisBriefV2] = None
    # Copyable OSS research brief built from grounded response fields.
    markdown_brief: Optional[str] = None
    # Harness-level verdict for whether the run produced user-reviewable value.
    product_harness: Optional[ProductHarnessReportV2] = None
    # Scenario-aware production output for market, policy/geopolitics, postmortem, or general use.
    scenario: Optional[ScenarioV2] = None
    production_brief: Optional[ProductionBriefV2] = None
    production_harness: Optional[ProductionHarnessReportV2] = None
    # Uncertainty report
    uncertainty_report: Optional[UncertaintyReportV2] = None
    # Error message when real analysis fails (non-empty = something went wrong)
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


def _scenario_from_key(key: str, confidence: float, detection_method: str) -> ScenarioV2:
    labels = {
        "market": "Market / Investment Brief",
        "policy_geopolitics": "Policy / Geopolitics Brief",
        "postmortem": "Postmortem Brief",
        "general": "General Causal Brief",
    }
    values = {
        "market": (
            "Helps users inspect market-moving factors, evidence freshness, "
            "and trade/research risks."
        ),
        "policy_geopolitics": (
            "Helps users inspect policy or geopolitical drivers, source reliability, "
            "and negotiation constraints."
        ),
        "postmortem": (
            "Helps teams inspect incident, product, or business causes and the evidence "
            "needed before action."
        ),
        "general": "Helps users inspect likely causes, evidence, counterpoints, and gaps.",
    }
    normalized_key = key if key in labels else "general"
    bounded_confidence = max(0.0, min(1.0, confidence))
    return ScenarioV2(
        key=normalized_key,
        label=labels[normalized_key],
        confidence=bounded_confidence,
        detection_method=detection_method,
        user_value=values[normalized_key],
    )


def _detect_production_scenario(
    query: str,
    domain: str = "general",
    override: Optional[str] = None,
) -> ScenarioV2:
    valid = {"market", "policy_geopolitics", "postmortem", "general"}
    if override in valid:
        return _scenario_from_key(override, 1.0, "override")

    normalized = f"{query} {domain}".lower()
    signals = {
        "market": [
            "market",
            "stock",
            "bitcoin",
            "crypto",
            "price",
            "yield",
            "rate",
            "earnings",
            "etf",
        ],
        "policy_geopolitics": [
            "policy",
            "sanction",
            "talks",
            "ceasefire",
            "negotiation",
            "election",
            "treaty",
            "war",
        ],
        "postmortem": [
            "our",
            "incident",
            "outage",
            "conversion",
            "release",
            "churn",
            "customer",
            "retention",
        ],
    }
    scored = {
        key: sum(1 for token in tokens if token in normalized) for key, tokens in signals.items()
    }
    key, count = max(scored.items(), key=lambda item: item[1])
    if count <= 0:
        return _scenario_from_key("general", 0.35, "auto")
    return _scenario_from_key(key, min(0.95, 0.45 + count * 0.15), "auto")


def _derive_partial_live_reasons(result: AnalysisResult) -> List[str]:
    reasons: List[str] = []
    if result.analysis_mode != "partial_live":
        return reasons

    if result.evaluation is not None:
        reasons.extend(result.evaluation.weaknesses[:3])

    if result.freshness_status in {"unknown", "stable"}:
        reasons.append("Fresh evidence is limited for this run.")

    # Preserve order while deduplicating.
    deduped: List[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped[:3]


def _is_live_failure(error_msg: str | None) -> bool:
    if not error_msg:
        return False
    lowered = error_msg.lower()
    return any(
        token in lowered
        for token in [
            "401",
            "authentication",
            "permission",
            "user not found",
            "connection error",
            "apiconnectionerror",
            "timed out",
            "empty result",
            "rate limit",
        ]
    )


def _resolve_provider_model(provider_key: str, explicit_model: str | None) -> tuple[dict | None, str]:
    provider_cfg = PROVIDERS.get(provider_key)
    if explicit_model:
        return provider_cfg, explicit_model
    if provider_cfg and provider_cfg.get("models"):
        return provider_cfg, list(provider_cfg["models"].keys())[0]
    return provider_cfg, provider_key


def _preflight_failure_code(error_msg: str | None) -> str:
    lowered = (error_msg or "").lower()
    if "invalid model" in lowered or ("model" in lowered and "not found" in lowered):
        return "invalid_model"
    if any(token in lowered for token in ["401", "authentication", "permission", "user not found"]):
        return "auth_or_permission"
    if any(token in lowered for token in ["balance", "quota", "insufficient", "credits"]):
        return "billing_or_quota"
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    if "unexpected payload" in lowered or "empty" in lowered or "json" in lowered:
        return "invalid_or_empty_payload"
    return "provider_error"


def _preflight_user_action(failure_code: str | None) -> str:
    actions = {
        "missing_api_key": "Enter an API key before running live analysis.",
        "unknown_provider": "Choose a configured provider or add provider settings first.",
        "invalid_model": "Pick a model listed by the provider, then run preflight again.",
        "auth_or_permission": "Check that the API key is valid and has access to this provider/model.",
        "billing_or_quota": "Check provider balance, quota, or account limits before retrying.",
        "timeout": "Try a faster model or retry when the provider is responsive.",
        "invalid_or_empty_payload": "Try a model with reliable JSON output before running the full analysis.",
    }
    return actions.get(failure_code or "", "Inspect the provider error, then retry preflight.")


def _harness_check(check_id: str, label: str, status: str, detail: str = "") -> HarnessCheckV2:
    return HarnessCheckV2(id=check_id, label=label, status=status, detail=detail)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _create_run_id() -> str:
    return f"run_{uuid4().hex[:12]}"


def _run_store_path() -> Path:
    configured_path = os.environ.get("RETROCAUSE_RUN_STORE_PATH")
    if configured_path:
        return Path(configured_path)
    return Path.cwd() / ".retrocause" / "saved_runs.json"


def _load_saved_run_records() -> list[dict]:
    path = _run_store_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _save_saved_run_records(records: list[dict]) -> None:
    path = _run_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_step(step_id: str, label: str, status: str, detail: str = "") -> RunStepV2:
    return RunStepV2(id=step_id, label=label, status=status, detail=detail)


def _build_run_steps(response: AnalyzeResponseV2, saved: bool) -> list[RunStepV2]:
    analysis_status = "failed" if response.error and not response.chains else "completed"
    brief_status = "completed" if response.markdown_brief or response.analysis_brief else "skipped"
    return [
        _run_step("queued", "Run accepted", "completed", "Local run record was created."),
        _run_step(
            "analysis",
            "Analysis pipeline",
            analysis_status,
            response.error or f"{len(response.chains)} causal chain(s) returned.",
        ),
        _run_step(
            "brief",
            "Reviewable brief",
            brief_status,
            "Markdown/readable brief available." if brief_status == "completed" else "No brief output.",
        ),
        _run_step(
            "saved",
            "Saved run",
            "completed" if saved else "failed",
            "Run payload persisted locally." if saved else "Run payload was not saved.",
        ),
    ]


def _quota_owner_for_source(item: RetrievalTraceItemV2) -> str:
    if item.cache_hit or item.status == "cached":
        return "cache_reuse"
    if item.source.startswith("uploaded") or item.source_kind == "uploaded":
        return "user_owned"
    return "source_specific"


def _build_usage_ledger(
    response: AnalyzeResponseV2,
    request: AnalyzeRequest,
) -> list[UsageLedgerItemV2]:
    provider_cfg, model_name = _resolve_provider_model(request.model, request.explicit_model)
    provider_label = provider_cfg.get("label", request.model) if provider_cfg else request.model
    ledger = [
        UsageLedgerItemV2(
            category="model_provider",
            name=model_name,
            quota_owner="user_owned" if request.api_key else "local_demo",
            status=response.analysis_mode,
            count=len(response.chains),
            detail=provider_label,
        )
    ]
    ledger.extend(
        UsageLedgerItemV2(
            category="retrieval_source",
            name=item.source_label or item.source,
            quota_owner=_quota_owner_for_source(item),
            status=item.status,
            count=item.result_count,
            detail=item.cache_policy,
        )
        for item in response.retrieval_trace
    )
    uploaded_count = sum(1 for item in response.evidences if item.source_tier == "uploaded")
    if uploaded_count:
        ledger.append(
            UsageLedgerItemV2(
                category="uploaded_evidence",
                name="Uploaded evidence library",
                quota_owner="user_owned",
                status="attached",
                count=uploaded_count,
                detail="User-provided evidence is stored locally.",
            )
        )
    return ledger


def _persist_saved_run(response: AnalyzeResponseV2) -> bool:
    if not response.run_id:
        return False
    records = _load_saved_run_records()
    records = [record for record in records if record.get("run_id") != response.run_id]
    scenario_key = response.scenario.key if response.scenario else "general"
    created_at = _utc_now_iso()
    records.insert(
        0,
        {
            "run_id": response.run_id,
            "query": response.query,
            "run_status": response.run_status,
            "analysis_mode": response.analysis_mode,
            "created_at": created_at,
            "scenario_key": scenario_key,
            "response": response.model_dump(mode="json"),
        },
    )
    _save_saved_run_records(records[:50])
    return True


def _finalize_run_response(
    response: AnalyzeResponseV2,
    request: AnalyzeRequest,
    run_id: str,
) -> AnalyzeResponseV2:
    response.run_id = run_id
    response.run_status = "failed" if response.error and not response.chains else "completed"
    response.usage_ledger = _build_usage_ledger(response, request)
    saved = _persist_saved_run(response)
    response.run_steps = _build_run_steps(response, saved=saved)
    if saved:
        # Persist once more so the saved payload includes the completed saved step.
        _persist_saved_run(response)
    return response


def _empty_live_failure_response(
    query: str,
    error_msg: str,
    scenario_override: Optional[str] = None,
) -> AnalyzeResponseV2:
    from retrocause.parser import parse_input

    parsed_query = parse_input(query)
    response = AnalyzeResponseV2(
        query=query,
        is_demo=False,
        demo_topic=None,
        analysis_mode="partial_live",
        freshness_status="unknown",
        time_range=parsed_query.time_range,
        partial_live_reasons=[error_msg],
        recommended_chain_id=None,
        chains=[],
        evidences=[],
        upstream_map=UpstreamMapV2(entries=[]),
        evaluation=None,
        retrieval_trace=[],
        uncertainty_report=None,
        error=error_msg,
    )
    scenario = _detect_production_scenario(
        query,
        domain="general",
        override=scenario_override,
    )
    response.scenario = scenario
    response.production_brief = _build_production_brief(response, scenario)
    response.production_harness = _build_production_harness(response)
    response.markdown_brief = _build_markdown_research_brief(response)
    response.product_harness = _build_product_harness(response)
    return response


def _classify_node_type(name: str, upstream_ids: List[str], downstream_ids: List[str]) -> str:
    if not upstream_ids:
        return "cause"
    if not downstream_ids:
        return "effect"
    return "mediator"


def _build_upstream_map(nodes_v2: List[GraphNodeV2]) -> UpstreamMapV2:
    return UpstreamMapV2(
        entries=[
            UpstreamMapEntryV2(
                node_id=n.id,
                node_label=n.label,
                upstream_node_ids=n.upstream_ids,
            )
            for n in nodes_v2
        ]
    )


def _refutation_status(
    refuting_ids: set[str] | list[str],
    evidence_pool: list | None = None,
    check_status: str | None = None,
) -> str:
    if refuting_ids:
        return "has_refutation"
    if check_status:
        return check_status
    if not evidence_pool:
        return "not_checked"
    for evidence in evidence_pool:
        basis = getattr(evidence, "stance_basis", "legacy_or_manual")
        if basis not in {"legacy_or_manual", ""}:
            return "no_refutation_in_retrieved_evidence"
    return "not_checked"


def _collect_evidence_bindings(
    chains: List[HypothesisChainV2],
    evidence_pool: list | None = None,
) -> List[EvidenceBindingV2]:
    from retrocause.app.demo_data import DEMO_EVIDENCES

    seen_ids: set[str] = set()
    bindings: List[EvidenceBindingV2] = []
    effective_pool = evidence_pool or DEMO_EVIDENCES
    demo_by_id = {ev.id: ev for ev in effective_pool}

    for chain in chains:
        for eid in chain.supporting_evidence_ids + chain.refuting_evidence_ids:
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            demo_ev = demo_by_id.get(eid)
            if demo_ev is not None:
                bindings.append(
                    EvidenceBindingV2(
                        id=eid,
                        content=demo_ev.content,
                        source=str(demo_ev.source_type),
                        reliability=f"{demo_ev.posterior_reliability:.2f}",
                        is_supporting=eid in chain.supporting_evidence_ids,
                        source_tier=getattr(demo_ev, "source_tier", "base"),
                        freshness=getattr(demo_ev, "freshness", "unknown"),
                        timestamp=getattr(demo_ev, "timestamp", None),
                        extraction_method=getattr(demo_ev, "extraction_method", "manual"),
                        stance="refuting"
                        if eid in chain.refuting_evidence_ids
                        else getattr(demo_ev, "stance", "supporting"),
                        stance_basis=getattr(demo_ev, "stance_basis", "legacy_or_manual"),
                    )
                )
            else:
                bindings.append(
                    EvidenceBindingV2(
                        id=eid,
                        content=f"Evidence {eid}",
                        source="unknown",
                        reliability="0.50",
                        is_supporting=eid in chain.supporting_evidence_ids,
                        source_tier="base",
                        freshness="unknown",
                        timestamp=None,
                        extraction_method="manual",
                        stance="refuting" if eid in chain.refuting_evidence_ids else "supporting",
                        stance_basis="edge_binding",
                    )
                )
    return bindings


def _challenge_check_v2(item: dict) -> ChallengeCheckV2:
    return ChallengeCheckV2(
        edge_id=str(item.get("edge_id", "")),
        source=str(item.get("source", "")),
        target=str(item.get("target", "")),
        query=str(item.get("query", "")),
        result_count=int(item.get("result_count", 0)),
        refuting_count=int(item.get("refuting_count", 0)),
        context_count=int(item.get("context_count", 0)),
        status=str(item.get("status", "not_checked")),
    )


def _humanize_identifier(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    if not text:
        return ""
    return text[:1].upper() + text[1:]


def _format_source_label(value: object) -> str:
    raw = str(value or "").strip()
    if raw.startswith("EvidenceType."):
        raw = raw.split(".", 1)[1]
    labels = {
        "NEWS": "News",
        "PAPER": "Paper",
        "OFFICIAL": "Official",
        "WEB": "Web",
        "OTHER": "Other",
    }
    return labels.get(raw.upper(), _humanize_identifier(raw) or "Unknown")


def _edge_challenge_phrase(edge: GraphEdgeV2) -> str:
    refuting_count = len(edge.refuting_evidence_ids)
    if refuting_count:
        return f"Challenge evidence on this edge: {refuting_count}"
    if edge.refutation_status in {
        "checked_no_refuting_claims",
        "no_refutation_in_retrieved_evidence",
    }:
        return "No challenge evidence attached to this edge after targeted retrieval"
    if edge.refutation_status == "checked_no_results":
        return "Challenge retrieval checked this edge but returned no source results"
    if edge.refutation_status == "not_checked":
        return "Challenge retrieval has not checked this edge"
    return "No challenge evidence attached to this edge"


def _challenge_check_phrase(refuting_count: int) -> str:
    if refuting_count:
        return f"challenge evidence found: {refuting_count}"
    return "no challenge evidence found"


def _trace_value(item: object, key: str, default: object = None) -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    if key == "source":
        return getattr(item, "source", getattr(item, "name", default))
    return getattr(item, key, default)


def _coerce_optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_result_count(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _retrieval_status_from_trace(item: object) -> str:
    explicit = str(_trace_value(item, "status", "") or "").strip()
    if explicit:
        return explicit
    if bool(_trace_value(item, "cache_hit", False)):
        return "cached"
    if _trace_value(item, "error"):
        return "source_error"
    return "ok"


def _retrieval_trace_item_v2(item: object) -> RetrievalTraceItemV2:
    source = str(_trace_value(item, "source", "") or "")
    source_metadata = describe_source_name(source)
    return RetrievalTraceItemV2(
        source=source,
        source_label=str(
            _trace_value(item, "source_label", "")
            or source_metadata.get("source_label", "")
        ),
        source_kind=str(
            _trace_value(item, "source_kind", "")
            or source_metadata.get("source_kind", "unknown")
        ),
        stability=str(
            _trace_value(item, "stability", "")
            or source_metadata.get("stability", "unknown")
        ),
        cache_policy=str(
            _trace_value(item, "cache_policy", "")
            or source_metadata.get("cache_policy", "no_cache_policy")
        ),
        query=str(_trace_value(item, "query", "") or ""),
        result_count=_coerce_result_count(_trace_value(item, "result_count", 0)),
        cache_hit=bool(_trace_value(item, "cache_hit", False)),
        error=_trace_value(item, "error"),
        status=_retrieval_status_from_trace(item),
        retry_after_seconds=_coerce_optional_int(
            _trace_value(item, "retry_after_seconds", None)
        ),
    )


def _source_trace_status_label(status: str) -> str:
    labels = {
        "ok": "ok",
        "cached": "cached",
        "source_limited": "source-limited",
        "rate_limited": "rate-limited",
        "forbidden": "forbidden",
        "timeout": "timeout",
        "source_error": "source-error",
    }
    return labels.get(status, status.replace("_", "-") if status else "unknown")


def _build_analysis_brief(
    result: AnalysisResult,
    chains: List[HypothesisChainV2],
    checks: List[ChallengeCheckV2],
) -> AnalysisBriefV2:
    if not chains:
        return AnalysisBriefV2(
            answer="No usable causal chain was produced for this run.",
            confidence=0.0,
            top_reasons=[],
            challenge_summary="Challenge retrieval could not run without a causal chain.",
            missing_evidence=["A usable causal graph is needed before evidence can be challenged."],
            source_coverage="No chain-level evidence coverage.",
        )

    top_chain = max(chains, key=lambda chain: chain.probability)
    top_reasons: List[str] = []
    evidence_by_id = {ev.id: ev for ev in result.evidences}
    for edge in top_chain.edges[:3]:
        excerpt = ""
        if edge.supporting_evidence_ids:
            evidence = evidence_by_id.get(edge.supporting_evidence_ids[0])
            if evidence is not None:
                excerpt = f" Evidence: {evidence.content[:120]}"
        top_reasons.append(
            f"{_humanize_identifier(edge.source)} -> {_humanize_identifier(edge.target)} "
            f"({edge.strength:.0%} edge strength, "
            f"{len(edge.supporting_evidence_ids)} supporting evidence item(s), "
            f"{_edge_challenge_phrase(edge)}).{excerpt}"
        )

    refuting_total = sum(check.refuting_count for check in checks)
    checked_total = len(checks)
    if refuting_total:
        challenge_summary = f"Found {refuting_total} challenge evidence item(s) across {checked_total} checked edge(s)."
    elif checked_total:
        challenge_summary = f"Checked {checked_total} key edge(s) and found no explicit refuting claim in retrieved evidence."
    else:
        challenge_summary = "Challenge retrieval has not checked this result yet."

    missing: List[str] = []
    if not checks:
        missing.append("Targeted challenge retrieval did not run for this result.")
    if any(edge.refutation_status == "checked_no_results" for edge in top_chain.edges):
        missing.append("At least one challenge query returned no source results.")
    if any(not edge.supporting_evidence_ids for edge in top_chain.edges):
        missing.append("At least one causal edge still lacks direct supporting evidence.")
    source_values = {str(ev.source_type) for ev in result.evidences}
    high_quality_count = sum(
        1
        for ev in result.evidences
        if getattr(ev, "extraction_method", "")
        in {
            "llm_fulltext_trusted",
            "llm_fulltext",
            "llm_trusted",
            "store_cache",
            "uploaded_evidence",
        }
    )
    if high_quality_count == 0:
        missing.append("No trusted full-text or cached high-quality evidence is attached.")
    if not missing:
        missing.append("Primary-source confirmation may still be needed for high-stakes use.")

    source_coverage = (
        f"{len(source_values)} source type(s), {high_quality_count} high-quality evidence item(s), "
        f"{len(result.evidences)} total evidence item(s)."
    )
    trace_statuses = [
        _retrieval_status_from_trace(item)
        for item in getattr(result, "retrieval_trace", [])
    ]
    degraded_count = sum(
        status
        in {
            "source_limited",
            "rate_limited",
            "forbidden",
            "timeout",
            "source_error",
        }
        for status in trace_statuses
    )
    if trace_statuses:
        source_coverage += (
            f" Retrieval trace: {len(trace_statuses)} source attempt(s), "
            f"{degraded_count} degraded or limited."
        )

    return AnalysisBriefV2(
        answer=(
            f"Most likely explanation: {top_chain.label} "
            f"({top_chain.probability:.0%} confidence signal)."
        ),
        confidence=top_chain.probability,
        top_reasons=top_reasons,
        challenge_summary=challenge_summary,
        missing_evidence=missing[:4],
        source_coverage=source_coverage,
    )


def _markdown_bullet(text: str) -> str:
    normalized = " ".join(str(text).split())
    return f"- {normalized}" if normalized else "- "


def _build_markdown_research_brief(response: AnalyzeResponseV2) -> str:
    title = (
        response.production_brief.title
        if response.production_brief
        else "RetroCause Research Brief"
    )
    lines: list[str] = [
        f"# {title}",
        "",
        "## Question",
        response.query or "(empty query)",
        "",
        "## Run Status",
        _markdown_bullet(f"Mode: {response.analysis_mode}"),
        _markdown_bullet(f"Freshness: {response.freshness_status}"),
    ]
    if response.time_range:
        lines.append(_markdown_bullet(f"Time range: {response.time_range}"))
    if response.partial_live_reasons:
        lines.append(_markdown_bullet(f"Limits: {'; '.join(response.partial_live_reasons)}"))

    brief = response.analysis_brief
    lines.extend(["", "## Likely Explanation"])
    if brief:
        lines.append(brief.answer)
        lines.append(_markdown_bullet(f"Confidence signal: {brief.confidence:.0%}"))
    else:
        lines.append("No analysis brief was produced for this run.")

    lines.extend(["", "## Top Reasons"])
    if brief and brief.top_reasons:
        lines.extend(_markdown_bullet(reason) for reason in brief.top_reasons)
    else:
        lines.append("- No reason list is available.")

    if response.production_brief:
        lines.extend(["", "## Production Brief", "", response.production_brief.executive_summary])
        for section in response.production_brief.sections:
            lines.extend(["", f"### {section.title}"])
            for item in section.items:
                evidence_note = (
                    ", ".join(item.evidence_ids)
                    if item.evidence_ids
                    else "verification needed"
                )
                lines.append(_markdown_bullet(f"{item.summary} Evidence: {evidence_note}."))

        lines.extend(["", "## Next Verification Steps"])
        if response.production_brief.next_verification_steps:
            lines.extend(
                _markdown_bullet(step)
                for step in response.production_brief.next_verification_steps
            )
        else:
            lines.append("- No production verification steps were generated.")

        lines.extend(["", "## Production Limits"])
        if response.production_brief.limits:
            lines.extend(_markdown_bullet(limit) for limit in response.production_brief.limits)
        else:
            lines.append("- No additional production limits were generated.")

    lines.extend(["", "## Challenge Coverage"])
    if brief and brief.challenge_summary:
        lines.append(_markdown_bullet(brief.challenge_summary))
    if response.challenge_checks:
        for check in response.challenge_checks[:5]:
            lines.append(
                _markdown_bullet(
                    f"{_humanize_identifier(check.source)} -> "
                    f"{_humanize_identifier(check.target)}: "
                    f"{check.status}, {_challenge_check_phrase(check.refuting_count)}, "
                    f"{check.context_count} context, {check.result_count} retrieved"
                )
            )
    elif not brief or not brief.challenge_summary:
        lines.append("- Challenge retrieval was not checked.")

    lines.extend(["", "## Gaps And Caveats"])
    if brief and brief.missing_evidence:
        lines.extend(_markdown_bullet(item) for item in brief.missing_evidence)
    else:
        lines.append("- No explicit gap list was produced.")

    lines.extend(["", "## Evidence"])
    if response.evidences:
        for item in response.evidences[:8]:
            stance = "Challenges" if item.stance == "refuting" or not item.is_supporting else "Supports"
            content = " ".join(item.content.split())
            lines.append(
                _markdown_bullet(
                    f"[{item.id}] {stance}. Source: {_format_source_label(item.source)}. "
                    f"Reliability: {item.reliability}. {content}"
                )
            )
    else:
        lines.append("- No evidence items are attached.")

    lines.extend(["", "## Source Trace"])
    if response.retrieval_trace:
        for item in response.retrieval_trace[:8]:
            label = item.source_label or item.source
            cache_note = "cache hit" if item.cache_hit else "fresh query"
            status_note = f"status: {_source_trace_status_label(item.status)}"
            retry_note = (
                f", retry after {item.retry_after_seconds}s"
                if item.retry_after_seconds is not None
                else ""
            )
            lines.append(
                _markdown_bullet(
                    f"{label}: {item.result_count} result(s), {status_note}{retry_note}, "
                    f"{cache_note}, source kind: {item.source_kind}, "
                    f"stability: {item.stability}, cache policy: {item.cache_policy}. "
                    f"Query: {item.query}"
                )
            )
    else:
        lines.append("- No retrieval trace is attached.")

    lines.extend(
        [
            "",
            "## Use Note",
            "This brief is evidence-grounded product output, not verified causal truth. Review source quality, challenge coverage, and missing evidence before relying on it.",
        ]
    )
    return "\n".join(lines)


def _brief_item_from_edge(edge: GraphEdgeV2) -> ProductionBriefItemV2:
    evidence_ids = list(dict.fromkeys(edge.supporting_evidence_ids))
    summary = (
        f"{_humanize_identifier(edge.source)} -> {_humanize_identifier(edge.target)} "
        f"with {edge.strength:.0%} edge strength and {len(evidence_ids)} supporting "
        "evidence item(s)."
    )
    return ProductionBriefItemV2(
        title=f"{_humanize_identifier(edge.source)} -> {_humanize_identifier(edge.target)}",
        summary=summary,
        evidence_ids=evidence_ids,
        confidence=max(0.0, min(1.0, edge.strength)),
    )


def _top_edge_items(response: AnalyzeResponseV2) -> List[ProductionBriefItemV2]:
    if not response.chains:
        return []
    top_chain = max(response.chains, key=lambda chain: chain.probability)
    items = [
        _brief_item_from_edge(edge)
        for edge in top_chain.edges
        if edge.supporting_evidence_ids
    ]
    return sorted(items, key=lambda item: item.confidence, reverse=True)


def _verification_items(
    response: AnalyzeResponseV2,
    scenario: ScenarioV2,
) -> List[ProductionBriefItemV2]:
    items: list[ProductionBriefItemV2] = []
    if response.challenge_checks:
        checked = len(response.challenge_checks)
        refuting = sum(check.refuting_count for check in response.challenge_checks)
        challenge_summary = (
            f"{refuting} challenge evidence item(s) were attached in this run."
            if refuting
            else "no explicit challenge evidence was attached in this run."
        )
        items.append(
            ProductionBriefItemV2(
                title="Challenge coverage",
                summary=(
                    f"Review {checked} checked edge(s); {challenge_summary}"
                ),
                confidence=1.0 if checked else 0.0,
            )
        )
    else:
        items.append(
            ProductionBriefItemV2(
                title="Challenge coverage",
                summary="Run or inspect targeted challenge retrieval before treating this as settled.",
                confidence=0.25,
            )
        )

    if scenario.key == "market":
        items.append(
            ProductionBriefItemV2(
                title="Market freshness",
                summary="Check whether the freshest retrieved sources cover the relevant market window.",
                confidence=0.5,
            )
        )
    elif scenario.key == "policy_geopolitics":
        items.append(
            ProductionBriefItemV2(
                title="Source reliability",
                summary="Compare official, wire, and regional-source evidence before relying on the brief.",
                confidence=0.5,
            )
        )
    elif scenario.key == "postmortem":
        items.append(
            ProductionBriefItemV2(
                title="Internal evidence",
                summary="Attach logs, tickets, metrics, or customer evidence before assigning action owners.",
                confidence=0.5,
            )
        )
    else:
        items.append(
            ProductionBriefItemV2(
                title="Evidence depth",
                summary="Inspect evidence coverage and missing evidence before relying on the conclusion.",
                confidence=0.5,
            )
        )
    return items


def _production_executive_summary(
    response: AnalyzeResponseV2,
    scenario: ScenarioV2,
    items: List[ProductionBriefItemV2],
) -> str:
    if items:
        top_item = items[0]
        return (
            f"{scenario.label}: the strongest evidence-anchored driver is "
            f"{top_item.title} ({top_item.confidence:.0%} confidence signal)."
        )
    if response.analysis_brief and response.analysis_brief.answer:
        return f"{scenario.label}: {response.analysis_brief.answer}"
    return f"{scenario.label}: no evidence-anchored production driver is available yet."


def _build_production_brief(
    response: AnalyzeResponseV2,
    scenario: ScenarioV2,
) -> ProductionBriefV2:
    items = _top_edge_items(response)
    section_titles = {
        "market": ["Market Drivers", "What Would Change The View"],
        "policy_geopolitics": ["Negotiation Constraints", "Source And Policy Risks"],
        "postmortem": ["Operational Causes", "Evidence Needed Before Action"],
        "general": ["Top Causes", "What To Check Next"],
    }
    primary_title, secondary_title = section_titles.get(scenario.key, section_titles["general"])
    verification_items = _verification_items(response, scenario)
    limits: list[str] = []
    if not items:
        limits.append("No evidence-anchored causal drivers were available in this run.")
    elif response.analysis_brief:
        limits.extend(response.analysis_brief.missing_evidence[:3])

    return ProductionBriefV2(
        title=scenario.label,
        scenario_key=scenario.key,
        executive_summary=_production_executive_summary(response, scenario, items),
        sections=[
            ProductionBriefSectionV2(kind="drivers", title=primary_title, items=items[:5]),
            ProductionBriefSectionV2(
                kind="verification",
                title=secondary_title,
                items=verification_items,
            ),
        ],
        limits=limits,
        next_verification_steps=[item.summary for item in verification_items],
    )


def _production_check(
    name: str,
    passed: bool,
    severity: str,
    message: str,
) -> ProductionHarnessCheckV2:
    return ProductionHarnessCheckV2(
        name=name,
        passed=passed,
        severity=severity,
        message=message,
    )


def _check_freshness_gate(response: AnalyzeResponseV2) -> ProductionHarnessCheckV2:
    scenario_key = response.scenario.key if response.scenario else "general"
    needs_freshness = (
        scenario_key in {"market", "policy_geopolitics"}
        and response.time_range in {"today", "yesterday", "this_week", "this month"}
    )
    if not needs_freshness:
        return _production_check(
            "freshness_gate",
            True,
            "info",
            "This scenario/query does not require a strict latest-information gate.",
        )
    fresh_enough = response.freshness_status in {"fresh", "recent"}
    return _production_check(
        "freshness_gate",
        fresh_enough,
        "warning",
        "Latest-information query has fresh/recent evidence."
        if fresh_enough
        else "Latest-information query needs fresh evidence before the brief is ready.",
    )


def _check_evidence_anchor_gate(response: AnalyzeResponseV2) -> ProductionHarnessCheckV2:
    anchored_items = [
        item
        for section in (response.production_brief.sections if response.production_brief else [])
        for item in section.items
        if section.kind not in {"limits", "verification"} and item.evidence_ids
    ]
    return _production_check(
        "evidence_anchor",
        bool(anchored_items),
        "blocker",
        "Production claims include evidence IDs."
        if anchored_items
        else "No evidence-anchored production claim is available.",
    )


def _check_source_risk_gate(response: AnalyzeResponseV2) -> ProductionHarnessCheckV2:
    scenario_key = response.scenario.key if response.scenario else "general"
    if scenario_key not in {"market", "policy_geopolitics"}:
        return _production_check(
            "source_risk",
            True,
            "info",
            "No policy/market source-risk gate is required for this scenario.",
        )
    if not response.retrieval_trace:
        return _production_check(
            "source_risk",
            False,
            "warning",
            "No source trace is attached, so source quality cannot be inspected.",
        )
    stable_rows = [
        item
        for item in response.retrieval_trace
        if item.stability in {"high", "medium"} and not item.error and item.result_count > 0
    ]
    passed = bool(stable_rows)
    return _production_check(
        "source_risk",
        passed,
        "warning",
        "At least one stable source returned evidence."
        if passed
        else "Only weak or empty source traces are attached.",
    )


def _check_challenge_gate(response: AnalyzeResponseV2) -> ProductionHarnessCheckV2:
    passed = bool(response.challenge_checks)
    return _production_check(
        "challenge_coverage",
        passed,
        "warning",
        f"{len(response.challenge_checks)} challenge check(s) are attached."
        if passed
        else "No targeted challenge checks are attached.",
    )


def _check_internal_evidence_gate(response: AnalyzeResponseV2) -> ProductionHarnessCheckV2:
    scenario_key = response.scenario.key if response.scenario else "general"
    if scenario_key != "postmortem":
        return _production_check(
            "internal_evidence",
            True,
            "info",
            "Internal operational evidence is not required for this scenario.",
        )
    internal_markers = ("log", "ticket", "metric", "customer", "incident", "internal")
    has_internal = any(
        any(marker in f"{item.source} {item.extraction_method} {item.content}".lower() for marker in internal_markers)
        for item in response.evidences
    )
    return _production_check(
        "internal_evidence",
        has_internal,
        "warning",
        "Internal postmortem evidence is attached."
        if has_internal
        else "Postmortem brief needs logs, tickets, metrics, or customer/internal evidence.",
    )


def _build_production_harness(response: AnalyzeResponseV2) -> ProductionHarnessReportV2:
    checks = [
        _check_freshness_gate(response),
        _check_evidence_anchor_gate(response),
        _check_source_risk_gate(response),
        _check_challenge_gate(response),
        _check_internal_evidence_gate(response),
    ]
    if any(check.severity == "blocker" and not check.passed for check in checks):
        status = "blocked"
    elif any(check.name == "internal_evidence" and not check.passed for check in checks):
        status = "not_actionable"
    elif any(check.severity == "warning" and not check.passed for check in checks):
        status = "needs_more_evidence"
    else:
        status = "ready_for_brief"

    score = sum(1 for check in checks if check.passed) / max(1, len(checks))
    next_actions = [check.message for check in checks if not check.passed]
    if not next_actions:
        next_actions.append("Review cited evidence and challenge coverage before relying on the brief.")

    return ProductionHarnessReportV2(
        status=status,
        score=max(0.0, min(1.0, score)),
        scenario_key=response.scenario.key if response.scenario else "general",
        checks=checks,
        next_actions=next_actions[:4],
    )


def _build_product_harness(response: AnalyzeResponseV2) -> ProductHarnessReportV2:
    """Score whether a result gives the user reviewable causal value."""

    checks: list[HarnessCheckV2] = []

    has_actionable_failure = bool(
        response.error or response.partial_live_reasons or response.analysis_mode == "demo"
    )
    if response.chains:
        checks.append(
            _harness_check(
                "causal_chain",
                "Causal chain present",
                "pass",
                f"{len(response.chains)} chain(s), {sum(len(c.edges) for c in response.chains)} edge(s).",
            )
        )
    else:
        checks.append(
            _harness_check(
                "causal_chain",
                "Causal chain present",
                "fail",
                "No causal chain is available for review.",
            )
        )

    if response.analysis_brief and (
        response.analysis_brief.answer or response.analysis_brief.top_reasons
    ):
        checks.append(
            _harness_check(
                "analysis_summary",
                "Analysis summary present",
                "pass",
                "The response includes a synthesized answer and reason list.",
            )
        )
    else:
        checks.append(
            _harness_check(
                "analysis_summary",
                "Analysis summary present",
                "fail",
                "No synthesized answer is attached.",
            )
        )

    if response.retrieval_trace:
        source_hits = sum(max(0, item.result_count) for item in response.retrieval_trace)
        status = "pass" if source_hits > 0 else "warn"
        checks.append(
            _harness_check(
                "source_trace",
                "Source trace visible",
                status,
                f"{len(response.retrieval_trace)} source query row(s), {source_hits} result hit(s).",
            )
        )
    else:
        checks.append(
            _harness_check(
                "source_trace",
                "Source trace visible",
                "fail",
                "No source-level retrieval trace is visible.",
            )
        )

    if response.evidences:
        stances = {item.stance or ("supporting" if item.is_supporting else "refuting") for item in response.evidences}
        checks.append(
            _harness_check(
                "evidence_stance",
                "Evidence stance visible",
                "pass",
                f"{len(response.evidences)} evidence item(s), stance(s): {', '.join(sorted(stances))}.",
            )
        )
    else:
        checks.append(
            _harness_check(
                "evidence_stance",
                "Evidence stance visible",
                "fail",
                "No evidence items are attached.",
            )
        )

    if response.challenge_checks:
        checked = len(response.challenge_checks)
        refuting = sum(item.refuting_count for item in response.challenge_checks)
        checks.append(
            _harness_check(
                "challenge_coverage",
                "Challenge coverage checked",
                "pass",
                f"{checked} edge(s) checked, {refuting} challenge item(s).",
            )
        )
    else:
        checks.append(
            _harness_check(
                "challenge_coverage",
                "Challenge coverage checked",
                "warn" if response.chains else "fail",
                "No targeted challenge retrieval is attached.",
            )
        )

    if has_actionable_failure:
        checks.append(
            _harness_check(
                "actionable_failure",
                "Failure state actionable",
                "pass",
                response.error or "; ".join(response.partial_live_reasons) or response.analysis_mode,
            )
        )
    elif response.analysis_mode == "live":
        checks.append(
            _harness_check(
                "actionable_failure",
                "Failure state actionable",
                "pass",
                "No failure state is present.",
            )
        )
    else:
        checks.append(
            _harness_check(
                "actionable_failure",
                "Failure state actionable",
                "warn",
                "The run is degraded but has no explicit reason.",
            )
        )

    score_map = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    score = sum(score_map.get(check.status, 0.0) for check in checks) / max(1, len(checks))
    score = max(0.0, min(1.0, score))

    next_actions: list[str] = []
    if not response.chains and response.error:
        status = "blocked_by_model"
        summary = "The run did not produce a causal answer; the useful output is the failure diagnosis."
        next_actions.append("Run provider preflight before starting another full analysis.")
    elif score >= 0.75 and response.chains:
        status = "ready_for_review"
        summary = "The result has enough structure for a user to review reasons, sources, and gaps."
    elif response.chains:
        status = "needs_more_evidence"
        summary = "The result has a causal shape, but evidence or challenge coverage is still thin."
    else:
        status = "not_reviewable"
        summary = "The result is not yet reviewable as a causal explanation."

    if not response.retrieval_trace:
        next_actions.append("Expose source trace rows so the user can see where evidence came from.")
    if not response.challenge_checks:
        next_actions.append("Run targeted challenge retrieval for the strongest causal edges.")
    if not response.analysis_brief:
        next_actions.append("Generate an analysis brief with top reasons and missing evidence.")
    if not response.evidences:
        next_actions.append("Collect or attach evidence before presenting causal conclusions.")
    if not next_actions:
        next_actions.append("Review the top reasons and inspect the cited evidence before trusting the conclusion.")

    return ProductHarnessReportV2(
        score=score,
        status=status,
        user_value_summary=summary,
        checks=checks,
        next_actions=next_actions[:4],
    )


def _result_to_v2(
    result: AnalysisResult,
    *,
    is_demo: bool = False,
    demo_topic: Optional[str] = None,
    scenario_override: Optional[str] = None,
) -> AnalyzeResponseV2:
    from retrocause.parser import parse_input

    parsed_query = parse_input(result.query)
    evaluation_v2: Optional[PipelineEvaluationV2] = None
    if result.evaluation is not None:
        evaluation_v2 = PipelineEvaluationV2(
            evidence_sufficiency=result.evaluation.evidence_sufficiency,
            probability_coherence=result.evaluation.probability_coherence,
            chain_diversity=result.evaluation.chain_diversity,
            overall_confidence=result.evaluation.overall_confidence,
            weaknesses=result.evaluation.weaknesses,
            recommended_actions=result.evaluation.recommended_actions,
        )
    all_edges_by_chain: dict[str, list[tuple[str, str]]] = {}
    for hyp in result.hypotheses:
        all_edges_by_chain[hyp.id] = [(e.source, e.target) for e in hyp.edges]

    chains_v2: List[HypothesisChainV2] = []
    check_status_by_edge = {
        str(item.get("edge_id", "")): str(item.get("status", "not_checked"))
        for item in getattr(result, "refutation_checks", [])
    }

    for hyp in result.hypotheses:
        var_names_in_order = [v.name for v in hyp.variables]
        depth_map = {name: idx for idx, name in enumerate(var_names_in_order)}

        upstream_map: dict[str, list[str]] = {name: [] for name in var_names_in_order}
        downstream_map: dict[str, list[str]] = {name: [] for name in var_names_in_order}
        for src, tgt in all_edges_by_chain.get(hyp.id, []):
            if src in upstream_map and tgt in upstream_map:
                upstream_map[tgt].append(src)
                downstream_map[src].append(tgt)

        nodes_v2: List[GraphNodeV2] = []
        for var in hyp.variables:
            ups = upstream_map.get(var.name, [])
            downs = downstream_map.get(var.name, [])
            node_type = _classify_node_type(var.name, ups, downs)
            supp_ev: set[str] = set()
            ref_ev: set[str] = set()
            for edge in hyp.edges:
                if edge.source == var.name or edge.target == var.name:
                    supp_ev.update(edge.supporting_evidence_ids)
                    ref_ev.update(edge.refuting_evidence_ids)
            supp_ev.update(var.evidence_ids)

            node_uncertainty = None
            if var.uncertainty:
                node_uncertainty = UncertaintyAssessmentV2(
                    uncertainty_types=[t.value for t in var.uncertainty.uncertainty_types],
                    overall_score=var.uncertainty.overall_score,
                    data_uncertainty=var.uncertainty.data_uncertainty,
                    model_uncertainty=var.uncertainty.model_uncertainty,
                    explanation=var.uncertainty.explanation,
                )

            nodes_v2.append(
                GraphNodeV2(
                    id=var.name,
                    label=var.name.replace("_", " ").title(),
                    description=var.description,
                    probability=var.posterior_support,
                    type=node_type,
                    depth=depth_map.get(var.name, 0),
                    upstream_ids=ups,
                    supporting_evidence_ids=sorted(supp_ev),
                    refuting_evidence_ids=sorted(ref_ev),
                    uncertainty=node_uncertainty,
                )
            )

        edges_v2: List[GraphEdgeV2] = []
        for edge in hyp.edges:
            spans_v2 = [
                CitationSpanV2(
                    evidence_id=cs.evidence_id,
                    start_char=cs.start_char,
                    end_char=cs.end_char,
                    quoted_text=cs.quoted_text,
                    relevance_score=cs.relevance_score,
                )
                for cs in edge.citation_spans
            ]
            edges_v2.append(
                GraphEdgeV2(
                    id=f"{edge.source}_{edge.target}",
                    source=edge.source,
                    target=edge.target,
                    strength=edge.conditional_prob,
                    type="causes",
                    supporting_evidence_ids=edge.supporting_evidence_ids,
                    refuting_evidence_ids=edge.refuting_evidence_ids,
                    citation_spans=spans_v2,
                    evidence_conflict=edge.evidence_conflict.value,
                    refutation_status=_refutation_status(
                        edge.refuting_evidence_ids,
                        result.evidences,
                        check_status_by_edge.get(f"{edge.source}->{edge.target}"),
                    ),
                )
            )

        chain_supp: set[str] = set()
        chain_ref: set[str] = set()
        for edge in hyp.edges:
            chain_supp.update(edge.supporting_evidence_ids)
            chain_ref.update(edge.refuting_evidence_ids)
        for var in hyp.variables:
            chain_supp.update(var.evidence_ids)

        cf_items: List[CounterfactualItemV2] = []
        for cf in hyp.counterfactual_results:
            cf_items.append(
                CounterfactualItemV2(
                    intervention=f"Remove {cf.intervention_var}",
                    original_outcome=f"P(chain) = {cf.original_path_prob:.2f}",
                    counterfactual_outcome=f"P(chain) = {cf.intervened_path_prob:.2f}",
                    strength=cf.counterfactual_score,
                )
            )
        cf_summary = CounterfactualSummaryV2(
            items=cf_items,
            overall_confidence=hyp.counterfactual_score,
        )

        max_depth = max(depth_map.values()) if depth_map else 0

        chains_v2.append(
            HypothesisChainV2(
                chain_id=hyp.id,
                label=hyp.name,
                description=hyp.description,
                probability=hyp.posterior_probability,
                nodes=nodes_v2,
                edges=edges_v2,
                supporting_evidence_ids=sorted(chain_supp),
                refuting_evidence_ids=sorted(chain_ref),
                refutation_status=_refutation_status(chain_ref, result.evidences),
                counterfactual=cf_summary,
                depth=max_depth,
            )
        )

    recommended_id: Optional[str] = None
    if chains_v2:
        recommended_id = max(chains_v2, key=lambda c: c.probability).chain_id

    all_nodes_v2: dict[str, GraphNodeV2] = {}
    for c in chains_v2:
        for n in c.nodes:
            if n.id not in all_nodes_v2:
                all_nodes_v2[n.id] = n
            else:
                existing = all_nodes_v2[n.id]
                merged_ups = list(dict.fromkeys(existing.upstream_ids + n.upstream_ids))
                all_nodes_v2[n.id] = GraphNodeV2(
                    id=n.id,
                    label=n.label,
                    description=n.description,
                    probability=n.probability,
                    type=n.type,
                    depth=n.depth,
                    upstream_ids=merged_ups,
                    supporting_evidence_ids=n.supporting_evidence_ids,
                    refuting_evidence_ids=n.refuting_evidence_ids,
                )

    uncertainty_v2: Optional[UncertaintyReportV2] = None
    if result.uncertainty_report:
        ur = result.uncertainty_report
        per_node_v2 = {}
        for k, v in ur.per_node.items():
            per_node_v2[k] = UncertaintyAssessmentV2(
                uncertainty_types=[t.value for t in v.uncertainty_types],
                overall_score=v.overall_score,
                data_uncertainty=v.data_uncertainty,
                model_uncertainty=v.model_uncertainty,
                explanation=v.explanation,
            )
        per_edge_v2 = {}
        for k, v in ur.per_edge.items():
            per_edge_v2[k] = UncertaintyAssessmentV2(
                uncertainty_types=[t.value for t in v.uncertainty_types],
                overall_score=v.overall_score,
                data_uncertainty=v.data_uncertainty,
                model_uncertainty=v.model_uncertainty,
                explanation=v.explanation,
            )
        uncertainty_v2 = UncertaintyReportV2(
            per_node=per_node_v2,
            per_edge=per_edge_v2,
            evidence_conflicts={k: v.value for k, v in ur.evidence_conflicts.items()},
            overall_uncertainty=ur.overall_uncertainty,
            dominant_uncertainty_type=ur.dominant_uncertainty_type.value
            if ur.dominant_uncertainty_type
            else None,
            summary=ur.summary,
        )

    challenge_checks = [
        _challenge_check_v2(item) for item in getattr(result, "refutation_checks", [])
    ]

    response = AnalyzeResponseV2(
        query=result.query,
        is_demo=is_demo,
        demo_topic=demo_topic,
        analysis_mode="demo" if is_demo else result.analysis_mode,
        freshness_status=result.freshness_status,
        time_range=parsed_query.time_range,
        partial_live_reasons=[] if is_demo else _derive_partial_live_reasons(result),
        recommended_chain_id=recommended_id,
        chains=chains_v2,
        evidences=_collect_evidence_bindings(chains_v2, result.evidences),
        upstream_map=_build_upstream_map(list(all_nodes_v2.values())),
        evaluation=evaluation_v2,
        retrieval_trace=[
            _retrieval_trace_item_v2(item)
            for item in getattr(result, "retrieval_trace", [])
        ],
        challenge_checks=challenge_checks,
        analysis_brief=_build_analysis_brief(result, chains_v2, challenge_checks),
        uncertainty_report=uncertainty_v2,
    )
    scenario = _detect_production_scenario(
        result.query,
        domain=result.domain,
        override=scenario_override,
    )
    response.scenario = scenario
    response.production_brief = _build_production_brief(response, scenario)
    response.production_harness = _build_production_harness(response)
    response.markdown_brief = _build_markdown_research_brief(response)
    response.product_harness = _build_product_harness(response)
    return response


@app.get("/")
async def root():
    return {"status": "ok", "message": "RetroCause API is running"}


@app.get("/api/providers")
async def list_providers():
    return {
        "providers": {
            key: {
                "label": cfg["label"],
                "models": {mid: mcfg["label"] for mid, mcfg in cfg["models"].items()},
            }
            for key, cfg in PROVIDERS.items()
        }
    }


@app.get("/api/runs", response_model=SavedRunListResponse)
async def list_saved_runs():
    summaries = [
        SavedRunSummaryV2(
            run_id=str(record.get("run_id", "")),
            query=str(record.get("query", "")),
            run_status=str(record.get("run_status", "unknown")),
            analysis_mode=str(record.get("analysis_mode", "unknown")),
            created_at=str(record.get("created_at", "")),
            scenario_key=str(record.get("scenario_key", "general")),
        )
        for record in _load_saved_run_records()
        if record.get("run_id")
    ]
    return SavedRunListResponse(runs=summaries)


@app.get("/api/runs/{run_id}")
async def get_saved_run(run_id: str):
    for record in _load_saved_run_records():
        if record.get("run_id") == run_id:
            return record
    raise HTTPException(status_code=404, detail="Saved run not found")


@app.post("/api/evidence/upload", response_model=UploadedEvidenceResponse)
async def upload_evidence(request: UploadedEvidenceRequest):
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded evidence content is empty")
    evidence = EvidenceStore().add_uploaded_evidence(
        query=request.query,
        domain=request.domain,
        title=request.title,
        content=content,
        source_name=request.source_name,
        time_scope=request.time_scope,
    )
    return UploadedEvidenceResponse(
        evidence_id=evidence.id,
        stored=True,
        source_tier=evidence.source_tier,
        extraction_method=evidence.extraction_method,
    )


@app.post("/api/providers/preflight", response_model=ProviderPreflightResponse)
async def preflight_provider(request: ProviderPreflightRequest):
    provider_cfg, model_name = _resolve_provider_model(request.model, request.explicit_model)
    checks: list[HarnessCheckV2] = []

    if provider_cfg is None:
        checks.append(
            _harness_check(
                "provider_config",
                "Provider configured",
                "fail",
                f"Provider {request.model!r} is not configured.",
            )
        )
        return ProviderPreflightResponse(
            provider=request.model,
            model_name=model_name,
            status="error",
            can_run_analysis=False,
            failure_code="unknown_provider",
            diagnosis="Provider is not configured in this RetroCause instance.",
            user_action=_preflight_user_action("unknown_provider"),
            checks=checks,
        )

    checks.append(
        _harness_check(
            "provider_config",
            "Provider configured",
            "pass",
            f"{request.model} resolves to {provider_cfg.get('base_url') or 'default OpenAI endpoint'}.",
        )
    )

    if not request.api_key:
        checks.append(
            _harness_check(
                "api_key_present",
                "API key present",
                "fail",
                "No API key was provided.",
            )
        )
        return ProviderPreflightResponse(
            provider=request.model,
            model_name=model_name,
            status="error",
            can_run_analysis=False,
            failure_code="missing_api_key",
            diagnosis="Live analysis needs a provider API key.",
            user_action=_preflight_user_action("missing_api_key"),
            checks=checks,
        )

    checks.append(
        _harness_check("api_key_present", "API key present", "pass", "API key was provided.")
    )

    configured_models = provider_cfg.get("models", {})
    catalog_status = "pass" if model_name in configured_models else "warn"
    catalog_detail = (
        "Model is listed in the configured provider catalog."
        if catalog_status == "pass"
        else "Model is not in the local catalog; preflight will still test provider access."
    )
    checks.append(
        _harness_check("model_catalog", "Model listed locally", catalog_status, catalog_detail)
    )

    try:
        from retrocause.config import RetroCauseConfig
        from retrocause.llm import LLMClient

        cfg = RetroCauseConfig.from_env()
        llm = LLMClient(
            api_key=request.api_key,
            model=model_name,
            base_url=provider_cfg.get("base_url"),
            timeout=min(cfg.request_timeout_seconds, 45),
        )
        ok, error_msg = run_with_timeout(llm.preflight_model_access, 50)
    except TimeoutError:
        ok = False
        error_msg = "Model preflight timed out."
    except Exception as exc:
        ok = False
        error_msg = f"{type(exc).__name__}: {exc}"

    if ok:
        checks.append(
            _harness_check(
                "model_access",
                "Model returns JSON",
                "pass",
                "Provider returned the expected tiny JSON payload.",
            )
        )
        return ProviderPreflightResponse(
            provider=request.model,
            model_name=model_name,
            status="ok",
            can_run_analysis=True,
            failure_code=None,
            diagnosis="Provider, key, and model passed the lightweight JSON preflight.",
            user_action="Run the full analysis.",
            checks=checks,
        )

    failure_code = _preflight_failure_code(error_msg)
    checks.append(
        _harness_check(
            "model_access",
            "Model returns JSON",
            "fail",
            error_msg or "Model preflight failed.",
        )
    )
    return ProviderPreflightResponse(
        provider=request.model,
        model_name=model_name,
        status="error",
        can_run_analysis=False,
        failure_code=failure_code,
        diagnosis=error_msg or "Model preflight failed.",
        user_action=_preflight_user_action(failure_code),
        checks=checks,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_query(request: AnalyzeRequest):
    try:
        from retrocause.parser import parse_input

        is_demo = False
        demo_topic: Optional[str] = None
        result: AnalysisResult | None = None
        parsed_query = parse_input(request.query)

        if request.api_key:
            from retrocause.app.demo_data import run_real_analysis

            provider_cfg = PROVIDERS.get(request.model)
            base_url = provider_cfg["base_url"] if provider_cfg else None
            if request.explicit_model:
                model_name = request.explicit_model
            else:
                model_name = (
                    list(provider_cfg["models"].keys())[0] if provider_cfg else request.model
                )
            try:
                result = run_with_timeout(
                    run_real_analysis, 400, request.query, request.api_key, model_name, base_url
                )
            except Exception:
                import traceback

                traceback.print_exc()
                result = None

            if result is not None:
                is_demo = False
            else:
                result = topic_aware_demo_result(request.query)
                is_demo = True
                demo_topic = detect_demo_topic(request.query) or "default"
        else:
            result = topic_aware_demo_result(request.query)
            is_demo = True
            demo_topic = detect_demo_topic(request.query) or "default"

        result.is_demo = is_demo
        result.demo_topic = demo_topic

        nodes = [
            GraphNode(
                id=var.name,
                title=var.name.replace("_", " ").title(),
                description=var.description,
                probability=int(var.posterior_support * 100),
            )
            for var in result.variables
        ]

        edges = [
            GraphEdge(
                id=f"{edge.source}_{edge.target}",
                source=edge.source,
                target=edge.target,
                label=f"prob: {edge.conditional_prob:.2f}",
            )
            for edge in result.edges
        ]

        from retrocause.app.demo_data import DEMO_EVIDENCES

        evidences = [
            Evidence(
                id=ev.id,
                content=ev.content,
                source=str(ev.source_type),
                reliability=f"{ev.posterior_reliability:.2f}",
            )
            for ev in DEMO_EVIDENCES
        ]

        return AnalyzeResponse(
            query=result.query,
            nodes=nodes,
            edges=edges,
            evidences=evidences,
            is_demo=is_demo,
            demo_topic=demo_topic,
            analysis_mode="demo" if is_demo else result.analysis_mode,
            freshness_status=result.freshness_status,
            time_range=parsed_query.time_range,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/v2", response_model=AnalyzeResponseV2)
async def analyze_query_v2(request: AnalyzeRequest):
    try:
        run_id = _create_run_id()
        is_demo = True
        demo_topic: Optional[str] = None
        result: AnalysisResult | None = None

        if request.api_key:
            from retrocause.app.demo_data import run_real_analysis

            provider_cfg = PROVIDERS.get(request.model)
            base_url = provider_cfg["base_url"] if provider_cfg else None
            if request.explicit_model:
                model_name = request.explicit_model
            else:
                model_name = (
                    list(provider_cfg["models"].keys())[0] if provider_cfg else request.model
                )
            error_msg: str | None = None
            try:
                result = run_with_timeout(
                    run_real_analysis, 400, request.query, request.api_key, model_name, base_url
                )
            except TimeoutError:
                error_msg = "Analysis timed out. Try a simpler query or try again later."
                result = None
            except Exception as exc:
                import traceback

                traceback.print_exc()
                error_msg = f"{type(exc).__name__}: {exc}"
                result = None

            if result is not None and len(result.hypotheses) == 0:
                error_msg = f"LLM calls failed for {model_name} — empty result (check API key balance and model access)"
                result = None

            if result is not None:
                is_demo = False

        if result is None and request.api_key and _is_live_failure(error_msg):
            return _finalize_run_response(
                _empty_live_failure_response(
                    request.query,
                    error_msg or "Live analysis failed.",
                    scenario_override=request.scenario_override,
                ),
                request,
                run_id,
            )

        if result is None:
            result = topic_aware_demo_result(request.query)
            is_demo = True
            demo_topic = detect_demo_topic(request.query) or "default"

        result.is_demo = is_demo
        result.demo_topic = demo_topic

        resp = _result_to_v2(
            result,
            is_demo=is_demo,
            demo_topic=demo_topic,
            scenario_override=request.scenario_override,
        )
        resp.error = error_msg if is_demo and request.api_key else None
        return _finalize_run_response(resp, request, run_id)

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/v2/stream")
async def analyze_query_v2_stream(request: AnalyzeRequest):
    run_id = _create_run_id()

    def generate():
        eq: queue.Queue[dict | None] = queue.Queue()

        def on_progress(step_name: str, step_index: int, total: int, message: str):
            eq.put(
                {
                    "type": "progress",
                    "step": step_name,
                    "step_index": step_index + 1,
                    "total_steps": total,
                    "message": message,
                }
            )

        def worker():
            import time as _time

            _t0 = _time.time()
            try:
                if not request.api_key:
                    eq.put({"type": "error", "error": "No API key provided"})
                    return

                logger.info(
                    f"[SSE-DEBUG] worker started — query={request.query!r}, "
                    f"model={request.model!r}, explicit_model={request.explicit_model!r}, "
                    f"api_key={request.api_key[:8]}..."
                )

                from retrocause.app.demo_data import run_real_analysis_with_progress

                provider_cfg = PROVIDERS.get(request.model)
                base_url = provider_cfg["base_url"] if provider_cfg else None
                model_name = (
                    request.explicit_model
                    if request.explicit_model
                    else (list(provider_cfg["models"].keys())[0] if provider_cfg else request.model)
                )

                logger.info(
                    f"[SSE-DEBUG] resolved model_name={model_name!r}, base_url={base_url!r}"
                )

                result = None
                error_msg = None
                try:
                    result = run_with_timeout(
                        run_real_analysis_with_progress,
                        400,
                        request.query,
                        request.api_key,
                        model_name,
                        base_url,
                        on_progress,
                    )
                    _elapsed = _time.time() - _t0
                    logger.info(
                        f"[SSE-DEBUG] run_with_timeout returned in {_elapsed:.1f}s — "
                        f"result={'None' if result is None else type(result).__name__}"
                    )
                except TimeoutError:
                    error_msg = "Analysis timed out. Try a simpler query or try again later."
                    logger.warning("SSE stream analysis timed out after 400s")
                except Exception as exc:
                    logger.error(f"SSE stream analysis error: {type(exc).__name__}: {exc}")
                    error_msg = f"{type(exc).__name__}: {exc}"

                if result is not None:
                    logger.info(
                        f"[SSE-DEBUG] result has {len(result.hypotheses)} hypotheses, "
                        f"{len(result.variables)} variables, {len(result.edges)} edges"
                    )

                if result is not None and len(result.hypotheses) == 0:
                    error_msg = f"LLM calls failed for {model_name} — empty result"
                    logger.warning("[SSE-DEBUG] zero hypotheses — falling back to demo")
                    result = None

                if result is not None:
                    result.is_demo = False
                    resp = _result_to_v2(
                        result,
                        is_demo=False,
                        scenario_override=request.scenario_override,
                    )
                    resp = _finalize_run_response(resp, request, run_id)
                    eq.put({"type": "done", "is_demo": False, "data": resp.model_dump(mode="json")})
                elif request.api_key and _is_live_failure(error_msg):
                    resp = _empty_live_failure_response(
                        request.query,
                        error_msg or "Live analysis failed.",
                        scenario_override=request.scenario_override,
                    )
                    resp = _finalize_run_response(resp, request, run_id)
                    eq.put(
                        {
                            "type": "done",
                            "is_demo": False,
                            "data": resp.model_dump(mode="json"),
                        }
                    )
                else:
                    demo_result = topic_aware_demo_result(request.query)
                    demo_topic = detect_demo_topic(request.query) or "default"
                    demo_result.is_demo = True
                    demo_result.demo_topic = demo_topic
                    resp = _result_to_v2(
                        demo_result,
                        is_demo=True,
                        demo_topic=demo_topic,
                        scenario_override=request.scenario_override,
                    )
                    resp = _finalize_run_response(resp, request, run_id)
                    eq.put(
                        {
                            "type": "done",
                            "is_demo": True,
                            "demo_topic": demo_topic,
                            "error": error_msg,
                            "data": resp.model_dump(mode="json"),
                        }
                    )

            except Exception as exc:
                eq.put({"type": "error", "error": f"{type(exc).__name__}: {exc}"})
            finally:
                eq.put(None)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        while True:
            try:
                item = eq.get(timeout=420)
            except queue.Empty:
                break
            if item is None:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            if item.get("type") in ("done", "error"):
                break

    return StreamingResponse(generate(), media_type="text/event-stream")
