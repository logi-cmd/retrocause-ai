"""假说链生成 — 从根因逆溯因果图到结果"""

from __future__ import annotations

from retrocause.models import CausalEdge, CausalVariable, HypothesisChain, HypothesisStatus
from retrocause.protocols import GraphProvider


class HypothesisGenerator:
    _counter: int

    def __init__(self):
        self._counter = 0

    def generate_from_graph(
        self,
        graph: GraphProvider,
        result_node: str,
        variables: list[CausalVariable],
        edges: list[CausalEdge],
    ) -> list[HypothesisChain]:
        root_names = set(graph.root_nodes())
        root_causes = [v for v in variables if v.name in root_names]

        chains: list[HypothesisChain] = []
        for root in root_causes:
            if root.name == result_node:
                continue
            paths = graph.all_paths(root.name, result_node)
            for path in paths:
                self._counter += 1
                path_edges = self._edges_on_path(path, edges)
                if not path_edges:
                    continue
                path_prob = 1.0
                for e in path_edges:
                    path_prob *= e.conditional_prob
                path_vars = [v for v in variables if v.name in path]
                chains.append(
                    HypothesisChain(
                        id=f"chain-{self._counter:03d}",
                        name=f"{root.description} → {result_node}",
                        description=f"因果路径: {' → '.join(path)}",
                        variables=path_vars,
                        edges=path_edges,
                        path_probability=path_prob,
                        posterior_probability=path_prob,
                        confidence_interval=(max(0, path_prob - 0.1), min(1, path_prob + 0.1)),
                        status=HypothesisStatus.ACTIVE,
                    )
                )

        chains.sort(key=lambda c: c.path_probability, reverse=True)
        return chains

    def _edges_on_path(self, path: list[str], edges: list[CausalEdge]) -> list[CausalEdge]:
        result: list[CausalEdge] = []
        for i in range(len(path) - 1):
            for e in edges:
                if e.source == path[i] and e.target == path[i + 1]:
                    result.append(e)
                    break
        return result
