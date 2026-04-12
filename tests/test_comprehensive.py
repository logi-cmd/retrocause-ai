"""全面边界测试 — API schema、空输入、极端值、类型安全、demo topic 覆盖"""

from __future__ import annotations

import pytest

from retrocause.api.main import (
    AnalyzeRequest,
    AnalyzeResponseV2,
    EvidenceBindingV2,
    GraphNodeV2,
    GraphEdgeV2,
    HypothesisChainV2,
    PipelineEvaluationV2,
    analyze_query_v2,
    _result_to_v2,
)
from retrocause.app.demo_data import (
    PROVIDERS,
    detect_demo_topic,
    topic_aware_demo_result,
)
from retrocause.evaluation import (
    EvaluationStep,
    PipelineEvaluation,
    _assess_probability_coherence,
    _assess_chain_diversity,
)
from retrocause.models import (
    AnalysisResult,
    CausalEdge,
    CausalVariable,
    HypothesisChain,
    HypothesisStatus,
)
from retrocause.pipeline import Pipeline, PipelineContext


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Demo topic 覆盖测试
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "query, expected_topic",
    [
        ("Why did SVB collapse?", "svb"),
        ("What caused the SVB bank failure?", "svb"),
        ("SVB倒闭的原因是什么？", "svb"),
        ("为什么某股票暴跌？", "stock"),
        ("What caused the stock market crash?", "stock"),
        ("Why did the 2008 financial crisis happen?", "crisis"),
        ("2008年金融危机的原因", "crisis"),
        ("Why is rent so high in New York?", "rent"),
        ("纽约房租为什么这么贵", "rent"),
        ("Why did dinosaurs go extinct?", None),  # default → None
        ("Some random unrelated question", None),
    ],
)
def test_detect_demo_topic_all_cases(query, expected_topic):
    topic = detect_demo_topic(query)
    assert topic == expected_topic, f"query={query!r}: expected {expected_topic}, got {topic}"


def test_topic_aware_demo_result_svb():
    result = topic_aware_demo_result("Why did SVB collapse?")
    assert result.domain == "finance"
    assert result.hypotheses[0].id == "demo_svb_primary"
    assert any(v.name == "svb_collapse" for v in result.variables)


def test_topic_aware_demo_result_stock():
    result = topic_aware_demo_result("为什么某股票暴跌？")
    assert result.domain == "finance"
    assert result.hypotheses[0].id == "demo_stock_primary"


def test_topic_aware_demo_result_crisis():
    result = topic_aware_demo_result("2008 financial crisis causes")
    assert result.domain == "finance"
    assert result.hypotheses[0].id == "demo_crisis_primary"


def test_topic_aware_demo_result_rent():
    result = topic_aware_demo_result("Why is rent so high?")
    assert result.domain == "economics"
    assert result.hypotheses[0].id == "demo_rent_primary"


def test_topic_aware_demo_result_default():
    result = topic_aware_demo_result("Why did dinosaurs go extinct?")
    assert result.domain == "paleontology"
    # default demo should still produce valid result
    assert len(result.hypotheses) >= 1
    assert len(result.variables) > 0
    assert len(result.edges) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. API Schema 验证 — V2 转换
# ═══════════════════════════════════════════════════════════════════════════════


def _make_minimal_result() -> AnalysisResult:
    """构造最小有效 AnalysisResult"""
    return AnalysisResult(
        query="test query",
        domain="general",
        variables=[
            CausalVariable(name="var_a", description="Cause A", posterior_support=0.8),
            CausalVariable(name="var_b", description="Effect B", posterior_support=0.6),
        ],
        edges=[
            CausalEdge(source="var_a", target="var_b", conditional_prob=0.7),
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Test Chain",
                description="A test chain",
                variables=[
                    CausalVariable(name="var_a", description="Cause A", posterior_support=0.8),
                    CausalVariable(name="var_b", description="Effect B", posterior_support=0.6),
                ],
                edges=[
                    CausalEdge(source="var_a", target="var_b", conditional_prob=0.7),
                ],
                path_probability=0.7,
                posterior_probability=0.6,
                evidence_coverage=0.5,
                counterfactual_score=0.4,
            ),
        ],
    )


def test_result_to_v2_minimal():
    result = _make_minimal_result()
    v2 = _result_to_v2(result, is_demo=True, demo_topic="test")

    assert v2.query == "test query"
    assert v2.is_demo is True
    assert v2.demo_topic == "test"
    assert v2.analysis_mode == "demo"
    assert v2.freshness_status == "unknown"
    assert len(v2.chains) == 1
    assert v2.chains[0].chain_id == "chain-1"
    assert v2.chains[0].probability == 0.6
    assert v2.recommended_chain_id == "chain-1"
    assert v2.evaluation is None  # no evaluation on minimal result


def test_result_to_v2_with_evaluation():
    result = _make_minimal_result()
    result.evaluation = PipelineEvaluation(
        evidence_sufficiency=0.7,
        probability_coherence=0.85,
        chain_diversity=0.6,
        overall_confidence=0.72,
        weaknesses=["weak evidence"],
        recommended_actions=["add more sources"],
    )
    v2 = _result_to_v2(result, is_demo=False)

    assert v2.is_demo is False
    assert v2.evaluation is not None
    assert v2.evaluation.evidence_sufficiency == 0.7
    assert v2.evaluation.probability_coherence == 0.85
    assert v2.evaluation.chain_diversity == 0.6
    assert v2.evaluation.overall_confidence == 0.72
    assert "weak evidence" in v2.evaluation.weaknesses
    assert "add more sources" in v2.evaluation.recommended_actions


def test_result_to_v2_empty_hypotheses():
    result = AnalysisResult(
        query="empty test",
        domain="general",
        variables=[],
        edges=[],
        hypotheses=[],
    )
    v2 = _result_to_v2(result, is_demo=True, demo_topic="default")

    assert v2.query == "empty test"
    assert len(v2.chains) == 0
    assert v2.recommended_chain_id is None
    assert len(v2.evidences) == 0


def test_result_to_v2_multiple_chains():
    result = AnalysisResult(
        query="multi chain",
        domain="general",
        variables=[
            CausalVariable(name="a", description="A"),
            CausalVariable(name="b", description="B"),
            CausalVariable(name="c", description="C"),
        ],
        edges=[
            CausalEdge(source="a", target="b", conditional_prob=0.8),
            CausalEdge(source="a", target="c", conditional_prob=0.5),
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-low",
                name="Low Prob Chain",
                description="Low",
                variables=[
                    CausalVariable(name="a", description="A"),
                    CausalVariable(name="b", description="B"),
                ],
                edges=[CausalEdge(source="a", target="b", conditional_prob=0.8)],
                path_probability=0.3,
                posterior_probability=0.3,
            ),
            HypothesisChain(
                id="chain-high",
                name="High Prob Chain",
                description="High",
                variables=[
                    CausalVariable(name="a", description="A"),
                    CausalVariable(name="c", description="C"),
                ],
                edges=[CausalEdge(source="a", target="c", conditional_prob=0.5)],
                path_probability=0.8,
                posterior_probability=0.7,
            ),
        ],
    )
    v2 = _result_to_v2(result, is_demo=False)
    assert v2.recommended_chain_id == "chain-high"


def test_result_to_v2_node_types():
    result = _make_minimal_result()
    v2 = _result_to_v2(result)
    nodes = v2.chains[0].nodes
    node_types = {n.id: n.type for n in nodes}
    # var_a has no upstream → "cause"
    # var_b has no downstream → "effect"
    assert node_types["var_a"] == "cause"
    assert node_types["var_b"] == "effect"


def test_result_to_v2_infers_time_range_from_query():
    result = _make_minimal_result()
    result.query = "Why did this stock fall today?"
    v2 = _result_to_v2(result)
    assert v2.time_range == "today"


def test_result_to_v2_partial_live_reasons_follow_evaluation():
    result = _make_minimal_result()
    result.analysis_mode = "partial_live"
    result.freshness_status = "stable"
    result.evaluation = PipelineEvaluationV2.model_validate(
        {
            "evidence_sufficiency": 0.4,
            "probability_coherence": 0.8,
            "chain_diversity": 0.5,
            "overall_confidence": 0.55,
            "weaknesses": ["Fallback-summary evidence dominates the run (3/4 items)."],
            "recommended_actions": ["Reduce fallback-summary evidence."],
        }
    )
    # Convert back to the dataclass-like shape expected by _result_to_v2.
    from retrocause.evaluation import PipelineEvaluation

    result.evaluation = PipelineEvaluation(
        evidence_sufficiency=result.evaluation.evidence_sufficiency,
        probability_coherence=result.evaluation.probability_coherence,
        chain_diversity=result.evaluation.chain_diversity,
        overall_confidence=result.evaluation.overall_confidence,
        weaknesses=result.evaluation.weaknesses,
        recommended_actions=result.evaluation.recommended_actions,
    )
    v2 = _result_to_v2(result)
    assert v2.partial_live_reasons
    assert "Fallback-summary evidence dominates the run" in v2.partial_live_reasons[0]


@pytest.mark.anyio
async def test_analyze_query_v2_returns_partial_live_instead_of_demo_on_live_failure(monkeypatch):
    def _fail_run_real_analysis(*args, **kwargs):
        raise RuntimeError("401 User not found.")

    monkeypatch.setattr("retrocause.app.demo_data.run_real_analysis", _fail_run_real_analysis)

    request = AnalyzeRequest(
        query="为什么美国会同意与伊朗进行首轮谈判？",
        model="openrouter",
        api_key="sk-test",
        explicit_model="openai/gpt-4o-mini",
    )
    response = await analyze_query_v2(request)
    assert response.is_demo is False
    assert response.analysis_mode == "partial_live"
    assert response.error is not None
    assert response.chains == []


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Pydantic Schema 验证 — 确保 API 模型能正确序列化
# ═══════════════════════════════════════════════════════════════════════════════


def test_v2_schema_round_trip():
    """验证 V2 schema 可以正确序列化/反序列化"""
    v2 = AnalyzeResponseV2(
        query="test",
        is_demo=True,
        demo_topic="svb",
        time_range="today",
        partial_live_reasons=[],
        recommended_chain_id="chain-1",
        chains=[
            HypothesisChainV2(
                chain_id="chain-1",
                label="Test",
                description="A test chain",
                probability=0.8,
                nodes=[
                    GraphNodeV2(
                        id="a",
                        label="A",
                        description="Cause A",
                        probability=0.9,
                        type="cause",
                        depth=0,
                        upstream_ids=[],
                        supporting_evidence_ids=[],
                        refuting_evidence_ids=[],
                    ),
                ],
                edges=[
                    GraphEdgeV2(
                        id="a_b",
                        source="a",
                        target="b",
                        strength=0.7,
                        type="causes",
                        supporting_evidence_ids=[],
                        refuting_evidence_ids=[],
                    ),
                ],
                supporting_evidence_ids=[],
                refuting_evidence_ids=[],
                counterfactual={"items": [], "overall_confidence": 0.0},
                depth=1,
            ),
        ],
        evidences=[
            EvidenceBindingV2(
                id="ev1",
                content="Test evidence",
                source="test",
                reliability="0.80",
                is_supporting=True,
                source_tier="base",
                freshness="stable",
                extraction_method="manual",
            ),
        ],
        upstream_map={"entries": []},
        evaluation=PipelineEvaluationV2(
            evidence_sufficiency=0.6,
            probability_coherence=0.8,
            chain_diversity=0.5,
            overall_confidence=0.63,
            weaknesses=["low diversity"],
            recommended_actions=["generate more chains"],
        ),
    )
    # Should serialize without error
    json_str = v2.model_dump_json()
    parsed = AnalyzeResponseV2.model_validate_json(json_str)
    assert parsed.query == "test"
    assert parsed.time_range == "today"
    assert parsed.partial_live_reasons == []
    assert parsed.evaluation.overall_confidence == 0.63
    assert parsed.evidences[0].source_tier == "base"
    assert parsed.evidences[0].freshness == "stable"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Pipeline Evaluation 边界
# ═══════════════════════════════════════════════════════════════════════════════


def test_evaluation_all_scores_bounded():
    """All evaluation scores must be in [0.0, 1.0]"""
    step = EvaluationStep()
    ctx = PipelineContext(query="test")
    ctx = step.execute(ctx)

    ev = ctx.evaluation
    assert ev is not None
    assert 0.0 <= ev.evidence_sufficiency <= 1.0
    assert 0.0 <= ev.probability_coherence <= 1.0
    assert 0.0 <= ev.chain_diversity <= 1.0
    assert 0.0 <= ev.overall_confidence <= 1.0


def test_evaluation_step_errors_penalty():
    """step_errors should reduce overall_confidence"""
    ctx_good = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=[CausalVariable(name="a", description="A")],
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
                evidence_coverage=0.8,
            ),
        ],
        total_evidence_count=5,
    )
    step = EvaluationStep()
    ctx_good = step.execute(ctx_good)
    score_good = ctx_good.evaluation.overall_confidence

    ctx_bad = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=[CausalVariable(name="a", description="A")],
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
                evidence_coverage=0.8,
            ),
        ],
        total_evidence_count=5,
        step_errors=[{"step": "x", "error": "fail"}],
    )
    ctx_bad = step.execute(ctx_bad)
    score_bad = ctx_bad.evaluation.overall_confidence

    assert score_bad < score_good, f"Errors should reduce confidence: {score_bad} >= {score_good}"


def test_probability_coherence_rejects_negative_ci():
    ctx = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=[],
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
                confidence_interval=(0.8, 0.2),  # lo > hi → incoherent
            ),
        ],
    )
    score, weaknesses = _assess_probability_coherence(ctx)
    assert score < 1.0
    assert any("异常" in w or "不自洽" in w for w in weaknesses)


def test_chain_diversity_identical_chains():
    vars_a = [CausalVariable(name=f"v{i}", description=f"V{i}") for i in range(3)]
    ctx = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=vars_a,
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
            ),
            HypothesisChain(
                id="h2",
                name="H2",
                description="Test",
                variables=vars_a,
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
            ),
        ],
    )
    score, weaknesses = _assess_chain_diversity(ctx)
    assert score == 0.0, f"Identical chains should have 0 diversity, got {score}"
    assert len(weaknesses) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Providers 配置验证
# ═══════════════════════════════════════════════════════════════════════════════


def test_providers_have_required_keys():
    assert "openrouter" in PROVIDERS
    assert "openai" in PROVIDERS
    assert "dashscope" in PROVIDERS
    for name, cfg in PROVIDERS.items():
        assert "base_url" in cfg, f"Provider {name} missing base_url"
        assert "models" in cfg, f"Provider {name} missing models"
        assert isinstance(cfg["models"], dict), f"Provider {name} models must be dict"
        assert len(cfg["models"]) > 0, f"Provider {name} has no models"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Models 数据类验证
# ═══════════════════════════════════════════════════════════════════════════════


def test_analysis_result_defaults():
    r = AnalysisResult(
        query="test",
        domain="general",
        variables=[],
        edges=[],
        hypotheses=[],
    )
    assert r.is_demo is False
    assert r.demo_topic is None
    assert r.evaluation is None
    assert r.analysis_mode == "live"
    assert r.freshness_status == "unknown"
    assert r.total_evidence_count == 0
    assert r.total_uncertainty == 0.0
    assert r.recommended_next_steps == []


def test_hypothesis_chain_defaults():
    h = HypothesisChain(
        id="h1",
        name="Test",
        description="A test chain",
    )
    assert h.status == HypothesisStatus.ACTIVE
    assert h.counterfactual_score == 0.0
    assert h.evidence_coverage == 0.0
    assert h.debate_rounds == []


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Pipeline 空运行
# ═══════════════════════════════════════════════════════════════════════════════


def test_pipeline_empty_steps():
    p = Pipeline()
    ctx = p.run()
    assert ctx.query == ""
    assert ctx.step_errors == []


def test_pipeline_step_failure_captured():
    class FailStep:
        @property
        def name(self):
            return "FailStep"

        @property
        def checkpoint(self):
            return False

        def execute(self, ctx):
            raise RuntimeError("intentional failure")

    p = Pipeline(steps=[FailStep()])
    ctx = p.run(PipelineContext(query="fail test"))
    assert len(ctx.step_errors) == 1
    assert ctx.step_errors[0]["step"] == "FailStep"
    assert "intentional failure" in ctx.step_errors[0]["error"]


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Demo 结果完整性和一致性
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "query",
    [
        "Why did SVB collapse?",
        "为什么某股票暴跌？",
        "2008 financial crisis",
        "Why is rent so high?",
        "Why did dinosaurs go extinct?",
    ],
)
def test_demo_result_completeness(query):
    """Every demo result must have non-empty hypotheses, variables, and edges"""
    result = topic_aware_demo_result(query)
    assert result.query == query
    assert len(result.hypotheses) >= 1, f"No hypotheses for: {query}"
    assert len(result.variables) >= 2, f"Too few variables for: {query}"
    assert len(result.edges) >= 1, f"No edges for: {query}"

    for h in result.hypotheses:
        assert h.id, "Hypothesis must have an id"
        assert h.name, "Hypothesis must have a name"
        assert len(h.variables) > 0, f"Chain {h.id} has no variables"
        assert len(h.edges) > 0, f"Chain {h.id} has no edges"
        assert 0.0 <= h.path_probability <= 1.0
        assert 0.0 <= h.posterior_probability <= 1.0


def test_demo_result_edges_reference_valid_variables():
    """All edge source/target must reference existing variables"""
    result = topic_aware_demo_result("Why did SVB collapse?")
    var_names = {v.name for v in result.variables}
    for edge in result.edges:
        assert edge.source in var_names, f"Edge source {edge.source} not in variables"
        assert edge.target in var_names, f"Edge target {edge.target} not in variables"


def test_demo_result_hypothesis_variables_match_result_variables():
    """Hypothesis chain variables must be a subset of result variables"""
    result = topic_aware_demo_result("Why did SVB collapse?")
    result_var_names = {v.name for v in result.variables}
    for h in result.hypotheses:
        hyp_var_names = {v.name for v in h.variables}
        assert hyp_var_names.issubset(result_var_names), (
            f"Chain {h.id} has variables not in result: {hyp_var_names - result_var_names}"
        )
