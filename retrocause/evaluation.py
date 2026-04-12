"""Structured pipeline quality evaluation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from retrocause.pipeline import PipelineContext, PipelineStep

logger = logging.getLogger(__name__)

_EVIDENCE_COVERAGE_THRESHOLD = 0.5
_PROBABILITY_EPSILON = 0.01
_CHAIN_SIMILARITY_THRESHOLD = 0.9


@dataclass
class PipelineEvaluation:
    evidence_sufficiency: float = 0.0
    probability_coherence: float = 0.0
    chain_diversity: float = 0.0
    overall_confidence: float = 0.0
    weaknesses: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)


def _assess_evidence_sufficiency(ctx: PipelineContext) -> tuple[float, list[str]]:
    weaknesses: list[str] = []
    hypotheses = ctx.hypotheses

    if not hypotheses:
        return 0.0, ["No hypothesis chains were produced, so evidence sufficiency cannot be assessed."]

    low_coverage = [h for h in hypotheses if h.evidence_coverage < _EVIDENCE_COVERAGE_THRESHOLD]
    if low_coverage:
        weaknesses.append(
            f"{len(low_coverage)}/{len(hypotheses)} chains have evidence coverage below "
            f"{_EVIDENCE_COVERAGE_THRESHOLD:.0%}"
        )

    unanchored_total = sum(len(h.unanchored_edges) for h in hypotheses)
    total_edges = sum(len(h.edges) for h in hypotheses)
    if total_edges > 0 and unanchored_total > total_edges * 0.5:
        weaknesses.append(f"More than half of causal edges are unanchored ({unanchored_total}/{total_edges})")

    avg_coverage = sum(h.evidence_coverage for h in hypotheses) / len(hypotheses)
    evidence_bonus = min(ctx.total_evidence_count / 10.0, 0.2)

    score = min(1.0, avg_coverage + evidence_bonus)
    if not ctx.total_evidence_count:
        score = 0.0
        weaknesses.append("No evidence was collected.")

    return score, weaknesses


def _assess_evidence_quality(ctx: PipelineContext) -> tuple[float, list[str]]:
    evidences = ctx.extra.get("evidences", [])
    if not evidences:
        return 0.0, ["No evidence quality metadata is available."]

    fallback_count = sum(
        1 for ev in evidences if getattr(ev, "extraction_method", "") == "fallback_summary"
    )
    fallback_ratio = fallback_count / len(evidences)
    weaknesses: list[str] = []

    if fallback_ratio >= 0.5:
        weaknesses.append(
            f"Fallback-summary evidence dominates the run ({fallback_count}/{len(evidences)} items)."
        )
    elif fallback_ratio > 0:
        weaknesses.append(
            f"Fallback-summary evidence is present ({fallback_count}/{len(evidences)} items)."
        )

    score = 1.0 - fallback_ratio * 0.7
    if any(getattr(ev, "freshness", "unknown") == "unknown" for ev in evidences):
        score -= 0.05

    return max(0.0, min(1.0, score)), weaknesses


def _assess_probability_coherence(ctx: PipelineContext) -> tuple[float, list[str]]:
    weaknesses: list[str] = []
    hypotheses = ctx.hypotheses

    if not hypotheses:
        return 0.0, ["No hypothesis chains were produced, so probability coherence cannot be assessed."]

    incoherent = 0
    for hypothesis in hypotheses:
        if not (0.0 <= hypothesis.path_probability <= 1.0 + _PROBABILITY_EPSILON):
            incoherent += 1
            continue
        if not (0.0 <= hypothesis.posterior_probability <= 1.0 + _PROBABILITY_EPSILON):
            incoherent += 1
            continue

        lower, upper = hypothesis.confidence_interval
        if lower > upper or lower < 0 or upper > 1:
            incoherent += 1
            weaknesses.append(
                f"Chain {hypothesis.id} has an invalid confidence interval [{lower:.2f}, {upper:.2f}] (异常)"
            )

    if incoherent:
        weaknesses.append(
            f"{incoherent}/{len(hypotheses)} chains have incoherent probabilities. (不自洽)"
        )

    posterior_sum = sum(h.posterior_probability for h in hypotheses)
    if len(hypotheses) > 1 and abs(posterior_sum - 1.0) > 0.5:
        weaknesses.append(
            f"Posterior probabilities drift too far from 1.0 (sum={posterior_sum:.2f})."
        )

    score = 1.0 - (incoherent / len(hypotheses))
    return score, weaknesses


def _assess_chain_diversity(ctx: PipelineContext) -> tuple[float, list[str]]:
    weaknesses: list[str] = []
    hypotheses = ctx.hypotheses

    if len(hypotheses) <= 1:
        return (1.0 if len(hypotheses) == 1 else 0.0), []

    var_sets = [set(v.name for v in h.variables) for h in hypotheses]
    max_jaccard = 0.0
    for i in range(len(var_sets)):
        for j in range(i + 1, len(var_sets)):
            if not var_sets[i] and not var_sets[j]:
                continue
            union = var_sets[i] | var_sets[j]
            if not union:
                continue
            jaccard = len(var_sets[i] & var_sets[j]) / len(union)
            max_jaccard = max(max_jaccard, jaccard)

    if max_jaccard > _CHAIN_SIMILARITY_THRESHOLD:
        weaknesses.append(f"Highest chain similarity is {max_jaccard:.0%}, so alternatives are too similar.")

    return 1.0 - max_jaccard, weaknesses


class EvaluationStep(PipelineStep):
    """Read pipeline outputs and compute structured quality signals."""

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        evidence_sufficiency, sufficiency_weaknesses = _assess_evidence_sufficiency(ctx)
        evidence_quality, quality_weaknesses = _assess_evidence_quality(ctx)
        probability_coherence, probability_weaknesses = _assess_probability_coherence(ctx)
        chain_diversity, diversity_weaknesses = _assess_chain_diversity(ctx)

        weaknesses = (
            sufficiency_weaknesses
            + quality_weaknesses
            + probability_weaknesses
            + diversity_weaknesses
        )

        if ctx.violations:
            weaknesses.append(f"Pipeline validation emitted {len(ctx.violations)} warnings.")
        if ctx.step_errors:
            weaknesses.append(f"Pipeline execution hit {len(ctx.step_errors)} step errors.")

        overall = (
            evidence_sufficiency * 0.3
            + evidence_quality * 0.2
            + probability_coherence * 0.3
            + chain_diversity * 0.2
        )

        if ctx.step_errors:
            overall *= max(0.5, 1.0 - 0.1 * len(ctx.step_errors))

        recommended: list[str] = []
        if evidence_sufficiency < 0.5:
            recommended.append("Add more evidence sources or refine the retrieval sub-queries.")
        if evidence_quality < 0.65:
            recommended.append("Reduce fallback-summary evidence and prioritize anchorable primary evidence.")
        if probability_coherence < 0.8:
            recommended.append("Inspect causal edge probabilities and confidence intervals for inconsistencies.")
        if chain_diversity < 0.3 and len(ctx.hypotheses) > 1:
            recommended.append("Generate more diverse competing chains.")
        if not ctx.total_evidence_count:
            recommended.append("Enable or repair evidence collection before trusting the output.")
        if not ctx.hypotheses:
            recommended.append("Upstream steps produced no chains; inspect retrieval and graph building.")

        evaluation = PipelineEvaluation(
            evidence_sufficiency=round(evidence_sufficiency, 3),
            probability_coherence=round(probability_coherence, 3),
            chain_diversity=round(chain_diversity, 3),
            overall_confidence=round(max(0.0, min(1.0, overall)), 3),
            weaknesses=weaknesses,
            recommended_actions=recommended,
        )

        logger.info(
            "Pipeline evaluation: overall=%.2f sufficiency=%.2f quality=%.2f coherence=%.2f diversity=%.2f weaknesses=%d",
            evaluation.overall_confidence,
            evidence_sufficiency,
            evidence_quality,
            evaluation.probability_coherence,
            evaluation.chain_diversity,
            len(evaluation.weaknesses),
        )

        ctx.evaluation = evaluation
        return ctx
