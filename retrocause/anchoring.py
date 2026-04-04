"""证据锚定 — 将每条因果边与证据绑定，计算覆盖率"""

from __future__ import annotations

import logging

from retrocause.collector import EvidenceCollector
from retrocause.models import CausalEdge, HypothesisChain
from retrocause.pipeline import PipelineContext, PipelineStep

logger = logging.getLogger(__name__)


def anchor_edge_to_evidence(
    edge: CausalEdge,
    evidence_by_var: dict[str, list[str]],
) -> tuple[int, int]:
    source_evidence = set(evidence_by_var.get(edge.source, []))
    target_evidence = set(evidence_by_var.get(edge.target, []))
    relevant = source_evidence | target_evidence

    if not relevant:
        return 0, 0

    edge.supporting_evidence_ids = sorted(relevant)
    return len(relevant), len(relevant)


def anchor_hypothesis(
    chain: HypothesisChain,
    evidence_by_var: dict[str, list[str]],
) -> None:
    if not chain.edges:
        chain.evidence_coverage = 0.0
        chain.unanchored_edges = []
        return
    anchored = 0
    unanchored: list[str] = []
    for edge in chain.edges:
        supporting, _ = anchor_edge_to_evidence(edge, evidence_by_var)
        if supporting > 0:
            anchored += 1
        else:
            unanchored.append(f"{edge.source}\u2192{edge.target}")
    chain.evidence_coverage = anchored / len(chain.edges)
    chain.unanchored_edges = unanchored


def build_evidence_index(collector: EvidenceCollector) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for ev in collector.get_evidence():
        for var in ev.linked_variables:
            index.setdefault(var, []).append(ev.id)
    return index


class EvidenceAnchoringStep(PipelineStep):
    def __init__(self, collector: EvidenceCollector):
        self.collector = collector

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        evidence_by_var = build_evidence_index(self.collector)
        for chain in ctx.hypotheses:
            anchor_hypothesis(chain, evidence_by_var)
        total_evidence = len(self.collector.get_evidence())
        total_hypotheses = len(ctx.hypotheses)
        anchored_count = sum(1 for h in ctx.hypotheses if h.evidence_coverage > 0)
        logger.info(
            "EvidenceAnchoringStep: %d evidence, %d hypotheses, %d anchored (coverage>0)",
            total_evidence,
            total_hypotheses,
            anchored_count,
        )
        return ctx
