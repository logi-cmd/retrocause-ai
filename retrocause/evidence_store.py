"""Local evidence cache/store for reusing high-quality evidence across runs."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from retrocause.models import Evidence, EvidenceType

_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "what",
    "why",
    "how",
    "did",
    "does",
    "cause",
    "causes",
    "into",
    "about",
    "which",
    "when",
    "where",
}

_CJK_STOPGRAMS = {
    "为什",
    "什么",
    "为什么",
    "原因",
    "怎么",
    "如何",
    "是否",
}


def _default_store_path() -> Path:
    return Path.cwd() / ".retrocause" / "evidence_store.json"


def _normalize_tokens(text: str) -> set[str]:
    ascii_tokens = {
        token
        for token in re.findall(r"[A-Za-z0-9_]+", text.lower())
        if len(token) >= 3 and token not in _STOPWORDS
    }
    cjk_tokens: set[str] = set()
    for match in re.findall(r"[\u4e00-\u9fff]+", text):
        compact = match.strip()
        if len(compact) <= 1:
            cjk_tokens.add(compact)
            continue
        for size in (2, 3):
            if len(compact) < size:
                continue
            for index in range(len(compact) - size + 1):
                token = compact[index : index + size]
                if token not in _CJK_STOPGRAMS:
                    cjk_tokens.add(token)
    return ascii_tokens | cjk_tokens


def _is_cjk_query(tokens: set[str]) -> bool:
    return any(re.search(r"[\u4e00-\u9fff]", token) for token in tokens)


def _has_enough_overlap(query_tokens: set[str], item_tokens: set[str]) -> bool:
    overlap = len(query_tokens & item_tokens)
    if overlap == 0:
        return False

    if _is_cjk_query(query_tokens):
        ascii_overlap = {
            token for token in query_tokens & item_tokens if re.fullmatch(r"[a-z0-9_]+", token)
        }
        if ascii_overlap and overlap >= 2:
            return True
        overlap_ratio = overlap / max(1, min(len(query_tokens), len(item_tokens)))
        return overlap >= 3 and overlap_ratio >= 0.12

    return overlap >= 1


class EvidenceStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else _default_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items = self._load()

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._items, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_evidences(
        self,
        query: str,
        domain: str,
        evidences: list[Evidence],
        time_scope: str | None = None,
    ) -> None:
        query_tokens = sorted(_normalize_tokens(query))
        known_contents = {
            (
                item["content"].strip().lower(),
                item.get("domain", ""),
                item.get("time_scope"),
            )
            for item in self._items
        }

        changed = False
        for evidence in evidences:
            if evidence.extraction_method == "fallback_summary":
                continue
            if evidence.posterior_reliability < 0.55:
                continue

            content_key = (evidence.content.strip().lower(), domain, time_scope)
            if content_key in known_contents:
                continue

            payload = asdict(evidence)
            payload["source_type"] = evidence.source_type.value
            payload["query_tokens"] = query_tokens
            payload["domain"] = domain
            payload["time_scope"] = time_scope
            self._items.append(payload)
            known_contents.add(content_key)
            changed = True

        if changed:
            self._save()

    def search(
        self,
        query: str,
        domain: str,
        limit: int = 8,
        time_scope: str | None = None,
    ) -> list[Evidence]:
        query_tokens = _normalize_tokens(query)
        if not query_tokens:
            return []

        ranked: list[tuple[float, dict]] = []
        for item in self._items:
            if time_scope and item.get("time_scope") != time_scope:
                continue
            item_tokens = set(item.get("query_tokens", [])) | _normalize_tokens(item.get("content", ""))
            if not _has_enough_overlap(query_tokens, item_tokens):
                continue

            overlap = len(query_tokens & item_tokens)
            score = overlap
            if item.get("domain") == domain:
                score += 2
            if item.get("time_scope") == time_scope:
                score += 2.5
            elif time_scope and item.get("time_scope") is None:
                score -= 1.5
            elif item.get("time_scope") and time_scope is None:
                score -= 0.5
            score += float(item.get("posterior_reliability", 0.5))
            if item.get("source_type") in {
                EvidenceType.SCIENTIFIC.value,
                EvidenceType.LITERATURE.value,
                EvidenceType.ARCHIVE.value,
            }:
                score += 0.35
            if item.get("source_tier") == "base":
                score += 0.5
            ranked.append((score, item))

        ranked.sort(key=lambda pair: pair[0], reverse=True)

        results: list[Evidence] = []
        for _, item in ranked[:limit]:
            results.append(
                Evidence(
                    id=item.get("id", ""),
                    content=item["content"],
                    source_type=EvidenceType(item["source_type"]),
                    source_url=item.get("source_url"),
                    timestamp=item.get("timestamp"),
                    prior_reliability=float(item.get("prior_reliability", 0.5)),
                    posterior_reliability=float(item.get("posterior_reliability", 0.5)),
                    linked_variables=list(item.get("linked_variables", [])),
                    source_tier=item.get("source_tier", "base"),
                    freshness=item.get("freshness", "unknown"),
                    captured_at=item.get("captured_at"),
                    extraction_method=item.get("extraction_method", "store_cache"),
                )
            )
        return results
