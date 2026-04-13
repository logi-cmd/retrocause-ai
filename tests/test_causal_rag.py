from __future__ import annotations

from retrocause.collector import EvidenceCollector, reset_source_limit_state
from retrocause.llm import ExtractedEvidence
from retrocause.models import CausalEdge, CausalVariable, EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult


class _FakeSource(BaseSourceAdapter):
    @property
    def name(self) -> str:
        return "fake"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.LITERATURE

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return [
            SearchResult(
                title=f"Result for {query}",
                content=f"Evidence about {query}",
                url=f"https://example.com/{query[:10]}",
                source_type=EvidenceType.LITERATURE,
                metadata={},
            )
        ]


class _FakeLLM:
    def decompose_query(self, query: str, domain: str) -> list[str]:
        return ["sub1", "sub2"]

    def extract_evidence(
        self, query: str, raw_text: str, source_type: str
    ) -> list[ExtractedEvidence]:
        return [
            ExtractedEvidence(
                content=f"Extracted: {raw_text[:30]}",
                relevance=0.8,
                variables=["var_a", "var_b"],
                confidence=0.7,
            )
        ]


def test_graph_guided_collect_basic():
    reset_source_limit_state()
    collector = EvidenceCollector()
    llm = _FakeLLM()
    source = _FakeSource()
    variables = [CausalVariable(name="var_a", description="variable a")]
    edges = [
        CausalEdge(source="var_a", target="var_b", conditional_prob=0.7),
    ]

    new_evidence = collector.graph_guided_collect(
        query="test query",
        domain="general",
        variables=variables,
        edges=edges,
        llm_client=llm,
        source_adapters=[source],
    )

    assert len(new_evidence) >= 1


def test_graph_guided_collect_no_llm():
    reset_source_limit_state()
    collector = EvidenceCollector()
    result = collector.graph_guided_collect(
        query="test",
        domain="general",
        variables=[],
        edges=[],
        llm_client=None,
        source_adapters=[],
    )
    assert result == []


def test_graph_guided_collect_fully_covered():
    reset_source_limit_state()
    collector = EvidenceCollector()
    llm = _FakeLLM()
    source = _FakeSource()
    edge = CausalEdge(
        source="var_a",
        target="var_b",
        conditional_prob=0.7,
        supporting_evidence_ids=["ev-0001"],
    )
    var = CausalVariable(name="var_a", description="variable a", evidence_ids=["ev-0001"])

    new_evidence = collector.graph_guided_collect(
        query="test",
        domain="general",
        variables=[var],
        edges=[edge],
        llm_client=llm,
        source_adapters=[source],
    )
    assert new_evidence == []


def test_graph_guided_collect_max_subqueries():
    reset_source_limit_state()
    collector = EvidenceCollector()
    llm = _FakeLLM()
    source = _FakeSource()
    variables = [CausalVariable(name=f"var_{i}", description=f"variable {i}") for i in range(10)]
    edges = [
        CausalEdge(source=f"var_{i}", target=f"var_{i + 1}", conditional_prob=0.5) for i in range(9)
    ]

    new_evidence = collector.graph_guided_collect(
        query="test",
        domain="general",
        variables=variables,
        edges=edges,
        llm_client=llm,
        source_adapters=[source],
        max_sub_queries=2,
    )

    assert len(new_evidence) >= 1


def test_search_by_causal_path():
    reset_source_limit_state()
    collector = EvidenceCollector()
    llm = _FakeLLM()
    source = _FakeSource()

    new_evidence = collector.search_by_causal_path(
        query="why did dinosaurs die?",
        path_variables=["asteroid_impact", "climate_change", "extinction"],
        llm_client=llm,
        source_adapters=[source],
    )

    assert len(new_evidence) >= 1


def test_search_by_causal_path_too_short():
    reset_source_limit_state()
    collector = EvidenceCollector()
    llm = _FakeLLM()
    source = _FakeSource()
    result = collector.search_by_causal_path(
        query="test",
        path_variables=["only_one"],
        llm_client=llm,
        source_adapters=[source],
    )
    assert result == []
