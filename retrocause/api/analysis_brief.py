from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from retrocause.api.briefs import humanize_identifier


DEGRADED_SOURCE_STATUSES = {
    "source_limited",
    "rate_limited",
    "forbidden",
    "timeout",
    "source_error",
}

HIGH_QUALITY_EXTRACTION_METHODS = {
    "llm_fulltext_trusted",
    "llm_fulltext",
    "llm_trusted",
    "store_cache",
    "uploaded_evidence",
}


def edge_challenge_phrase(edge: object) -> str:
    refuting_count = len(_field(edge, "refuting_evidence_ids", []) or [])
    if refuting_count:
        return f"Challenge evidence on this edge: {refuting_count}"
    refutation_status = str(_field(edge, "refutation_status", ""))
    if refutation_status in {
        "checked_no_refuting_claims",
        "no_refutation_in_retrieved_evidence",
    }:
        return "No challenge evidence attached to this edge after targeted retrieval"
    if refutation_status == "checked_no_results":
        return "Challenge retrieval checked this edge but returned no source results"
    if refutation_status == "not_checked":
        return "Challenge retrieval has not checked this edge"
    return "No challenge evidence attached to this edge"


def build_analysis_brief_payload(
    *,
    result: object,
    chains: Sequence[object],
    checks: Sequence[object],
    retrieval_statuses: Sequence[str],
) -> dict[str, Any]:
    if not chains:
        return {
            "answer": "No usable causal chain was produced for this run.",
            "confidence": 0.0,
            "top_reasons": [],
            "challenge_summary": "Challenge retrieval could not run without a causal chain.",
            "missing_evidence": [
                "A usable causal graph is needed before evidence can be challenged."
            ],
            "source_coverage": "No chain-level evidence coverage.",
        }

    top_chain = max(chains, key=lambda chain: float(_field(chain, "probability", 0.0) or 0.0))
    top_reasons = _build_top_reason_lines(result=result, top_chain=top_chain)
    challenge_summary = _build_challenge_summary(checks)
    missing = _build_missing_evidence_notes(result=result, top_chain=top_chain, checks=checks)
    source_coverage = _build_source_coverage(result, retrieval_statuses)

    return {
        "answer": (
            f"Most likely explanation: {_field(top_chain, 'label', '')} "
            f"({float(_field(top_chain, 'probability', 0.0) or 0.0):.0%} confidence signal)."
        ),
        "confidence": float(_field(top_chain, "probability", 0.0) or 0.0),
        "top_reasons": top_reasons,
        "challenge_summary": challenge_summary,
        "missing_evidence": missing[:4],
        "source_coverage": source_coverage,
    }


def _build_top_reason_lines(*, result: object, top_chain: object) -> list[str]:
    top_reasons: list[str] = []
    evidences = list(_field(result, "evidences", []) or [])
    evidence_by_id = {str(_field(ev, "id", "")): ev for ev in evidences}
    for edge in list(_field(top_chain, "edges", []) or [])[:3]:
        supporting_ids = list(_field(edge, "supporting_evidence_ids", []) or [])
        excerpt = ""
        if supporting_ids:
            evidence = evidence_by_id.get(str(supporting_ids[0]))
            if evidence is not None:
                excerpt = f" Evidence: {str(_field(evidence, 'content', ''))[:120]}"
        top_reasons.append(
            f"{humanize_identifier(str(_field(edge, 'source', '')))} -> "
            f"{humanize_identifier(str(_field(edge, 'target', '')))} "
            f"({float(_field(edge, 'strength', 0.0) or 0.0):.0%} edge strength, "
            f"{len(supporting_ids)} supporting evidence item(s), "
            f"{edge_challenge_phrase(edge)}).{excerpt}"
        )
    return top_reasons


def _build_challenge_summary(checks: Sequence[object]) -> str:
    refuting_total = sum(int(_field(check, "refuting_count", 0) or 0) for check in checks)
    checked_total = len(checks)
    if refuting_total:
        return (
            f"Found {refuting_total} challenge evidence item(s) across "
            f"{checked_total} checked edge(s)."
        )
    if checked_total:
        return (
            f"Checked {checked_total} key edge(s) and found no explicit refuting claim "
            "in retrieved evidence."
        )
    return "Challenge retrieval has not checked this result yet."


def _build_missing_evidence_notes(
    *,
    result: object,
    top_chain: object,
    checks: Sequence[object],
) -> list[str]:
    missing: list[str] = []
    edges = list(_field(top_chain, "edges", []) or [])
    if not checks:
        missing.append("Targeted challenge retrieval did not run for this result.")
    if any(str(_field(edge, "refutation_status", "")) == "checked_no_results" for edge in edges):
        missing.append("At least one challenge query returned no source results.")
    if any(not list(_field(edge, "supporting_evidence_ids", []) or []) for edge in edges):
        missing.append("At least one causal edge still lacks direct supporting evidence.")
    high_quality_count = _high_quality_evidence_count(result)
    if high_quality_count == 0:
        missing.append("No trusted full-text or cached high-quality evidence is attached.")
    if not missing:
        missing.append("Primary-source confirmation may still be needed for high-stakes use.")
    return missing


def _build_source_coverage(result: object, retrieval_statuses: Sequence[str]) -> str:
    evidences = list(_field(result, "evidences", []) or [])
    source_values = {str(_field(ev, "source_type", "")) for ev in evidences}
    high_quality_count = _high_quality_evidence_count(result)
    source_coverage = (
        f"{len(source_values)} source type(s), {high_quality_count} high-quality "
        f"evidence item(s), {len(evidences)} total evidence item(s)."
    )

    degraded_count = sum(status in DEGRADED_SOURCE_STATUSES for status in retrieval_statuses)
    if retrieval_statuses:
        source_coverage += (
            f" Retrieval trace: {len(retrieval_statuses)} source attempt(s), "
            f"{degraded_count} degraded or limited."
        )
    return source_coverage


def _high_quality_evidence_count(result: object) -> int:
    return sum(
        1
        for ev in list(_field(result, "evidences", []) or [])
        if str(_field(ev, "extraction_method", "")) in HIGH_QUALITY_EXTRACTION_METHODS
    )


def _field(item: object, key: str, default: object = None) -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    if key == "source":
        return getattr(item, "source", getattr(item, "name", default))
    return getattr(item, key, default)
