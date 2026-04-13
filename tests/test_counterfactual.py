"""反事实验证模块测试"""

from __future__ import annotations

import networkx as nx
import pytest

from retrocause.config import RetroCauseConfig
from retrocause.counterfactual import (
    CounterfactualVerificationStep,
    check_reachability,
    compute_counterfactual_score,
    compute_probability_delta,
    compute_sensitivity_bounds,
    perform_graph_surgery,
)
from retrocause.graph import CausalGraphBuilder
from retrocause.models import (
    CausalEdge,
    CausalVariable,
    CounterfactualResult,
    HypothesisChain,
)
from retrocause.pipeline import PipelineContext
from retrocause.rules import CounterfactualBoundRule


def _build_graph():
    g = CausalGraphBuilder()
    g.add_variable(CausalVariable(name="A", description="root cause"))
    g.add_variable(CausalVariable(name="B", description="mediator"))
    g.add_variable(CausalVariable(name="C", description="result"))
    g.add_edge(CausalEdge(source="A", target="B", conditional_prob=0.8))
    g.add_edge(CausalEdge(source="B", target="C", conditional_prob=0.7))
    return g


def _build_graph_with_alt_path() -> CausalGraphBuilder:
    g = CausalGraphBuilder()
    g.add_variable(CausalVariable(name="A", description="root 1"))
    g.add_variable(CausalVariable(name="D", description="root 2"))
    g.add_variable(CausalVariable(name="B", description="mediator"))
    g.add_variable(CausalVariable(name="C", description="result"))
    g.add_edge(CausalEdge(source="A", target="B", conditional_prob=0.8))
    g.add_edge(CausalEdge(source="B", target="C", conditional_prob=0.7))
    g.add_edge(CausalEdge(source="D", target="C", conditional_prob=0.5))
    return g


def _make_chain(
    chain_id: str = "chain-001",
    path_prob: float = 0.56,
    unanchored: int = 0,
    coverage: float = 1.0,
) -> HypothesisChain:
    chain = HypothesisChain(
        id=chain_id,
        name="test chain",
        description="test",
        variables=[
            CausalVariable(name="A", description="root"),
            CausalVariable(name="B", description="mediator"),
            CausalVariable(name="C", description="result"),
        ],
        edges=[
            CausalEdge(source="A", target="B", conditional_prob=0.8),
            CausalEdge(source="B", target="C", conditional_prob=0.7),
        ],
        path_probability=path_prob,
        evidence_coverage=coverage,
    )
    if unanchored > 0:
        chain.unanchored_edges = [f"edge-{i}" for i in range(unanchored)]
    return chain


def test_graph_surgery_remove():
    g = _build_graph()
    surgical = perform_graph_surgery(g.graph, "A", mode="remove")
    assert "A" not in surgical
    assert "B" in surgical
    assert "C" in surgical
    assert len(surgical.edges) == 1


def test_graph_surgery_intervene():
    g = _build_graph()
    surgical = perform_graph_surgery(g.graph, "B", mode="intervene")
    assert "B" in surgical
    assert "A" in surgical
    assert len(list(surgical.in_edges("B"))) == 0
    assert len(list(surgical.out_edges("B"))) == 1


def test_graph_surgery_nonexistent():
    g = _build_graph()
    original_nodes = set(g.graph.nodes)
    surgical = perform_graph_surgery(g.graph, "ZZZ")
    assert set(surgical.nodes) == original_nodes


def test_reachability_connected():
    g = nx.DiGraph([("A", "B"), ("B", "C")])
    assert check_reachability(g, ["A"], "C") is True


def test_reachability_disconnected():
    g = nx.DiGraph([("A", "B"), ("B", "C")])
    assert check_reachability(g, ["X"], "C") is False


def test_reachability_target_missing():
    g = nx.DiGraph([("A", "B")])
    assert check_reachability(g, ["A"], "Z") is False


def test_delta_positive():
    assert compute_probability_delta(0.8, 0.3) == 0.5


def test_delta_clamped():
    assert compute_probability_delta(0.5, 0.5) == 0.0
    assert compute_probability_delta(1.5, -0.5) == 1.0


def test_delta_negative_clamped():
    assert compute_probability_delta(0.3, 0.8) == 0.0


def test_sensitivity_full_evidence():
    chain = _make_chain(unanchored=0)
    lower, upper = compute_sensitivity_bounds(chain)
    assert lower == chain.path_probability
    assert upper == chain.path_probability


def test_sensitivity_partial():
    chain = _make_chain(path_prob=0.5, unanchored=1, coverage=0.5)
    lower, upper = compute_sensitivity_bounds(chain)
    assert lower < upper
    assert 0.0 <= lower <= 1.0
    assert 0.0 <= upper <= 1.0


def test_sensitivity_empty_chain():
    chain = HypothesisChain(id="x", name="x", description="x", path_probability=0.5)
    lower, upper = compute_sensitivity_bounds(chain)
    assert lower == 0.5
    assert upper == 0.5


def test_score_ideal():
    score = compute_counterfactual_score(delta=0.8, sensitivity_width=0.0, coverage=1.0)
    assert score == 0.8


def test_score_zero_coverage():
    score = compute_counterfactual_score(delta=0.8, sensitivity_width=0.0, coverage=0.0)
    assert score == 0.0


def test_score_full_uncertainty():
    score = compute_counterfactual_score(delta=0.8, sensitivity_width=1.0, coverage=1.0)
    assert score == 0.0


def test_step_removes_root():
    g = _build_graph()
    chain = _make_chain()
    ctx = PipelineContext(
        hypotheses=[chain],
        edges=[
            CausalEdge(source="A", target="B", conditional_prob=0.8),
            CausalEdge(source="B", target="C", conditional_prob=0.7),
        ],
    )
    step = CounterfactualVerificationStep(g, RetroCauseConfig())
    ctx = step.execute(ctx)

    assert len(chain.counterfactual_results) == 1
    result = chain.counterfactual_results[0]
    assert result.intervention_var == "A"
    assert result.still_reachable is False
    assert result.intervened_path_prob == 0.0
    assert result.probability_delta == 0.56
    assert chain.counterfactual_score > 0


def test_step_alt_path_reachable():
    g = _build_graph_with_alt_path()
    chain = _make_chain()
    ctx = PipelineContext(
        hypotheses=[chain],
        edges=[
            CausalEdge(source="A", target="B", conditional_prob=0.8),
            CausalEdge(source="B", target="C", conditional_prob=0.7),
            CausalEdge(source="D", target="C", conditional_prob=0.5),
        ],
    )
    step = CounterfactualVerificationStep(g, RetroCauseConfig())
    ctx = step.execute(ctx)

    result = chain.counterfactual_results[0]
    assert result.still_reachable is True
    assert result.intervened_path_prob == 0.5
    assert result.probability_delta == pytest.approx(0.06, abs=0.01)


def test_step_no_hypotheses():
    g = _build_graph()
    ctx = PipelineContext(hypotheses=[])
    step = CounterfactualVerificationStep(g, RetroCauseConfig())
    ctx = step.execute(ctx)
    assert "counterfactual" not in ctx.extra


def test_bound_rule_pass():
    chain = _make_chain()
    chain.counterfactual_score = 0.5
    rule = CounterfactualBoundRule(min_score=0.1)
    assert rule.check({"hypotheses": [chain]}) is None


def test_bound_rule_fail():
    chain = _make_chain()
    chain.counterfactual_score = 0.05
    rule = CounterfactualBoundRule(min_score=0.1)
    violation = rule.check({"hypotheses": [chain]})
    assert violation is not None
    assert "反事实得分不足" in violation.message


def test_bound_rule_empty():
    rule = CounterfactualBoundRule()
    assert rule.check({"hypotheses": []}) is None


def test_counterfactual_result_creation():
    r = CounterfactualResult(
        hypothesis_id="h1",
        intervention_var="A",
        original_path_prob=0.8,
        intervened_path_prob=0.0,
        probability_delta=0.8,
        still_reachable=False,
        sensitivity_lower=0.7,
        sensitivity_upper=0.9,
        counterfactual_score=0.6,
    )
    assert r.probability_delta == 0.8
    assert r.still_reachable is False
