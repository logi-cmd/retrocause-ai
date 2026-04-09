"""证据收集协调器 — 手动 + LLM 自动收集 + graph-guided retrieval"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from retrocause.models import CausalEdge, CausalVariable, Evidence, EvidenceType

logger = logging.getLogger(__name__)


class SearchResult:
    """搜索适配器返回的单条搜索结果"""

    __slots__ = ("title", "content", "source_type", "url")

    def __init__(self, title: str, content: str, source_type: EvidenceType, url: str = ""):
        self.title = title
        self.content = content
        self.source_type = source_type
        self.url = url


def _parallel_search(
    sub_query: str,
    source_adapters: list[object],
    max_results: int,
) -> list[SearchResult]:
    """并行搜索所有源，返回合并结果。"""
    results: list[SearchResult] = []

    def _search_one(adapter: object) -> list[SearchResult]:
        try:
            return adapter.search(sub_query, max_results=max_results)  # type: ignore[attr-defined]
        except Exception:
            logger.warning("_parallel_search: %s 搜索失败 (query=%s)", adapter.name, sub_query)  # type: ignore[attr-defined]
            return []

    with ThreadPoolExecutor(max_workers=min(len(source_adapters), 4)) as pool:
        futures = [pool.submit(_search_one, a) for a in source_adapters]
        for future in as_completed(futures):
            results.extend(future.result())

    return results


class EvidenceCollector:
    """证据收集、去重、检索"""

    evidence_store: list[Evidence]
    _counter: int
    _seen_contents: set[str]

    def __init__(self):
        self.evidence_store = []
        self._counter = 0
        self._seen_contents = set()

    def add_evidence(
        self,
        content: str,
        source_type: EvidenceType,
        source_url: str | None = None,
        linked_variables: list[str] | None = None,
        reliability: float = 0.5,
    ) -> Evidence | None:
        content_key = content.strip().lower()
        if content_key in self._seen_contents:
            return None
        self._seen_contents.add(content_key)

        self._counter += 1
        ev = Evidence(
            id=f"ev-{self._counter:04d}",
            content=content.strip(),
            source_type=source_type,
            source_url=source_url,
            linked_variables=linked_variables or [],
            prior_reliability=reliability,
            posterior_reliability=reliability,
        )
        self.evidence_store.append(ev)
        return ev

    def get_evidence(self) -> list[Evidence]:
        return self.evidence_store

    def get_evidence_by_variable(self, variable_name: str) -> list[Evidence]:
        return [ev for ev in self.evidence_store if variable_name in ev.linked_variables]

    def auto_collect(
        self,
        query: str,
        domain: str,
        llm_client: object | None = None,
        source_adapters: list[object] | None = None,
        max_sub_queries: int | None = None,
        max_results_per_source: int = 5,
    ) -> list[Evidence]:
        if llm_client is None or source_adapters is None:
            logger.info("auto_collect: 未提供 llm_client 或 source_adapters，跳过自动收集")
            return []

        sub_queries = llm_client.decompose_query(query, domain)
        if not sub_queries:
            logger.warning("auto_collect: 查询分解返回空，使用原始查询")
            sub_queries = [query]
        elif max_sub_queries is not None:
            sub_queries = sub_queries[:max_sub_queries]

        logger.info("auto_collect: 分解为 %d 个子查询", len(sub_queries))

        new_evidence: list[Evidence] = []
        for sub_q in sub_queries:
            all_results = _parallel_search(sub_q, source_adapters, max_results_per_source)

            if not all_results:
                continue

            merged_text = "\n---\n".join(f"Title: {r.title}\n\n{r.content}" for r in all_results)
            first_source = all_results[0].source_type
            first_url = all_results[0].url

            extracted = llm_client.extract_evidence(query, merged_text, first_source.value)
            for ext in extracted:
                ev = self.add_evidence(
                    content=ext.content,
                    source_type=first_source,
                    source_url=first_url,
                    linked_variables=ext.variables,
                    reliability=ext.confidence,
                )
                if ev is not None:
                    new_evidence.append(ev)

        logger.info("auto_collect: 新增 %d 条证据（去重后）", len(new_evidence))
        return new_evidence

    def graph_guided_collect(
        self,
        query: str,
        domain: str,
        variables: list[CausalVariable],
        edges: list[CausalEdge],
        llm_client: object | None = None,
        source_adapters: list[object] | None = None,
        max_sub_queries: int | None = None,
        max_results_per_source: int = 5,
    ) -> list[Evidence]:
        if llm_client is None or source_adapters is None:
            logger.info("graph_guided_collect: 缺少 llm_client 或 source_adapters，跳过")
            return []

        sub_queries = self._build_graph_aware_subqueries(query, variables, edges)
        if max_sub_queries is not None:
            sub_queries = sub_queries[:max_sub_queries]

        if not sub_queries:
            logger.info("graph_guided_collect: 无需补充检索（图已充分覆盖）")
            return []

        logger.info("graph_guided_collect: 生成 %d 个定向子查询", len(sub_queries))
        return self._execute_subqueries(
            query, sub_queries, llm_client, source_adapters, max_results_per_source
        )

    def search_by_causal_path(
        self,
        query: str,
        path_variables: list[str],
        llm_client: object | None = None,
        source_adapters: list[object] | None = None,
        max_results_per_source: int = 5,
    ) -> list[Evidence]:
        if llm_client is None or source_adapters is None or len(path_variables) < 2:
            return []

        path_str = " → ".join(path_variables)
        chain_query = f"{query} causal chain {path_str} evidence mechanism"
        sub_queries = [chain_query]

        for i in range(len(path_variables) - 1):
            src, tgt = path_variables[i], path_variables[i + 1]
            sub_queries.append(f"{query} {src} causes {tgt} evidence")

        logger.info("search_by_causal_path: %d 个链式子查询 (%s)", len(sub_queries), path_str)
        return self._execute_subqueries(
            query, sub_queries, llm_client, source_adapters, max_results_per_source
        )

    def _build_graph_aware_subqueries(
        self,
        query: str,
        variables: list[CausalVariable],
        edges: list[CausalEdge],
    ) -> list[str]:
        sub_queries: list[str] = []

        for edge in edges:
            has_support = bool(edge.supporting_evidence_ids)
            if not has_support:
                src_label = edge.source.replace("_", " ")
                tgt_label = edge.target.replace("_", " ")
                sub_queries.append(f"{query} how does {src_label} causally affect {tgt_label}")

        for var in variables:
            if not var.evidence_ids:
                var_label = var.name.replace("_", " ")
                sub_queries.append(f"{query} {var_label} evidence {var.description}")

        return sub_queries

    def _execute_subqueries(
        self,
        original_query: str,
        sub_queries: list[str],
        llm_client: object,
        source_adapters: list[object],
        max_results_per_source: int,
    ) -> list[Evidence]:
        new_evidence: list[Evidence] = []
        for sub_q in sub_queries:
            all_results = _parallel_search(sub_q, source_adapters, max_results_per_source)

            if not all_results:
                continue

            merged_text = "\n---\n".join(f"Title: {r.title}\n\n{r.content}" for r in all_results)
            first_source = all_results[0].source_type
            first_url = all_results[0].url

            extracted = llm_client.extract_evidence(original_query, merged_text, first_source.value)
            for ext in extracted:
                ev = self.add_evidence(
                    content=ext.content,
                    source_type=first_source,
                    source_url=first_url,
                    linked_variables=ext.variables,
                    reliability=ext.confidence,
                )
                if ev is not None:
                    new_evidence.append(ev)

        logger.info("_execute_subqueries: 新增 %d 条证据（去重后）", len(new_evidence))
        return new_evidence
