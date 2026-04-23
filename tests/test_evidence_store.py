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
    stored_query = "MH370为什么失踪？"
    related_query = "为什么MH370会失踪？"
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
    iran_query = "为什么美国会同意与伊朗进行首轮谈判？"
    different_query = "美国为什么会推出新的半导体出口管制？"

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
