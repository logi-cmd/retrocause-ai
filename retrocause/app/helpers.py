from __future__ import annotations

import streamlit as st
from streamlit_agraph import agraph, Config, Edge, Node

from retrocause.models import AnalysisResult, Evidence, HypothesisStatus


def _prob_color(prob: float) -> str:
    if prob >= 0.8:
        return "#2ecc71"
    if prob >= 0.6:
        return "#f39c12"
    if prob >= 0.4:
        return "#e67e22"
    return "#e74c3c"


def _status_badge(status: HypothesisStatus) -> str:
    mapping = {
        HypothesisStatus.ACTIVE: "🟡 活跃",
        HypothesisStatus.DEBATING: "🔵 辩论中",
        HypothesisStatus.REFINED: "🟢 已精炼",
        HypothesisStatus.REFUTED: "🔴 已反驳",
        HypothesisStatus.COLLAPSED: "⚫ 已坍塌",
    }
    return mapping.get(status, str(status))


def _build_graph_config() -> Config:
    return Config(
        width=900,
        height=500,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=True,
    )


def _render_graph(result: AnalysisResult) -> str | None:
    nodes = []
    for v in result.variables:
        opacity = max(0.3, v.posterior_support)
        size = 15 + int(v.posterior_support * 25)
        nodes.append(
            Node(
                id=v.name,
                label=v.name.replace("_", "\n"),
                size=size,
                color=f"rgba(52, 152, 219, {opacity:.2f})",
                title=f"{v.description}\n后验支持: {v.posterior_support:.2f}",
            )
        )

    agraph_edges = []
    for e in result.edges:
        color = _prob_color(e.conditional_prob)
        width = max(1, int(e.conditional_prob * 8))
        agraph_edges.append(
            Edge(
                source=e.source,
                target=e.target,
                color=color,
                width=width,
            )
        )

    config = _build_graph_config()
    return agraph(nodes=nodes, edges=agraph_edges, config=config)


def _get_evidences(result: AnalysisResult) -> list[Evidence]:
    if "demo_evidences" in st.session_state:
        return st.session_state["demo_evidences"]
    return []
