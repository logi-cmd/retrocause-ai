from __future__ import annotations

from typing import List, Optional

from retrocause.api.analysis_brief import build_analysis_brief_payload
from retrocause.api.briefs import build_markdown_research_brief
from retrocause.api.harness import (
    build_product_harness_payload,
    build_production_harness_payload,
)
from retrocause.api.production_brief import build_production_brief_payload
from retrocause.api.retrieval_trace import (
    build_retrieval_trace_item_v2,
    retrieval_status_from_trace,
)
from retrocause.api.scenarios import detect_production_scenario_payload
from retrocause.api.schemas import (
    AnalysisBriefV2,
    AnalyzeResponseV2,
    ChallengeCheckV2,
    CitationSpanV2,
    CounterfactualItemV2,
    CounterfactualSummaryV2,
    EvidenceBindingV2,
    GraphEdgeV2,
    GraphNodeV2,
    HypothesisChainV2,
    PipelineEvaluationV2,
    ProductHarnessReportV2,
    ProductionBriefV2,
    ProductionHarnessReportV2,
    ScenarioV2,
    UncertaintyAssessmentV2,
    UncertaintyReportV2,
    UpstreamMapEntryV2,
    UpstreamMapV2,
)
from retrocause.models import AnalysisResult


def detect_production_scenario(
    query: str,
    domain: str = "general",
    override: Optional[str] = None,
) -> ScenarioV2:
    payload = detect_production_scenario_payload(query, domain=domain, override=override)
    return ScenarioV2(
        key=payload.key,
        label=payload.label,
        confidence=payload.confidence,
        detection_method=payload.detection_method,
        user_value=payload.user_value,
    )


def derive_partial_live_reasons(result: AnalysisResult) -> List[str]:
    reasons: List[str] = []
    if result.analysis_mode != "partial_live":
        return reasons

    if result.evaluation is not None:
        reasons.extend(result.evaluation.weaknesses[:3])

    if result.freshness_status in {"unknown", "stable"}:
        reasons.append("Fresh evidence is limited for this run.")

    deduped: List[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped[:3]


def classify_node_type(name: str, upstream_ids: List[str], downstream_ids: List[str]) -> str:
    if not upstream_ids:
        return "cause"
    if not downstream_ids:
        return "effect"
    return "mediator"


def build_upstream_map(nodes_v2: List[GraphNodeV2]) -> UpstreamMapV2:
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


def refutation_status(
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


def collect_evidence_bindings(
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


def challenge_check_v2(item: dict) -> ChallengeCheckV2:
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


def result_to_v2(
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
            node_type = classify_node_type(var.name, ups, downs)
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
                    refutation_status=refutation_status(
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
                refutation_status=refutation_status(chain_ref, result.evidences),
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
        challenge_check_v2(item) for item in getattr(result, "refutation_checks", [])
    ]

    response = AnalyzeResponseV2(
        query=result.query,
        is_demo=is_demo,
        demo_topic=demo_topic,
        analysis_mode="demo" if is_demo else result.analysis_mode,
        freshness_status=result.freshness_status,
        time_range=parsed_query.time_range,
        partial_live_reasons=[] if is_demo else derive_partial_live_reasons(result),
        recommended_chain_id=recommended_id,
        chains=chains_v2,
        evidences=collect_evidence_bindings(chains_v2, result.evidences),
        upstream_map=build_upstream_map(list(all_nodes_v2.values())),
        evaluation=evaluation_v2,
        retrieval_trace=[
            build_retrieval_trace_item_v2(item)
            for item in getattr(result, "retrieval_trace", [])
        ],
        challenge_checks=challenge_checks,
        analysis_brief=AnalysisBriefV2(
            **build_analysis_brief_payload(
                result=result,
                chains=chains_v2,
                checks=challenge_checks,
                retrieval_statuses=[
                    retrieval_status_from_trace(item)
                    for item in getattr(result, "retrieval_trace", [])
                ],
            )
        ),
        uncertainty_report=uncertainty_v2,
    )
    scenario = detect_production_scenario(
        result.query,
        domain=result.domain,
        override=scenario_override,
    )
    response.scenario = scenario
    response.production_brief = ProductionBriefV2(
        **build_production_brief_payload(response, scenario)
    )
    response.production_harness = ProductionHarnessReportV2(
        **build_production_harness_payload(response)
    )
    response.markdown_brief = build_markdown_research_brief(response)
    response.product_harness = ProductHarnessReportV2(
        **build_product_harness_payload(response)
    )
    return response
