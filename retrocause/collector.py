"""证据收集协调器 — 手动 + LLM 自动收集 + graph-guided retrieval"""

from __future__ import annotations

import logging

from retrocause.models import CausalEdge, CausalVariable, Evidence, EvidenceType

logger = logging.getLogger(__name__)


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
        """
        添加一条证据。对相同 content 去重。

        Returns:
            新建的 Evidence，若重复则返回 None。
        """
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
        """
        全自动证据收集管线：
        1. LLM 分解查询为子查询
        2. 每个子查询在各证据源搜索
        3. LLM 从原始搜索结果中提取结构化证据
        4. 去重后添加到 evidence_store

        Args:
            query: 用户原始因果查询
            domain: 查询领域
            llm_client: LLMClient 实例（需有 decompose_query / extract_evidence 方法）
            source_adapters: BaseSourceAdapter 实例列表
            max_sub_queries: 最大子查询数，None 表示不截断
            max_results_per_source: 每个证据源的最大返回数

        Returns:
            本次新增的 Evidence 列表（去重后）
        """
        if llm_client is None or source_adapters is None:
            logger.info("auto_collect: 未提供 llm_client 或 source_adapters，跳过自动收集")
            return []

        # Step 1: 查询分解
        sub_queries = llm_client.decompose_query(query, domain)
        if not sub_queries:
            logger.warning("auto_collect: 查询分解返回空，使用原始查询")
            sub_queries = [query]
        elif max_sub_queries is not None:
            sub_queries = sub_queries[:max_sub_queries]

        logger.info("auto_collect: 分解为 %d 个子查询", len(sub_queries))

        # Step 2 + 3: 搜索 + 提取
        new_evidence: list[Evidence] = []
        for sub_q in sub_queries:
            for adapter in source_adapters:
                try:
                    search_results = adapter.search(sub_q, max_results=max_results_per_source)
                except Exception:
                    logger.warning("auto_collect: %s 搜索失败 (query=%s)", adapter.name, sub_q)
                    continue

                for result in search_results:
                    raw_text = f"Title: {result.title}\n\n{result.content}"
                    extracted = llm_client.extract_evidence(
                        query, raw_text, result.source_type.value
                    )
                    for ext in extracted:
                        ev = self.add_evidence(
                            content=ext.content,
                            source_type=result.source_type,
                            source_url=result.url,
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
        """
        基于因果图结构的第二轮检索 — 针对薄弱边和低覆盖变量定向补充证据。

        生成 graph-aware 子查询：
        - 无证据支撑的边 → "A 如何因果影响 B" 的定向检索
        - 无关联证据的变量 → 针对变量名的补充检索
        """
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
        """沿因果路径检索 — 针对 A→B→C 链式结构搜索跨跳证据。"""
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
            for adapter in source_adapters:
                try:
                    search_results = adapter.search(sub_q, max_results=max_results_per_source)
                except Exception:
                    logger.warning("搜索失败: %s (query=%s)", adapter.name, sub_q)
                    continue

                for result in search_results:
                    raw_text = f"Title: {result.title}\n\n{result.content}"
                    extracted = llm_client.extract_evidence(
                        original_query, raw_text, result.source_type.value
                    )
                    for ext in extracted:
                        ev = self.add_evidence(
                            content=ext.content,
                            source_type=result.source_type,
                            source_url=result.url,
                            linked_variables=ext.variables,
                            reliability=ext.confidence,
                        )
                        if ev is not None:
                            new_evidence.append(ev)

        logger.info("_execute_subqueries: 新增 %d 条证据（去重后）", len(new_evidence))
        return new_evidence
