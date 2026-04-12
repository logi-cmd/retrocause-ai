"""Stable evidence access service layer.

This module owns query planning, source brokering, source pacing, short-lived
search-result caching, and retrieval-quality ordering. Source adapters stay
small: they only know how to search one upstream service.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

from retrocause.models import EvidenceType
from retrocause.parser import ParsedQuery, parse_input
from retrocause.sources.base import SearchResult

logger = logging.getLogger(__name__)

QUALITY_ORDER = {
    "trusted_fulltext": 0,
    "fulltext": 1,
    "structured_source": 2,
    "trusted_snippet": 3,
    "snippet": 4,
    "store_cache": 5,
    "fallback": 6,
    "fallback_summary": 6,
}

_SOURCE_LAST_CALL_AT: dict[str, float] = {}
_SOURCE_QUERY_CACHE: dict[tuple[str, str, int], tuple[float, list[SearchResult]]] = {}
_SOURCE_COOLDOWN_UNTIL: dict[str, float] = {}


@dataclass(frozen=True)
class QueryPlan:
    """Normalized retrieval plan for one user question."""

    query: str
    domain: str
    time_range: str | None
    language: str
    entities: list[str]
    scenario: str


@dataclass(frozen=True)
class EvidenceAccessPolicy:
    """Runtime budgets for upstream evidence access."""

    min_interval_seconds: float = 0.0
    query_cache_ttl: float = 180.0
    source_error_cooldown_seconds: float = 30.0


@dataclass(frozen=True)
class SourceAttempt:
    """Trace record for one source-adapter attempt."""

    name: str
    query: str
    result_count: int
    cache_hit: bool = False
    error: str | None = None


@dataclass(frozen=True)
class EvidenceAccessBatch:
    """Aggregated search results plus trace metadata."""

    query: str
    results: list[SearchResult]
    attempts: list[SourceAttempt] = field(default_factory=list)
    cache_hits: int = 0
    errors: dict[str, str] = field(default_factory=dict)


def reset_evidence_access_state() -> None:
    """Clear process-local caches and source pacing state."""

    _SOURCE_LAST_CALL_AT.clear()
    _SOURCE_QUERY_CACHE.clear()
    _SOURCE_COOLDOWN_UNTIL.clear()


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", text))


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(key)
    return output


def _infer_entities(query: str, parsed: ParsedQuery) -> list[str]:
    entities: list[str] = []
    lowered = query.lower()

    crypto_markers = ["bitcoin", "btc", "比特币"]
    if any(marker in lowered for marker in crypto_markers):
        entities.extend(["bitcoin", "btc"])

    policy_markers = {
        "iran": ["iran"],
        "伊朗": ["iran"],
        "semiconductor": ["semiconductor"],
        "半导体": ["semiconductor"],
        "export control": ["export_controls"],
        "出口管制": ["export_controls"],
    }
    for marker, values in policy_markers.items():
        if marker in lowered:
            entities.extend(values)

    entities.extend(
        token.lower()
        for token in re.findall(r"\b[A-Z][A-Za-z0-9&.-]{2,}\b", query)
        if token.lower() not in {"why", "what", "how"}
    )
    if parsed.domain:
        entities.append(parsed.domain)
    return _dedupe(entities)


def _infer_scenario(parsed: ParsedQuery, entities: list[str]) -> str:
    if parsed.domain in {"finance", "business"}:
        return "market"
    if parsed.domain == "geopolitics":
        return "policy" if {"export_controls", "semiconductor"} & set(entities) else "news"
    if parsed.time_range is not None:
        return "news"
    if parsed.domain in {"science", "paleontology"}:
        return "academic"
    return "evergreen"


def plan_query(query: str, parsed: ParsedQuery | None = None) -> QueryPlan:
    """Plan retrieval from the user query before touching source adapters."""

    resolved = parsed or parse_input(query)
    language = "zh" if _has_cjk(query) else "en"
    entities = _infer_entities(query, resolved)
    scenario = _infer_scenario(resolved, entities)
    return QueryPlan(
        query=query,
        domain=resolved.domain,
        time_range=resolved.time_range,
        language=language,
        entities=entities,
        scenario=scenario,
    )


def broker_source_names(configured_sources: str | None, plan: QueryPlan) -> list[str]:
    """Select source classes by scenario, while honoring explicit operator overrides."""

    if configured_sources:
        return [item.strip() for item in configured_sources.split(",") if item.strip()]

    if plan.scenario == "policy":
        return ["ap_news", "federal_register", "gdelt", "web"]
    if plan.scenario in {"market", "news"}:
        return ["ap_news", "web", "gdelt", "arxiv"]
    if plan.scenario == "academic":
        return ["arxiv", "semantic_scholar", "web"]
    return ["arxiv", "semantic_scholar", "web"]


def _result_quality(result: SearchResult) -> str:
    return str((result.metadata or {}).get("content_quality", "snippet"))


def _quality_rank(result: SearchResult) -> tuple[int, float, str]:
    quality = _result_quality(result)
    freshness = str((result.metadata or {}).get("freshness", ""))
    freshness_bonus = -0.5 if freshness in {"fresh", "recent"} else 0.0
    return (QUALITY_ORDER.get(quality, 4), freshness_bonus, result.url)


def sort_results_by_quality(results: list[SearchResult]) -> list[SearchResult]:
    """Prefer fulltext/trusted evidence before snippets and fallbacks."""

    return sorted(results, key=_quality_rank)


class EvidenceAccessLayer:
    """Search aggregator and source broker boundary for evidence retrieval."""

    def __init__(self, policy: EvidenceAccessPolicy | None = None):
        self.policy = policy or EvidenceAccessPolicy()

    def search(
        self,
        query: str,
        source_adapters: list[object],
        max_results: int,
        *,
        min_source_adapters: int = 1,
    ) -> EvidenceAccessBatch:
        """Search multiple source adapters with cache, cooldown, and trace metadata."""

        results: list[SearchResult] = []
        attempts: list[SourceAttempt] = []
        errors: dict[str, str] = {}
        cache_hits = 0
        searched_adapters = 0
        min_adapters = max(1, min(min_source_adapters, len(source_adapters)))

        for adapter in source_adapters:
            adapter_name = str(getattr(adapter, "name", adapter.__class__.__name__))
            cache_key = (adapter_name, query.strip().lower(), max_results)
            now = time.time()
            cached = _SOURCE_QUERY_CACHE.get(cache_key)
            if cached and now - cached[0] <= self.policy.query_cache_ttl:
                adapter_results = cached[1]
                attempts.append(
                    SourceAttempt(
                        name=adapter_name,
                        query=query,
                        result_count=len(adapter_results),
                        cache_hit=True,
                    )
                )
                cache_hits += 1
                searched_adapters += 1
                results.extend(adapter_results)
                if len(results) >= max_results and searched_adapters >= min_adapters:
                    break
                continue

            cooldown_until = _SOURCE_COOLDOWN_UNTIL.get(adapter_name, 0.0)
            if cooldown_until > now:
                errors[adapter_name] = "cooldown"
                attempts.append(
                    SourceAttempt(
                        name=adapter_name,
                        query=query,
                        result_count=0,
                        error="cooldown",
                    )
                )
                continue

            self._pace_source(adapter_name, now)
            try:
                adapter_results = adapter.search(query, max_results=max_results)  # type: ignore[attr-defined]
            except Exception as exc:
                error_name = exc.__class__.__name__
                errors[adapter_name] = error_name
                attempts.append(
                    SourceAttempt(
                        name=adapter_name,
                        query=query,
                        result_count=0,
                        error=error_name,
                    )
                )
                logger.warning(
                    "EvidenceAccessLayer: %s search failed (query=%s)",
                    adapter_name,
                    query,
                )
                _SOURCE_COOLDOWN_UNTIL[adapter_name] = (
                    time.time() + self.policy.source_error_cooldown_seconds
                )
                continue

            _SOURCE_LAST_CALL_AT[adapter_name] = time.time()
            _SOURCE_QUERY_CACHE[cache_key] = (time.time(), adapter_results)
            attempts.append(
                SourceAttempt(
                    name=adapter_name,
                    query=query,
                    result_count=len(adapter_results),
                )
            )
            searched_adapters += 1
            results.extend(adapter_results)
            if len(results) >= max_results and searched_adapters >= min_adapters:
                break

        return EvidenceAccessBatch(
            query=query,
            results=sort_results_by_quality(results),
            attempts=attempts,
            cache_hits=cache_hits,
            errors=errors,
        )

    def _pace_source(self, adapter_name: str, now: float) -> None:
        last_called = _SOURCE_LAST_CALL_AT.get(adapter_name, 0.0)
        remaining = max(0.0, self.policy.min_interval_seconds - (now - last_called))
        if remaining <= 0:
            return
        logger.info(
            "EvidenceAccessLayer: source %s delayed by shared limiter for %.3fs",
            adapter_name,
            remaining,
        )
        time.sleep(remaining)


def infer_source_tier(source_type: EvidenceType) -> str:
    """Classify source tier for evidence metadata."""

    fresh_types = {EvidenceType.NEWS, EvidenceType.SOCIAL, EvidenceType.TESTIMONY}
    return "fresh" if source_type in fresh_types else "base"
