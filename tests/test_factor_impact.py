from __future__ import annotations

from retrocause.counterfactual import (
    compute_factor_impact,
    compute_sensitivity_profile,
    find_downstream_variables,
)
from retrocause.models import (
    AnalysisResult,
    CausalEdge,
    CausalVariable,
    FactorIntervention,
    HypothesisChain,
    SensitivityPoint,
)


def _make_result() -> AnalysisResult:
    asteroid = CausalVariable(name="asteroid_impact", description="asteroid", posterior_support=0.9)
    volcanic = CausalVariable(
        name="volcanic_activity", description="volcano", posterior_support=0.6
    )
    climate = CausalVariable(name="climate_change", description="climate", posterior_support=0.8)
    extinction = CausalVariable(
        name="dinosaur_extinction", description="extinction", posterior_support=0.95
    )

    edge1 = CausalEdge(source="asteroid_impact", target="climate_change", conditional_prob=0.9)
    edge2 = CausalEdge(source="climate_change", target="dinosaur_extinction", conditional_prob=0.8)
    edge3 = CausalEdge(source="volcanic_activity", target="climate_change", conditional_prob=0.5)

    h1 = HypothesisChain(
        id="h1",
        name="asteroid chain",
        description="asteroid -> climate -> extinction",
        variables=[asteroid, climate, extinction],
        edges=[edge1, edge2],
        path_probability=0.72,
        evidence_coverage=0.8,
    )
    h2 = HypothesisChain(
        id="h2",
        name="volcano chain",
        description="volcano -> climate -> extinction",
        variables=[volcanic, climate, extinction],
        edges=[edge3, edge2],
        path_probability=0.4,
        evidence_coverage=0.5,
    )

    return AnalysisResult(
        query="why did dinosaurs go extinct",
        domain="paleontology",
        variables=[asteroid, volcanic, climate, extinction],
        edges=[edge1, edge2, edge3],
        hypotheses=[h1, h2],
        total_evidence_count=4,
    )


def test_find_downstream_variables():
    result = _make_result()
    import networkx as nx

    graph = nx.DiGraph()
    for edge in result.edges:
        graph.add_edge(edge.source, edge.target)

    downstream = find_downstream_variables(graph, "asteroid_impact")
    assert downstream == ["climate_change", "dinosaur_extinction"]


def test_compute_factor_impact_scales_affected_hypothesis():
    result = _make_result()
    intervention = FactorIntervention(
        variable_name="asteroid_impact",
        original_value=0.9,
        new_value=0.45,
    )

    impact = compute_factor_impact(result, intervention)

    assert impact.new_result_probs["h1"] < impact.original_result_probs["h1"]
    assert impact.new_result_probs["h2"] == impact.original_result_probs["h2"]
    assert "h1" in impact.affected_hypotheses


def test_compute_factor_impact_remove_sets_zero():
    result = _make_result()
    intervention = FactorIntervention(
        variable_name="volcanic_activity",
        original_value=0.6,
        new_value=0.0,
        intervention_type="remove",
    )

    impact = compute_factor_impact(result, intervention)

    assert impact.new_result_probs["h2"] == 0.0
    assert impact.new_result_probs["h1"] == impact.original_result_probs["h1"]


def test_compute_factor_impact_result_node_scaling():
    result = _make_result()
    intervention = FactorIntervention(
        variable_name="dinosaur_extinction",
        original_value=0.95,
        new_value=0.475,
    )

    impact = compute_factor_impact(result, intervention)

    assert impact.new_result_probs["h1"] == 0.36
    assert impact.new_result_probs["h2"] == 0.2


def test_compute_factor_impact_bounds():
    result = _make_result()
    intervention = FactorIntervention(
        variable_name="asteroid_impact",
        original_value=0.9,
        new_value=1.0,
    )

    impact = compute_factor_impact(result, intervention)
    for value in impact.new_result_probs.values():
        assert 0.0 <= value <= 1.0


def test_compute_sensitivity_profile():
    result = _make_result()
    profile = compute_sensitivity_profile(result, "asteroid_impact", 0.9, [0.0, 0.5, 1.0])

    assert len(profile) == 3
    assert all(isinstance(point, SensitivityPoint) for point in profile)
    assert profile[0].tested_value == 0.0
    assert profile[-1].tested_value == 1.0
    assert profile[0].hypothesis_probs["h1"] <= profile[-1].hypothesis_probs["h1"]
