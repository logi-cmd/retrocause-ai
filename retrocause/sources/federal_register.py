"""Federal Register adapter for official U.S. policy and regulatory evidence."""

from __future__ import annotations

import logging
import re
import time

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

_API_URL = "https://www.federalregister.gov/api/v1/documents.json"
_TIMEOUT = 12.0
_QUERY_CACHE_TTL = 900.0
_query_cache: dict[tuple[str, int], tuple[float, list[SearchResult]]] = {}
_POLICY_TOKENS = {
    "bis",
    "commerce",
    "control",
    "controls",
    "export",
    "exports",
    "restriction",
    "restrictions",
    "sanction",
    "sanctions",
    "semiconductor",
    "semiconductors",
    "tariff",
    "tariffs",
}
_STOPWORDS = {"the", "and", "for", "with", "from", "what", "why", "did", "does", "this"}


def _query_tokens(query: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z]{3,}", query.lower())
        if token not in _STOPWORDS
    }


def _should_search(query: str) -> bool:
    return bool(_query_tokens(query) & _POLICY_TOKENS)


def _overlap_score(text: str, query_tokens: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for token in query_tokens if token in lowered)


class FederalRegisterAdapter(BaseSourceAdapter):
    """Search official Federal Register documents for U.S. policy evidence."""

    @property
    def name(self) -> str:
        return "federal_register"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.ARCHIVE

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not _should_search(query):
            return []

        cache_key = (query.strip().lower(), max_results)
        cached = _query_cache.get(cache_key)
        now = time.time()
        if cached and now - cached[0] <= _QUERY_CACHE_TTL:
            return cached[1]

        try:
            response = httpx.get(
                _API_URL,
                params={
                    "conditions[term]": query,
                    "per_page": min(max_results * 3, 20),
                    "order": "relevance",
                },
                timeout=_TIMEOUT,
                headers={"User-Agent": "RetroCause/0.1 (research tool)"},
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Federal Register request failed: %s", exc)
            return cached[1] if cached else []

        query_tokens = _query_tokens(query)
        ranked_documents = sorted(
            data.get("results") or [],
            key=lambda item: _overlap_score(
                " ".join(
                    [
                        str(item.get("title", "")),
                        str(item.get("abstract", "")),
                        str(item.get("type", "")),
                    ]
                ),
                query_tokens,
            ),
            reverse=True,
        )

        results: list[SearchResult] = []
        for item in ranked_documents:
            title = str(item.get("title", "")).strip()
            abstract = str(item.get("abstract", "")).strip()
            url = str(item.get("html_url", "")).strip()
            if not title or not url:
                continue

            body = "\n".join(
                part
                for part in [
                    f"Title: {title}",
                    f"Type: {item.get('type', '')}",
                    f"Publication date: {item.get('publication_date', '')}",
                    f"Agency: {item.get('agency_names', [])}",
                    abstract,
                ]
                if str(part).strip()
            )
            if _overlap_score(body, query_tokens) < 2:
                continue

            results.append(
                SearchResult(
                    title=title,
                    content=abstract or title,
                    url=url,
                    source_type=EvidenceType.ARCHIVE,
                    metadata={
                        "published": str(item.get("publication_date", "")),
                        "source_domain": "federalregister.gov",
                        "trusted_domain": True,
                        "page_content": body[:12000],
                        "content_quality": "trusted_fulltext",
                    },
                )
            )
            if len(results) >= max_results:
                break

        if results:
            _query_cache[cache_key] = (time.time(), results)
        return results
