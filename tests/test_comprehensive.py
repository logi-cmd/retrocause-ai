"""全面边界测试 — API schema、空输入、极端值、类型安全、demo topic 覆盖"""

from __future__ import annotations

import pytest
from pathlib import Path

from retrocause.api.main import (
    AnalyzeRequest,
    AnalyzeResponseV2,
    EvidenceBindingV2,
    GraphNodeV2,
    GraphEdgeV2,
    HypothesisChainV2,
    PipelineEvaluationV2,
    ProviderPreflightRequest,
    analyze_query_v2,
    preflight_provider,
    _build_product_harness,
    _detect_production_scenario,
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
from retrocause.evidence_access import SourceAttempt
from retrocause.models import (
    AnalysisResult,
    CausalEdge,
    CausalVariable,
    Evidence,
    EvidenceType,
    HypothesisChain,
    HypothesisStatus,
)
from retrocause.pipeline import Pipeline, PipelineContext


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def _sample_result_with_one_supported_chain(query: str) -> AnalysisResult:
    return AnalysisResult(
        query=query,
        domain="general",
        variables=[
            CausalVariable(name="primary_driver", description="Primary driver"),
            CausalVariable(name="observed_outcome", description="Observed outcome"),
        ],
        edges=[
            CausalEdge(
                source="primary_driver",
                target="observed_outcome",
                conditional_prob=0.72,
                supporting_evidence_ids=["ev-support"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Primary supported explanation",
                description="A supported driver explains the observed outcome.",
                variables=[
                    CausalVariable(name="primary_driver", description="Primary driver"),
                    CausalVariable(name="observed_outcome", description="Observed outcome"),
                ],
                edges=[
                    CausalEdge(
                        source="primary_driver",
                        target="observed_outcome",
                        conditional_prob=0.72,
                        supporting_evidence_ids=["ev-support"],
                    )
                ],
                posterior_probability=0.66,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Source evidence links the primary driver to the observed outcome.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            )
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


def test_detects_market_production_scenario():
    scenario = _detect_production_scenario(
        "Why did bitcoin fall today after ETF outflows and rate headlines?"
    )

    assert scenario.key == "market"
    assert 0 <= scenario.confidence <= 1
    assert "market" in scenario.user_value.lower()


def test_detects_policy_geopolitics_production_scenario():
    scenario = _detect_production_scenario(
        "Why did the ceasefire talks fail after the latest sanctions announcement?"
    )

    assert scenario.key == "policy_geopolitics"
    assert 0 <= scenario.confidence <= 1
    assert "policy" in scenario.user_value.lower() or "geopolitical" in scenario.user_value.lower()


def test_detects_postmortem_production_scenario():
    scenario = _detect_production_scenario(
        "Why did our checkout conversion drop after the release incident?"
    )

    assert scenario.key == "postmortem"
    assert 0 <= scenario.confidence <= 1
    assert "incident" in scenario.user_value.lower() or "postmortem" in scenario.user_value.lower()


def test_scenario_override_wins_over_auto_detection():
    scenario = _detect_production_scenario(
        "Why did bitcoin fall today?",
        override="postmortem",
    )

    assert scenario.key == "postmortem"
    assert scenario.detection_method == "override"


def test_market_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)

    assert response.scenario is not None
    assert response.scenario.key == "market"
    assert response.production_brief is not None
    titles = [section.title for section in response.production_brief.sections]
    assert "Market Drivers" in titles
    assert "What Would Change The View" in titles
    assert all(
        item.evidence_ids
        for section in response.production_brief.sections
        for item in section.items
        if section.kind not in {"limits", "verification"}
    )


def test_policy_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain("Why did the ceasefire talks fail?")
    response = _result_to_v2(result, is_demo=False)

    assert response.scenario is not None
    assert response.scenario.key == "policy_geopolitics"
    assert response.production_brief is not None
    assert "Negotiation Constraints" in [
        section.title for section in response.production_brief.sections
    ]


def test_postmortem_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain(
        "Why did our checkout conversion drop after the release incident?"
    )
    response = _result_to_v2(result, is_demo=False)

    assert response.scenario is not None
    assert response.scenario.key == "postmortem"
    assert response.production_brief is not None
    assert "Operational Causes" in [section.title for section in response.production_brief.sections]


def test_recent_market_result_needs_fresh_evidence_before_ready():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    result.freshness_status = "stale"
    response = _result_to_v2(result, is_demo=False)

    assert response.production_harness is not None
    assert response.production_harness.status == "needs_more_evidence"
    assert any(
        check.name == "freshness_gate" and not check.passed
        for check in response.production_harness.checks
    )


def test_policy_result_with_weak_source_trace_surfaces_source_risk():
    result = _sample_result_with_one_supported_chain("Why did sanctions talks fail today?")
    result.retrieval_trace = [
        {
            "source": "web_search",
            "query": "sanctions talks failed",
            "result_count": 1,
            "cache_hit": False,
        }
    ]
    response = _result_to_v2(result, is_demo=False)

    assert response.production_harness is not None
    assert any(check.name == "source_risk" for check in response.production_harness.checks)


def test_retrieval_trace_exposes_degraded_source_metadata():
    result = _sample_result_with_one_supported_chain(
        "Why did US Iran talks in Islamabad end without agreement?"
    )
    result.retrieval_trace = [
        SourceAttempt(
            name="ap_news",
            query="US Iran Islamabad talks no agreement AP",
            result_count=0,
            cache_hit=False,
            error="rate_limited",
            status="rate_limited",
            retry_after_seconds=7,
            source_label="AP News",
            source_kind="wire_news",
            stability="high",
            cache_policy="short_lived_cache_allowed",
        ),
        {
            "source": "web",
            "query": "US Iran Islamabad talks no agreement",
            "result_count": 2,
            "cache_hit": True,
            "status": "cached",
            "source_label": "Trusted web search",
            "source_kind": "web_search",
            "stability": "medium",
            "cache_policy": "derived_cache_allowed",
        },
    ]

    response = _result_to_v2(result, is_demo=False)

    degraded = response.retrieval_trace[0]
    assert degraded.source == "ap_news"
    assert degraded.status == "rate_limited"
    assert degraded.retry_after_seconds == 7
    assert degraded.source_kind == "wire_news"
    assert degraded.stability == "high"
    assert degraded.cache_policy == "short_lived_cache_allowed"

    cached = response.retrieval_trace[1]
    assert cached.status == "cached"
    assert cached.cache_policy == "derived_cache_allowed"
    assert cached.cache_hit is True

    assert response.markdown_brief is not None
    assert "status: rate-limited" in response.markdown_brief
    assert "retry after 7s" in response.markdown_brief
    assert "cache policy: short_lived_cache_allowed" in response.markdown_brief


def test_degraded_source_drill_surfaces_all_limited_states_for_review():
    result = _sample_result_with_one_supported_chain(
        "Why did US Iran talks in Islamabad end without agreement?"
    )
    result.retrieval_trace = [
        {
            "source": "ap_news",
            "query": "US Iran Islamabad talks AP",
            "result_count": 0,
            "cache_hit": False,
            "status": "rate_limited",
            "retry_after_seconds": 30,
            "source_label": "AP News",
            "source_kind": "wire_news",
            "stability": "high",
            "cache_policy": "short_lived_cache_allowed",
        },
        {
            "source": "federal_register",
            "query": "US Iran official sanctions register",
            "result_count": 0,
            "cache_hit": False,
            "status": "forbidden",
            "source_label": "Federal Register",
            "source_kind": "official_record",
            "stability": "high",
            "cache_policy": "public_record_cache_allowed",
        },
        {
            "source": "gdelt",
            "query": "US Iran talks timeout",
            "result_count": 0,
            "cache_hit": False,
            "status": "timeout",
            "source_label": "GDELT",
            "source_kind": "news_index",
            "stability": "medium",
            "cache_policy": "short_lived_cache_allowed",
        },
        {
            "source": "brave",
            "query": "US Iran talks broad web",
            "result_count": 0,
            "cache_hit": False,
            "status": "source_error",
            "source_label": "Brave Search",
            "source_kind": "web_search",
            "stability": "medium",
            "cache_policy": "transient_results_only",
        },
        {
            "source": "tavily",
            "query": "US Iran talks fallback",
            "result_count": 0,
            "cache_hit": False,
            "status": "source_limited",
            "source_label": "Tavily Search",
            "source_kind": "hosted_search",
            "stability": "medium",
            "cache_policy": "derived_cache_allowed",
        },
        {
            "source": "web",
            "query": "US Iran talks cached evidence",
            "result_count": 3,
            "cache_hit": True,
            "status": "cached",
            "source_label": "Trusted web search",
            "source_kind": "web_search",
            "stability": "medium",
            "cache_policy": "derived_cache_allowed",
        },
    ]

    response = _result_to_v2(result, is_demo=False)

    assert response.analysis_brief is not None
    assert "6 source attempt(s), 5 degraded or limited" in response.analysis_brief.source_coverage
    assert response.markdown_brief is not None
    for status in [
        "status: rate-limited",
        "status: forbidden",
        "status: timeout",
        "status: source-error",
        "status: source-limited",
        "status: cached",
    ]:
        assert status in response.markdown_brief
    assert "retry after 30s" in response.markdown_brief
    assert "cache policy: transient_results_only" in response.markdown_brief


def test_postmortem_without_internal_evidence_is_not_actionable():
    result = _sample_result_with_one_supported_chain(
        "Why did our checkout conversion drop after the release incident?"
    )
    response = _result_to_v2(result, is_demo=False)

    assert response.production_harness is not None
    assert response.production_harness.status in {"needs_more_evidence", "not_actionable"}
    assert any(
        check.name == "internal_evidence" and not check.passed
        for check in response.production_harness.checks
    )


def test_result_to_v2_surfaces_refutation_status_and_stance():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="hardline_demands", description="Hardline demands"),
            CausalVariable(name="failed_talks", description="Failed talks"),
        ],
        edges=[
            CausalEdge(
                source="hardline_demands",
                target="failed_talks",
                conditional_prob=0.7,
                supporting_evidence_ids=["ev-support"],
                refuting_evidence_ids=["ev-refute"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-refute",
                name="Refuted chain",
                description="A chain with a challenge",
                variables=[
                    CausalVariable(name="hardline_demands", description="Hardline demands"),
                    CausalVariable(name="failed_talks", description="Failed talks"),
                ],
                edges=[
                    CausalEdge(
                        source="hardline_demands",
                        target="failed_talks",
                        conditional_prob=0.7,
                        supporting_evidence_ids=["ev-support"],
                        refuting_evidence_ids=["ev-refute"],
                    )
                ],
                posterior_probability=0.6,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Officials cited hardline demands as a cause.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
            ),
            Evidence(
                id="ev-refute",
                content="Officials denied that hardline demands caused the failure.",
                source_type=EvidenceType.NEWS,
                stance="refuting",
                stance_basis="llm_extraction",
            ),
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.chains[0].refutation_status == "has_refutation"
    assert v2.chains[0].edges[0].refutation_status == "has_refutation"
    refuting = next(item for item in v2.evidences if item.id == "ev-refute")
    assert refuting.is_supporting is False
    assert refuting.stance == "refuting"
    assert refuting.stance_basis == "llm_extraction"


def test_result_to_v2_marks_missing_refutation_coverage_honestly():
    result = _make_minimal_result()
    result.evidences = [
        Evidence(
            id="ev-support",
            content="A retrieved claim supports the explanation.",
            source_type=EvidenceType.NEWS,
            stance="supporting",
            stance_basis="llm_extraction",
        )
    ]
    result.hypotheses[0].edges[0].supporting_evidence_ids = ["ev-support"]

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.chains[0].refutation_status == "no_refutation_in_retrieved_evidence"


def test_result_to_v2_surfaces_challenge_checks_and_analysis_brief():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
            CausalVariable(name="talks_failed", description="Talks failed"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_pressure",
                target="talks_failed",
                conditional_prob=0.72,
                supporting_evidence_ids=["ev-support"],
                refuting_evidence_ids=["ev-refute"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions explanation",
                description="Sanctions pressure contributed to failure",
                variables=[
                    CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
                    CausalVariable(name="talks_failed", description="Talks failed"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_pressure",
                        target="talks_failed",
                        conditional_prob=0.72,
                        supporting_evidence_ids=["ev-support"],
                        refuting_evidence_ids=["ev-refute"],
                    )
                ],
                posterior_probability=0.64,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Diplomats linked sanctions pressure to the failed talks.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
            ),
            Evidence(
                id="ev-refute",
                content="Officials denied sanctions pressure was the reason talks failed.",
                source_type=EvidenceType.NEWS,
                stance="refuting",
                stance_basis="challenge_retrieval",
            ),
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_pressure->talks_failed",
                "source": "sanctions_pressure",
                "target": "talks_failed",
                "query": "why did talks fail evidence against sanctions pressure causing talks failed",
                "result_count": 1,
                "refuting_count": 1,
                "status": "has_refutation",
            }
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.challenge_checks[0].status == "has_refutation"
    assert v2.analysis_brief is not None
    assert "Sanctions explanation" in v2.analysis_brief.answer
    assert v2.analysis_brief.top_reasons
    assert v2.analysis_brief.challenge_summary.startswith("Found")
    assert v2.analysis_brief.missing_evidence


def test_result_to_v2_builds_copyable_markdown_research_brief():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
            CausalVariable(name="talks_failed", description="Talks failed"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_pressure",
                target="talks_failed",
                conditional_prob=0.72,
                supporting_evidence_ids=["ev-support"],
                refuting_evidence_ids=["ev-refute"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions explanation",
                description="Sanctions pressure contributed to failure",
                variables=[
                    CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
                    CausalVariable(name="talks_failed", description="Talks failed"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_pressure",
                        target="talks_failed",
                        conditional_prob=0.72,
                        supporting_evidence_ids=["ev-support"],
                        refuting_evidence_ids=["ev-refute"],
                    )
                ],
                posterior_probability=0.64,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Diplomats linked sanctions pressure to the failed talks.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            ),
            Evidence(
                id="ev-refute",
                content="Officials denied sanctions pressure was the reason talks failed.",
                source_type=EvidenceType.NEWS,
                stance="refuting",
                stance_basis="challenge_retrieval",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            ),
        ],
        retrieval_trace=[
            {
                "source": "ap_news",
                "query": "talks failed sanctions pressure",
                "result_count": 2,
                "cache_hit": False,
            }
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_pressure->talks_failed",
                "source": "sanctions_pressure",
                "target": "talks_failed",
                "query": "evidence against sanctions pressure causing talks failed",
                "result_count": 1,
                "refuting_count": 1,
                "status": "has_refutation",
            }
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.markdown_brief is not None
    assert v2.markdown_brief.startswith("# Policy / Geopolitics Brief")
    assert "## Question" in v2.markdown_brief
    assert "why did talks fail" in v2.markdown_brief
    assert "## Likely Explanation" in v2.markdown_brief
    assert "Sanctions explanation" in v2.markdown_brief
    assert "## Top Reasons" in v2.markdown_brief
    assert "Sanctions pressure -> Talks failed" in v2.markdown_brief
    assert "Challenge evidence on this edge: 1" in v2.markdown_brief
    assert "## Challenge Coverage" in v2.markdown_brief
    assert "Found 1 challenge evidence" in v2.markdown_brief
    assert "## Evidence" in v2.markdown_brief
    assert "[ev-support] Supports. Source: News." in v2.markdown_brief
    assert "[ev-refute] Challenges. Source: News." in v2.markdown_brief
    assert "EvidenceType.NEWS" not in v2.markdown_brief
    assert "## Source Trace" in v2.markdown_brief
    assert "AP News" in v2.markdown_brief


def test_markdown_brief_title_uses_detected_market_scenario():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)

    assert response.markdown_brief is not None
    assert response.markdown_brief.startswith("# Market / Investment Brief")


def test_markdown_brief_includes_production_verification_steps():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)

    assert response.markdown_brief is not None
    assert "## Production Brief" in response.markdown_brief
    assert "## Next Verification Steps" in response.markdown_brief
    assert "## Production Limits" in response.markdown_brief


def test_markdown_brief_explains_checked_edges_without_refuting_evidence():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
            CausalVariable(name="failed_agreement", description="No agreement"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_dispute",
                target="failed_agreement",
                conditional_prob=0.74,
                supporting_evidence_ids=["ev-support"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions and sequencing gap",
                description="Disagreement over sanctions relief and sequencing blocked agreement.",
                variables=[
                    CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
                    CausalVariable(name="failed_agreement", description="No agreement"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_dispute",
                        target="failed_agreement",
                        conditional_prob=0.74,
                        supporting_evidence_ids=["ev-support"],
                    )
                ],
                posterior_probability=0.68,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Officials said sanctions relief sequencing remained unresolved.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            )
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_dispute->failed_agreement",
                "source": "sanctions_dispute",
                "target": "failed_agreement",
                "query": "evidence against sanctions sequencing causing failed talks",
                "result_count": 2,
                "refuting_count": 0,
                "status": "checked_no_refuting_claims",
            }
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.markdown_brief is not None
    assert "No challenge evidence attached to this edge after targeted retrieval" in v2.markdown_brief
    assert "Challenge evidence on this edge: 0" not in v2.markdown_brief
    assert "0 challenge" not in v2.markdown_brief


def test_frontend_renders_readable_brief_instead_of_raw_markdown_copy():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert 'data-testid="readable-brief"' in page_source
    assert "Readable brief" in page_source
    assert "Top reasons" in page_source
    assert "What to check" in page_source
    assert 'data-testid="copy-report-button"' in page_source
    assert "Copy report" in page_source
    assert "Copy Markdown" not in page_source


def test_frontend_offers_manual_report_copy_fallback():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert 'data-testid="manual-copy-report"' in page_source
    assert "Manual copy" in page_source
    assert "select()" in page_source
    assert "readOnly" in page_source


def test_frontend_summarizes_source_transparency_in_readable_brief():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert 'data-testid="source-health-summary"' in page_source
    assert "Sources checked" in page_source
    assert "Stable sources" in page_source
    assert "Failed sources" in page_source


def test_frontend_surfaces_rate_limited_source_trace_language():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert "formatSourceStatusLabel" in page_source
    assert "Rate limited" in page_source
    assert "Source limited" in page_source
    assert "Timed out" in page_source
    assert "Source error" in page_source
    assert "retry_after_seconds" in page_source
    assert "data-testid=\"source-trace-status\"" in page_source
    assert "Reviewability" in page_source
    assert "Needs source attention" in page_source


def test_frontend_localizes_source_trace_status():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert "\\u53ef\\u7528" in page_source
    assert "\\u7f13\\u5b58" in page_source
    assert "\\u6765\\u6e90\\u53d7\\u9650" in page_source
    assert "\\u9650\\u6d41" in page_source
    assert "\\u65e0\\u6743\\u9650" in page_source
    assert "\\u8d85\\u65f6" in page_source
    assert "\\u6765\\u6e90\\u9519\\u8bef" in page_source


def test_frontend_renders_production_brief_and_use_case_selector():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert 'data-testid="scenario-selector"' in page_source
    assert 'data-testid="production-brief"' in page_source
    assert "scenario_override" in page_source
    assert "Production brief" in page_source


def test_frontend_offers_three_production_use_cases():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert "Market / Investment" in page_source
    assert "Policy / Geopolitics" in page_source
    assert "Postmortem" in page_source


def test_frontend_does_not_hardcode_single_case_product_labels():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    forbidden_terms = [
        "nuclear program",
        "negotiation refusal",
        "no deal reached",
        "iran",
        "united states",
    ]
    lowered = page_source.lower()
    for term in forbidden_terms:
        assert term not in lowered
    assert 'return "市场影响因素"' not in page_source
    assert "hasUnlocalizedEnglishLabel(localized)" not in page_source


def test_frontend_keeps_specific_live_node_labels():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert 'return "市场影响因素"' not in page_source
    assert "hasUnlocalizedEnglishLabel(localized)" not in page_source


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


@pytest.mark.anyio
async def test_analyze_v2_accepts_scenario_override_without_live_key():
    response = await analyze_query_v2(
        AnalyzeRequest(
            query="Why did bitcoin fall today?",
            scenario_override="postmortem",
        )
    )

    assert response.scenario is not None
    assert response.scenario.key == "postmortem"
    assert response.scenario.detection_method == "override"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Pydantic Schema 验证 — 确保 API 模型能正确序列化
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_multi_user_persona_outputs_are_actionable(monkeypatch):
    novice_response = await analyze_query_v2(
        AnalyzeRequest(query="Why did a product launch fail to convert trial users?")
    )

    assert novice_response.analysis_mode == "demo"
    assert novice_response.product_harness is not None
    assert novice_response.product_harness.status in {"ready_for_review", "needs_more_evidence"}
    assert novice_response.analysis_brief is not None
    assert novice_response.markdown_brief
    assert novice_response.product_harness.next_actions

    def _fail_run_real_analysis(*args, **kwargs):
        raise RuntimeError("401 invalid API key")

    monkeypatch.setattr("retrocause.app.demo_data.run_real_analysis", _fail_run_real_analysis)

    blocked_response = await analyze_query_v2(
        AnalyzeRequest(
            query="Why did Bitcoin move today?",
            model="openrouter",
            api_key="sk-test",
            explicit_model="deepseek/deepseek-chat-v3-0324",
        )
    )

    assert blocked_response.is_demo is False
    assert blocked_response.analysis_mode == "partial_live"
    assert blocked_response.product_harness is not None
    assert blocked_response.product_harness.status == "blocked_by_model"
    assert blocked_response.error is not None
    assert blocked_response.markdown_brief
    assert any("preflight" in action.lower() for action in blocked_response.product_harness.next_actions)


def test_multi_user_reviewer_can_audit_degraded_source_states():
    result = _sample_result_with_one_supported_chain(
        "Why did US Iran talks in Islamabad end without agreement?"
    )
    result.retrieval_trace = [
        {
            "source": "ap_news",
            "query": "US Iran Islamabad talks AP",
            "result_count": 0,
            "cache_hit": False,
            "status": "rate_limited",
            "retry_after_seconds": 30,
            "source_kind": "wire_news",
            "stability": "high",
            "cache_policy": "short_lived_cache_allowed",
        },
        {
            "source": "brave_search",
            "query": "US Iran talks sanctions disagreement",
            "result_count": 0,
            "cache_hit": False,
            "status": "forbidden",
            "source_kind": "hosted_search",
            "stability": "medium",
            "cache_policy": "transient_results_only",
        },
        {
            "source": "web_search",
            "query": "US Iran negotiations failed reasons",
            "result_count": 2,
            "cache_hit": False,
            "status": "ok",
            "source_kind": "general_search",
            "stability": "medium",
            "cache_policy": "short_lived_cache_allowed",
        },
    ]
    result.refutation_checks = [
        {
            "edge_id": "primary_driver->observed_outcome",
            "source": "primary_driver",
            "target": "observed_outcome",
            "query": "evidence against primary driver causing observed outcome",
            "result_count": 1,
            "refuting_count": 0,
            "status": "checked_no_refuting_claims",
        }
    ]

    response = _result_to_v2(result, is_demo=False)

    statuses = {item.source: item.status for item in response.retrieval_trace}
    assert statuses == {
        "ap_news": "rate_limited",
        "brave_search": "forbidden",
        "web_search": "ok",
    }
    assert response.product_harness is not None
    assert response.product_harness.status in {"ready_for_review", "needs_more_evidence"}
    assert response.analysis_brief is not None
    assert "3 source attempt(s), 2 degraded or limited" in response.analysis_brief.source_coverage
    assert response.markdown_brief is not None
    assert "status: rate-limited" in response.markdown_brief
    assert "status: forbidden" in response.markdown_brief
    assert "retry after 30s" in response.markdown_brief


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


@pytest.mark.anyio
async def test_provider_preflight_classifies_missing_api_key():
    response = await preflight_provider(
        ProviderPreflightRequest(model="openrouter", api_key=None, explicit_model=None)
    )

    assert response.status == "error"
    assert response.can_run_analysis is False
    assert response.failure_code == "missing_api_key"
    assert any(check.id == "api_key_present" and check.status == "fail" for check in response.checks)
    assert "API key" in response.user_action


@pytest.mark.anyio
async def test_provider_preflight_runs_model_health_check(monkeypatch):
    class FakeLLM:
        def __init__(self, api_key, model, base_url, timeout):
            self.api_key = api_key
            self.model = model
            self.base_url = base_url
            self.timeout = timeout

        def preflight_model_access(self):
            return False, "BadRequestError: invalid model ID"

    monkeypatch.setattr("retrocause.llm.LLMClient", FakeLLM)

    response = await preflight_provider(
        ProviderPreflightRequest(
            model="openrouter",
            api_key="sk-test",
            explicit_model="not-a-real-model",
        )
    )

    assert response.status == "error"
    assert response.can_run_analysis is False
    assert response.failure_code == "invalid_model"
    assert response.model_name == "not-a-real-model"
    assert any(check.id == "model_access" and check.status == "fail" for check in response.checks)
    assert "model" in response.user_action.lower()


def test_product_harness_marks_model_blocked_empty_result_as_actionable():
    response = AnalyzeResponseV2(
        query="US Iran Islamabad talks ended without agreement",
        is_demo=False,
        demo_topic=None,
        analysis_mode="partial_live",
        freshness_status="unknown",
        time_range=None,
        partial_live_reasons=["LLM calls failed for deepseek/deepseek-chat-v3-0324 - empty result"],
        recommended_chain_id=None,
        chains=[],
        evidences=[],
        upstream_map={"entries": []},
        retrieval_trace=[],
        challenge_checks=[],
        analysis_brief=None,
        error="LLM calls failed for deepseek/deepseek-chat-v3-0324 - empty result",
    )

    report = _build_product_harness(response)

    assert report.status == "blocked_by_model"
    assert report.score < 0.5
    assert any(check.id == "actionable_failure" and check.status == "pass" for check in report.checks)
    assert any("preflight" in action.lower() for action in report.next_actions)


def test_product_harness_rewards_useful_evidence_backed_result():
    result = AnalysisResult(
        query="US Iran Islamabad talks ended without agreement",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
            CausalVariable(name="failed_agreement", description="No agreement"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_dispute",
                target="failed_agreement",
                conditional_prob=0.74,
                supporting_evidence_ids=["ev-support"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions and sequencing gap",
                description="Disagreement over sanctions relief and sequencing blocked agreement.",
                variables=[
                    CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
                    CausalVariable(name="failed_agreement", description="No agreement"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_dispute",
                        target="failed_agreement",
                        conditional_prob=0.74,
                        supporting_evidence_ids=["ev-support"],
                    )
                ],
                posterior_probability=0.68,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Officials said sanctions relief sequencing remained unresolved.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            )
        ],
        retrieval_trace=[
            {
                "source": "ap_news",
                "query": "US Iran Islamabad talks no agreement sanctions sequencing",
                "result_count": 2,
                "cache_hit": False,
            }
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_dispute->failed_agreement",
                "source": "sanctions_dispute",
                "target": "failed_agreement",
                "query": "evidence against sanctions sequencing causing failed talks",
                "result_count": 1,
                "refuting_count": 0,
                "status": "checked_no_refuting_claims",
            }
        ],
    )
    response = _result_to_v2(result, is_demo=False)

    assert response.product_harness is not None
    assert response.product_harness.status == "ready_for_review"
    assert response.product_harness.score >= 0.7
    assert any(
        check.id == "analysis_summary" and check.status == "pass"
        for check in response.product_harness.checks
    )
