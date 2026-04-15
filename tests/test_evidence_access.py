from __future__ import annotations

from retrocause.evidence_access import (
    EvidenceAccessLayer,
    EvidenceAccessPolicy,
    broker_source_names,
    describe_source_name,
    enrich_query_with_time_context,
    plan_query,
    reset_evidence_access_state,
    result_matches_time_range,
    source_profile,
    time_scope_key,
)
from datetime import date

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult


class _Source(BaseSourceAdapter):
    def __init__(
        self,
        name: str,
        results: list[SearchResult],
        *,
        fail: bool | Exception = False,
    ):
        self._name = name
        self._results = results
        self._fail = fail
        self.calls: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.NEWS

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self.calls.append(query)
        if isinstance(self._fail, Exception):
            raise self._fail
        if self._fail:
            raise ConnectionError("source unavailable")
        return self._results[:max_results]


class _Response:
    def __init__(self, status_code: int, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.headers = headers or {}


class _HttpError(Exception):
    def __init__(self, status_code: int, headers: dict[str, str] | None = None):
        super().__init__(f"HTTP {status_code}")
        self.response = _Response(status_code, headers)


def _result(title: str, quality: str, url: str) -> SearchResult:
    return SearchResult(
        title=title,
        content=f"{title} content",
        url=url,
        source_type=EvidenceType.NEWS,
        metadata={"content_quality": quality},
    )


def _dated_result(title: str, published: str) -> SearchResult:
    return SearchResult(
        title=title,
        content=f"{title} content",
        url=f"https://example.com/{title}",
        source_type=EvidenceType.NEWS,
        metadata={"content_quality": "trusted_fulltext", "published": published},
    )


def test_access_layer_attempts_minimum_source_coverage_before_stopping():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    first = _Source("first", [_result("snippet", "snippet", "https://example.com/a")])
    second = _Source(
        "second",
        [_result("trusted", "trusted_fulltext", "https://trusted.example.com/b")],
    )

    batch = access.search(
        "US Iran talks",
        [first, second],
        max_results=1,
        min_source_adapters=2,
    )

    assert [item.name for item in batch.attempts] == ["first", "second"]
    assert len(first.calls) == 1
    assert len(second.calls) == 1
    assert [result.title for result in batch.results] == ["trusted", "snippet"]


def test_access_layer_reuses_cached_adapter_results_without_new_upstream_call():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    source = _Source("cached", [_result("cached item", "fulltext", "https://example.com/c")])

    first = access.search("bitcoin selloff", [source], max_results=2)
    second = access.search("bitcoin selloff", [source], max_results=2)

    assert len(source.calls) == 1
    assert first.results[0].title == "cached item"
    assert second.results[0].title == "cached item"
    assert second.cache_hits == 1


def test_access_cache_key_separates_scenario_and_language():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    source = _Source("cached", [_result("cached item", "fulltext", "https://example.com/c")])

    market_en = access.search(
        "US Iran talks",
        [source],
        max_results=2,
        scenario="market",
        language="en",
        source_policy="news",
    )
    policy_en = access.search(
        "US Iran talks",
        [source],
        max_results=2,
        scenario="policy",
        language="en",
        source_policy="news",
    )
    policy_zh = access.search(
        "US Iran talks",
        [source],
        max_results=2,
        scenario="policy",
        language="zh",
        source_policy="news",
    )

    assert len(source.calls) == 3
    assert market_en.cache_hits == 0
    assert policy_en.cache_hits == 0
    assert policy_zh.cache_hits == 0


def test_access_cache_key_reuses_same_absolute_time_bucket():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    source = _Source(
        "cached",
        [_dated_result("yesterday bitcoin selloff", "2026-04-12")],
    )

    first = access.search(
        "bitcoin price drop",
        [source],
        max_results=2,
        time_range="yesterday",
        today=date(2026, 4, 13),
        scenario="market",
        language="en",
        source_policy="news",
    )
    second = access.search(
        "bitcoin price drop",
        [source],
        max_results=2,
        time_range="yesterday",
        today=date(2026, 4, 13),
        scenario="market",
        language="en",
        source_policy="news",
    )
    next_day = access.search(
        "bitcoin price drop",
        [source],
        max_results=2,
        time_range="yesterday",
        today=date(2026, 4, 14),
        scenario="market",
        language="en",
        source_policy="news",
    )

    assert len(source.calls) == 2
    assert first.cache_hits == 0
    assert second.cache_hits == 1
    assert next_day.cache_hits == 0


def test_access_layer_filters_stale_results_for_yesterday_queries():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    source = _Source(
        "dated",
        [
            _dated_result("old bitcoin selloff", "2026-04-10"),
            _dated_result("yesterday bitcoin selloff", "2026-04-12"),
        ],
    )

    batch = access.search(
        "bitcoin price drop April 12 2026",
        [source],
        max_results=5,
        time_range="yesterday",
        today=date(2026, 4, 13),
    )

    assert [item.title for item in batch.results] == ["yesterday bitcoin selloff"]
    assert batch.attempts[0].result_count == 1


def test_access_layer_records_source_errors_and_continues_to_next_adapter():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    broken = _Source("broken", [], fail=True)
    healthy = _Source("healthy", [_result("healthy item", "fulltext", "https://example.com/h")])

    batch = access.search("policy shock", [broken, healthy], max_results=1)

    assert [item.name for item in batch.attempts] == ["broken", "healthy"]
    assert batch.errors == {"broken": "source_error"}
    assert batch.attempts[0].status == "source_error"
    assert [result.title for result in batch.results] == ["healthy item"]


def test_access_layer_classifies_rate_limited_sources():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    limited = _Source("tavily", [], fail=_HttpError(429, {"retry-after": "7"}))
    healthy = _Source("web", [_result("healthy item", "fulltext", "https://example.com/h")])

    batch = access.search("latest market shock", [limited, healthy], max_results=1)

    assert batch.errors == {"tavily": "rate_limited"}
    assert batch.attempts[0].status == "rate_limited"
    assert batch.attempts[0].retry_after_seconds == 7
    assert batch.attempts[0].source_label == "Tavily Search"
    assert batch.attempts[0].source_kind == "hosted_ai_search"
    assert batch.attempts[1].status == "ok"
    assert [result.title for result in batch.results] == ["healthy item"]


def test_access_layer_classifies_forbidden_sources():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(EvidenceAccessPolicy(query_cache_ttl=60))
    forbidden = _Source("brave", [], fail=_HttpError(403))

    batch = access.search("policy shock", [forbidden], max_results=1)

    assert batch.errors == {"brave": "forbidden"}
    assert batch.attempts[0].status == "forbidden"
    assert batch.attempts[0].retry_after_seconds is None
    assert batch.attempts[0].source_label == "Brave Search API"
    assert batch.attempts[0].cache_policy == "transient_results_only"


def test_access_layer_cools_down_recently_failed_sources():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(
        EvidenceAccessPolicy(query_cache_ttl=60, source_error_cooldown_seconds=30)
    )
    broken = _Source("broken", [], fail=True)
    healthy = _Source("healthy", [_result("healthy item", "fulltext", "https://example.com/h")])

    first = access.search("policy shock", [broken, healthy], max_results=1)
    second = access.search("policy shock updated", [broken, healthy], max_results=1)

    assert first.errors == {"broken": "source_error"}
    assert second.errors == {"broken": "source_limited"}
    assert len(broken.calls) == 1
    assert [result.title for result in second.results] == ["healthy item"]


def test_access_layer_marks_cooldown_as_source_limited():
    reset_evidence_access_state()
    access = EvidenceAccessLayer(
        EvidenceAccessPolicy(query_cache_ttl=60, source_error_cooldown_seconds=30)
    )
    broken = _Source("broken", [], fail=ConnectionError("source unavailable"))

    first = access.search("policy shock", [broken], max_results=1)
    second = access.search("policy shock updated", [broken], max_results=1)

    assert first.attempts[0].status == "source_error"
    assert second.errors == {"broken": "source_limited"}
    assert second.attempts[0].status == "source_limited"
    assert second.attempts[0].error == "source_limited"
    assert second.attempts[0].source_label == "broken"
    assert len(broken.calls) == 1


def test_query_planner_detects_language_time_entities_and_scenario():
    plan = plan_query("比特币今日价格为何跳水")

    assert plan.language == "zh"
    assert plan.time_range == "today"
    assert plan.scenario == "market"
    assert "bitcoin" in plan.entities
    assert "btc" in plan.entities


def test_time_scope_uses_absolute_calendar_bucket_for_relative_queries():
    assert time_scope_key("yesterday", today=date(2026, 4, 13)) == "yesterday:2026-04-12"
    assert time_scope_key("today", today=date(2026, 4, 13)) == "today:2026-04-13"


def test_time_context_adds_absolute_date_to_yesterday_query():
    query = enrich_query_with_time_context(
        "Bitcoin BTC price drop yesterday",
        "yesterday",
        today=date(2026, 4, 13),
    )

    assert "2026-04-12" in query
    assert "April 12, 2026" in query


def test_result_time_matching_rejects_stale_published_dates():
    assert result_matches_time_range(
        _dated_result("fresh", "2026-04-12"),
        "yesterday",
        today=date(2026, 4, 13),
    )
    assert not result_matches_time_range(
        _dated_result("stale", "2026-03-01"),
        "yesterday",
        today=date(2026, 4, 13),
    )


def test_result_time_matching_requires_date_signal_when_metadata_missing():
    undated_old = SearchResult(
        title="Bitcoin price drop explained",
        content="A generic old market explanation without a date.",
        url="https://example.com/bitcoin-drop",
        source_type=EvidenceType.NEWS,
        metadata={"content_quality": "trusted_fulltext"},
    )
    undated_target = SearchResult(
        title="Bitcoin price drop April 12, 2026",
        content="Market coverage for the target session.",
        url="https://example.com/bitcoin-drop-april-12-2026",
        source_type=EvidenceType.NEWS,
        metadata={"content_quality": "trusted_fulltext"},
    )

    assert not result_matches_time_range(undated_old, "yesterday", today=date(2026, 4, 13))
    assert result_matches_time_range(undated_target, "yesterday", today=date(2026, 4, 13))


def test_source_broker_routes_market_and_policy_queries_to_scenario_fit_sources():
    market_plan = plan_query("比特币今日价格为何跳水")
    policy_plan = plan_query("美国为什么会推出新的半导体出口管制？")

    assert broker_source_names(None, market_plan)[:3] == ["ap_news", "gdelt", "web"]
    assert broker_source_names(None, policy_plan)[:4] == [
        "ap_news",
        "federal_register",
        "gdelt",
        "web",
    ]


def test_source_broker_respects_explicit_source_override():
    plan = plan_query("Why did dinosaurs go extinct?")

    assert broker_source_names("web,arxiv", plan) == ["web", "arxiv"]


def test_source_descriptions_explain_reliability_for_ui_trace():
    ap = describe_source_name("ap_news")
    web = describe_source_name("web")
    official = describe_source_name("federal_register")

    assert ap == {
        "source_label": "AP News",
        "source_kind": "wire_news",
        "stability": "high",
        "cache_policy": "short_lived_cache_allowed",
    }
    assert web == {
        "source_label": "Trusted web search",
        "source_kind": "web_search",
        "stability": "medium",
        "cache_policy": "short_lived_cache_allowed",
    }
    assert official["source_kind"] == "official_record"
    assert official["stability"] == "high"


def test_source_profiles_expose_budget_and_storage_policy():
    tavily = source_profile("tavily")
    brave = source_profile("brave")
    ap = describe_source_name("ap_news")

    assert tavily.requires_api_key
    assert tavily.cache_policy == "derived_cache_allowed"
    assert tavily.default_rpm > 0
    assert tavily.default_monthly_budget > 0
    assert brave.requires_api_key
    assert brave.cache_policy == "transient_results_only"
    assert ap["cache_policy"] == "short_lived_cache_allowed"


def test_broker_source_names_can_include_optional_hosted_sources_when_enabled():
    market_plan = plan_query("Why did Bitcoin price fall today?")
    policy_plan = plan_query("Why did the US announce new semiconductor export controls?")
    override_plan = plan_query("Why did dinosaurs go extinct?")

    assert broker_source_names(None, market_plan, optional_sources=["tavily", "brave"])[:5] == [
        "tavily",
        "brave",
        "ap_news",
        "gdelt",
        "web",
    ]
    assert broker_source_names(None, policy_plan, optional_sources=["tavily"])[:5] == [
        "ap_news",
        "federal_register",
        "tavily",
        "gdelt",
        "web",
    ]
    assert broker_source_names("web,arxiv", override_plan, optional_sources=["tavily"]) == [
        "web",
        "arxiv",
    ]
