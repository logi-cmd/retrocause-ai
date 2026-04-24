from __future__ import annotations

import types

from retrocause.app.demo_data import _select_source_names
from retrocause.llm import (
    LLMClient,
    _heuristic_search_queries,
    _queries_look_invalid,
    _should_retry_graph_coverage,
)
from retrocause.parser import parse_input


def test_parse_input_detects_geopolitics_domain():
    parsed = parse_input("为什么美国会同意与伊朗进行首轮谈判？")
    assert parsed.domain == "geopolitics"


def test_parse_input_detects_chinese_bitcoin_market_move_as_finance():
    parsed = parse_input("比特币今日价格为何跳水")
    assert parsed.domain == "finance"
    assert parsed.time_range == "today"


def test_invalid_queries_detected():
    assert _queries_look_invalid(
        "为什么美国会同意与伊朗进行首轮谈判？",
        [
            "how to determine causal relationships in a general context",
            "methods for identifying causality in broad domains",
        ],
    )


def test_unanchored_years_make_queries_invalid():
    assert _queries_look_invalid(
        "why did the United States agree to talks with Iran",
        [
            "US Iran first round negotiations reasons 2021",
            "Biden administration Iran nuclear deal negotiation motives",
        ],
    )


def test_cjk_geopolitics_has_english_search_fallback():
    queries = _heuristic_search_queries(
        "为什么美国会同意与伊朗进行首轮谈判？",
        "geopolitics",
    )
    assert queries[0].startswith("United States Iran")
    assert "official statements" in queries[1]


def test_cjk_policy_query_keeps_event_specific_terms():
    query = "美国为什么会推出新的半导体出口管制？"

    queries = _heuristic_search_queries(query, "geopolitics")

    assert not _queries_look_invalid(query, queries)
    assert any("semiconductor" in item.lower() for item in queries)
    assert any("export controls" in item.lower() for item in queries)
    assert all("diplomacy foreign policy" not in item.lower() for item in queries)
    assert _queries_look_invalid(
        query,
        [
            "United States why reasons diplomacy foreign policy",
            "United States why reasons official statements",
        ],
    )


def test_cjk_bitcoin_query_gets_search_effective_finance_terms():
    query = "比特币今日价格为何跳水"

    queries = _heuristic_search_queries(query, "finance")

    assert not _queries_look_invalid(query, queries)
    assert any("bitcoin" in item.lower() for item in queries)
    assert any("price" in item.lower() for item in queries)
    assert any("selloff" in item.lower() or "drop" in item.lower() for item in queries)


def test_cjk_a_share_stock_query_preserves_company_anchor():
    query = "芯原股份今日午后股价为什么直线跳水？"

    parsed = parse_input(query)
    queries = _heuristic_search_queries(query, parsed.domain)

    assert parsed.domain == "finance"
    assert parsed.time_range == "today"
    assert not _queries_look_invalid(query, queries)
    assert any("芯原股份" in item for item in queries)
    assert any("share price" in item.lower() or "stock price" in item.lower() for item in queries)
    assert any("selloff" in item.lower() or "plunge" in item.lower() for item in queries)


def test_build_search_queries_rejects_cjk_stock_rewrite_without_company_anchor():
    query = "芯原股份今日午后股价为什么直线跳水？"
    client = object.__new__(LLMClient)
    client.decompose_query = types.MethodType(
        lambda self, query, domain: [
            "how to determine causal relationships in a general context",
            "methods for identifying causality in broad domains",
        ],
        client,
    )
    client._rewrite_search_queries = types.MethodType(
        lambda self, query, domain: [
            "today stock price plunge market analysis",
            "today share price selloff official statements",
        ],
        client,
    )

    queries = client.build_search_queries(query, "finance")

    assert any("芯原股份" in item for item in queries)
    assert all("causal relationships in a general context" not in item for item in queries)


def test_finance_crypto_graph_retries_when_too_narrow():
    assert _should_retry_graph_coverage(
        "比特币今日价格为何跳水",
        "finance",
        ["Bitcoin price dropped today after ETF outflows.", "Liquidations amplified losses."],
        {"variables": [{"name": "bitcoin_price_drop"}, {"name": "market_selloff"}]},
    )


def test_build_search_queries_falls_back_to_rewrite():
    client = object.__new__(LLMClient)
    client.decompose_query = types.MethodType(
        lambda self, query, domain: [
            "how to determine causal relationships in a general context",
            "methods for identifying causality in broad domains",
        ],
        client,
    )
    client._rewrite_search_queries = types.MethodType(
        lambda self, query, domain: [
            "why did the United States agree to talks with Iran",
            "US Iran negotiations official statement reasons",
        ],
        client,
    )

    queries = client.build_search_queries("为什么美国会同意与伊朗进行首轮谈判？", "geopolitics")
    assert queries == [
        "why did the United States agree to talks with Iran",
        "US Iran negotiations official statement reasons",
    ]


def test_build_search_queries_uses_heuristic_when_rewrite_is_too_generic():
    client = object.__new__(LLMClient)
    client.decompose_query = types.MethodType(
        lambda self, query, domain: [
            "how to determine causal relationships in a general context",
            "methods for identifying causality in broad domains",
        ],
        client,
    )
    client._rewrite_search_queries = types.MethodType(
        lambda self, query, domain: [
            "United States why reasons diplomacy foreign policy",
            "United States why reasons official statements",
        ],
        client,
    )

    queries = client.build_search_queries("美国为什么会推出新的半导体出口管制？", "geopolitics")

    assert any("semiconductor" in item.lower() for item in queries)
    assert any("export controls" in item.lower() for item in queries)


def test_select_source_names_prefers_news_sources_for_geopolitics():
    assert _select_source_names(None, "geopolitics") == [
        "ap_news",
        "federal_register",
        "gdelt",
        "web",
    ]


def test_select_source_names_preserves_explicit_override():
    assert _select_source_names("web,arxiv", "geopolitics") == ["web", "arxiv"]
