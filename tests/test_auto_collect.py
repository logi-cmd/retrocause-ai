"""LLM自动收集证据的 mock 测试"""

from __future__ import annotations

from retrocause.collector import EvidenceCollector
from retrocause.engine import RetroCauseEngine, analyze
from retrocause.llm import ExtractedEvidence
from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult


class _FakeSourceAdapter(BaseSourceAdapter):
    def __init__(self, results: list[SearchResult]):
        self._results = results

    @property
    def name(self) -> str:
        return "fake_source"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.LITERATURE

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return self._results[:max_results]


class _FakeLLMClient:
    def __init__(
        self, sub_queries: list[str] | None = None, extracted: list[ExtractedEvidence] | None = None
    ):
        self._sub_queries = sub_queries or ["test query 1", "test query 2"]
        self._extracted = extracted or [
            ExtractedEvidence(
                content="Asteroid impact caused iridium anomaly",
                relevance=0.9,
                variables=["asteroid_impact", "ir_anomaly"],
                confidence=0.85,
            ),
        ]

    def decompose_query(self, query: str, domain: str) -> list[str]:
        return self._sub_queries

    def extract_evidence(
        self, query: str, raw_text: str, source_type: str
    ) -> list[ExtractedEvidence]:
        return self._extracted


def _make_search_results() -> list[SearchResult]:
    return [
        SearchResult(
            title="Dinosaur Extinction Evidence",
            content="The Chicxulub crater provides strong evidence for asteroid impact.",
            url="https://example.com/paper1",
            source_type=EvidenceType.LITERATURE,
            metadata={"year": "2020"},
        ),
        SearchResult(
            title="Volcanic Activity and Extinction",
            content="Deccan Traps volcanic activity coincided with the K-Pg boundary.",
            url="https://example.com/paper2",
            source_type=EvidenceType.LITERATURE,
            metadata={"year": "2019"},
        ),
    ]


def test_auto_collect_basic():
    collector = EvidenceCollector()
    fake_llm = _FakeLLMClient()
    fake_source = _FakeSourceAdapter(_make_search_results())

    new_evidence = collector.auto_collect(
        query="恐龙为什么灭绝？",
        domain="paleontology",
        llm_client=fake_llm,
        source_adapters=[fake_source],
    )

    assert len(new_evidence) >= 1
    assert new_evidence[0].content == "Asteroid impact caused iridium anomaly"
    assert new_evidence[0].source_url == "https://example.com/paper1"
    assert "asteroid_impact" in new_evidence[0].linked_variables


def test_auto_collect_dedup():
    collector = EvidenceCollector()
    extracted = [
        ExtractedEvidence(content="Same claim", relevance=0.8, variables=["x"], confidence=0.7),
        ExtractedEvidence(content="Same claim", relevance=0.8, variables=["x"], confidence=0.7),
        ExtractedEvidence(
            content="Different claim", relevance=0.6, variables=["y"], confidence=0.6
        ),
    ]
    fake_llm = _FakeLLMClient(extracted=extracted)
    fake_source = _FakeSourceAdapter(_make_search_results())

    new_evidence = collector.auto_collect(
        query="test query",
        domain="general",
        llm_client=fake_llm,
        source_adapters=[fake_source],
    )

    assert len(new_evidence) == 2
    assert new_evidence[0].content == "Same claim"
    assert new_evidence[1].content == "Different claim"


def test_auto_collect_no_llm():
    collector = EvidenceCollector()
    result = collector.auto_collect(
        query="test", domain="general", llm_client=None, source_adapters=[]
    )
    assert result == []


def test_auto_collect_no_sources():
    collector = EvidenceCollector()
    fake_llm = _FakeLLMClient()
    result = collector.auto_collect(
        query="test",
        domain="general",
        llm_client=fake_llm,
        source_adapters=None,
    )
    assert result == []


def test_auto_collect_source_error_graceful():
    collector = EvidenceCollector()
    fake_llm = _FakeLLMClient()

    class _BrokenSource(BaseSourceAdapter):
        @property
        def name(self) -> str:
            return "broken"

        @property
        def source_type(self) -> EvidenceType:
            return EvidenceType.LITERATURE

        def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
            raise ConnectionError("API down")

    new_evidence = collector.auto_collect(
        query="test",
        domain="general",
        llm_client=fake_llm,
        source_adapters=[_BrokenSource()],
    )
    assert new_evidence == []


def test_engine_with_auto_collect():
    fake_llm = _FakeLLMClient()
    fake_source = _FakeSourceAdapter(_make_search_results())

    engine = RetroCauseEngine(
        query="恐龙为什么灭绝？",
        llm_client=fake_llm,
        source_adapters=[fake_source],
    )
    result = engine.run()

    assert result.domain == "paleontology"
    assert result.total_evidence_count >= 1


def test_engine_without_auto_collect():
    result = analyze("恐龙为什么灭绝？")
    assert result.domain == "paleontology"
    assert result.total_evidence_count == 0


def test_collector_add_evidence_dedup():
    collector = EvidenceCollector()
    ev1 = collector.add_evidence("test content", EvidenceType.DATA)
    ev2 = collector.add_evidence("test content", EvidenceType.DATA)
    ev3 = collector.add_evidence("different content", EvidenceType.DATA)

    assert ev1 is not None
    assert ev2 is None
    assert ev3 is not None
    assert len(collector.get_evidence()) == 2
