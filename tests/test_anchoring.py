from __future__ import annotations

from retrocause.anchoring import (
    EvidenceAnchoringStep,
    anchor_edge_to_evidence,
    anchor_hypothesis,
    build_evidence_index,
)
from retrocause.collector import EvidenceCollector
from retrocause.models import (
    CausalEdge,
    EvidenceType,
    HypothesisChain,
)
from retrocause.pipeline import PipelineContext
from retrocause.rules import EvidenceCoverageRule, ProbabilityBoundRule
from retrocause.hooks import HookEngine
from retrocause.engine import analyze


def test_anchor_edge_with_evidence():
    edge = CausalEdge(source="asteroid_impact", target="iridium_anomaly", conditional_prob=0.8)
    evidence_by_var = {"asteroid_impact": ["ev-0001"], "iridium_anomaly": ["ev-0002"]}
    anchor_edge_to_evidence(edge, evidence_by_var)
    assert edge.supporting_evidence_ids == ["ev-0001", "ev-0002"]


def test_anchor_edge_no_match():
    edge = CausalEdge(source="a", target="b", conditional_prob=0.5)
    anchor_edge_to_evidence(edge, {})
    assert edge.supporting_evidence_ids == []


def test_anchor_hypothesis_full():
    e1 = CausalEdge(source="asteroid_impact", target="mid", conditional_prob=0.8)
    e2 = CausalEdge(source="mid", target="extinction", conditional_prob=0.7)
    chain = HypothesisChain(
        id="h1",
        name="test",
        description="test",
        edges=[e1, e2],
    )
    evidence_by_var = {"asteroid_impact": ["ev-0001"], "mid": ["ev-0002"]}
    anchor_hypothesis(chain, evidence_by_var)
    assert chain.evidence_coverage == 1.0
    assert chain.unanchored_edges == []


def test_anchor_hypothesis_partial():
    e1 = CausalEdge(source="asteroid_impact", target="mid", conditional_prob=0.8)
    e2 = CausalEdge(source="mid", target="extinction", conditional_prob=0.7)
    chain = HypothesisChain(
        id="h1",
        name="test",
        description="test",
        edges=[e1, e2],
    )
    anchor_hypothesis(chain, {"asteroid_impact": ["ev-0001"]})
    assert chain.evidence_coverage == 0.5
    assert len(chain.unanchored_edges) == 1
    assert "mid\u2192extinction" in chain.unanchored_edges[0]


def test_anchor_hypothesis_empty():
    chain = HypothesisChain(id="h1", name="test", description="test")
    anchor_hypothesis(chain, {})
    assert chain.evidence_coverage == 0.0
    assert chain.unanchored_edges == []


def test_build_evidence_index():
    collector = EvidenceCollector()
    collector.add_evidence("e1", EvidenceType.DATA, linked_variables=["x", "y"])
    collector.add_evidence("e2", EvidenceType.DATA, linked_variables=["a", "b"])
    collector.add_evidence("shared", EvidenceType.LITERATURE, linked_variables=["x", "z"])
    index = build_evidence_index(collector)
    assert "x" in index
    assert "y" in index
    assert "z" in index
    assert "a" in index
    assert "b" in index
    assert index["x"] == ["ev-0001", "ev-0003"]


def test_build_evidence_index_empty():
    collector = EvidenceCollector()
    index = build_evidence_index(collector)
    assert index == {}


def test_evidence_anchoring_step():
    collector = EvidenceCollector()
    collector.add_evidence(
        "asteroid impact evidence",
        EvidenceType.SCIENTIFIC,
        linked_variables=["asteroid_impact", "iridium_anomaly"],
    )
    step = EvidenceAnchoringStep(collector)
    ctx = PipelineContext()
    ctx.hypotheses = [
        HypothesisChain(
            id="h1",
            name="test",
            description="test",
            edges=[
                CausalEdge(
                    source="asteroid_impact", target="iridium_anomaly", conditional_prob=0.8
                ),
            ],
        ),
    ]
    ctx = step.execute(ctx)
    chain = ctx.hypotheses[0]
    assert chain.evidence_coverage == 1.0
    assert chain.unanchored_edges == []
    assert chain.edges[0].supporting_evidence_ids == ["ev-0001"]


def test_evidence_coverage_rule_pass():
    rule = EvidenceCoverageRule(threshold=0.5)
    h = HypothesisChain(id="h1", name="test", description="test")
    h.evidence_coverage = 0.8
    result = rule.check({"hypotheses": [h]})
    assert result is None


def test_evidence_coverage_rule_fail():
    rule = EvidenceCoverageRule(threshold=0.5)
    h = HypothesisChain(id="h1", name="test", description="test")
    h.evidence_coverage = 0.2
    result = rule.check({"hypotheses": [h]})
    assert result is not None
    assert "覆盖不足" in result.message


def test_probability_bound_rule_pass():
    rule = ProbabilityBoundRule()
    h = HypothesisChain(id="h1", name="test", description="test")
    h.path_probability = 0.5
    h.posterior_probability = 0.5
    h.confidence_interval = (0.2, 0.8)
    result = rule.check({"hypotheses": [h]})
    assert result is None


def test_probability_bound_rule_fail_path():
    rule = ProbabilityBoundRule()
    h = HypothesisChain(id="h1", name="test", description="test")
    h.path_probability = 1.5
    h.posterior_probability = 0.5
    h.confidence_interval = (0.0, 1.0)
    result = rule.check({"hypotheses": [h]})
    assert result is not None
    assert "path_probability" in result.message


def test_probability_bound_rule_fail_ci():
    rule = ProbabilityBoundRule()
    h = HypothesisChain(id="h1", name="test", description="test")
    h.path_probability = 0.5
    h.posterior_probability = 0.5
    h.confidence_interval = (-0.1, 1.2)
    result = rule.check({"hypotheses": [h]})
    assert result is not None
    assert "CI" in result.message


def test_hook_engine_with_both_rules():
    engine = HookEngine(
        rules=[
            EvidenceCoverageRule(threshold=0.5),
            ProbabilityBoundRule(),
        ]
    )
    h_good = HypothesisChain(id="h1", name="good", description="good")
    h_good.evidence_coverage = 0.8
    h_good.path_probability = 0.5
    h_good.posterior_probability = 0.5
    h_good.confidence_interval = (0.2, 0.8)
    violations = engine.evaluate({"hypotheses": [h_good]})
    assert len(violations) == 0


def test_hook_engine_catches_both():
    engine = HookEngine(
        rules=[
            EvidenceCoverageRule(threshold=0.5),
            ProbabilityBoundRule(),
        ]
    )
    h_bad = HypothesisChain(id="h1", name="bad", description="bad")
    h_bad.evidence_coverage = 0.2
    h_bad.path_probability = 1.5
    h_bad.posterior_probability = 0.5
    h_bad.confidence_interval = (0.0, 1.0)
    violations = engine.evaluate({"hypotheses": [h_bad]})
    assert len(violations) == 2


def test_engine_no_evidence_coverage_zero():
    result = analyze("恐龙为什么灭绝？")
    assert result.domain == "paleontology"
    for h in result.hypotheses:
        assert h.evidence_coverage == 0.0
        assert h.unanchored_edges == []
