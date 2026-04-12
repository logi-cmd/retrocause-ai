"""Evidence collection orchestration."""

from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime

from retrocause.models import CausalEdge, CausalVariable, Evidence, EvidenceType

logger = logging.getLogger(__name__)

_FRESH_TYPES = {EvidenceType.NEWS, EvidenceType.SOCIAL, EvidenceType.TESTIMONY}
_SOURCE_MIN_INTERVAL_SECONDS = 0.0
_SOURCE_QUERY_CACHE_TTL = 180.0
_EXTRACTION_TEXT_LIMIT = 16000
_EXTRACTION_TEXT_PER_RESULT_LIMIT = 6000
_GEOPOLITICS_MIN_EVIDENCE = 6
_GEOPOLITICS_MIN_SOURCE_ADAPTERS = 2
_SOURCE_LAST_CALL_AT: dict[str, float] = {}
_SOURCE_QUERY_CACHE: dict[tuple[str, str, int], tuple[float, list]] = {}


def configure_source_limits(
    *,
    min_interval_seconds: float | None = None,
    query_cache_ttl: float | None = None,
) -> None:
    global _SOURCE_MIN_INTERVAL_SECONDS, _SOURCE_QUERY_CACHE_TTL
    if min_interval_seconds is not None:
        _SOURCE_MIN_INTERVAL_SECONDS = max(0.0, float(min_interval_seconds))
    if query_cache_ttl is not None:
        _SOURCE_QUERY_CACHE_TTL = max(0.0, float(query_cache_ttl))


def reset_source_limit_state() -> None:
    _SOURCE_LAST_CALL_AT.clear()
    _SOURCE_QUERY_CACHE.clear()


def _infer_source_tier(source_type: EvidenceType) -> str:
    return "fresh" if source_type in _FRESH_TYPES else "base"


def _infer_freshness(source_type: EvidenceType, timestamp: str | None) -> str:
    if not timestamp:
        return "recent" if source_type in _FRESH_TYPES else "stable"

    raw_date = timestamp[:10]
    try:
        evidence_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        return "unknown"

    age_days = (date.today() - evidence_date).days
    if age_days <= 30:
        return "fresh"
    if age_days <= 180:
        return "recent"
    return "stable"


class SearchResult:
    """Single search result returned by a source adapter."""

    __slots__ = ("title", "content", "source_type", "url")

    def __init__(self, title: str, content: str, source_type: EvidenceType, url: str = ""):
        self.title = title
        self.content = content
        self.source_type = source_type
        self.url = url


def _result_quality(result: object) -> str:
    metadata = (getattr(result, "metadata", {}) or {}) if result is not None else {}
    return str(metadata.get("content_quality", "snippet"))


def _result_text_for_extraction(
    result: object, limit: int = _EXTRACTION_TEXT_PER_RESULT_LIMIT
) -> str:
    metadata = (getattr(result, "metadata", {}) or {}) if result is not None else {}
    page_content = str(metadata.get("page_content", "")).strip()
    if page_content:
        body = page_content[:limit]
    else:
        body = str(getattr(result, "content", ""))[:limit]
    return f"Title: {getattr(result, 'title', '')}\nURL: {getattr(result, 'url', '')}\n\n{body}"


def _merged_result_text(results: list[object]) -> str:
    merged = "\n---\n".join(_result_text_for_extraction(result) for result in results)
    return merged[:_EXTRACTION_TEXT_LIMIT]


def _match_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())
        if token
        not in {
            "and",
            "for",
            "from",
            "that",
            "the",
            "this",
            "with",
        }
    }


def _best_result_for_evidence(content: str, results: list[object]) -> object:
    """Best-effort attribution for evidence extracted from a merged source batch."""
    content_tokens = _match_tokens(content)
    if not content_tokens or not results:
        return results[0]

    best_result = results[0]
    best_score = -1
    for result in results:
        metadata = (getattr(result, "metadata", {}) or {}) if result is not None else {}
        haystack = " ".join(
            [
                str(getattr(result, "title", "")),
                str(getattr(result, "content", "")),
                str(metadata.get("page_content", ""))[:2000],
            ]
        )
        score = len(content_tokens & _match_tokens(haystack))
        if score > best_score:
            best_result = result
            best_score = score
    return best_result


def _extraction_method_from_results(results: list[object]) -> str:
    quality_values = {_result_quality(result) for result in results}
    if "trusted_fulltext" in quality_values:
        return "llm_fulltext_trusted"
    if "fulltext" in quality_values:
        return "llm_fulltext"
    if "trusted_snippet" in quality_values:
        return "llm_trusted"
    return "llm"


def _reliability_from_extraction(confidence: float, extraction_method: str) -> float:
    bonus_by_method = {
        "llm_fulltext_trusted": 0.12,
        "llm_fulltext": 0.08,
        "llm_trusted": 0.04,
    }
    bonus = bonus_by_method.get(extraction_method, 0.0)
    return max(0.0, min(1.0, confidence + bonus))


def _parallel_search(
    sub_query: str,
    source_adapters: list[object],
    max_results: int,
    min_source_adapters: int = 1,
) -> list[SearchResult]:
    """Search adapters in priority order and stop once enough results are collected."""
    results: list[SearchResult] = []
    searched_adapters = 0
    for adapter in source_adapters:
        cache_key = (getattr(adapter, "name", "unknown"), sub_query.strip().lower(), max_results)
        cached = _SOURCE_QUERY_CACHE.get(cache_key)
        now = time.time()
        if cached and now - cached[0] <= _SOURCE_QUERY_CACHE_TTL:
            adapter_results = cached[1]
            results.extend(adapter_results)
            searched_adapters += 1
            if len(results) >= max_results and searched_adapters >= min_source_adapters:
                break
            continue

        last_called = _SOURCE_LAST_CALL_AT.get(cache_key[0], 0.0)
        remaining = _SOURCE_MIN_INTERVAL_SECONDS - (now - last_called)
        if remaining > 0:
            logger.info(
                "_parallel_search: source %s delayed by shared limiter for %.3fs",
                cache_key[0],
                remaining,
            )
            time.sleep(remaining)
        try:
            adapter_results = adapter.search(sub_query, max_results=max_results)  # type: ignore[attr-defined]
        except Exception:
            logger.warning(
                "_parallel_search: %s search failed (query=%s)",
                adapter.name,  # type: ignore[attr-defined]
                sub_query,
            )
            continue

        _SOURCE_LAST_CALL_AT[cache_key[0]] = time.time()
        _SOURCE_QUERY_CACHE[cache_key] = (time.time(), adapter_results)
        searched_adapters += 1
        results.extend(adapter_results)
        if len(results) >= max_results and searched_adapters >= min_source_adapters:
            break

    return results


def _collection_quality_met(domain: str, evidences: list[Evidence]) -> bool:
    if domain != "geopolitics":
        return bool(evidences)
    high_quality_count = sum(
        1
        for evidence in evidences
        if evidence.extraction_method
        in {"llm_fulltext_trusted", "llm_fulltext", "llm_trusted", "store_cache"}
    )
    return high_quality_count >= _GEOPOLITICS_MIN_EVIDENCE


class EvidenceCollector:
    """Collect, deduplicate, and retrieve evidence."""

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
        timestamp: str | None = None,
        extraction_method: str = "manual",
        source_tier: str | None = None,
        freshness: str | None = None,
        captured_at: str | None = None,
    ) -> Evidence | None:
        content_key = content.strip().lower()
        if content_key in self._seen_contents:
            return None
        self._seen_contents.add(content_key)

        self._counter += 1
        evidence = Evidence(
            id=f"ev-{self._counter:04d}",
            content=content.strip(),
            source_type=source_type,
            source_url=source_url,
            linked_variables=linked_variables or [],
            prior_reliability=reliability,
            posterior_reliability=reliability,
            timestamp=timestamp,
            source_tier=source_tier or _infer_source_tier(source_type),
            freshness=freshness or _infer_freshness(source_type, timestamp),
            captured_at=captured_at or date.today().isoformat(),
            extraction_method=extraction_method,
        )
        self.evidence_store.append(evidence)
        return evidence

    def get_evidence(self) -> list[Evidence]:
        return self.evidence_store

    def get_evidence_by_variable(self, variable_name: str) -> list[Evidence]:
        return [ev for ev in self.evidence_store if variable_name in ev.linked_variables]

    def _fallback_extract_from_results(
        self,
        results: list[SearchResult],
    ) -> list[tuple[str, EvidenceType, str, float]]:
        """Keep a small amount of sourced evidence when LLM extraction returns nothing."""
        fallback_items: list[tuple[str, EvidenceType, str, float]] = []
        for item in results[:2]:
            title = item.title.strip()
            snippet = item.content.strip()
            if not title and not snippet:
                continue
            combined = f"{title}. {snippet}".strip().strip(".")
            if len(combined) < 40:
                continue
            fallback_items.append((combined, item.source_type, item.url, 0.35))
        return fallback_items

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
            logger.info("auto_collect: missing llm_client or source_adapters, skipping")
            return []

        query_builder = getattr(llm_client, "build_search_queries", None)
        if callable(query_builder):
            sub_queries = query_builder(query, domain)
        else:
            sub_queries = llm_client.decompose_query(query, domain)
        if not sub_queries:
            logger.warning("auto_collect: query decomposition returned empty, using original query")
            sub_queries = [query]
        elif max_sub_queries is not None:
            sub_queries = sub_queries[:max_sub_queries]

        if domain == "geopolitics":
            sub_queries = sub_queries[:2]
        elif domain in {"finance", "business"}:
            sub_queries = sub_queries[:2]

        logger.info("auto_collect: generated %d sub-queries", len(sub_queries))

        new_evidence: list[Evidence] = []
        for sub_query in sub_queries:
            min_source_adapters = (
                min(_GEOPOLITICS_MIN_SOURCE_ADAPTERS, len(source_adapters))
                if domain == "geopolitics"
                else 1
            )
            all_results = _parallel_search(
                sub_query,
                source_adapters,
                max_results_per_source,
                min_source_adapters=min_source_adapters,
            )
            if not all_results:
                continue

            merged_text = _merged_result_text(all_results)
            first_source = all_results[0].source_type
            extraction_method = _extraction_method_from_results(all_results)

            extracted = llm_client.extract_evidence(query, merged_text, first_source.value)
            for item in extracted:
                matched_result = _best_result_for_evidence(item.content, all_results)
                matched_metadata = (getattr(matched_result, "metadata", {}) or {})
                matched_method = _extraction_method_from_results([matched_result])
                evidence = self.add_evidence(
                    content=item.content,
                    source_type=matched_result.source_type,
                    source_url=matched_result.url,
                    linked_variables=item.variables,
                    reliability=_reliability_from_extraction(item.confidence, matched_method),
                    timestamp=matched_metadata.get("published"),
                    extraction_method=matched_method or extraction_method,
                )
                if evidence is not None:
                    new_evidence.append(evidence)

            if extracted:
                continue

            logger.info(
                "auto_collect: LLM extraction returned nothing, preserving low-confidence summaries"
            )
            for content, source_type, source_url, reliability in self._fallback_extract_from_results(
                all_results
            ):
                evidence = self.add_evidence(
                    content=content,
                    source_type=source_type,
                    source_url=source_url,
                    reliability=reliability,
                    timestamp=(getattr(all_results[0], "metadata", {}) or {}).get("published"),
                    extraction_method="fallback_summary",
                )
                if evidence is not None:
                    new_evidence.append(evidence)

            if _collection_quality_met(domain, new_evidence):
                break

        logger.info("auto_collect: added %d evidence items after dedupe", len(new_evidence))
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
            logger.info("graph_guided_collect: missing llm_client or source_adapters, skipping")
            return []

        sub_queries = self._build_graph_aware_subqueries(query, variables, edges)
        if max_sub_queries is not None:
            sub_queries = sub_queries[:max_sub_queries]

        if not sub_queries:
            logger.info("graph_guided_collect: graph already has enough coverage")
            return []

        logger.info("graph_guided_collect: generated %d targeted sub-queries", len(sub_queries))
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

        path_str = " -> ".join(path_variables)
        sub_queries = [f"{query} causal chain {path_str} evidence mechanism"]
        for index in range(len(path_variables) - 1):
            src, tgt = path_variables[index], path_variables[index + 1]
            sub_queries.append(f"{query} {src} causes {tgt} evidence")

        logger.info("search_by_causal_path: generated %d chain queries (%s)", len(sub_queries), path_str)
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
            if edge.supporting_evidence_ids:
                continue
            src_label = edge.source.replace("_", " ")
            tgt_label = edge.target.replace("_", " ")
            sub_queries.append(f"{query} how does {src_label} causally affect {tgt_label}")

        for variable in variables:
            if variable.evidence_ids:
                continue
            var_label = variable.name.replace("_", " ")
            sub_queries.append(f"{query} {var_label} evidence {variable.description}")

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
        for sub_query in sub_queries:
            all_results = _parallel_search(sub_query, source_adapters, max_results_per_source)
            if not all_results:
                continue

            merged_text = _merged_result_text(all_results)
            first_source = all_results[0].source_type
            first_url = all_results[0].url
            extraction_method = _extraction_method_from_results(all_results)

            extracted = llm_client.extract_evidence(original_query, merged_text, first_source.value)
            for item in extracted:
                evidence = self.add_evidence(
                    content=item.content,
                    source_type=first_source,
                    source_url=first_url,
                    linked_variables=item.variables,
                    reliability=_reliability_from_extraction(item.confidence, extraction_method),
                    timestamp=(getattr(all_results[0], "metadata", {}) or {}).get("published"),
                    extraction_method=extraction_method,
                )
                if evidence is not None:
                    new_evidence.append(evidence)

            if extracted:
                continue

            logger.info(
                "graph_guided_collect: LLM extraction returned nothing, preserving low-confidence summaries"
            )
            for content, source_type, source_url, reliability in self._fallback_extract_from_results(
                all_results
            ):
                evidence = self.add_evidence(
                    content=content,
                    source_type=source_type,
                    source_url=source_url,
                    reliability=reliability,
                    timestamp=(getattr(all_results[0], "metadata", {}) or {}).get("published"),
                    extraction_method="fallback_summary",
                )
                if evidence is not None:
                    new_evidence.append(evidence)

        logger.info("_execute_subqueries: added %d evidence items after dedupe", len(new_evidence))
        return new_evidence
