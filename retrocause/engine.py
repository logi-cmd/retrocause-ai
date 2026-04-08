"""主引擎 — 基于 Pipeline 的可组合分析流程"""

from __future__ import annotations

import logging

from retrocause.models import AnalysisResult, CausalEdge, CausalVariable, HypothesisChain
from retrocause.parser import parse_input, ParsedQuery
from retrocause.collector import EvidenceCollector
from retrocause.graph import CausalGraphBuilder
from retrocause.hypothesis import HypothesisGenerator
from retrocause.debate import DebateOrchestrator
from retrocause.formatter import ReportFormatter
from retrocause.config import RetroCauseConfig
from retrocause.pipeline import Pipeline, PipelineContext, PipelineStep
from retrocause.anchoring import EvidenceAnchoringStep
from retrocause.counterfactual import CounterfactualVerificationStep
from retrocause.evaluation import EvaluationStep
from retrocause.protocols import LLMProvider, SourceAdapter
from retrocause.hooks import HookEngine
from retrocause.rules import (
    CounterfactualBoundRule,
    EvidenceCoverageRule,
    ProbabilityBoundRule,
)

logger = logging.getLogger(__name__)


class EvidenceCollectionStep(PipelineStep):
    """证据收集步骤"""

    def __init__(
        self,
        collector: EvidenceCollector,
        llm_client: LLMProvider | None = None,
        source_adapters: list[SourceAdapter] | None = None,
        config: RetroCauseConfig | None = None,
    ):
        self.collector = collector
        self._llm_client = llm_client
        self._source_adapters = source_adapters
        self._config = config or RetroCauseConfig()

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if self._llm_client is None or self._source_adapters is None:
            logger.info("EvidenceCollectionStep: 无 LLM/源配置，跳过自动收集")
            return ctx
        self.collector.auto_collect(
            query=ctx.query,
            domain=ctx.domain,
            llm_client=self._llm_client,
            source_adapters=self._source_adapters,
            max_sub_queries=self._config.max_sub_queries,
            max_results_per_source=self._config.max_results_per_source,
        )
        ctx.total_evidence_count = len(self.collector.get_evidence())
        return ctx


class GraphBuildingStep(PipelineStep):
    """因果图构建步骤"""

    def __init__(
        self,
        graph: CausalGraphBuilder,
        collector: EvidenceCollector,
        llm_client: LLMProvider | None = None,
    ):
        self.graph = graph
        self.collector = collector
        self._llm_client = llm_client

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if self._llm_client is None:
            return ctx

        if not hasattr(self._llm_client, "build_causal_graph"):
            return ctx

        evidence = self.collector.get_evidence()
        if not evidence:
            return ctx

        evidence_texts = [ev.content for ev in evidence]
        result = self._llm_client.build_causal_graph(ctx.query, evidence_texts, ctx.domain)

        if not result:
            return ctx

        for var_data in result.get("variables", []):
            var = CausalVariable(
                name=var_data["name"],
                description=var_data.get("description", ""),
            )
            self.graph.add_variable(var)
            ctx.variables.append(var)

        for edge_data in result.get("edges", []):
            edge = CausalEdge(
                source=edge_data["source"],
                target=edge_data["target"],
                conditional_prob=float(edge_data.get("conditional_prob", 0.5)),
            )
            self.graph.add_edge(edge)
            ctx.edges.append(edge)

        ctx.extra["result_variable"] = result.get("result_variable", "")

        return ctx


class HypothesisGenerationStep(PipelineStep):
    """假说链生成步骤"""

    def __init__(self, graph: CausalGraphBuilder, gen: HypothesisGenerator):
        self.graph = graph
        self.gen = gen

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        result_node = ctx.extra.get("result_variable", "")
        if not result_node or not ctx.variables:
            return ctx
        ctx.hypotheses = self.gen.generate_from_graph(
            self.graph,
            result_node,
            ctx.variables,
            ctx.edges,
        )
        return ctx


class DebateRefinementStep(PipelineStep):
    """6角色辩论精炼步骤"""

    def __init__(self, orchestrator: DebateOrchestrator):
        self.orchestrator = orchestrator

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.hypotheses:
            self.orchestrator.run_debate(ctx.hypotheses)
        return ctx


class RetroCauseEngine:
    """向后兼容的引擎封装"""

    query: str
    parsed: ParsedQuery
    collector: EvidenceCollector
    graph: CausalGraphBuilder
    variables: list[CausalVariable]
    edges: list[CausalEdge]
    hypotheses: list[HypothesisChain]
    _llm_client: LLMProvider | None
    _source_adapters: list[SourceAdapter] | None
    _config: RetroCauseConfig
    _pipeline: Pipeline

    def __init__(
        self,
        query: str,
        llm_client: LLMProvider | None = None,
        source_adapters: list[SourceAdapter] | None = None,
        config: RetroCauseConfig | None = None,
    ):
        self.query = query
        self.parsed = parse_input(query)
        self.collector = EvidenceCollector()
        self.graph = CausalGraphBuilder()
        self.variables: list[CausalVariable] = []
        self.edges: list[CausalEdge] = []
        self.hypotheses: list[HypothesisChain] = []
        self._llm_client = llm_client
        self._source_adapters = source_adapters
        self._config = config or RetroCauseConfig()
        self._pipeline = self._build_pipeline()

    def _build_pipeline(self) -> Pipeline:
        hook_engine = HookEngine(
            [
                ProbabilityBoundRule(),
                EvidenceCoverageRule(),
                CounterfactualBoundRule(min_score=self._config.counterfactual_min_score),
            ]
        )
        return Pipeline(
            [
                EvidenceCollectionStep(
                    self.collector,
                    self._llm_client,
                    self._source_adapters,
                    config=self._config,
                ),
                GraphBuildingStep(self.graph, self.collector, self._llm_client),
                HypothesisGenerationStep(self.graph, HypothesisGenerator()),
                EvidenceAnchoringStep(self.collector),
                CounterfactualVerificationStep(self.graph, self._config),
                DebateRefinementStep(
                    DebateOrchestrator(
                        max_rounds=self._config.debate_max_rounds,
                        llm_client=self._llm_client,
                    )
                ),
                EvaluationStep(),
            ],
            hook_engine=hook_engine,
        )

    def run(self) -> AnalysisResult:
        ctx = PipelineContext(query=self.query, domain=self.parsed.domain)
        ctx = self._pipeline.run(ctx)
        self.hypotheses = ctx.hypotheses
        self.variables = ctx.variables
        self.edges = ctx.edges
        return self._compile_result(ctx)

    def _compile_result(self, ctx: PipelineContext) -> AnalysisResult:
        result = AnalysisResult(
            query=self.query,
            domain=ctx.domain,
            variables=ctx.variables,
            edges=ctx.edges,
            hypotheses=ctx.hypotheses,
            total_evidence_count=len(self.collector.get_evidence()),
            evaluation=ctx.evaluation,
        )
        result.total_uncertainty = float(len(ctx.violations) + len(ctx.step_errors))
        if ctx.violations:
            result.recommended_next_steps.extend(
                [f"Review validation warning: {item['message']}" for item in ctx.violations]
            )
        if ctx.step_errors:
            result.recommended_next_steps.extend(
                [f"Retry failed step: {item['step']} ({item['error']})" for item in ctx.step_errors]
            )
        return result


def analyze(
    query: str,
    llm_client: LLMProvider | None = None,
    source_adapters: list[SourceAdapter] | None = None,
    config: RetroCauseConfig | None = None,
) -> AnalysisResult:
    return RetroCauseEngine(
        query, llm_client=llm_client, source_adapters=source_adapters, config=config
    ).run()


def analyze_and_print(
    query: str,
    llm_client: LLMProvider | None = None,
    source_adapters: list[SourceAdapter] | None = None,
    config: RetroCauseConfig | None = None,
) -> str:
    result = analyze(query, llm_client=llm_client, source_adapters=source_adapters, config=config)
    return ReportFormatter().format(result)
