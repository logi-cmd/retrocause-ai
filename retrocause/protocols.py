"""接口协议定义"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from retrocause.llm import ExtractedEvidence
from retrocause.models import (
    AnalysisResult,
    CausalEdge,
    CausalVariable,
    Evidence,
    EvidenceType,
    HypothesisChain,
)
from retrocause.sources.base import SearchResult


@runtime_checkable
class LLMProvider(Protocol):
    """LLM 服务提供者接口"""

    def decompose_query(self, query: str, domain: str) -> list[str]: ...
    def extract_evidence(
        self, query: str, raw_text: str, source_type: str
    ) -> list[ExtractedEvidence]: ...
    def score_relevance(self, query: str, evidence_content: str) -> float: ...
    def build_causal_graph(self, query: str, evidence_texts: list[str], domain: str) -> dict: ...
    def debate_hypothesis(self, hypothesis: HypothesisChain, context: str) -> dict: ...


@runtime_checkable
class SourceAdapter(Protocol):
    """证据源适配器接口"""

    @property
    def name(self) -> str: ...

    @property
    def source_type(self) -> EvidenceType: ...

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]: ...


@runtime_checkable
class GraphProvider(Protocol):
    """因果图操作接口 — 隐藏 NetworkX 实现细节"""

    def add_variable(self, var: CausalVariable) -> None: ...
    def add_edge(self, edge: CausalEdge) -> None: ...
    def root_nodes(self) -> list[str]: ...
    def all_paths(self, source: str, target: str) -> list[list[str]]: ...
    def successors(self, node: str) -> list[str]: ...
    def predecessors(self, node: str) -> list[str]: ...
    def validate_dag(self) -> bool: ...
    def topological_order(self) -> list[str]: ...
    def edge_list(self) -> list[dict]: ...


@runtime_checkable
class EvidenceStore(Protocol):
    """证据存储接口"""

    def add_evidence(
        self,
        content: str,
        source_type: EvidenceType,
        source_url: str | None = None,
        linked_variables: list[str] | None = None,
        reliability: float = 0.5,
    ) -> Evidence | None: ...
    def get_evidence(self) -> list[Evidence]: ...
    def get_evidence_by_variable(self, variable_name: str) -> list[Evidence]: ...


@runtime_checkable
class HypothesisGenerator(Protocol):
    """假说生成器接口"""

    def generate_from_graph(
        self,
        graph: GraphProvider,
        target: str,
        variables: list[CausalVariable],
        edges: list[CausalEdge],
    ) -> list[HypothesisChain]: ...


@runtime_checkable
class DebateRunner(Protocol):
    """辩论执行器接口"""

    def run_debate(self, hypotheses: list[HypothesisChain]) -> list[HypothesisChain]: ...


@runtime_checkable
class ReportFormatter(Protocol):
    """报告格式化器接口"""

    def format(self, result: AnalysisResult) -> str: ...
