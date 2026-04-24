"""主引擎 — 基于 Pipeline 的可组合分析流程"""

from __future__ import annotations

import copy
import logging
import re
import threading
import time

from retrocause.models import AnalysisResult, CausalEdge, CausalVariable, HypothesisChain
from retrocause.parser import parse_input, ParsedQuery
from retrocause.collector import EvidenceCollector, configure_source_limits
from retrocause.evidence_store import EvidenceStore
from retrocause.evidence_access import time_scope_key
from retrocause.graph import CausalGraphBuilder
from retrocause.hypothesis import HypothesisGenerator
from retrocause.debate import DebateOrchestrator
from retrocause.formatter import ReportFormatter
from retrocause.config import RetroCauseConfig
from retrocause.pipeline import Pipeline, PipelineContext, PipelineStep, ProgressCallback
from retrocause.anchoring import EvidenceAnchoringStep, reanchor_hypotheses
from retrocause.counterfactual import CounterfactualVerificationStep
from retrocause.evaluation import EvaluationStep
from retrocause.uncertainty import UncertaintyAssessmentStep
from retrocause.protocols import LLMProvider, SourceAdapter
from retrocause.hooks import HookEngine
from retrocause.rules import (
    CounterfactualBoundRule,
    EvidenceCoverageRule,
    ProbabilityBoundRule,
)

logger = logging.getLogger(__name__)
_ANALYSIS_CACHE: dict[str, tuple[float, AnalysisResult]] = {}
_INFLIGHT_ANALYSES: dict[str, threading.Event] = {}
_ANALYSIS_LOCK = threading.Lock()


def _summarize_freshness(evidences: list) -> str:
    if not evidences:
        return "unknown"

    freshness_values = {getattr(ev, "freshness", "unknown") for ev in evidences}
    if "fresh" in freshness_values:
        return "fresh"
    if "recent" in freshness_values and "stable" in freshness_values:
        return "mixed"
    if "recent" in freshness_values:
        return "recent"
    if "stable" in freshness_values:
        return "stable"
    return "unknown"


def _infer_analysis_mode(evidences: list) -> str:
    if not evidences:
        return "partial_live"
    fallback_count = sum(
        1 for ev in evidences if getattr(ev, "extraction_method", "") == "fallback_summary"
    )
    if fallback_count and fallback_count / max(len(evidences), 1) >= 0.25:
        return "partial_live"
    quality_anchor_count = sum(
        1
        for ev in evidences
        if getattr(ev, "extraction_method", "")
        in {"llm_fulltext_trusted", "llm_fulltext", "store_cache", "llm_trusted"}
    )
    if quality_anchor_count == 0:
        return "partial_live"
    return "live"


def _evidence_quality_score(evidence) -> float:
    method = getattr(evidence, "extraction_method", "manual")
    score = float(getattr(evidence, "posterior_reliability", 0.5))
    if method == "fallback_summary":
        score *= 0.45
    elif method == "store_cache":
        score *= 0.95
    elif method == "llm_fulltext_trusted":
        score = min(1.0, score + 0.12)
    elif method == "llm_fulltext":
        score = min(1.0, score + 0.08)
    elif method == "llm_trusted":
        score = min(1.0, score + 0.04)
    elif method == "llm":
        score *= 1.0
    if getattr(evidence, "source_tier", "base") == "base":
        score += 0.05
    return max(0.1, min(1.0, score))


def _select_graph_evidence_texts(evidences: list, limit: int = 12) -> list[str]:
    ranked = sorted(evidences, key=_evidence_quality_score, reverse=True)
    high_quality = [ev for ev in ranked if _evidence_quality_score(ev) >= 0.65]
    chosen = high_quality[:limit] if high_quality else ranked[:limit]
    return [ev.content for ev in chosen]


def _average_quality(evidences: list) -> float:
    if not evidences:
        return 0.45
    return sum(_evidence_quality_score(ev) for ev in evidences) / len(evidences)


def _is_time_sensitive(parsed: ParsedQuery) -> bool:
    return parsed.time_range is not None or parsed.domain in {"finance", "business"}


def _is_cjk_time_sensitive_market(ctx: PipelineContext) -> bool:
    return (
        ctx.domain in {"finance", "business"}
        and bool(ctx.extra.get("time_range"))
        and bool(re.search(r"[\u4e00-\u9fff]", ctx.query))
    )


def _source_signature(source_adapters: list[SourceAdapter] | None) -> str:
    if source_adapters is None:
        return "sources:none"
    names = sorted(getattr(adapter, "name", adapter.__class__.__name__) for adapter in source_adapters)
    return "sources:" + ",".join(names)


def _query_key(parsed: ParsedQuery, source_adapters: list[SourceAdapter] | None = None) -> str:
    time_scope = time_scope_key(parsed.time_range) or "evergreen"
    return f"{parsed.domain}::{time_scope}::{_source_signature(source_adapters)}::{parsed.query.strip().lower()}"


def _cache_ttl(parsed: ParsedQuery, config: RetroCauseConfig) -> float:
    if _is_time_sensitive(parsed):
        return config.hot_query_cache_seconds
    return config.evergreen_query_cache_seconds


def _time_quality_ok(parsed: ParsedQuery, evidences: list) -> bool:
    if not _is_time_sensitive(parsed):
        return True
    return any(getattr(ev, "freshness", "unknown") in {"fresh", "recent"} for ev in evidences)


def _clamp_probability(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _normalize_signal(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _signal_tokens(text: str) -> set[str]:
    latin_tokens = {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text.lower().replace("_", " "))
        if token
        not in {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "into",
            "about",
            "because",
        }
    }
    cjk_tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}", text))
    return latin_tokens | cjk_tokens


def _cjk_phrases(text: str) -> set[str]:
    phrases: set[str] = set()
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        phrases.add(chunk)
        max_window = min(6, len(chunk))
        for size in range(2, max_window + 1):
            for index in range(0, len(chunk) - size + 1):
                phrases.add(chunk[index : index + size])
    return phrases


def _evidence_matches_variable(evidence, variable_name: str, description: str = "") -> bool:
    evidence_text = (
        f"{getattr(evidence, 'content', '')} "
        f"{' '.join(getattr(evidence, 'linked_variables', []) or [])}"
    )
    for phrase in _cjk_phrases(f"{variable_name} {description}"):
        if phrase in evidence_text:
            return True

    normalized_name = _normalize_signal(variable_name)
    evidence_signals = [
        _normalize_signal(item) for item in getattr(evidence, "linked_variables", []) or []
    ]
    if normalized_name in evidence_signals:
        return True

    content_signal = _normalize_signal(getattr(evidence, "content", ""))
    if normalized_name and normalized_name in content_signal:
        return True

    variable_tokens = _signal_tokens(f"{variable_name} {description}")
    if not variable_tokens:
        return False
    content_tokens = _signal_tokens(
        f"{getattr(evidence, 'content', '')} {' '.join(getattr(evidence, 'linked_variables', []) or [])}"
    )
    overlap = variable_tokens & content_tokens
    return len(overlap) >= min(2, len(variable_tokens))


def _collect_variable_evidence(evidences: list, variable_name: str, description: str = "") -> list:
    return [
        ev
        for ev in evidences
        if _evidence_matches_variable(ev, variable_name, description)
    ]


def _collect_edge_evidence(evidences: list, source: str, target: str) -> list:
    linked: list = []
    for evidence in evidences:
        if _evidence_matches_variable(evidence, source) or _evidence_matches_variable(evidence, target):
            linked.append(evidence)
    return linked


def _fallback_market_graph_from_evidence(query: str, evidences: list) -> dict:
    """Build a conservative, evidence-anchored market graph when LLM DAG extraction fails."""
    if not evidences:
        return {}

    text = "\n".join(str(getattr(evidence, "content", "") or "") for evidence in evidences)
    result_variable = "stock_price_decline"
    result_description = f"Observed market move in the user query: {query}"
    cause_specs: list[tuple[str, str, tuple[str, ...]]] = [
        (
            "sector_pressure",
            "Retrieved evidence mentions sector or semiconductor pressure around the move.",
            ("板块", "半导体", "芯片", "sector", "semiconductor", "chip"),
        ),
        (
            "fund_flow_pressure",
            "Retrieved evidence mentions selling pressure, capital flow, or fund-flow pressure.",
            ("资金", "流出", "主力", "卖出", "selloff", "selling", "outflow"),
        ),
        (
            "company_news_flow",
            "Retrieved evidence mentions company news, earnings, orders, guidance, or disclosures.",
            ("公告", "业绩", "收入", "订单", "指引", "earnings", "revenue", "guidance"),
        ),
        (
            "broader_market_pressure",
            "Retrieved evidence mentions broader market, index, or risk-sentiment pressure.",
            ("市场", "指数", "A股", "情绪", "market", "index", "risk"),
        ),
    ]

    variables = [
        {
            "name": result_variable,
            "description": result_description,
        }
    ]
    edges: list[dict] = []
    lowered_text = text.lower()
    for name, description, markers in cause_specs:
        if not any(marker.lower() in lowered_text for marker in markers):
            continue
        variables.append({"name": name, "description": description})
        edges.append(
            {
                "source": name,
                "target": result_variable,
                "conditional_prob": 0.48,
                "description": description,
            }
        )

    if not edges:
        variables.append(
            {
                "name": "retrieved_market_context",
                "description": "Retrieved source context is relevant to the market move, but no specific cause label was extracted.",
            }
        )
        edges.append(
            {
                "source": "retrieved_market_context",
                "target": result_variable,
                "conditional_prob": 0.38,
                "description": "Use as context only until a stronger cause label is extracted.",
            }
        )

    return {
        "variables": variables,
        "edges": edges,
        "result_variable": result_variable,
    }


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
        self._evidence_store = EvidenceStore()
        configure_source_limits(
            min_interval_seconds=self._config.source_min_interval_seconds,
            source_error_cooldown_seconds=self._config.source_error_cooldown_seconds,
        )

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if self._llm_client is None or self._source_adapters is None:
            logger.info("EvidenceCollectionStep: 无 LLM/源配置，跳过自动收集")
            return ctx
        time_scope = ctx.extra.get("time_scope_key")
        cached_evidence = self._evidence_store.search(
            ctx.query,
            ctx.domain,
            limit=8,
            time_scope=time_scope,
        )
        for evidence in cached_evidence:
            self.collector.add_evidence(
                content=evidence.content,
                source_type=evidence.source_type,
                source_url=evidence.source_url,
                linked_variables=evidence.linked_variables,
                reliability=evidence.posterior_reliability,
                timestamp=evidence.timestamp,
                extraction_method="store_cache",
                source_tier=evidence.source_tier,
                freshness=evidence.freshness,
                captured_at=evidence.captured_at,
            )

        self.collector.auto_collect(
            query=ctx.query,
            domain=ctx.domain,
            llm_client=self._llm_client,
            source_adapters=self._source_adapters,
            max_sub_queries=self._config.max_sub_queries,
            max_results_per_source=self._config.max_results_per_source,
            time_range=ctx.extra.get("time_range"),
        )
        evidence = self.collector.get_evidence()
        ctx.total_evidence_count = len(evidence)
        ctx.extra["evidences"] = evidence
        ctx.extra["evidence_access_trace"] = [
            {
                "source": item.name,
                "query": item.query,
                "result_count": item.result_count,
                "cache_hit": item.cache_hit,
                "error": item.error,
            }
            for item in self.collector.access_trace
        ]
        self._evidence_store.add_evidences(
            ctx.query,
            ctx.domain,
            evidence,
            time_scope=time_scope,
        )
        if not evidence:
            logger.warning("EvidenceCollectionStep: 证据收集结果为空")
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
            logger.warning("GraphBuildingStep: 无 LLM 客户端，跳过")
            return ctx

        if not hasattr(self._llm_client, "build_causal_graph"):
            logger.warning("GraphBuildingStep: LLM 客户端无 build_causal_graph 方法")
            return ctx

        evidence = self.collector.get_evidence()
        if not evidence:
            logger.warning("GraphBuildingStep: 无证据，跳过因果图构建")
            return ctx

        evidence_texts = _select_graph_evidence_texts(evidence)
        result = self._llm_client.build_causal_graph(ctx.query, evidence_texts, ctx.domain)

        if not result:
            if _is_cjk_time_sensitive_market(ctx):
                result = _fallback_market_graph_from_evidence(ctx.query, evidence)
                if result:
                    ctx.extra["fallback_graph_reason"] = "llm_graph_empty"
                    ctx.extra.setdefault("pipeline_notes", []).append(
                        "Used a conservative evidence-anchored fallback market graph after LLM graph extraction returned empty."
                    )
                    logger.warning(
                        "GraphBuildingStep: build_causal_graph 返回空结果，使用财经 fallback 图"
                    )
                else:
                    logger.warning("GraphBuildingStep: build_causal_graph 返回空结果")
                    return ctx
            else:
                logger.warning("GraphBuildingStep: build_causal_graph 返回空结果")
                return ctx

        evidence_by_variable_name: dict[str, list] = {}
        for var_data in result.get("variables", []):
            linked_evidence = _collect_variable_evidence(
                evidence,
                var_data["name"],
                var_data.get("description", ""),
            )
            evidence_by_variable_name[var_data["name"]] = linked_evidence
            var = CausalVariable(
                name=var_data["name"],
                description=var_data.get("description", ""),
                evidence_ids=[ev.id for ev in linked_evidence],
                posterior_support=_clamp_probability(
                    _average_quality(linked_evidence),
                    minimum=0.3,
                    maximum=1.0,
                ),
            )
            self.graph.add_variable(var)
            ctx.variables.append(var)

        for edge_data in result.get("edges", []):
            source_name = edge_data["source"]
            target_name = edge_data["target"]
            linked_evidence_by_id = {
                ev.id: ev
                for ev in (
                    evidence_by_variable_name.get(source_name, [])
                    + evidence_by_variable_name.get(target_name, [])
                    + _collect_edge_evidence(evidence, source_name, target_name)
                )
            }
            linked_evidence = list(linked_evidence_by_id.values())
            quality_factor = _average_quality(linked_evidence)
            conditional_prob = float(edge_data.get("conditional_prob", 0.5))
            weighted_probability = conditional_prob * (0.7 + 0.3 * quality_factor)
            if linked_evidence:
                weighted_probability = max(weighted_probability, conditional_prob * 0.75)
            edge = CausalEdge(
                source=source_name,
                target=target_name,
                conditional_prob=_clamp_probability(weighted_probability),
                supporting_evidence_ids=[ev.id for ev in linked_evidence],
            )
            self.graph.add_edge(edge)
            ctx.edges.append(edge)

        ctx.extra["result_variable"] = result.get("result_variable", "")
        logger.info(
            "GraphBuildingStep: 构建 %d 变量, %d 边, result=%s",
            len(ctx.variables),
            len(ctx.edges),
            ctx.extra["result_variable"],
        )

        return ctx


class HypothesisGenerationStep(PipelineStep):
    """假说链生成步骤"""

    def __init__(self, graph: CausalGraphBuilder, gen: HypothesisGenerator):
        self.graph = graph
        self.gen = gen

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        result_node = ctx.extra.get("result_variable", "")
        if not result_node or not ctx.variables:
            logger.warning(
                "HypothesisGenerationStep: 跳过 (result_node=%s, variables=%d)",
                result_node or "(empty)",
                len(ctx.variables),
            )
            return ctx
        ctx.hypotheses = self.gen.generate_from_graph(
            self.graph,
            result_node,
            ctx.variables,
            ctx.edges,
        )
        logger.info("HypothesisGenerationStep: 生成 %d 条假说链", len(ctx.hypotheses))
        return ctx


class DebateRefinementStep(PipelineStep):
    """6角色辩论精炼步骤"""

    def __init__(self, orchestrator: DebateOrchestrator):
        self.orchestrator = orchestrator

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.hypotheses:
            self.orchestrator.run_debate(ctx.hypotheses)
        return ctx


class CausalRAGStep(PipelineStep):
    """graph-guided 第二轮检索 — 仅在证据覆盖不足时触发"""

    COVERAGE_THRESHOLD = 0.5

    def __init__(
        self,
        collector: EvidenceCollector,
        llm_client: LLMProvider | None = None,
        source_adapters: list[SourceAdapter] | None = None,
    ):
        self.collector = collector
        self._llm_client = llm_client
        self._source_adapters = source_adapters

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if self._llm_client is None or self._source_adapters is None:
            return ctx
        if not ctx.variables or not ctx.edges:
            return ctx
        if _is_cjk_time_sensitive_market(ctx):
            logger.info("CausalRAGStep: skipping second retrieval for fast Chinese market path")
            ctx.extra.setdefault("pipeline_notes", []).append(
                "Skipped graph-guided second retrieval for a time-sensitive Chinese market query."
            )
            return ctx

        covered_vars = sum(1 for v in ctx.variables if v.evidence_ids)
        coverage = covered_vars / max(len(ctx.variables), 1)
        if coverage >= self.COVERAGE_THRESHOLD:
            logger.info(
                "CausalRAGStep: 变量覆盖率 %.0f%% >= %.0f%%，跳过第二轮检索",
                coverage * 100,
                self.COVERAGE_THRESHOLD * 100,
            )
            return ctx

        logger.info(
            "CausalRAGStep: 变量覆盖率 %.0f%% < %.0f%%，启动定向补充检索",
            coverage * 100,
            self.COVERAGE_THRESHOLD * 100,
        )

        self.collector.graph_guided_collect(
            query=ctx.query,
            domain=ctx.domain,
            variables=ctx.variables,
            edges=ctx.edges,
            llm_client=self._llm_client,
            source_adapters=self._source_adapters,
            max_results_per_source=3,
            time_range=ctx.extra.get("time_range"),
        )
        ctx.total_evidence_count = len(self.collector.get_evidence())
        ctx.extra["evidences"] = self.collector.get_evidence()
        reanchor_hypotheses(ctx, self.collector)
        return ctx


class RefutationCoverageStep(PipelineStep):
    """Challenge the strongest causal edges with targeted counter-evidence retrieval."""

    def __init__(
        self,
        collector: EvidenceCollector,
        llm_client: LLMProvider | None = None,
        source_adapters: list[SourceAdapter] | None = None,
    ):
        self.collector = collector
        self._llm_client = llm_client
        self._source_adapters = source_adapters

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if self._llm_client is None or self._source_adapters is None:
            return ctx
        if not ctx.hypotheses:
            return ctx
        if _is_cjk_time_sensitive_market(ctx):
            logger.info("RefutationCoverageStep: skipping challenge retrieval for fast Chinese market path")
            ctx.extra.setdefault("pipeline_notes", []).append(
                "Skipped targeted challenge retrieval for a time-sensitive Chinese market query."
            )
            return ctx

        candidate_edges: list[CausalEdge] = []
        for chain in ctx.hypotheses[:3]:
            candidate_edges.extend(chain.edges)
        if not candidate_edges:
            return ctx

        new_evidence, checks = self.collector.collect_refutations(
            query=ctx.query,
            domain=ctx.domain,
            edges=candidate_edges,
            llm_client=self._llm_client,
            source_adapters=self._source_adapters,
            max_edges=3,
            max_results_per_source=2,
            time_range=ctx.extra.get("time_range"),
        )
        ctx.extra["refutation_checks"] = checks
        if new_evidence:
            ctx.total_evidence_count = len(self.collector.get_evidence())
            ctx.extra["evidences"] = self.collector.get_evidence()
            reanchor_hypotheses(ctx, self.collector)
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
                CausalRAGStep(
                    self.collector,
                    self._llm_client,
                    self._source_adapters,
                ),
                RefutationCoverageStep(
                    self.collector,
                    self._llm_client,
                    self._source_adapters,
                ),
                CounterfactualVerificationStep(self.graph, self._config),
                DebateRefinementStep(
                    DebateOrchestrator(
                        max_rounds=self._config.debate_max_rounds,
                        llm_client=self._llm_client,
                    )
                ),
                UncertaintyAssessmentStep(self.collector),
                EvaluationStep(),
            ],
            hook_engine=hook_engine,
        )

    def run(self, on_progress: ProgressCallback | None = None) -> AnalysisResult:
        ctx = PipelineContext(query=self.query, domain=self.parsed.domain, on_progress=on_progress)
        ctx.extra["time_range"] = self.parsed.time_range
        ctx.extra["time_scope_key"] = time_scope_key(self.parsed.time_range)
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
            evidences=self.collector.get_evidence(),
            total_evidence_count=len(self.collector.get_evidence()),
            evaluation=ctx.evaluation,
            uncertainty_report=ctx.extra.get("uncertainty_report"),
        )
        result.total_uncertainty = ctx.total_uncertainty
        result.retrieval_trace = [
            {
                "source": item.name,
                "query": item.query,
                "result_count": item.result_count,
                "cache_hit": item.cache_hit,
                "error": item.error,
                "status": item.status,
                "retry_after_seconds": item.retry_after_seconds,
                "source_label": item.source_label,
                "source_kind": item.source_kind,
                "stability": item.stability,
                "cache_policy": item.cache_policy,
            }
            for item in self.collector.access_trace
        ]
        result.refutation_checks = ctx.extra.get("refutation_checks", [])
        result.analysis_mode = _infer_analysis_mode(result.evidences)
        result.freshness_status = _summarize_freshness(result.evidences)
        if not _time_quality_ok(self.parsed, result.evidences):
            result.analysis_mode = "partial_live"
            result.recommended_next_steps.append(
                "Fresh evidence is insufficient for the inferred time window."
            )
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
    on_progress: ProgressCallback | None = None,
) -> AnalysisResult:
    resolved_config = config or RetroCauseConfig()
    if llm_client is None or source_adapters is None:
        return RetroCauseEngine(
            query,
            llm_client=llm_client,
            source_adapters=source_adapters,
            config=resolved_config,
        ).run(on_progress=on_progress)

    parsed = parse_input(query)
    cache_key = _query_key(parsed, source_adapters)
    ttl = _cache_ttl(parsed, resolved_config)
    now = time.time()

    with _ANALYSIS_LOCK:
        cached = _ANALYSIS_CACHE.get(cache_key)
        if cached and now - cached[0] <= ttl:
            return copy.deepcopy(cached[1])

        inflight = _INFLIGHT_ANALYSES.get(cache_key)
        if inflight is None:
            inflight = threading.Event()
            _INFLIGHT_ANALYSES[cache_key] = inflight
            is_owner = True
        else:
            is_owner = False

    if not is_owner:
        inflight.wait(timeout=max(5.0, resolved_config.request_timeout_seconds))
        with _ANALYSIS_LOCK:
            cached = _ANALYSIS_CACHE.get(cache_key)
            if cached:
                return copy.deepcopy(cached[1])
        return RetroCauseEngine(
            query,
            llm_client=llm_client,
            source_adapters=source_adapters,
            config=resolved_config,
        ).run(on_progress=on_progress)

    try:
        result = RetroCauseEngine(
            query,
            llm_client=llm_client,
            source_adapters=source_adapters,
            config=resolved_config,
        ).run(on_progress=on_progress)
        with _ANALYSIS_LOCK:
            _ANALYSIS_CACHE[cache_key] = (time.time(), copy.deepcopy(result))
        return result
    finally:
        with _ANALYSIS_LOCK:
            event = _INFLIGHT_ANALYSES.pop(cache_key, None)
            if event is not None:
                event.set()


def analyze_and_print(
    query: str,
    llm_client: LLMProvider | None = None,
    source_adapters: list[SourceAdapter] | None = None,
    config: RetroCauseConfig | None = None,
    on_progress: ProgressCallback | None = None,
) -> str:
    result = analyze(
        query,
        llm_client=llm_client,
        source_adapters=source_adapters,
        config=config,
        on_progress=on_progress,
    )
    return ReportFormatter().format(result)
