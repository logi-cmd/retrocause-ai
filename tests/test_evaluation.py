from __future__ import annotations

from retrocause.evaluation import (
    EvaluationStep,
    PipelineEvaluation,
    _assess_chain_diversity,
    _assess_evidence_quality,
    _assess_evidence_sufficiency,
    _assess_probability_coherence,
)
from retrocause.models import CausalEdge, CausalVariable, HypothesisChain
from retrocause.pipeline import PipelineContext


def _make_chain(
    chain_id: str = "h1",
    path_prob: float = 0.7,
    posterior: float = 0.6,
    coverage: float = 0.8,
    ci: tuple[float, float] = (0.4, 0.8),
    variables: list[CausalVariable] | None = None,
    edges: list[CausalEdge] | None = None,
    unanchored: list[str] | None = None,
) -> HypothesisChain:
    return HypothesisChain(
        id=chain_id,
        name=f"chain_{chain_id}",
        description=f"test chain {chain_id}",
        path_probability=path_prob,
        posterior_probability=posterior,
        confidence_interval=ci,
        evidence_coverage=coverage,
        variables=variables or [CausalVariable(name="a", description="var a")],
        edges=edges or [],
        unanchored_edges=unanchored or [],
    )


def _make_ctx(**overrides) -> PipelineContext:
    defaults = dict(
        query="test",
        domain="test",
        hypotheses=[],
        total_evidence_count=5,
    )
    defaults.update(overrides)
    return PipelineContext(**defaults)


def test_evidence_sufficiency_good():
    ctx = _make_ctx(hypotheses=[_make_chain(coverage=0.8)], total_evidence_count=10)
    score, weaknesses = _assess_evidence_sufficiency(ctx)
    assert score > 0.5
    assert not weaknesses


def test_evidence_sufficiency_no_evidence():
    ctx = _make_ctx(total_evidence_count=0, hypotheses=[_make_chain(coverage=0.0)])
    score, weaknesses = _assess_evidence_sufficiency(ctx)
    assert score == 0.0
    assert any("No evidence was collected" in w for w in weaknesses)


def test_evidence_sufficiency_no_hypotheses():
    ctx = _make_ctx(hypotheses=[], total_evidence_count=5)
    score, weaknesses = _assess_evidence_sufficiency(ctx)
    assert score == 0.0
    assert any("No hypothesis chains were produced" in w for w in weaknesses)


def test_evidence_sufficiency_low_coverage():
    ctx = _make_ctx(hypotheses=[_make_chain(coverage=0.2)])
    score, weaknesses = _assess_evidence_sufficiency(ctx)
    assert any("coverage below" in w for w in weaknesses)


def test_evidence_sufficiency_many_unanchored():
    edges = [CausalEdge(source=f"s{i}", target=f"t{i}", conditional_prob=0.5) for i in range(6)]
    ctx = _make_ctx(
        hypotheses=[_make_chain(edges=edges, unanchored=["s0_t0", "s1_t1", "s2_t2", "s3_t3"])],
        total_evidence_count=2,
    )
    score, weaknesses = _assess_evidence_sufficiency(ctx)
    assert any("unanchored" in w for w in weaknesses)


def test_evidence_quality_penalizes_fallback_summaries():
    ctx = _make_ctx()
    ctx.extra["evidences"] = [
        type("Ev", (), {"extraction_method": "fallback_summary", "freshness": "unknown"})(),
        type("Ev", (), {"extraction_method": "fallback_summary", "freshness": "unknown"})(),
        type("Ev", (), {"extraction_method": "llm", "freshness": "stable"})(),
    ]
    score, weaknesses = _assess_evidence_quality(ctx)
    assert score < 0.7
    assert any("Fallback-summary evidence" in w for w in weaknesses)


def test_probability_coherence_good():
    ctx = _make_ctx(hypotheses=[_make_chain(path_prob=0.7, posterior=0.6, ci=(0.4, 0.8))])
    score, weaknesses = _assess_probability_coherence(ctx)
    assert score == 1.0
    assert not weaknesses


def test_probability_coherence_out_of_range():
    ctx = _make_ctx(hypotheses=[_make_chain(path_prob=1.5, posterior=0.5, ci=(0.3, 0.7))])
    score, weaknesses = _assess_probability_coherence(ctx)
    assert score < 1.0
    assert any("incoherent probabilities" in w for w in weaknesses)


def test_probability_coherence_bad_ci():
    ctx = _make_ctx(hypotheses=[_make_chain(posterior=0.5, ci=(0.8, 0.3))])
    score, weaknesses = _assess_probability_coherence(ctx)
    assert any("invalid confidence interval" in w for w in weaknesses)


def test_probability_coherence_posterior_sum_drift():
    h1 = _make_chain(chain_id="h1", posterior=0.8)
    h2 = _make_chain(chain_id="h2", posterior=0.8)
    ctx = _make_ctx(hypotheses=[h1, h2])
    score, weaknesses = _assess_probability_coherence(ctx)
    assert any("drift too far from 1.0" in w for w in weaknesses)


def test_probability_coherence_no_hypotheses():
    ctx = _make_ctx(hypotheses=[])
    score, weaknesses = _assess_probability_coherence(ctx)
    assert score == 0.0


def test_chain_diversity_single_chain():
    ctx = _make_ctx(hypotheses=[_make_chain()])
    score, weaknesses = _assess_chain_diversity(ctx)
    assert score == 1.0
    assert not weaknesses


def test_chain_diversity_no_chains():
    ctx = _make_ctx(hypotheses=[])
    score, weaknesses = _assess_chain_diversity(ctx)
    assert score == 0.0


def test_chain_diversity_diverse():
    h1 = _make_chain(chain_id="h1", variables=[CausalVariable(name="asteroid", description="")])
    h2 = _make_chain(chain_id="h2", variables=[CausalVariable(name="volcano", description="")])
    ctx = _make_ctx(hypotheses=[h1, h2])
    score, weaknesses = _assess_chain_diversity(ctx)
    assert score > 0.5
    assert not weaknesses


def test_chain_diversity_too_similar():
    vars_a = [CausalVariable(name=f"v{i}", description="") for i in range(5)]
    vars_b = [CausalVariable(name=f"v{i}", description="") for i in range(5)]
    h1 = _make_chain(chain_id="h1", variables=vars_a)
    h2 = _make_chain(chain_id="h2", variables=vars_b)
    ctx = _make_ctx(hypotheses=[h1, h2])
    score, weaknesses = _assess_chain_diversity(ctx)
    assert score < 0.2
    assert any("too similar" in w for w in weaknesses)


def test_evaluation_step_populates_ctx():
    ctx = _make_ctx(hypotheses=[_make_chain(coverage=0.9, path_prob=0.7, posterior=0.6)], total_evidence_count=10)
    ctx.extra["evidences"] = [type("Ev", (), {"extraction_method": "llm", "freshness": "stable"})()]
    ctx = EvaluationStep().execute(ctx)

    assert ctx.evaluation is not None
    assert isinstance(ctx.evaluation, PipelineEvaluation)
    assert 0.0 <= ctx.evaluation.overall_confidence <= 1.0
    assert ctx.evaluation.evidence_sufficiency > 0.5
    assert ctx.evaluation.probability_coherence == 1.0


def test_evaluation_step_empty_pipeline():
    ctx = _make_ctx(hypotheses=[], total_evidence_count=0)
    ctx = EvaluationStep().execute(ctx)

    assert ctx.evaluation is not None
    assert ctx.evaluation.overall_confidence < 0.3
    assert len(ctx.evaluation.weaknesses) >= 2
    assert len(ctx.evaluation.recommended_actions) >= 2


def test_evaluation_step_with_step_errors():
    ctx = _make_ctx(hypotheses=[_make_chain(coverage=0.7)], total_evidence_count=5)
    ctx.extra["evidences"] = [type("Ev", (), {"extraction_method": "llm", "freshness": "stable"})()]
    ctx.step_errors.append({"step": "GraphBuildingStep", "error": "LLM timeout"})
    ctx = EvaluationStep().execute(ctx)

    assert ctx.evaluation is not None
    assert any("step errors" in w for w in ctx.evaluation.weaknesses)
    assert ctx.evaluation.overall_confidence < 0.9


def test_evaluation_step_recommended_actions():
    ctx = _make_ctx(hypotheses=[_make_chain(coverage=0.2)], total_evidence_count=1)
    ctx.extra["evidences"] = [
        type("Ev", (), {"extraction_method": "fallback_summary", "freshness": "unknown"})()
    ]
    ctx = EvaluationStep().execute(ctx)

    assert ctx.evaluation is not None
    assert any("evidence" in action.lower() for action in ctx.evaluation.recommended_actions)
