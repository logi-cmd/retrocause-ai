from __future__ import annotations

from retrocause.evidence_store import EvidenceStore
from retrocause.models import Evidence, EvidenceType


def _make_evidence(
    *,
    evidence_id: str,
    content: str,
    source_type: EvidenceType = EvidenceType.SCIENTIFIC,
    reliability: float = 0.82,
    linked_variables: list[str] | None = None,
    extraction_method: str = "llm",
) -> Evidence:
    return Evidence(
        id=evidence_id,
        content=content,
        source_type=source_type,
        source_url="https://example.com/evidence",
        prior_reliability=reliability,
        posterior_reliability=reliability,
        linked_variables=linked_variables or [],
        source_tier="base",
        freshness="stable",
        captured_at="2026-04-11",
        extraction_method=extraction_method,
    )


class InMemoryEvidenceStore(EvidenceStore):
    def _save(self) -> None:
        return None


def test_evidence_store_reuses_high_quality_cjk_queries():
    store = InMemoryEvidenceStore("evidence_store.json")
    stored_query = "\u004d\u0048\u0033\u0037\u0030\u4e3a\u4ec0\u4e48\u5931\u8e2a\uff1f"
    related_query = "\u4e3a\u4ec0\u4e48\u004d\u0048\u0033\u0037\u0030\u4f1a\u5931\u8e2a\uff1f"
    evidence = _make_evidence(
        evidence_id="ev-0001",
        content="MH370 disappearance remains linked to flight path deviation and delayed tracking.",
        linked_variables=["flight_path_deviation", "mh370_disappearance"],
    )

    store.add_evidences(stored_query, "aviation", [evidence])
    results = store.search(related_query, "aviation")

    assert len(results) == 1
    assert results[0].content == evidence.content
    assert results[0].extraction_method == "llm"


def test_evidence_store_filters_out_low_quality_or_fallback_items():
    store = InMemoryEvidenceStore("evidence_store.json")
    store.add_evidences(
        "MH370 why did it disappear?",
        "aviation",
        [
            _make_evidence(
                evidence_id="ev-0001",
                content="Low quality rumor.",
                reliability=0.45,
            ),
            _make_evidence(
                evidence_id="ev-0002",
                content="Fallback-only summary.",
                extraction_method="fallback_summary",
            ),
            _make_evidence(
                evidence_id="ev-0003",
                content="Official report ties aircraft diversion to loss of contact.",
                linked_variables=["aircraft_diversion", "loss_of_contact"],
            ),
        ],
    )

    results = store.search("loss of contact aircraft diversion", "aviation")

    assert [item.id for item in results] == ["ev-0003"]


def test_evidence_store_respects_time_scope_for_time_sensitive_queries():
    store = InMemoryEvidenceStore("evidence_store.json")
    store.add_evidences(
        "Why did this stock fall?",
        "finance",
        [_make_evidence(evidence_id="ev-0001", content="Yesterday-only explanation.")],
        time_scope="yesterday",
    )
    store.add_evidences(
        "Why did this stock fall?",
        "finance",
        [_make_evidence(evidence_id="ev-0002", content="Today trading-day explanation.")],
        time_scope="trading_day",
    )

    results = store.search(
        "Why did this stock fall?",
        "finance",
        time_scope="trading_day",
    )

    assert results
    assert results[0].id == "ev-0002"


def test_evidence_store_does_not_reuse_relative_yesterday_across_calendar_days():
    store = InMemoryEvidenceStore("evidence_store.json")
    store.add_evidences(
        "Why did Bitcoin fall yesterday?",
        "finance",
        [_make_evidence(evidence_id="ev-0001", content="April 12 trading explanation.")],
        time_scope="yesterday:2026-04-12",
    )

    results = store.search(
        "Why did Bitcoin fall yesterday?",
        "finance",
        time_scope="yesterday:2026-04-13",
    )

    assert results == []


def test_evidence_store_does_not_reuse_thin_cjk_overlap_between_different_us_questions():
    store = InMemoryEvidenceStore("evidence_store.json")
    iran_query = "\u4e3a\u4ec0\u4e48\u7f8e\u56fd\u4f1a\u540c\u610f\u4e0e\u4f0a\u6717\u8fdb\u884c\u9996\u8f6e\u8c08\u5224\uff1f"
    different_query = "\u7f8e\u56fd\u4e3a\u4ec0\u4e48\u4f1a\u63a8\u51fa\u65b0\u7684\u534a\u5bfc\u4f53\u51fa\u53e3\u7ba1\u5236\uff1f"

    evidence = _make_evidence(
        evidence_id="ev-iran",
        content="US and Iran talks were linked to diplomatic pressure and sanctions leverage.",
        source_type=EvidenceType.NEWS,
        reliability=0.84,
        linked_variables=["diplomacy", "sanctions"],
        extraction_method="llm_fulltext_trusted",
    )

    store.add_evidences(iran_query, "geopolitics", [evidence], time_scope="last_24h")
    results = store.search(different_query, "geopolitics", time_scope="last_24h")

    assert results == []
