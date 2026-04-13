from __future__ import annotations

from retrocause.sources.federal_register import FederalRegisterAdapter


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_federal_register_only_searches_policy_queries(monkeypatch):
    calls = {"count": 0}

    def _fake_get(*args, **kwargs):
        calls["count"] += 1
        return _FakeResponse({"results": []})

    monkeypatch.setattr("retrocause.sources.federal_register.httpx.get", _fake_get)

    results = FederalRegisterAdapter().search("United States Iran first round talks", max_results=3)

    assert results == []
    assert calls["count"] == 0


def test_federal_register_returns_trusted_fulltext_policy_results(monkeypatch):
    payload = {
        "results": [
            {
                "title": "Export Controls on Semiconductor Manufacturing Items",
                "type": "Rule",
                "publication_date": "2023-10-25",
                "agency_names": ["Bureau of Industry and Security"],
                "abstract": (
                    "The Bureau of Industry and Security released export controls "
                    "on semiconductor manufacturing items."
                ),
                "html_url": "https://www.federalregister.gov/documents/example",
            }
        ]
    }

    monkeypatch.setattr(
        "retrocause.sources.federal_register.httpx.get",
        lambda *args, **kwargs: _FakeResponse(payload),
    )
    monkeypatch.setattr("retrocause.sources.federal_register._query_cache", {})

    results = FederalRegisterAdapter().search(
        "export controls semiconductor chips United States Commerce Department",
        max_results=3,
    )

    assert len(results) == 1
    assert results[0].metadata["trusted_domain"] is True
    assert results[0].metadata["content_quality"] == "trusted_fulltext"
    assert results[0].metadata["published"] == "2023-10-25"
