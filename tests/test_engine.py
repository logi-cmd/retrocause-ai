"""端到端测试"""

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


def test_parse_input():
    q = parse_input("恐龙为什么灭绝？")
    assert q.domain == "paleontology"
    assert q.query == "恐龙为什么灭绝？"


def test_parse_finance():
    q = parse_input("2008年金融危机的原因")
    assert q.domain == "finance"


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
