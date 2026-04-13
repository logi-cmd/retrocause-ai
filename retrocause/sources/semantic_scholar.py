"""Semantic Scholar paper search adapter."""

from __future__ import annotations

import logging
import time

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_TIMEOUT = 5.0
_FIELDS = "title,abstract,url,year,authors"
_DISABLE_SECONDS = 120.0
_disabled_until = 0.0


class SemanticScholarAdapter(BaseSourceAdapter):
    """Semantic Scholar adapter with a short-lived 429 circuit breaker."""

    @property
    def name(self) -> str:
        return "semantic_scholar"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.LITERATURE

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        global _disabled_until

        if time.time() < _disabled_until:
            logger.info("Semantic Scholar search temporarily disabled after recent failures")
            return []

        try:
            response = httpx.get(
                _API_URL,
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": _FIELDS,
                },
                timeout=_TIMEOUT,
                headers={"User-Agent": "RetroCause/0.1 (research tool)"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                _disabled_until = time.time() + _DISABLE_SECONDS
            logger.warning("Semantic Scholar request failed: %s", exc)
            return []
        except httpx.HTTPError as exc:
            _disabled_until = time.time() + _DISABLE_SECONDS
            logger.warning("Semantic Scholar request failed: %s", exc)
            return []

        return self._parse_json(response.json())

    @staticmethod
    def _parse_json(data: dict) -> list[SearchResult]:
        results: list[SearchResult] = []
        papers = data.get("data") or []

        for paper in papers:
            title = paper.get("title", "").strip()
            url = paper.get("url", "").strip()
            abstract = (paper.get("abstract") or "").strip()
            if not title:
                continue

            metadata: dict = {}
            year = paper.get("year")
            if year is not None:
                metadata["year"] = str(year)

            raw_authors = paper.get("authors") or []
            author_names = [a.get("name", "").strip() for a in raw_authors if a.get("name", "").strip()]
            if author_names:
                metadata["authors"] = author_names

            paper_id = paper.get("paperId")
            if paper_id:
                metadata["paper_id"] = paper_id

            results.append(
                SearchResult(
                    title=title,
                    content=abstract,
                    url=url,
                    source_type=EvidenceType.LITERATURE,
                    metadata=metadata,
                )
            )

        return results
