"""端到端集成测试 — mock LLM + source adapters，验证完整管道串联"""

from __future__ import annotations

from retrocause.engine import analyze
from retrocause.evidence_store import EvidenceStore
from retrocause.llm import ExtractedEvidence
from retrocause.models import Evidence, EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult


class MockSourceAdapter(BaseSourceAdapter):
    """模拟 ArXiv 搜索返回"""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.SCIENTIFIC

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return [
            SearchResult(
                title="Asteroid impact and dinosaur extinction",
                content="Large asteroid impact at Chicxulub caused global climate catastrophe",
                url="https://example.com/paper1",
                source_type=EvidenceType.SCIENTIFIC,
            ),
            SearchResult(
                title="Deccan Traps volcanism",
                content="Massive volcanic activity released greenhouse gases over 750kyr",
                url="https://example.com/paper2",
                source_type=EvidenceType.LITERATURE,
            ),
        ]


class MockLLMClient:
    """模拟 LLM 返回，覆盖所有管道需要的接口"""

    def decompose_query(self, query: str, domain: str) -> list[str]:
        return ["asteroid impact dinosaur extinction", "volcanic activity K-Pg boundary"]

    def extract_evidence(
        self, query: str, raw_text: str, source_type: str
    ) -> list[ExtractedEvidence]:
        return [
            ExtractedEvidence(
                content=raw_text[:80],
                relevance=0.9,
                variables=["asteroid_impact", "dinosaur_extinction"],
                confidence=0.85,
            ),
        ]

    def score_relevance(self, query: str, evidence_content: str) -> float:
        return 0.85

    def build_causal_graph(self, query: str, evidence_texts: list[str], domain: str) -> dict:
        return {
            "variables": [
                {"name": "asteroid_impact", "description": "Chicxulub asteroid impact"},
                {"name": "volcanic_activity", "description": "Deccan Traps volcanism"},
                {"name": "climate_change", "description": "Global climate catastrophe"},
                {"name": "dinosaur_extinction", "description": "K-Pg mass extinction"},
            ],
            "edges": [
                {
                    "source": "asteroid_impact",
                    "target": "climate_change",
                    "conditional_prob": 0.90,
                },
                {
                    "source": "volcanic_activity",
                    "target": "climate_change",
                    "conditional_prob": 0.60,
                },
                {
                    "source": "climate_change",
                    "target": "dinosaur_extinction",
                    "conditional_prob": 0.85,
                },
            ],
            "result_variable": "dinosaur_extinction",
        }

    def debate_hypothesis(self, hypothesis, context: str) -> dict:
        return {
            "abductive": f"Best explanation for {hypothesis.name}",
            "deductive": "If true, expected observations should follow",
            "inductive": "Observed evidence is broadly consistent",
            "devil_advocate": "Evidence gaps remain on alternative paths",
            "arbiter": "Plausible but still uncertain",
        }


class FallbackOnlyLLMClient(MockLLMClient):
    def __init__(self):
        self.last_evidence_texts: list[str] = []

    def extract_evidence(
        self, query: str, raw_text: str, source_type: str
    ) -> list[ExtractedEvidence]:
        return []

    def build_causal_graph(self, query: str, evidence_texts: list[str], domain: str) -> dict:
        self.last_evidence_texts = evidence_texts
        return {
            "variables": [
                {"name": "flight_path_deviation", "description": "Unexpected route change"},
                {"name": "mh370_disappearance", "description": "Aircraft loss event"},
            ],
            "edges": [
                {
                    "source": "flight_path_deviation",
                    "target": "mh370_disappearance",
                    "conditional_prob": 0.82,
                }
            ],
            "result_variable": "mh370_disappearance",
        }


class InMemoryEvidenceStore(EvidenceStore):
    def _save(self) -> None:
        return None


def test_full_pipeline_with_mock():
    """完整管道测试: mock LLM + mock source → 非空结果"""
    result = analyze(
        query="恐龙为什么灭绝？",
        llm_client=MockLLMClient(),
        source_adapters=[MockSourceAdapter()],
    )

    assert result.query == "恐龙为什么灭绝？"
    assert result.domain == "paleontology"
    assert result.total_evidence_count > 0, f"Expected evidence, got {result.total_evidence_count}"
    assert len(result.variables) == 4, f"Expected 4 variables, got {len(result.variables)}"
    assert len(result.edges) == 3, f"Expected 3 edges, got {len(result.edges)}"
    assert len(result.hypotheses) > 0, "Expected at least 1 hypothesis"


def test_pipeline_variables_match_graph():
    """变量应与因果图节点对应"""
    result = analyze(
        query="恐龙为什么灭绝？",
        llm_client=MockLLMClient(),
        source_adapters=[MockSourceAdapter()],
    )

    var_names = {v.name for v in result.variables}
    assert "asteroid_impact" in var_names
    assert "dinosaur_extinction" in var_names


def test_pipeline_hypotheses_have_probabilities():
    """假说链应有有效概率值"""
    result = analyze(
        query="恐龙为什么灭绝？",
        llm_client=MockLLMClient(),
        source_adapters=[MockSourceAdapter()],
    )

    for h in result.hypotheses:
        assert 0.0 <= h.path_probability <= 1.0, f"path_prob={h.path_probability}"
        assert h.id.startswith("chain-")
        assert len(h.variables) > 0
        assert len(h.edges) > 0


def test_pipeline_counterfactual_scores():
    """假说链应有反事实得分"""
    result = analyze(
        query="恐龙为什么灭绝？",
        llm_client=MockLLMClient(),
        source_adapters=[MockSourceAdapter()],
    )

    for h in result.hypotheses:
        assert 0.0 <= h.counterfactual_score <= 1.0
        if h.counterfactual_results:
            for cf in h.counterfactual_results:
                assert cf.intervention_var != ""
                assert 0.0 <= cf.probability_delta <= 1.0


def test_pipeline_evidence_coverage():
    """假说链应有证据覆盖率"""
    result = analyze(
        query="恐龙为什么灭绝？",
        llm_client=MockLLMClient(),
        source_adapters=[MockSourceAdapter()],
    )

    for h in result.hypotheses:
        assert 0.0 <= h.evidence_coverage <= 1.0


def test_pipeline_debate_refined():
    """辩论步骤应将假说标记为 REFINED"""
    result = analyze(
        query="恐龙为什么灭绝？",
        llm_client=MockLLMClient(),
        source_adapters=[MockSourceAdapter()],
    )

    for h in result.hypotheses:
        assert h.status.value == "refined"
        assert len(h.debate_rounds) > 0


def test_pipeline_no_llm_graceful():
    """无 LLM 时不应崩溃，返回空结果"""
    result = analyze("恐龙为什么灭绝？")
    assert result.query == "恐龙为什么灭绝？"
    assert result.total_evidence_count == 0
    assert len(result.variables) == 0
    assert len(result.hypotheses) == 0


def test_pipeline_prefers_cached_high_quality_evidence_for_graph(monkeypatch):
    store = InMemoryEvidenceStore("evidence_store.json")
    store.add_evidences(
        "MH370为什么失踪",
        "aviation",
        [
            Evidence(
                id="ev-cache-1",
                content="Satellite handshake analysis links route deviation to the MH370 disappearance.",
                source_type=EvidenceType.SCIENTIFIC,
                source_url="https://example.com/report",
                prior_reliability=0.88,
                posterior_reliability=0.88,
                linked_variables=["flight_path_deviation", "mh370_disappearance"],
                source_tier="base",
                freshness="stable",
                captured_at="2026-04-11",
                extraction_method="llm",
            )
        ],
    )
    monkeypatch.setattr("retrocause.engine.EvidenceStore", lambda: store)

    llm_client = FallbackOnlyLLMClient()

    class ThinSourceAdapter(BaseSourceAdapter):
        @property
        def name(self) -> str:
            return "thin-source"

        @property
        def source_type(self) -> EvidenceType:
            return EvidenceType.NEWS

        def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
            return [
                SearchResult(
                    title="Speculation roundup",
                    content="Short summary with weak detail.",
                    url="https://example.com/speculation",
                    source_type=EvidenceType.NEWS,
                )
            ]

    result = analyze(
        query="MH370为什么失踪",
        llm_client=llm_client,
        source_adapters=[ThinSourceAdapter()],
    )

    assert any(
        item.extraction_method == "store_cache" and "Satellite handshake analysis" in item.content
        for item in result.evidences
    )
    assert any("Satellite handshake analysis" in text for text in llm_client.last_evidence_texts)

    variable = next(item for item in result.variables if item.name == "flight_path_deviation")
    edge = next(item for item in result.edges if item.source == "flight_path_deviation")

    assert variable.evidence_ids
    assert variable.posterior_support >= 0.75
    assert edge.supporting_evidence_ids
    assert 0.6 <= edge.conditional_prob <= 1.0


def test_time_sensitive_query_with_only_stable_evidence_degrades_to_partial_live(monkeypatch):
    store = InMemoryEvidenceStore("evidence_store.json")
    store.add_evidences(
        "Why did this stock fall today?",
        "finance",
        [
            Evidence(
                id="ev-cache-stale",
                content="Long-term valuation concerns pressured the stock.",
                source_type=EvidenceType.SCIENTIFIC,
                source_url="https://example.com/report",
                prior_reliability=0.9,
                posterior_reliability=0.9,
                linked_variables=["valuation", "stock_drop"],
                source_tier="base",
                freshness="stable",
                captured_at="2026-04-11",
                extraction_method="llm",
            )
        ],
        time_scope="trading_day",
    )
    monkeypatch.setattr("retrocause.engine.EvidenceStore", lambda: store)

    result = analyze(
        query="Why did this stock fall today?",
        llm_client=FallbackOnlyLLMClient(),
        source_adapters=[],
    )

    assert result.analysis_mode == "partial_live"
    assert any("Fresh evidence is insufficient" in item for item in result.recommended_next_steps)
