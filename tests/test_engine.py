"""端到端测试"""

from __future__ import annotations

import threading
import time

from retrocause.parser import parse_input
from retrocause.models import (
    Evidence,
    EvidenceType,
    CausalVariable,
    CausalEdge,
    HypothesisChain,
)
from retrocause.collector import EvidenceCollector
from retrocause.reliability import cross_validate
from retrocause.graph import CausalGraphBuilder
from retrocause.hypothesis import HypothesisGenerator
from retrocause.debate import DebateOrchestrator
from retrocause.engine import analyze
from retrocause.engine import _ANALYSIS_CACHE, _INFLIGHT_ANALYSES, _collect_variable_evidence


def test_parse_input():
    q = parse_input("恐龙为什么灭绝？")
    assert q.domain == "paleontology"
    assert q.query == "恐龙为什么灭绝？"


def test_parse_finance():
    q = parse_input("2008年金融危机的原因")
    assert q.domain == "finance"


def test_parse_finance_time_window_defaults_to_trading_day():
    q = parse_input("Why did this stock fall?")
    assert q.domain == "finance"
    assert q.time_range == "trading_day"


def test_collector():
    c = EvidenceCollector()
    ev = c.add_evidence("satellite data", EvidenceType.DATA, linked_variables=["fuel"])
    assert ev.id == "ev-0001"
    assert len(c.get_evidence()) == 1
    assert len(c.get_evidence_by_variable("fuel")) == 1


def test_reliability():
    ev1 = Evidence(id="1", content="a", source_type=EvidenceType.LITERATURE)
    ev2 = Evidence(id="2", content="b", source_type=EvidenceType.SOCIAL)
    cross_validate([ev1, ev2])
    assert ev1.posterior_reliability > ev2.posterior_reliability


def test_variable_evidence_matching_accepts_snake_case_and_natural_language():
    ev = Evidence(
        id="1",
        content="Trump began diplomatic communication by writing a letter to Iran.",
        source_type=EvidenceType.NEWS,
        linked_variables=["diplomatic communication"],
        extraction_method="llm_fulltext_trusted",
    )

    linked = _collect_variable_evidence([ev], "diplomatic_communication")
    assert linked == [ev]


def test_graph_builder():
    g = CausalGraphBuilder()
    v1 = CausalVariable(name="cause", description="原因")
    v2 = CausalVariable(name="result", description="结果")
    g.add_variable(v1)
    g.add_variable(v2)
    g.add_edge(CausalEdge(source="cause", target="result", conditional_prob=0.8))
    assert g.validate_dag()
    paths = g.get_paths("cause", "result")
    assert len(paths) == 1


def test_hypothesis_generation():
    g = CausalGraphBuilder()
    v1 = CausalVariable(name="root_cause", description="根因")
    v2 = CausalVariable(name="mid", description="中间")
    v3 = CausalVariable(name="result", description="结果")
    for v in [v1, v2, v3]:
        g.add_variable(v)
    e1 = CausalEdge(source="root_cause", target="mid", conditional_prob=0.8)
    e2 = CausalEdge(source="mid", target="result", conditional_prob=0.7)
    g.add_edge(e1)
    g.add_edge(e2)

    gen = HypothesisGenerator()
    chains = gen.generate_from_graph(g, "result", [v1, v2, v3], [e1, e2])
    assert len(chains) == 1
    assert abs(chains[0].path_probability - 0.56) < 0.01


def test_hypothesis_generation_adds_evidence_wide_map_for_branched_graph():
    g = CausalGraphBuilder()
    root = CausalVariable(name="root_cause", description="root cause")
    policy = CausalVariable(name="policy_motive", description="policy motive")
    mechanism = CausalVariable(name="control_mechanism", description="control mechanism")
    supply = CausalVariable(name="supply_chain_pressure", description="supply chain pressure")
    result = CausalVariable(name="result", description="result")
    variables = [root, policy, mechanism, supply, result]
    for variable in variables:
        g.add_variable(variable)

    edges = [
        CausalEdge(source="root_cause", target="policy_motive", conditional_prob=0.8),
        CausalEdge(source="policy_motive", target="control_mechanism", conditional_prob=0.7),
        CausalEdge(source="control_mechanism", target="result", conditional_prob=0.6),
        CausalEdge(source="supply_chain_pressure", target="result", conditional_prob=0.5),
    ]
    for edge in edges:
        g.add_edge(edge)

    gen = HypothesisGenerator()
    chains = gen.generate_from_graph(g, "result", variables, edges)

    assert chains[0].id == "chain-000"
    assert len(chains[0].variables) == len(variables)
    assert len(chains[0].edges) == len(edges)
    assert "Evidence-wide causal map" in chains[0].name
    assert any(chain.id != "chain-000" for chain in chains)


def test_debate():
    h = HypothesisChain(id="h1", name="Test Chain", description="测试链")
    h = DebateOrchestrator(max_rounds=1).run_debate([h])[0]
    assert len(h.debate_rounds) == 1
    assert h.status.value == "refined"


class MockDebateLLM:
    def debate_hypothesis(self, hypothesis: HypothesisChain, context: str) -> dict:
        return {
            "abductive": "mock abductive",
            "deductive": "mock deductive",
            "inductive": "mock inductive",
            "devil_advocate": "mock devil",
            "arbiter": "mock arbiter",
        }


def test_debate_with_llm():
    h = HypothesisChain(id="h1", name="Test Chain", description="测试链")
    h = DebateOrchestrator(max_rounds=1, llm_client=MockDebateLLM()).run_debate([h])[0]
    assert len(h.debate_rounds) == 1
    round1 = h.debate_rounds[0]
    assert round1["abductive"] == "mock abductive"
    assert round1["arbiter"] == "mock arbiter"
    assert h.status.value == "refined"


def test_engine():
    result = analyze("恐龙为什么灭绝？")
    assert result.query == "恐龙为什么灭绝？"
    assert result.domain == "paleontology"
    assert result.total_evidence_count == 0


class _CoalescingSource:
    @property
    def name(self) -> str:
        return "coalescing"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.LITERATURE

    def search(self, query: str, max_results: int = 5):
        from retrocause.sources.base import SearchResult

        time.sleep(0.05)
        return [
            SearchResult(
                title="Stable evidence",
                content="Evidence content",
                url="https://example.com/evidence",
                source_type=EvidenceType.LITERATURE,
                metadata={},
            )
        ]


class _CoalescingLLM:
    def __init__(self):
        self.calls = 0

    def decompose_query(self, query: str, domain: str) -> list[str]:
        self.calls += 1
        time.sleep(0.05)
        return [query]

    def extract_evidence(self, query: str, raw_text: str, source_type: str):
        from retrocause.llm import ExtractedEvidence

        return [
            ExtractedEvidence(
                content="Evidence content",
                relevance=0.8,
                variables=["a", "b"],
                confidence=0.8,
            )
        ]

    def score_relevance(self, query: str, evidence_content: str) -> float:
        return 0.8

    def build_causal_graph(self, query: str, evidence_texts: list[str], domain: str) -> dict:
        return {
            "variables": [
                {"name": "a", "description": "A"},
                {"name": "b", "description": "B"},
            ],
            "edges": [{"source": "a", "target": "b", "conditional_prob": 0.8}],
            "result_variable": "b",
        }

    def debate_hypothesis(self, hypothesis: HypothesisChain, context: str) -> dict:
        return {}


def test_analyze_request_coalescing():
    _ANALYSIS_CACHE.clear()
    _INFLIGHT_ANALYSES.clear()
    llm = _CoalescingLLM()
    source = _CoalescingSource()
    results: list = []

    def _run():
        results.append(analyze("Why did this stock fall today?", llm_client=llm, source_adapters=[source]))

    threads = [threading.Thread(target=_run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 2
    assert llm.calls == 1
