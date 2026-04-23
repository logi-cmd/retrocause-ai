"""LLM自动收集证据的 mock 测试"""

from __future__ import annotations

from datetime import date

import retrocause.collector as collector_module
from retrocause.collector import EvidenceCollector, reset_source_limit_state
from retrocause.config import RetroCauseConfig
from retrocause.engine import RetroCauseEngine, _collect_variable_evidence, analyze
from retrocause.llm import ExtractedEvidence
from retrocause.models import CausalEdge, EvidenceType
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


class _NamedFakeSourceAdapter(_FakeSourceAdapter):
    def __init__(self, name: str, results: list[SearchResult]):
        super().__init__(results)
        self._name = name
        self.calls: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self.calls.append(query)
        return super().search(query, max_results=max_results)


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


def _reset_source_state() -> None:
    reset_source_limit_state()


def test_auto_collect_basic():
    _reset_source_state()
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
    _reset_source_state()
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


def test_auto_collect_fallback_summary_preserves_source_metadata():
    _reset_source_state()
    collector = EvidenceCollector()
    fake_source = _FakeSourceAdapter(_make_search_results())

    class _EmptyExtractLLM(_FakeLLMClient):
        def extract_evidence(
            self, query: str, raw_text: str, source_type: str
        ) -> list[ExtractedEvidence]:
            return []

    fake_llm = _EmptyExtractLLM()

    new_evidence = collector.auto_collect(
        query="test query",
        domain="general",
        llm_client=fake_llm,
        source_adapters=[fake_source],
    )

    assert len(new_evidence) >= 1
    assert new_evidence[0].extraction_method == "fallback_summary"
    assert new_evidence[0].source_tier == "base"
    assert new_evidence[0].freshness in {"stable", "recent", "unknown"}


def test_auto_collect_fallback_runs_when_extracted_items_do_not_store():
    _reset_source_state()
    collector = EvidenceCollector()
    collector.add_evidence("Duplicate claim", EvidenceType.NEWS)
    fake_source = _FakeSourceAdapter(_make_search_results())

    fake_llm = _FakeLLMClient(
        extracted=[
            ExtractedEvidence(
                content="Duplicate claim",
                relevance=0.9,
                variables=["asteroid_impact"],
                confidence=0.9,
            )
        ]
    )

    new_evidence = collector.auto_collect(
        query="test query",
        domain="general",
        llm_client=fake_llm,
        source_adapters=[fake_source],
    )

    assert any(item.extraction_method == "fallback_summary" for item in new_evidence)


def test_chinese_evidence_matches_chinese_variable_name():
    _reset_source_state()
    collector = EvidenceCollector()
    evidence = collector.add_evidence(
        "芯原股份盘中下跌与半导体板块走弱和资金流出有关。",
        EvidenceType.NEWS,
        extraction_method="fallback_summary",
    )

    matched = _collect_variable_evidence(
        collector.get_evidence(),
        "芯原股份股价",
        "芯原股份今天盘中下跌",
    )

    assert evidence in matched


def test_chinese_market_analysis_builds_fallback_graph_when_llm_graph_empty():
    _reset_source_state()

    class _MarketLLM(_FakeLLMClient):
        def decompose_query(self, query: str, domain: str) -> list[str]:
            return ["芯原股份 今日 盘中 下跌 半导体 板块 资金 流出"]

        def extract_evidence(
            self, query: str, raw_text: str, source_type: str
        ) -> list[ExtractedEvidence]:
            return [
                ExtractedEvidence(
                    content="芯原股份盘中下跌，报道提到半导体板块走弱和资金流出。",
                    relevance=0.9,
                    variables=["芯原股份股价", "半导体板块", "资金流出"],
                    confidence=0.82,
                )
            ]

        def build_causal_graph(self, query: str, evidence_texts: list[str], domain: str) -> dict:
            return {}

    source = _NamedFakeSourceAdapter(
        "tavily",
        [
            SearchResult(
                title="芯原股份盘中下跌原因",
                content="半导体板块走弱，资金流出。",
                url="https://example.com/verisilicon",
                source_type=EvidenceType.NEWS,
                metadata={
                    "provider": "tavily",
                    "content_quality": "fulltext",
                    "page_content": "芯原股份盘中下跌，报道提到半导体板块走弱和资金流出。",
                },
            )
        ],
    )

    result = analyze(
        "芯原股份今天盘中为什么下跌？",
        llm_client=_MarketLLM(),
        source_adapters=[source],
        config=RetroCauseConfig(debate_max_rounds=0, max_sub_queries=1),
    )

    assert result.hypotheses
    assert result.edges
    assert any(edge.supporting_evidence_ids for edge in result.edges)
    assert result.retrieval_trace[0]["source"] == "tavily"
    assert result.refutation_checks == []


def test_auto_collect_prefers_page_content_for_web_quality():
    _reset_source_state()
    collector = EvidenceCollector()

    class _CapturingLLM(_FakeLLMClient):
        def __init__(self):
            super().__init__(
                extracted=[
                    ExtractedEvidence(
                        content="Satellite handshake evidence supports route deviation.",
                        relevance=0.92,
                        variables=["satellite_handshake", "route_deviation"],
                        confidence=0.74,
                    )
                ]
            )
            self.last_raw_text = ""

        def extract_evidence(
            self, query: str, raw_text: str, source_type: str
        ) -> list[ExtractedEvidence]:
            self.last_raw_text = raw_text
            return self._extracted

    fake_llm = _CapturingLLM()
    fake_source = _FakeSourceAdapter(
        [
            SearchResult(
                title="MH370 analysis",
                content="Short snippet that should not dominate.",
                url="https://example.com/report",
                source_type=EvidenceType.NEWS,
                metadata={
                    "page_content": (
                        "Detailed report with satellite handshake analysis, radar gaps, "
                        "and route deviation evidence."
                    ),
                    "content_quality": "fulltext",
                },
            )
        ]
    )

    new_evidence = collector.auto_collect(
        query="MH370为什么失踪",
        domain="aviation",
        llm_client=fake_llm,
        source_adapters=[fake_source],
    )

    assert "Detailed report with satellite handshake analysis" in fake_llm.last_raw_text
    assert "Short snippet that should not dominate." not in fake_llm.last_raw_text
    assert len(new_evidence) == 1
    assert new_evidence[0].extraction_method == "llm_fulltext"
    assert new_evidence[0].posterior_reliability > 0.74


def test_geopolitics_collects_more_than_one_source_when_coverage_is_thin():
    _reset_source_state()
    collector = EvidenceCollector()

    class _CoverageLLM(_FakeLLMClient):
        def __init__(self):
            super().__init__(
                sub_queries=["United States Iran talks", "US Iran negotiation reasons"]
            )
            self.extract_calls = 0

        def build_search_queries(self, query: str, domain: str) -> list[str]:
            return self._sub_queries

        def extract_evidence(
            self, query: str, raw_text: str, source_type: str
        ) -> list[ExtractedEvidence]:
            self.extract_calls += 1
            return [
                ExtractedEvidence(
                    content=f"Claim {self.extract_calls}A from {source_type}",
                    relevance=0.9,
                    variables=["diplomacy"],
                    confidence=0.8,
                ),
                ExtractedEvidence(
                    content=f"Claim {self.extract_calls}B from {source_type}",
                    relevance=0.8,
                    variables=["negotiations"],
                    confidence=0.75,
                ),
            ]

    first_source = _NamedFakeSourceAdapter(
        "ap_news",
        [
            SearchResult(
                title="AP talks",
                content="AP evidence about US Iran talks",
                url="https://apnews.com/article/one",
                source_type=EvidenceType.NEWS,
                metadata={"content_quality": "trusted_fulltext", "page_content": "AP full text"},
            )
        ],
    )
    second_source = _NamedFakeSourceAdapter(
        "web",
        [
            SearchResult(
                title="Official statement",
                content="Official evidence about US Iran negotiations",
                url="https://state.gov/example",
                source_type=EvidenceType.NEWS,
                metadata={"content_quality": "trusted_fulltext", "page_content": "Official text"},
            )
        ],
    )
    fake_llm = _CoverageLLM()

    new_evidence = collector.auto_collect(
        query="为什么美国会同意与伊朗进行首轮谈判？",
        domain="geopolitics",
        llm_client=fake_llm,
        source_adapters=[first_source, second_source],
        max_results_per_source=1,
    )

    assert len(new_evidence) >= 4
    assert len(first_source.calls) >= 1
    assert len(second_source.calls) >= 1


def test_auto_collect_attributes_extracted_evidence_to_best_matching_source():
    _reset_source_state()
    collector = EvidenceCollector()

    ap_source = _NamedFakeSourceAdapter(
        "ap_news",
        [
            SearchResult(
                title="Semiconductor market update",
                content="AP report about chip supply chains.",
                url="https://apnews.com/article/chips",
                source_type=EvidenceType.NEWS,
                metadata={
                    "content_quality": "trusted_fulltext",
                    "page_content": "Chip supply chain market update.",
                },
            )
        ],
    )
    official_source = _NamedFakeSourceAdapter(
        "federal_register",
        [
            SearchResult(
                title="Export Controls on Semiconductor Manufacturing Items",
                content="BIS revised the Export Administration Regulations.",
                url="https://www.federalregister.gov/documents/export-controls",
                source_type=EvidenceType.ARCHIVE,
                metadata={
                    "published": "2024-12-05",
                    "content_quality": "trusted_fulltext",
                    "page_content": (
                        "The Bureau of Industry and Security revised the Export "
                        "Administration Regulations for semiconductor manufacturing items."
                    ),
                },
            )
        ],
    )
    fake_llm = _FakeLLMClient(
        sub_queries=["export controls semiconductor"],
        extracted=[
            ExtractedEvidence(
                content=(
                    "The Bureau of Industry and Security revised the Export "
                    "Administration Regulations for semiconductor manufacturing items."
                ),
                relevance=0.9,
                variables=["export_controls"],
                confidence=0.86,
            )
        ],
    )

    new_evidence = collector.auto_collect(
        query="美国为什么会推出新的半导体出口管制？",
        domain="geopolitics",
        llm_client=fake_llm,
        source_adapters=[ap_source, official_source],
        max_results_per_source=1,
    )

    assert len(new_evidence) == 1
    assert new_evidence[0].source_type == EvidenceType.ARCHIVE
    assert new_evidence[0].source_url == "https://www.federalregister.gov/documents/export-controls"
    assert new_evidence[0].timestamp == "2024-12-05"


def test_auto_collect_excludes_stale_dated_results_for_yesterday_market_query(monkeypatch):
    _reset_source_state()
    monkeypatch.setattr(collector_module, "_today", lambda: date(2026, 4, 13))
    collector = EvidenceCollector()

    class _CapturingLLM(_FakeLLMClient):
        def __init__(self):
            super().__init__(
                sub_queries=["Bitcoin BTC price drop"],
                extracted=[
                    ExtractedEvidence(
                        content="Bitcoin fell during the April 12 trading session after liquidations.",
                        relevance=0.9,
                        variables=["bitcoin_price_drop", "liquidations"],
                        confidence=0.82,
                    )
                ],
            )
            self.last_raw_text = ""

        def build_search_queries(self, query: str, domain: str) -> list[str]:
            return self._sub_queries

        def extract_evidence(
            self, query: str, raw_text: str, source_type: str
        ) -> list[ExtractedEvidence]:
            self.last_raw_text = raw_text
            return self._extracted

    source = _NamedFakeSourceAdapter(
        "market_news",
        [
            SearchResult(
                title="Old Bitcoin selloff",
                content="A stale article about a March selloff.",
                url="https://example.com/old",
                source_type=EvidenceType.NEWS,
                metadata={
                    "published": "2026-03-01",
                    "content_quality": "trusted_fulltext",
                    "page_content": "Bitcoin fell in March after old macro worries.",
                },
            ),
            SearchResult(
                title="April 12 Bitcoin selloff",
                content="A fresh article about yesterday's selloff.",
                url="https://example.com/yesterday",
                source_type=EvidenceType.NEWS,
                metadata={
                    "published": "2026-04-12",
                    "content_quality": "trusted_fulltext",
                    "page_content": (
                        "Bitcoin fell during the April 12, 2026 trading session after "
                        "liquidations and ETF outflows."
                    ),
                },
            ),
        ],
    )
    fake_llm = _CapturingLLM()

    new_evidence = collector.auto_collect(
        query="昨天比特币价格跳水",
        domain="finance",
        llm_client=fake_llm,
        source_adapters=[source],
        max_results_per_source=5,
    )

    assert "2026-04-12" in source.calls[0]
    assert "Old Bitcoin selloff" not in fake_llm.last_raw_text
    assert "April 12 Bitcoin selloff" in fake_llm.last_raw_text
    assert len(new_evidence) == 1
    assert new_evidence[0].timestamp == "2026-04-12"


def test_auto_collect_no_llm():
    _reset_source_state()
    collector = EvidenceCollector()
    result = collector.auto_collect(
        query="test", domain="general", llm_client=None, source_adapters=[]
    )
    assert result == []


def test_auto_collect_no_sources():
    _reset_source_state()
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
    _reset_source_state()
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
    _reset_source_state()
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
    _reset_source_state()
    collector = EvidenceCollector()
    ev1 = collector.add_evidence("test content", EvidenceType.DATA)
    ev2 = collector.add_evidence("test content", EvidenceType.DATA)
    ev3 = collector.add_evidence("different content", EvidenceType.DATA)

    assert ev1 is not None
    assert ev2 is None
    assert ev3 is not None
    assert len(collector.get_evidence()) == 2


def test_collect_refutations_searches_challenge_queries_and_marks_stance():
    reset_source_limit_state()
    collector = EvidenceCollector()

    class _ChallengeLLM(_FakeLLMClient):
        def __init__(self):
            super().__init__(extracted=[])
            self.prompts: list[str] = []

        def extract_evidence(
            self, query: str, raw_text: str, source_type: str
        ) -> list[ExtractedEvidence]:
            self.prompts.append(query)
            return [
                ExtractedEvidence(
                    content="Officials said sanctions were not the reason talks failed.",
                    relevance=0.88,
                    variables=["sanctions_pressure", "talks_failed"],
                    confidence=0.8,
                    stance="refuting",
                )
            ]

    source = _NamedFakeSourceAdapter(
        "web",
        [
            SearchResult(
                title="Officials deny sanctions caused failure",
                content="Officials said sanctions were not the reason talks failed.",
                url="https://example.com/deny",
                source_type=EvidenceType.NEWS,
                metadata={"content_quality": "trusted_fulltext"},
            )
        ],
    )

    new_evidence, checks = collector.collect_refutations(
        query="Why did the Islamabad talks fail?",
        domain="geopolitics",
        edges=[
            CausalEdge(
                source="sanctions_pressure",
                target="talks_failed",
                conditional_prob=0.7,
                supporting_evidence_ids=["ev-existing"],
            )
        ],
        llm_client=_ChallengeLLM(),
        source_adapters=[source],
    )

    assert len(new_evidence) == 1
    assert new_evidence[0].stance == "refuting"
    assert new_evidence[0].stance_basis == "challenge_retrieval"
    assert "evidence against" in source.calls[0]
    assert "sanctions pressure" in source.calls[0]
    assert checks[0]["status"] == "has_refutation"
    assert checks[0]["refuting_count"] == 1
