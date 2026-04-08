from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from retrocause.app.demo_data import (
    PROVIDERS,
    detect_demo_topic,
    topic_aware_demo_result,
)
from retrocause.models import AnalysisResult

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
    model: str = "openrouter"  # provider key (e.g. "zhipu") or explicit model name
    api_key: Optional[str] = None
    explicit_model: Optional[str] = None  # user-selected model name (e.g. "glm-4-air")


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


class AnalyzeResponseV2(BaseModel):
    """
    Enriched top-level response for multi-hop causal tracing.
    Preserves query field and adds chain-aware structures.
    """

    query: str
    # True when the engine could not run real analysis and demo data was returned
    is_demo: bool = False
    demo_topic: Optional[str] = None
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
    # Error message when real analysis fails (non-empty = something went wrong)
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    query: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    evidences: List[Evidence]
    is_demo: bool = False
    demo_topic: Optional[str] = None


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


def _collect_evidence_bindings(
    chains: List[HypothesisChainV2],
) -> List[EvidenceBindingV2]:
    from retrocause.app.demo_data import DEMO_EVIDENCES

    seen_ids: set[str] = set()
    bindings: List[EvidenceBindingV2] = []
    demo_by_id = {ev.id: ev for ev in DEMO_EVIDENCES}

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
                    )
                )
    return bindings


def _result_to_v2(
    result: AnalysisResult, *, is_demo: bool = False, demo_topic: Optional[str] = None
) -> AnalyzeResponseV2:
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
                )
            )

        edges_v2: List[GraphEdgeV2] = []
        for edge in hyp.edges:
            edges_v2.append(
                GraphEdgeV2(
                    id=f"{edge.source}_{edge.target}",
                    source=edge.source,
                    target=edge.target,
                    strength=edge.conditional_prob,
                    type="causes",
                    supporting_evidence_ids=edge.supporting_evidence_ids,
                    refuting_evidence_ids=edge.refuting_evidence_ids,
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

    return AnalyzeResponseV2(
        query=result.query,
        is_demo=is_demo,
        demo_topic=demo_topic,
        recommended_chain_id=recommended_id,
        chains=chains_v2,
        evidences=_collect_evidence_bindings(chains_v2),
        upstream_map=_build_upstream_map(list(all_nodes_v2.values())),
        evaluation=evaluation_v2,
    )


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


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_query(request: AnalyzeRequest):
    try:
        is_demo = False
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
            try:
                result = run_real_analysis(request.query, request.api_key, model_name, base_url)
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
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/v2", response_model=AnalyzeResponseV2)
async def analyze_query_v2(request: AnalyzeRequest):
    try:
        is_demo = True
        demo_topic: Optional[str] = None
        result: AnalysisResult | None = None

        # ── Attempt real analysis when the caller supplies an API key ──
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
                result = run_real_analysis(request.query, request.api_key, model_name, base_url)
            except Exception as exc:
                import traceback

                traceback.print_exc()
                error_msg = f"{type(exc).__name__}: {exc}"
                result = None

            if result is not None:
                is_demo = False

        # ── Fallback: topic-aware demo data ──
        if result is None:
            result = topic_aware_demo_result(request.query)
            is_demo = True
            demo_topic = detect_demo_topic(request.query) or "default"

        # Stamp honesty fields on the dataclass itself
        result.is_demo = is_demo
        result.demo_topic = demo_topic

        resp = _result_to_v2(result, is_demo=is_demo, demo_topic=demo_topic)
        resp.error = error_msg if is_demo and request.api_key else None
        return resp

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
