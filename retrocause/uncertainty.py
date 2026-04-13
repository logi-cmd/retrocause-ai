"""不确定性建模 — per-node / per-edge 不确定性评估 + 全局汇总"""

from __future__ import annotations

import logging
from collections import Counter

from retrocause.collector import EvidenceCollector
from retrocause.models import (
    CausalEdge,
    CausalVariable,
    EvidenceConflictType,
    HypothesisChain,
    UncertaintyAssessment,
    UncertaintyReport,
    UncertaintyType,
)
from retrocause.pipeline import PipelineContext, PipelineStep

logger = logging.getLogger(__name__)


def assess_variable_uncertainty(
    var: CausalVariable,
    evidence_count: int,
    total_evidence: int,
) -> UncertaintyAssessment:
    types: list[UncertaintyType] = []
    explanations: list[str] = []

    if evidence_count == 0:
        types.append(UncertaintyType.THIN_EVIDENCE)
        explanations.append(f"变量 {var.name} 无关联证据")
    elif evidence_count <= 2:
        types.append(UncertaintyType.THIN_EVIDENCE)
        explanations.append(f"变量 {var.name} 证据薄弱 ({evidence_count} 条)")

    if var.posterior_support < 0.2 or var.posterior_support > 0.8:
        if var.posterior_support < 0.2:
            types.append(UncertaintyType.LOW_CONFIDENCE_REASONING)
            explanations.append(f"变量 {var.name} 后验支持度极低 ({var.posterior_support:.2f})")

    data_unc = min(1.0, max(0.0, 1.0 - evidence_count / max(total_evidence, 1)))
    model_unc = 1.0 - var.posterior_support if var.posterior_support < 0.5 else 0.2
    overall = 0.6 * data_unc + 0.4 * model_unc

    return UncertaintyAssessment(
        uncertainty_types=types,
        overall_score=round(overall, 3),
        data_uncertainty=round(data_unc, 3),
        model_uncertainty=round(model_unc, 3),
        explanation="; ".join(explanations) if explanations else "不确定性较低",
    )


def assess_edge_uncertainty(
    edge: CausalEdge,
    evidence_by_var: dict[str, list[str]],
) -> UncertaintyAssessment:
    types: list[UncertaintyType] = []
    explanations: list[str] = []

    supp_count = len(edge.supporting_evidence_ids)
    ref_count = len(edge.refuting_evidence_ids)
    total = supp_count + ref_count

    if total == 0:
        types.append(UncertaintyType.THIN_EVIDENCE)
        explanations.append(f"边 {edge.source}→{edge.target} 无证据锚定")
    elif supp_count > 0 and ref_count > 0:
        conflict_ratio = min(supp_count, ref_count) / total
        if conflict_ratio > 0.3:
            types.append(UncertaintyType.CONFLICTING_EVIDENCE)
            explanations.append(
                f"边 {edge.source}→{edge.target} 存在证据冲突 "
                f"(support={supp_count}, refute={ref_count})"
            )

    ci_width = edge.confidence_interval[1] - edge.confidence_interval[0]
    if ci_width > 0.6:
        types.append(UncertaintyType.EPISTEMIC)
        explanations.append(f"边 {edge.source}→{edge.target} 置信区间过宽 ({ci_width:.2f})")

    prob = edge.conditional_prob
    if prob < 0.1 or prob > 0.95:
        types.append(UncertaintyType.MODEL)
        if prob < 0.1:
            explanations.append(f"边 {edge.source}→{edge.target} 条件概率极低 ({prob:.2f})")

    data_unc = min(1.0, max(0.0, 1.0 - total / 5.0))
    model_unc = ci_width * 0.5
    overall = 0.5 * data_unc + 0.3 * model_unc + 0.2 * (1.0 - prob if prob < 0.3 else 0.0)

    if UncertaintyType.CONFLICTING_EVIDENCE in types:
        overall = min(1.0, overall + 0.2)

    return UncertaintyAssessment(
        uncertainty_types=types,
        overall_score=round(overall, 3),
        data_uncertainty=round(data_unc, 3),
        model_uncertainty=round(model_unc, 3),
        explanation="; ".join(explanations) if explanations else "不确定性较低",
    )


def detect_evidence_conflict(
    edge: CausalEdge,
) -> EvidenceConflictType:
    supp = len(edge.supporting_evidence_ids)
    ref = len(edge.refuting_evidence_ids)

    if ref == 0:
        return EvidenceConflictType.NONE
    if supp == 0:
        return EvidenceConflictType.DIRECT

    ratio = ref / (supp + ref)
    if ratio > 0.5:
        return EvidenceConflictType.DIRECT
    if ratio > 0.2:
        return EvidenceConflictType.PARTIAL
    return EvidenceConflictType.NONE


def build_uncertainty_report(
    variables: list[CausalVariable],
    edges: list[CausalEdge],
    chains: list[HypothesisChain],
    evidence_by_var: dict[str, list[str]],
    total_evidence: int,
) -> UncertaintyReport:
    per_node: dict[str, UncertaintyAssessment] = {}
    for var in variables:
        ev_count = len(evidence_by_var.get(var.name, []))
        assessment = assess_variable_uncertainty(var, ev_count, total_evidence)
        var.uncertainty = assessment
        per_node[var.name] = assessment

    per_edge: dict[str, UncertaintyAssessment] = {}
    conflicts: dict[str, EvidenceConflictType] = {}
    for edge in edges:
        key = f"{edge.source}→{edge.target}"
        assessment = assess_edge_uncertainty(edge, evidence_by_var)
        edge.uncertainty = assessment
        per_edge[key] = assessment

        conflict = detect_evidence_conflict(edge)
        edge.evidence_conflict = conflict
        if conflict != EvidenceConflictType.NONE:
            conflicts[key] = conflict

    all_scores = [a.overall_score for a in per_node.values()] + [
        a.overall_score for a in per_edge.values()
    ]
    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

    type_counter: Counter[UncertaintyType] = Counter()
    for a in list(per_node.values()) + list(per_edge.values()):
        type_counter.update(a.uncertainty_types)

    dominant = type_counter.most_common(1)[0][0] if type_counter else None

    summary_parts: list[str] = []
    if conflicts:
        summary_parts.append(f"{len(conflicts)} 条边存在证据冲突")
    thin_nodes = sum(1 for v in variables if not v.evidence_ids)
    if thin_nodes:
        summary_parts.append(f"{thin_nodes}/{len(variables)} 个变量缺乏证据")
    summary = "；".join(summary_parts) if summary_parts else "整体不确定性较低"

    return UncertaintyReport(
        per_node=per_node,
        per_edge=per_edge,
        evidence_conflicts=conflicts,
        overall_uncertainty=round(overall, 3),
        dominant_uncertainty_type=dominant,
        summary=summary,
    )


class UncertaintyAssessmentStep(PipelineStep):
    """Pipeline step: 评估 per-node/edge 不确定性并生成汇总报告"""

    def __init__(self, collector: EvidenceCollector):
        self.collector = collector

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        evidence_by_var: dict[str, list[str]] = {}
        for ev in self.collector.get_evidence():
            for var in ev.linked_variables:
                evidence_by_var.setdefault(var, []).append(ev.id)

        report = build_uncertainty_report(
            variables=ctx.variables,
            edges=ctx.edges,
            chains=ctx.hypotheses,
            evidence_by_var=evidence_by_var,
            total_evidence=ctx.total_evidence_count,
        )

        ctx.total_uncertainty = report.overall_uncertainty
        ctx.extra["uncertainty_report"] = report
        logger.info(
            "UncertaintyAssessmentStep: overall=%.2f conflicts=%d dominant=%s",
            report.overall_uncertainty,
            len(report.evidence_conflicts),
            report.dominant_uncertainty_type,
        )
        return ctx
