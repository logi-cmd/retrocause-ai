"""反事实验证 — 图手术 + 敏感性分析"""

from __future__ import annotations

import logging

import networkx as nx

from retrocause.config import RetroCauseConfig
from retrocause.graph import CausalGraphBuilder
from retrocause.models import (
    AnalysisResult,
    CausalEdge,
    CounterfactualResult,
    FactorIntervention,
    HypothesisChain,
    ImpactResult,
    SensitivityPoint,
)
from retrocause.pipeline import PipelineContext, PipelineStep

logger = logging.getLogger(__name__)


def perform_graph_surgery(
    graph: nx.DiGraph, intervention_var: str, mode: str = "remove"
) -> nx.DiGraph:
    """干预手术: 从因果图副本中移除干预变量。

    mode="remove": 移除节点及其所有边
    mode="intervene": 仅移除入边（硬干预）
    """
    surgical = graph.copy()
    if intervention_var not in surgical:
        return surgical
    if mode == "remove":
        surgical.remove_node(intervention_var)
    elif mode == "intervene":
        surgical.remove_edges_from(list(surgical.in_edges(intervention_var)))
    return surgical


def check_reachability(graph: nx.DiGraph, source_roots: list[str], target: str) -> bool:
    if target not in graph:
        return False
    return any(root in graph and nx.has_path(graph, root, target) for root in source_roots)


def _edge_prob(edges: list[CausalEdge], source: str, target: str) -> float:
    return next(
        (e.conditional_prob for e in edges if e.source == source and e.target == target),
        0.5,
    )


def _path_probability(path: list[str], edges: list[CausalEdge]) -> float:
    p = 1.0
    for i in range(len(path) - 1):
        p *= _edge_prob(edges, path[i], path[i + 1])
    return p


def compute_intervened_probability(
    surgical_graph: nx.DiGraph,
    remaining_roots: list[str],
    target: str,
    all_edges: list[CausalEdge],
) -> float:
    max_prob = 0.0
    for root in remaining_roots:
        if root not in surgical_graph or target not in surgical_graph:
            continue
        try:
            for path in nx.all_simple_paths(surgical_graph, root, target):
                max_prob = max(max_prob, _path_probability(path, all_edges))
        except nx.NetworkXNoPath:
            continue
    return max_prob


def compute_probability_delta(original_prob: float, intervened_prob: float) -> float:
    """original - intervened，钳位 [0, 1]。"""
    return max(0.0, min(1.0, original_prob - intervened_prob))


def compute_sensitivity_bounds(chain: HypothesisChain) -> tuple[float, float]:
    """基于未锚定边比例计算 delta 的可信范围。

    unanchored_ratio 越高 → 边界越宽 → 估计越不确定。
    """
    n_edges = max(len(chain.edges), 1)
    unanchored_ratio = len(chain.unanchored_edges) / n_edges
    delta = chain.path_probability
    lower = delta * max(0.0, 1.0 - unanchored_ratio)
    upper = min(1.0, delta * (1.0 + unanchored_ratio))
    return (max(0.0, lower), max(0.0, upper))


def compute_counterfactual_score(delta: float, sensitivity_width: float, coverage: float) -> float:
    """delta × coverage × (1 - sensitivity_width)，钳位 [0, 1]。

    高 delta (强因果效应) × 高 coverage (证据充分) × 高 robustness (窄敏感性) = 高分。
    """
    robustness = max(0.0, 1.0 - sensitivity_width)
    return max(0.0, min(1.0, delta * coverage * robustness))


def find_downstream_variables(graph: nx.DiGraph, variable: str) -> list[str]:
    if variable not in graph:
        return []
    return sorted(str(node) for node in nx.descendants(graph, variable))


def _scaled_edge_probability(edge: CausalEdge, intervention: FactorIntervention) -> float:
    if intervention.intervention_type == "remove":
        return 0.0

    if intervention.original_value <= 0:
        if intervention.new_value <= 0:
            return 0.0
        ratio = 1.0
    else:
        ratio = intervention.new_value / intervention.original_value

    return max(0.0, min(1.0, edge.conditional_prob * ratio))


def compute_factor_impact(result: AnalysisResult, intervention: FactorIntervention) -> ImpactResult:
    graph = nx.DiGraph()
    for edge in result.edges:
        graph.add_edge(edge.source, edge.target)

    affected_variables = find_downstream_variables(graph, intervention.variable_name)
    impact = ImpactResult(
        intervention=intervention,
        affected_variables=[intervention.variable_name, *affected_variables],
    )

    for hypothesis in result.hypotheses:
        original_prob = max(0.0, min(1.0, hypothesis.path_probability))
        impact.original_result_probs[hypothesis.id] = original_prob

        path_var_names = {variable.name for variable in hypothesis.variables}
        if intervention.variable_name not in path_var_names:
            impact.new_result_probs[hypothesis.id] = original_prob
            impact.probability_deltas[hypothesis.id] = 0.0
            continue

        if intervention.intervention_type == "remove":
            new_prob = 0.0
        elif hypothesis.variables and hypothesis.variables[-1].name == intervention.variable_name:
            if intervention.original_value <= 0:
                ratio = 1.0 if intervention.new_value > 0 else 0.0
            else:
                ratio = intervention.new_value / intervention.original_value
            new_prob = max(0.0, min(1.0, original_prob * ratio))
        else:
            new_prob = 1.0
            cascade_detail: list[dict] = []
            for edge in hypothesis.edges:
                edge_prob = edge.conditional_prob
                if edge.source == intervention.variable_name:
                    new_edge_prob = _scaled_edge_probability(edge, intervention)
                    cascade_detail.append(
                        {
                            "hypothesis_id": hypothesis.id,
                            "edge": f"{edge.source}->{edge.target}",
                            "old_prob": edge_prob,
                            "new_prob": new_edge_prob,
                        }
                    )
                    edge_prob = new_edge_prob
                new_prob *= edge_prob
            impact.cascade_detail.extend(cascade_detail)
            new_prob = max(0.0, min(1.0, new_prob))

        impact.affected_hypotheses.append(hypothesis.id)
        impact.new_result_probs[hypothesis.id] = new_prob
        impact.probability_deltas[hypothesis.id] = new_prob - original_prob

    return impact


def compute_sensitivity_profile(
    result: AnalysisResult,
    variable_name: str,
    original_value: float,
    tested_values: list[float],
) -> list[SensitivityPoint]:
    profile: list[SensitivityPoint] = []
    for value in tested_values:
        impact = compute_factor_impact(
            result,
            FactorIntervention(
                variable_name=variable_name,
                original_value=original_value,
                new_value=value,
            ),
        )
        profile.append(
            SensitivityPoint(
                variable_name=variable_name,
                tested_value=value,
                hypothesis_probs=dict(impact.new_result_probs),
            )
        )
    return profile


class CounterfactualVerificationStep(PipelineStep):
    def __init__(self, graph: CausalGraphBuilder, config: RetroCauseConfig):
        self.graph = graph
        self.config = config

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.hypotheses:
            logger.info("CounterfactualVerificationStep: 无假说链，跳过")
            return ctx

        summaries: list[dict] = []
        for chain in ctx.hypotheses:
            result = self._verify_chain(chain, ctx.edges)
            chain.counterfactual_results.append(result)
            chain.counterfactual_score = result.counterfactual_score
            summaries.append(
                {
                    "hypothesis_id": chain.id,
                    "intervention_var": result.intervention_var,
                    "delta": result.probability_delta,
                    "score": result.counterfactual_score,
                }
            )

        avg_score = sum(s["score"] for s in summaries) / max(len(summaries), 1)
        logger.info(
            "CounterfactualVerificationStep: %d hypotheses, avg score=%.3f",
            len(summaries),
            avg_score,
        )
        ctx.extra["counterfactual"] = {"results": summaries, "average_score": avg_score}
        return ctx

    def _verify_chain(
        self, chain: HypothesisChain, all_edges: list[CausalEdge]
    ) -> CounterfactualResult:
        root_names = set(self.graph.root_nodes())
        chain_root = next((v.name for v in chain.variables if v.name in root_names), None)
        if chain_root is None:
            return self._empty_result(chain)

        result_node = chain.variables[-1].name if chain.variables else ""
        surgical = perform_graph_surgery(self.graph.graph, chain_root, mode="remove")
        remaining_roots = [r for r in root_names if r != chain_root and r in surgical]
        reachable = check_reachability(surgical, remaining_roots, result_node)

        intervened_prob = (
            compute_intervened_probability(surgical, remaining_roots, result_node, all_edges)
            if reachable
            else 0.0
        )
        delta = compute_probability_delta(chain.path_probability, intervened_prob)
        sens_lower, sens_upper = compute_sensitivity_bounds(chain)
        score = compute_counterfactual_score(
            delta, sens_upper - sens_lower, chain.evidence_coverage
        )

        return CounterfactualResult(
            hypothesis_id=chain.id,
            intervention_var=chain_root,
            original_path_prob=chain.path_probability,
            intervened_path_prob=intervened_prob,
            probability_delta=delta,
            still_reachable=reachable,
            sensitivity_lower=sens_lower,
            sensitivity_upper=sens_upper,
            counterfactual_score=score,
        )

    @staticmethod
    def _empty_result(chain: HypothesisChain) -> CounterfactualResult:
        return CounterfactualResult(
            hypothesis_id=chain.id,
            intervention_var="",
            original_path_prob=chain.path_probability,
            intervened_path_prob=chain.path_probability,
            probability_delta=0.0,
            still_reachable=True,
            sensitivity_lower=0.0,
            sensitivity_upper=0.0,
            counterfactual_score=0.0,
        )
