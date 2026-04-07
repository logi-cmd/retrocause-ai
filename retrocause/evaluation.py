"""独立评估步骤 — 在所有生成步骤完成后对 pipeline 输出进行质量评估"""

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
        return 0.0, ["无假说链产出，无法评估证据充分性"]

    low_coverage = [h for h in hypotheses if h.evidence_coverage < _EVIDENCE_COVERAGE_THRESHOLD]
    if low_coverage:
        weaknesses.append(
            f"{len(low_coverage)}/{len(hypotheses)} 条链证据覆盖率低于 "
            f"{_EVIDENCE_COVERAGE_THRESHOLD:.0%}"
        )

    unanchored_total = sum(len(h.unanchored_edges) for h in hypotheses)
    total_edges = sum(len(h.edges) for h in hypotheses)
    if total_edges > 0 and unanchored_total > total_edges * 0.5:
        weaknesses.append(f"超过半数因果边无证据锚定 ({unanchored_total}/{total_edges})")

    avg_coverage = sum(h.evidence_coverage for h in hypotheses) / len(hypotheses)
    evidence_bonus = min(ctx.total_evidence_count / 10.0, 0.2)

    score = min(1.0, avg_coverage + evidence_bonus)
    if not ctx.total_evidence_count:
        score = 0.0
        weaknesses.append("未收集到任何证据")

    return score, weaknesses


def _assess_probability_coherence(ctx: PipelineContext) -> tuple[float, list[str]]:
    weaknesses: list[str] = []
    hypotheses = ctx.hypotheses

    if not hypotheses:
        return 0.0, ["无假说链产出，无法评估概率自洽性"]

    incoherent = 0
    for h in hypotheses:
        if not (0.0 <= h.path_probability <= 1.0 + _PROBABILITY_EPSILON):
            incoherent += 1
            continue
        if not (0.0 <= h.posterior_probability <= 1.0 + _PROBABILITY_EPSILON):
            incoherent += 1
            continue
        lo, hi = h.confidence_interval
        if lo > hi or lo < 0 or hi > 1:
            incoherent += 1
            weaknesses.append(f"链 {h.id} 置信区间异常 [{lo:.2f}, {hi:.2f}]")

    if incoherent:
        weaknesses.append(f"{incoherent}/{len(hypotheses)} 条链概率不自洽")

    prob_sum = sum(h.posterior_probability for h in hypotheses)
    if len(hypotheses) > 1 and abs(prob_sum - 1.0) > 0.5:
        weaknesses.append(f"后验概率之和偏离 1.0 较远 (sum={prob_sum:.2f})，链间概率分配可能不合理")

    score = 1.0 - (incoherent / len(hypotheses))
    return score, weaknesses


def _assess_chain_diversity(ctx: PipelineContext) -> tuple[float, list[str]]:
    weaknesses: list[str] = []
    hypotheses = ctx.hypotheses

    if len(hypotheses) <= 1:
        return 1.0 if len(hypotheses) == 1 else 0.0, []

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
        weaknesses.append(f"最高链间相似度 {max_jaccard:.0%}，竞争链可能过于相似")

    diversity = 1.0 - max_jaccard
    return diversity, weaknesses


class EvaluationStep(PipelineStep):
    """独立评估步骤 — 读取 pipeline 产出，生成结构化质量评估"""

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        ev_sufficiency, ev_weaknesses = _assess_evidence_sufficiency(ctx)
        prob_coherence, prob_weaknesses = _assess_probability_coherence(ctx)
        chain_diversity, div_weaknesses = _assess_chain_diversity(ctx)

        all_weaknesses = ev_weaknesses + prob_weaknesses + div_weaknesses

        # Add violation and step_error derived weaknesses
        if ctx.violations:
            all_weaknesses.append(f"pipeline 规则检查产生 {len(ctx.violations)} 条告警")
        if ctx.step_errors:
            all_weaknesses.append(f"pipeline 执行中 {len(ctx.step_errors)} 个步骤报错")

        # Weighted overall confidence
        # evidence is most important (40%), then coherence (35%), then diversity (25%)
        overall = ev_sufficiency * 0.4 + prob_coherence * 0.35 + chain_diversity * 0.25

        # Penalty for execution problems
        if ctx.step_errors:
            overall *= max(0.5, 1.0 - 0.1 * len(ctx.step_errors))

        recommended: list[str] = []
        if ev_sufficiency < 0.5:
            recommended.append("增加证据来源或细化搜索子查询以提高证据覆盖")
        if prob_coherence < 0.8:
            recommended.append("检查因果边概率估计的一致性")
        if chain_diversity < 0.3 and len(ctx.hypotheses) > 1:
            recommended.append("竞争链过于相似，考虑生成更发散的假说")
        if not ctx.total_evidence_count:
            recommended.append("配置 LLM 与搜索源以启用自动证据收集")
        if not ctx.hypotheses:
            recommended.append("pipeline 未产出假说链，检查上游步骤是否正常")

        evaluation = PipelineEvaluation(
            evidence_sufficiency=round(ev_sufficiency, 3),
            probability_coherence=round(prob_coherence, 3),
            chain_diversity=round(chain_diversity, 3),
            overall_confidence=round(max(0.0, min(1.0, overall)), 3),
            weaknesses=all_weaknesses,
            recommended_actions=recommended,
        )

        logger.info(
            "Pipeline evaluation: overall=%.2f evidence=%.2f coherence=%.2f diversity=%.2f weaknesses=%d",
            evaluation.overall_confidence,
            evaluation.evidence_sufficiency,
            evaluation.probability_coherence,
            evaluation.chain_diversity,
            len(evaluation.weaknesses),
        )

        ctx.evaluation = evaluation
        return ctx
