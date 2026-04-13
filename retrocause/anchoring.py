"""证据锚定 — 将每条因果边与证据绑定，span-level citation grounding"""

from __future__ import annotations

import logging

from retrocause.collector import EvidenceCollector
from retrocause.models import CausalEdge, CitationSpan, Evidence, HypothesisChain
from retrocause.pipeline import PipelineContext, PipelineStep

logger = logging.getLogger(__name__)


def _evidence_quality_score(evidence: Evidence) -> float:
    method = getattr(evidence, "extraction_method", "manual")
    base = 1.0
    if method == "fallback_summary":
        base = 0.45
    elif method == "llm":
        base = 0.9
    freshness = getattr(evidence, "freshness", "unknown")
    if freshness == "unknown":
        base -= 0.05
    return max(0.2, min(1.0, base))


def _apply_chain_quality_penalty(chain: HypothesisChain, evidence_lookup: dict[str, Evidence]) -> None:
    if not chain.edges:
        return

    edge_scores: list[float] = []
    for edge in chain.edges:
        if not edge.supporting_evidence_ids:
            edge_scores.append(0.35)
            continue
        scores = [
            _evidence_quality_score(evidence_lookup[eid])
            for eid in edge.supporting_evidence_ids
            if eid in evidence_lookup
        ]
        edge_scores.append(sum(scores) / len(scores) if scores else 0.35)

    quality_factor = sum(edge_scores) / len(edge_scores)
    quality_multiplier = 0.55 + 0.45 * quality_factor
    adjusted_posterior = chain.path_probability * quality_multiplier
    chain.posterior_probability = max(0.0, min(chain.posterior_probability, adjusted_posterior))

    interval_half_width = 0.1 + (1.0 - quality_factor) * 0.2
    chain.confidence_interval = (
        max(0.0, chain.posterior_probability - interval_half_width),
        min(1.0, chain.posterior_probability + interval_half_width),
    )


def anchor_edge_to_evidence(
    edge: CausalEdge,
    evidence_by_var: dict[str, list[str]],
    evidence_stance_by_id: dict[str, str] | None = None,
) -> tuple[int, int]:
    source_evidence = set(evidence_by_var.get(edge.source, []))
    target_evidence = set(evidence_by_var.get(edge.target, []))
    relevant = source_evidence | target_evidence

    if not relevant:
        return 0, 0

    stance_by_id = evidence_stance_by_id or {}
    edge.supporting_evidence_ids = sorted(
        ev_id for ev_id in relevant if stance_by_id.get(ev_id, "supporting") != "refuting"
    )
    edge.refuting_evidence_ids = sorted(
        ev_id for ev_id in relevant if stance_by_id.get(ev_id, "supporting") == "refuting"
    )
    return len(edge.supporting_evidence_ids), len(relevant)


def anchor_hypothesis(
    chain: HypothesisChain,
    evidence_by_var: dict[str, list[str]],
    evidence_stance_by_id: dict[str, str] | None = None,
) -> None:
    if not chain.edges:
        chain.evidence_coverage = 0.0
        chain.unanchored_edges = []
        return
    anchored = 0
    unanchored: list[str] = []
    for edge in chain.edges:
        supporting, total = anchor_edge_to_evidence(edge, evidence_by_var, evidence_stance_by_id)
        if total > 0 or edge.supporting_evidence_ids or edge.refuting_evidence_ids:
            anchored += 1
        else:
            unanchored.append(f"{edge.source}\u2192{edge.target}")
    chain.evidence_coverage = anchored / len(chain.edges)
    chain.unanchored_edges = unanchored


def build_evidence_index(collector: EvidenceCollector) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for ev in collector.get_evidence():
        if getattr(ev, "extraction_method", "") == "fallback_summary":
            continue
        for var in ev.linked_variables:
            index.setdefault(var, []).append(ev.id)
    return index


def ground_citation_spans(
    edge: CausalEdge,
    evidence_lookup: dict[str, str],
) -> list[CitationSpan]:
    """为因果边生成 citation span — 从证据文本中定位与 source→target 因果关系相关的片段。"""
    spans: list[CitationSpan] = []
    edge_vars = {edge.source.replace("_", " "), edge.target.replace("_", " ")}

    for ev_id in edge.supporting_evidence_ids:
        content = evidence_lookup.get(ev_id, "")
        if not content:
            continue

        span_text = _extract_relevant_span(content, edge_vars)
        if span_text:
            start = content.lower().find(span_text.lower())
            if start < 0:
                start = 0
            spans.append(
                CitationSpan(
                    evidence_id=ev_id,
                    start_char=start,
                    end_char=start + len(span_text),
                    quoted_text=span_text,
                    relevance_score=_compute_span_relevance(span_text, edge_vars),
                )
            )

    edge.citation_spans = spans
    return spans


def _extract_relevant_span(content: str, keywords: set[str], max_len: int = 200) -> str:
    """从证据文本中提取包含关键词的最相关句子或片段。"""
    sentences = content.replace("。", ".").replace("！", "!").replace("？", "?")
    for sep in [". ", "! ", "? ", "\n"]:
        parts = sentences.split(sep)
        for part in parts:
            part_stripped = part.strip()
            if not part_stripped or len(part_stripped) < 10:
                continue
            part_lower = part_stripped.lower()
            matches = sum(1 for kw in keywords if kw.lower() in part_lower)
            if matches >= 1:
                return part_stripped[:max_len]

    if len(content) <= max_len:
        return content
    return content[:max_len]


def _compute_span_relevance(span_text: str, keywords: set[str]) -> float:
    """计算 span 与关键词集合的相关度。"""
    span_lower = span_text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in span_lower)
    return min(1.0, matches / max(len(keywords), 1))


class EvidenceAnchoringStep(PipelineStep):
    def __init__(self, collector: EvidenceCollector):
        self.collector = collector

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        evidence_by_var = build_evidence_index(self.collector)
        quality_lookup: dict[str, Evidence] = {}

        evidence_lookup: dict[str, str] = {}
        for ev in self.collector.get_evidence():
            evidence_lookup[ev.id] = ev.content
            quality_lookup[ev.id] = ev
        evidence_stance_by_id = {
            ev.id: getattr(ev, "stance", "supporting") for ev in self.collector.get_evidence()
        }

        for chain in ctx.hypotheses:
            anchor_hypothesis(chain, evidence_by_var, evidence_stance_by_id)
            _apply_chain_quality_penalty(chain, quality_lookup)

            for edge in chain.edges:
                if edge.supporting_evidence_ids:
                    ground_citation_spans(edge, evidence_lookup)

        total_evidence = len(self.collector.get_evidence())
        total_hypotheses = len(ctx.hypotheses)
        anchored_count = sum(1 for h in ctx.hypotheses if h.evidence_coverage > 0)
        total_spans = sum(len(e.citation_spans) for h in ctx.hypotheses for e in h.edges)
        logger.info(
            "EvidenceAnchoringStep: %d evidence, %d hypotheses, %d anchored, %d citation spans",
            total_evidence,
            total_hypotheses,
            anchored_count,
            total_spans,
        )
        return ctx


def reanchor_hypotheses(ctx: PipelineContext, collector: EvidenceCollector) -> None:
    """Refresh evidence bindings after a retrieval step appends new evidence."""
    evidence_by_var = build_evidence_index(collector)
    evidence_lookup = {ev.id: ev.content for ev in collector.get_evidence()}
    evidence_stance_by_id = {
        ev.id: getattr(ev, "stance", "supporting") for ev in collector.get_evidence()
    }
    quality_lookup = {ev.id: ev for ev in collector.get_evidence()}

    for chain in ctx.hypotheses:
        anchor_hypothesis(chain, evidence_by_var, evidence_stance_by_id)
        _apply_chain_quality_penalty(chain, quality_lookup)
        for edge in chain.edges:
            if edge.supporting_evidence_ids:
                ground_citation_spans(edge, evidence_lookup)
