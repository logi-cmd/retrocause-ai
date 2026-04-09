from __future__ import annotations

from retrocause.anchoring import ground_citation_spans
from retrocause.models import CausalEdge, CitationSpan


def test_ground_citation_spans_basic():
    edge = CausalEdge(source="asteroid_impact", target="extinction", conditional_prob=0.8)
    edge.supporting_evidence_ids = ["ev-0001"]
    evidence_lookup = {
        "ev-0001": "The asteroid impact caused a mass extinction event killing all dinosaurs.",
    }
    spans = ground_citation_spans(edge, evidence_lookup)
    assert len(spans) >= 1
    assert isinstance(spans[0], CitationSpan)
    assert spans[0].evidence_id == "ev-0001"
    assert (
        "asteroid" in spans[0].quoted_text.lower() or "extinction" in spans[0].quoted_text.lower()
    )
    assert spans[0].relevance_score > 0


def test_ground_citation_spans_no_evidence():
    edge = CausalEdge(source="a", target="b", conditional_prob=0.5)
    spans = ground_citation_spans(edge, {})
    assert spans == []


def test_ground_citation_spans_empty_content():
    edge = CausalEdge(source="a", target="b", conditional_prob=0.5)
    edge.supporting_evidence_ids = ["ev-0001"]
    spans = ground_citation_spans(edge, {"ev-0001": ""})
    assert spans == []


def test_ground_citation_spans_no_keyword_match():
    edge = CausalEdge(source="quantum_field", target="particle_decay", conditional_prob=0.3)
    edge.supporting_evidence_ids = ["ev-0001"]
    evidence_lookup = {
        "ev-0001": "The weather was sunny and birds were singing in the garden.",
    }
    spans = ground_citation_spans(edge, evidence_lookup)
    assert len(spans) >= 1  # fallback to first N chars
    assert edge.citation_spans == spans


def test_ground_citation_spans_multiple_evidence():
    edge = CausalEdge(source="climate_change", target="extinction", conditional_prob=0.7)
    edge.supporting_evidence_ids = ["ev-0001", "ev-0002"]
    evidence_lookup = {
        "ev-0001": "Climate change led to habitat loss for many species.",
        "ev-0002": "Rapid temperature increase caused extinction of megafauna.",
    }
    spans = ground_citation_spans(edge, evidence_lookup)
    assert len(spans) == 2
    ids = {s.evidence_id for s in spans}
    assert ids == {"ev-0001", "ev-0002"}
