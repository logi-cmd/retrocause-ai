from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from retrocause.api.briefs import humanize_identifier


SECTION_TITLES = {
    "market": ("Market Drivers", "What Would Change The View"),
    "policy_geopolitics": ("Negotiation Constraints", "Source And Policy Risks"),
    "postmortem": ("Operational Causes", "Evidence Needed Before Action"),
    "general": ("Top Causes", "What To Check Next"),
}


def production_brief_item_from_edge_payload(
    edge: object,
    evidence_by_id: dict[str, object],
) -> dict[str, Any]:
    evidence_ids = list(dict.fromkeys(_field(edge, "supporting_evidence_ids", []) or []))
    source = humanize_identifier(str(_field(edge, "source", "")))
    target = humanize_identifier(str(_field(edge, "target", "")))
    strength = float(_field(edge, "strength", 0.0) or 0.0)
    title = f"{source} -> {target}"
    summary = (
        f"{source} is likely pushing {target} "
        f"({strength:.0%} confidence signal, {len(evidence_ids)} supporting evidence item(s))."
    )
    excerpt = _first_evidence_excerpt(evidence_ids, evidence_by_id)
    if excerpt:
        summary = f"{summary} Supporting clue: {excerpt}"
    return {
        "title": title,
        "summary": summary,
        "evidence_ids": evidence_ids,
        "confidence": max(0.0, min(1.0, strength)),
    }


def build_production_brief_payload(response: object, scenario: object) -> dict[str, Any]:
    items = _top_edge_item_payloads(response)
    scenario_key = str(_field(scenario, "key", "general") or "general")
    primary_title, secondary_title = SECTION_TITLES.get(
        scenario_key,
        SECTION_TITLES["general"],
    )
    verification_items = _verification_item_payloads(response, scenario)
    limits: list[str] = []
    if not items:
        limits.append("No evidence-anchored causal drivers were available in this run.")
    else:
        analysis_brief = _field(response, "analysis_brief", None)
        if analysis_brief:
            limits.extend(list(_field(analysis_brief, "missing_evidence", []) or [])[:3])

    return {
        "title": str(_field(scenario, "label", "")),
        "scenario_key": scenario_key,
        "executive_summary": _production_executive_summary(response, scenario, items),
        "sections": [
            {"kind": "drivers", "title": primary_title, "items": items[:5]},
            {
                "kind": "verification",
                "title": secondary_title,
                "items": verification_items,
            },
        ],
        "limits": limits,
        "next_verification_steps": [str(item["summary"]) for item in verification_items],
    }


def _top_edge_item_payloads(response: object) -> list[dict[str, Any]]:
    chains = list(_field(response, "chains", []) or [])
    if not chains:
        return []
    top_chain = max(chains, key=lambda chain: float(_field(chain, "probability", 0.0) or 0.0))
    evidence_by_id = {
        str(_field(evidence, "id", "")): evidence
        for evidence in list(_field(response, "evidences", []) or [])
    }
    items = [
        production_brief_item_from_edge_payload(edge, evidence_by_id)
        for edge in list(_field(top_chain, "edges", []) or [])
        if _field(edge, "supporting_evidence_ids", [])
    ]
    return sorted(items, key=lambda item: float(item["confidence"]), reverse=True)


def _verification_item_payloads(response: object, scenario: object) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    challenge_checks = list(_field(response, "challenge_checks", []) or [])
    if challenge_checks:
        checked = len(challenge_checks)
        refuting = sum(int(_field(check, "refuting_count", 0) or 0) for check in challenge_checks)
        challenge_summary = (
            f"{refuting} challenge evidence item(s) were attached in this run."
            if refuting
            else "no explicit challenge evidence was attached in this run."
        )
        items.append(
            {
                "title": "Challenge coverage",
                "summary": f"Review {checked} checked edge(s); {challenge_summary}",
                "confidence": 1.0 if checked else 0.0,
            }
        )
    else:
        items.append(
            {
                "title": "Challenge coverage",
                "summary": (
                    "Run or inspect targeted challenge retrieval before treating this as settled."
                ),
                "confidence": 0.25,
            }
        )

    scenario_key = str(_field(scenario, "key", "general") or "general")
    scenario_items = {
        "market": {
            "title": "Market freshness",
            "summary": "Check whether the freshest retrieved sources cover the relevant market window.",
            "confidence": 0.5,
        },
        "policy_geopolitics": {
            "title": "Source reliability",
            "summary": "Compare official, wire, and regional-source evidence before relying on the brief.",
            "confidence": 0.5,
        },
        "postmortem": {
            "title": "Internal evidence",
            "summary": "Attach logs, tickets, metrics, or customer evidence before assigning action owners.",
            "confidence": 0.5,
        },
    }
    items.append(
        scenario_items.get(
            scenario_key,
            {
                "title": "Evidence depth",
                "summary": "Inspect evidence coverage and missing evidence before relying on the conclusion.",
                "confidence": 0.5,
            },
        )
    )
    return items


def _production_executive_summary(
    response: object,
    scenario: object,
    items: Sequence[dict[str, Any]],
) -> str:
    scenario_label = str(_field(scenario, "label", ""))
    if items:
        top_item = items[0]
        return (
            f"{scenario_label}: the strongest evidence-anchored driver is "
            f"{top_item['title']} ({float(top_item['confidence']):.0%} confidence signal)."
        )
    analysis_brief = _field(response, "analysis_brief", None)
    brief_answer = str(_field(analysis_brief, "answer", "")) if analysis_brief else ""
    if brief_answer:
        return f"{scenario_label}: {brief_answer}"
    return f"{scenario_label}: no evidence-anchored production driver is available yet."


def _first_evidence_excerpt(
    evidence_ids: Sequence[str],
    evidence_by_id: dict[str, object],
) -> str:
    for evidence_id in evidence_ids:
        evidence = evidence_by_id.get(str(evidence_id))
        if evidence is None:
            continue
        content = " ".join(str(_field(evidence, "content", "")).split())
        if not content:
            continue
        return content[:180]
    return ""


def _field(item: object, key: str, default: object = None) -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)
