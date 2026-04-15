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
from datetime import date, datetime, timedelta

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


def _today() -> date:
    return date.today()


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
class SourceProfile:
    """Stable retrieval-source policy metadata for broker and UI traces."""

    name: str
    source_label: str
    source_kind: str
    stability: str
    cache_policy: str
    default_monthly_budget: int
    default_rpm: int
    requires_api_key: bool


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


SOURCE_PROFILES: dict[str, SourceProfile] = {
    "ap_news": SourceProfile(
        name="ap_news",
        source_label="AP News",
        source_kind="wire_news",
        stability="high",
        cache_policy="short_lived_cache_allowed",
        default_monthly_budget=5000,
        default_rpm=30,
        requires_api_key=False,
    ),
    "gdelt": SourceProfile(
        name="gdelt",
        source_label="GDELT Global Knowledge Graph",
        source_kind="news_index",
        stability="medium",
        cache_policy="short_lived_cache_allowed",
        default_monthly_budget=10000,
        default_rpm=60,
        requires_api_key=False,
    ),
    "gdelt_news": SourceProfile(
        name="gdelt_news",
        source_label="GDELT Global Knowledge Graph",
        source_kind="news_index",
        stability="medium",
        cache_policy="short_lived_cache_allowed",
        default_monthly_budget=10000,
        default_rpm=60,
        requires_api_key=False,
    ),
    "web": SourceProfile(
        name="web",
        source_label="Trusted web search",
        source_kind="web_search",
        stability="medium",
        cache_policy="short_lived_cache_allowed",
        default_monthly_budget=3000,
        default_rpm=20,
        requires_api_key=False,
    ),
    "federal_register": SourceProfile(
        name="federal_register",
        source_label="Federal Register",
        source_kind="official_record",
        stability="high",
        cache_policy="long_lived_cache_allowed",
        default_monthly_budget=5000,
        default_rpm=60,
        requires_api_key=False,
    ),
    "arxiv": SourceProfile(
        name="arxiv",
        source_label="arXiv",
        source_kind="academic_index",
        stability="high",
        cache_policy="long_lived_cache_allowed",
        default_monthly_budget=5000,
        default_rpm=30,
        requires_api_key=False,
    ),
    "semantic_scholar": SourceProfile(
        name="semantic_scholar",
        source_label="Semantic Scholar",
        source_kind="academic_index",
        stability="medium",
        cache_policy="short_lived_cache_allowed",
        default_monthly_budget=5000,
        default_rpm=30,
        requires_api_key=False,
    ),
    "tavily": SourceProfile(
        name="tavily",
        source_label="Tavily Search",
        source_kind="hosted_ai_search",
        stability="medium",
        cache_policy="derived_cache_allowed",
        default_monthly_budget=1000,
        default_rpm=30,
        requires_api_key=True,
    ),
    "brave": SourceProfile(
        name="brave",
        source_label="Brave Search API",
        source_kind="hosted_web_search",
        stability="medium",
        cache_policy="transient_results_only",
        default_monthly_budget=1000,
        default_rpm=30,
        requires_api_key=True,
    ),
}


def source_profile(source_name: str) -> SourceProfile:
    """Return source policy metadata, falling back to a conservative unknown profile."""

    normalized = source_name.strip().lower()
    return SOURCE_PROFILES.get(
        normalized,
        SourceProfile(
            name=normalized or "unknown",
            source_label=source_name or "Unknown source",
            source_kind="unknown",
            stability="unknown",
            cache_policy="no_cache_policy",
            default_monthly_budget=0,
            default_rpm=0,
            requires_api_key=False,
        ),
    )


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


def _parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def _target_date_signals(target_date: date) -> set[str]:
    month = target_date.strftime("%B").lower()
    short_month = target_date.strftime("%b").lower()
    day = str(target_date.day)
    year = str(target_date.year)
    iso = target_date.isoformat()
    compact = target_date.strftime("%Y%m%d")
    return {
        iso,
        compact,
        f"{month} {day} {year}",
        f"{month} {day}, {year}",
        f"{short_month} {day} {year}",
        f"{short_month} {day}, {year}",
        f"{day} {month} {year}",
        f"{day} {short_month} {year}",
    }


def _result_has_target_date_signal(result: SearchResult, target_date: date) -> bool:
    metadata = result.metadata or {}
    text = " ".join(
        [
            result.title,
            result.content,
            result.url,
            str(metadata.get("page_content", ""))[:4000],
        ]
    ).lower()
    normalized = re.sub(r"[/_.-]+", " ", text)
    return any(signal in text or signal in normalized for signal in _target_date_signals(target_date))


def _target_date_for_range(time_range: str | None, today: date | None = None) -> date | None:
    resolved_today = today or _today()
    if time_range in {"today", "trading_day"}:
        return resolved_today
    if time_range in {"yesterday", "last_24h"}:
        return resolved_today - timedelta(days=1)
    return None


def time_scope_key(time_range: str | None, today: date | None = None) -> str | None:
    """Return an absolute cache bucket for relative time windows."""

    if not time_range:
        return None
    resolved_today = today or _today()
    target_date = _target_date_for_range(time_range, resolved_today)
    if target_date is not None:
        return f"{time_range}:{target_date.isoformat()}"
    if time_range == "last_7d":
        return f"last_7d:{resolved_today.isoformat()}"
    return time_range


def enrich_query_with_time_context(
    query: str,
    time_range: str | None,
    today: date | None = None,
) -> str:
    """Append explicit date context for relative fresh-news queries."""

    if not time_range:
        return query
    target_date = _target_date_for_range(time_range, today)
    if target_date is None:
        return query
    iso_date = target_date.isoformat()
    month_date = f"{target_date.strftime('%B')} {target_date.day}, {target_date.year}"
    if iso_date in query or month_date in query:
        return query
    return f"{query} {iso_date} {month_date}"


def result_matches_time_range(
    result: SearchResult,
    time_range: str | None,
    today: date | None = None,
) -> bool:
    """Reject explicitly stale dated results for relative time-sensitive queries."""

    if not time_range:
        return True
    metadata = result.metadata or {}
    published = _parse_date(metadata.get("published") or metadata.get("date") or metadata.get("year"))

    resolved_today = today or _today()
    target_date = _target_date_for_range(time_range, resolved_today)
    if time_range in {"today", "trading_day"}:
        if published is None:
            return target_date is not None and _result_has_target_date_signal(result, target_date)
        return published == resolved_today
    if time_range == "yesterday":
        if published is None:
            return target_date is not None and _result_has_target_date_signal(result, target_date)
        return published == resolved_today - timedelta(days=1)
    if time_range == "last_24h":
        if published is None:
            return target_date is not None and _result_has_target_date_signal(result, target_date)
        return resolved_today - timedelta(days=1) <= published <= resolved_today
    if time_range == "last_7d":
        if published is None:
            return True
        return resolved_today - timedelta(days=7) <= published <= resolved_today
    return True


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


def _prepend_unique(items: list[str], prefix: list[str]) -> list[str]:
    ordered: list[str] = []
    for item in [*prefix, *items]:
        if item not in ordered:
            ordered.append(item)
    return ordered


def broker_source_names(
    configured_sources: str | None,
    plan: QueryPlan,
    *,
    optional_sources: list[str] | None = None,
) -> list[str]:
    """Select source classes by scenario, while honoring explicit operator overrides."""

    if configured_sources:
        return [item.strip() for item in configured_sources.split(",") if item.strip()]

    optional = [item.strip().lower() for item in optional_sources or [] if item.strip()]
    if plan.scenario == "policy":
        return _prepend_unique(["gdelt", "web"], ["ap_news", "federal_register", *optional])
    if plan.scenario in {"market", "news"}:
        if plan.time_range is not None:
            return _prepend_unique(["ap_news", "gdelt", "web"], optional)
        return _prepend_unique(["ap_news", "web", "gdelt", "arxiv"], optional)
    if plan.scenario == "academic":
        return ["arxiv", "semantic_scholar", "web"]
    return ["arxiv", "semantic_scholar", "web"]


def describe_source_name(source_name: str) -> dict[str, str]:
    """Return stable UI-facing metadata for a retrieval source adapter."""

    profile = source_profile(source_name)
    return {
        "source_label": profile.source_label,
        "source_kind": profile.source_kind,
        "stability": profile.stability,
        "cache_policy": profile.cache_policy,
    }


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
        time_range: str | None = None,
        today: date | None = None,
    ) -> EvidenceAccessBatch:
        """Search multiple source adapters with cache, cooldown, and trace metadata."""

        results: list[SearchResult] = []
        attempts: list[SourceAttempt] = []
        errors: dict[str, str] = {}
        cache_hits = 0
        searched_adapters = 0
        min_adapters = max(1, min(min_source_adapters, len(source_adapters)))
        scoped_query = enrich_query_with_time_context(query, time_range, today)

        for adapter in source_adapters:
            adapter_name = str(getattr(adapter, "name", adapter.__class__.__name__))
            cache_key = (
                adapter_name,
                f"{time_scope_key(time_range, today) or 'evergreen'}::{scoped_query.strip().lower()}",
                max_results,
            )
            now = time.time()
            cached = _SOURCE_QUERY_CACHE.get(cache_key)
            if cached and now - cached[0] <= self.policy.query_cache_ttl:
                adapter_results = cached[1]
                attempts.append(
                    SourceAttempt(
                        name=adapter_name,
                        query=scoped_query,
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
                        query=scoped_query,
                        result_count=0,
                        error="cooldown",
                    )
                )
                continue

            self._pace_source(adapter_name, now)
            try:
                raw_results = adapter.search(scoped_query, max_results=max_results)  # type: ignore[attr-defined]
                adapter_results = [
                    result
                    for result in raw_results
                    if result_matches_time_range(result, time_range, today)
                ]
            except Exception as exc:
                error_name = exc.__class__.__name__
                errors[adapter_name] = error_name
                attempts.append(
                    SourceAttempt(
                        name=adapter_name,
                        query=scoped_query,
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
                    query=scoped_query,
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
