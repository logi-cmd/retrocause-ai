from __future__ import annotations

import httpx

from retrocause.sources.web import DEFAULT_TRUSTED_DOMAINS, WebSearchAdapter


class _FakeResponse:
    def __init__(self, text: str, content_type: str = "text/html"):
        self.text = text
        self.headers = {"content-type": content_type}

    def raise_for_status(self) -> None:
        return None


def test_web_parse_html_prefers_trusted_domains(monkeypatch):
    html = """
    <div class="result">
      <a class="result__a" href="https://randomblog.example/mh370">Random blog</a>
      <a class="result__snippet">Weak summary from an unknown site.</a>
    </div>
    <div class="result">
      <a class="result__a" href="https://www.ntsb.gov/investigations/mh370">NTSB report</a>
      <a class="result__snippet">Official summary from a trusted source.</a>
    </div>
    """

    monkeypatch.setattr(
        "retrocause.sources.web._fetch_page_content",
        lambda url: "Detailed official report body." if "ntsb.gov" in url else None,
    )

    results = WebSearchAdapter._parse_html(html, max_results=2)

    assert len(results) == 2
    assert results[0].url == "https://www.ntsb.gov/investigations/mh370"
    assert results[0].metadata["trusted_domain"] is True
    assert results[0].metadata["content_quality"] == "trusted_fulltext"
    assert results[1].metadata["trusted_domain"] is False


def test_web_search_uses_cached_results_when_live_search_fails(monkeypatch):
    adapter = WebSearchAdapter()
    html = """
    <div class="result">
      <a class="result__a" href="https://www.reuters.com/world/example">Reuters item</a>
      <a class="result__snippet">Trusted report snippet.</a>
    </div>
    """

    call_count = {"value": 0}

    def _fake_get(url: str, **kwargs):
        call_count["value"] += 1
        if "duckduckgo" in url and call_count["value"] > 1:
            raise httpx.ConnectTimeout("rate limited")
        return _FakeResponse(html)

    monkeypatch.setattr("retrocause.sources.web.httpx.get", _fake_get)
    monkeypatch.setattr("retrocause.sources.web._fetch_page_content", lambda url: None)
    monkeypatch.setattr("retrocause.sources.web._query_cache", {})
    monkeypatch.setattr("retrocause.sources.web._disabled_until", 0.0)

    first = adapter.search("mh370 disappearance", max_results=2)
    second = adapter.search("mh370 disappearance", max_results=2)

    assert len(first) == 1
    assert len(second) == 1
    assert second[0].url == first[0].url


def test_default_trusted_domains_include_stable_diplomacy_sources():
    assert "state.gov" in DEFAULT_TRUSTED_DOMAINS
    assert "un.org" in DEFAULT_TRUSTED_DOMAINS
    assert "reuters.com" in DEFAULT_TRUSTED_DOMAINS
