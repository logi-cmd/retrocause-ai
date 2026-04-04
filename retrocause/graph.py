"""因果图构建 + DAG操作"""

from __future__ import annotations

import networkx as nx

from retrocause.models import CausalEdge, CausalVariable


class CausalGraphBuilder:
    graph: nx.DiGraph

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_variable(self, var: CausalVariable) -> None:
        self.graph.add_node(var.name, description=var.description, support=var.posterior_support)

    def add_edge(self, edge: CausalEdge) -> None:
        self.graph.add_edge(
            edge.source,
            edge.target,
            weight=edge.conditional_prob,
            ci=edge.confidence_interval,
        )

    def validate_dag(self) -> bool:
        return nx.is_directed_acyclic_graph(self.graph)

    def get_paths(self, source: str, target: str) -> list[list[str]]:
        if source not in self.graph or target not in self.graph:
            return []
        return list(nx.all_simple_paths(self.graph, source, target))

    def all_paths(self, source: str, target: str) -> list[list[str]]:
        return self.get_paths(source, target)

    def inverse_paths_from(self, target: str) -> list[list[str]]:
        if target not in self.graph:
            return []
        rev = self.graph.reverse()
        return list(nx.dfs_edges(rev, target))

    def root_nodes(self) -> list[str]:
        return [n for n in self.graph if self.graph.in_degree(n) == 0]

    def topological_order(self) -> list[str]:
        return list(nx.topological_sort(self.graph))

    def topological_vars(self) -> list[str]:
        return self.topological_order()

    def predecessors(self, node: str) -> list[str]:
        return list(self.graph.predecessors(node))

    def successors(self, node: str) -> list[str]:
        return list(self.graph.successors(node))

    def to_edge_list(self) -> list[dict]:
        return self.edge_list()

    def edge_list(self) -> list[dict]:
        return [
            {"source": u, "target": v, "weight": d.get("weight", 0.5)}
            for u, v, d in self.graph.edges(data=True)
        ]
