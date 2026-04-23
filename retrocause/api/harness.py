from __future__ import annotations

from typing import Any

from retrocause.api.provider_preflight import (
    classify_preflight_failure_code,
    preflight_user_action,
)


def build_production_harness_payload(response: object) -> dict[str, Any]:
    checks = [
        _check_freshness_gate(response),
        _check_evidence_anchor_gate(response),
        _check_source_risk_gate(response),
        _check_challenge_gate(response),
        _check_internal_evidence_gate(response),
    ]
    if any(check["severity"] == "blocker" and not check["passed"] for check in checks):
        status = "blocked"
    elif any(check["name"] == "internal_evidence" and not check["passed"] for check in checks):
        status = "not_actionable"
    elif any(check["severity"] == "warning" and not check["passed"] for check in checks):
        status = "needs_more_evidence"
    else:
        status = "ready_for_brief"

    score = sum(1 for check in checks if check["passed"]) / max(1, len(checks))
    next_actions = [str(check["message"]) for check in checks if not check["passed"]]
    if not next_actions:
        next_actions.append("Review cited evidence and challenge coverage before relying on the brief.")

    scenario = _field(response, "scenario", None)
    return {
        "status": status,
        "score": max(0.0, min(1.0, score)),
        "scenario_key": str(_field(scenario, "key", "general") or "general"),
        "checks": checks,
        "next_actions": next_actions[:4],
    }


def build_product_harness_payload(response: object) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    has_actionable_failure = bool(
        _field(response, "error", None)
        or _field(response, "partial_live_reasons", None)
        or _field(response, "analysis_mode", "") == "demo"
    )
    chains = list(_field(response, "chains", []) or [])
    if chains:
        checks.append(
            _harness_check_payload(
                "causal_chain",
                "Causal chain present",
                "pass",
                f"{len(chains)} chain(s), {sum(len(_field(c, 'edges', []) or []) for c in chains)} edge(s).",
            )
        )
    else:
        checks.append(
            _harness_check_payload(
                "causal_chain",
                "Causal chain present",
                "fail",
                "No causal chain is available for review.",
            )
        )

    analysis_brief = _field(response, "analysis_brief", None)
    if analysis_brief and (
        _field(analysis_brief, "answer", "") or _field(analysis_brief, "top_reasons", [])
    ):
        checks.append(
            _harness_check_payload(
                "analysis_summary",
                "Analysis summary present",
                "pass",
                "The response includes a synthesized answer and reason list.",
            )
        )
    else:
        checks.append(
            _harness_check_payload(
                "analysis_summary",
                "Analysis summary present",
                "fail",
                "No synthesized answer is attached.",
            )
        )

    retrieval_trace = list(_field(response, "retrieval_trace", []) or [])
    has_source_trace = bool(retrieval_trace)
    if retrieval_trace:
        source_hits = sum(
            max(0, int(_field(item, "result_count", 0) or 0))
            for item in retrieval_trace
        )
        recovered_rows = sum(
            1 for item in retrieval_trace if str(_field(item, "status", "") or "") == "recovered"
        )
        status = "pass" if source_hits > 0 else "warn"
        detail = f"{len(retrieval_trace)} source query row(s), {source_hits} result hit(s)."
        if recovered_rows:
            detail += f" {recovered_rows} recovered retry row(s)."
        checks.append(
            _harness_check_payload(
                "source_trace",
                "Source trace visible",
                status,
                detail,
            )
        )
    else:
        checks.append(
            _harness_check_payload(
                "source_trace",
                "Source trace visible",
                "fail",
                "No source-level retrieval trace is visible.",
            )
        )

    evidences = list(_field(response, "evidences", []) or [])
    has_anchored_evidence = _has_anchored_evidence(chains)
    if evidences:
        stances = {
            _field(item, "stance", "")
            or ("supporting" if bool(_field(item, "is_supporting", False)) else "refuting")
            for item in evidences
        }
        checks.append(
            _harness_check_payload(
                "evidence_stance",
                "Evidence stance visible",
                "pass",
                f"{len(evidences)} evidence item(s), stance(s): {', '.join(sorted(stances))}.",
            )
        )
    else:
        checks.append(
            _harness_check_payload(
                "evidence_stance",
                "Evidence stance visible",
                "fail",
                "No evidence items are attached.",
            )
        )

    if has_anchored_evidence:
        checks.append(
            _harness_check_payload(
                "evidence_anchor",
                "Evidence attached to causal chain",
                "pass",
                "At least one chain or edge references evidence IDs.",
            )
        )
    else:
        checks.append(
            _harness_check_payload(
                "evidence_anchor",
                "Evidence attached to causal chain",
                "fail" if chains else "warn",
                "No causal chain or edge references evidence IDs.",
            )
        )

    challenge_checks = list(_field(response, "challenge_checks", []) or [])
    if challenge_checks:
        checked = len(challenge_checks)
        refuting = sum(int(_field(item, "refuting_count", 0) or 0) for item in challenge_checks)
        checks.append(
            _harness_check_payload(
                "challenge_coverage",
                "Challenge coverage checked",
                "pass",
                f"{checked} edge(s) checked, {refuting} challenge item(s).",
            )
        )
    else:
        checks.append(
            _harness_check_payload(
                "challenge_coverage",
                "Challenge coverage checked",
                "warn" if chains else "fail",
                "No targeted challenge retrieval is attached.",
            )
        )

    if has_actionable_failure:
        checks.append(
            _harness_check_payload(
                "actionable_failure",
                "Failure state actionable",
                "pass",
                _field(response, "error", None)
                or "; ".join(list(_field(response, "partial_live_reasons", []) or []))
                or str(_field(response, "analysis_mode", "")),
            )
        )
    elif _field(response, "analysis_mode", "") == "live":
        checks.append(
            _harness_check_payload(
                "actionable_failure",
                "Failure state actionable",
                "pass",
                "No failure state is present.",
            )
        )
    else:
        checks.append(
            _harness_check_payload(
                "actionable_failure",
                "Failure state actionable",
                "warn",
                "The run is degraded but has no explicit reason.",
            )
        )

    score_map = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    score = sum(score_map.get(str(check["status"]), 0.0) for check in checks) / max(1, len(checks))
    score = max(0.0, min(1.0, score))

    next_actions: list[str] = []
    if not chains and _field(response, "error", None):
        error_msg = str(_field(response, "error", None) or "")
        status = "blocked_by_model"
        summary = "The run did not produce a causal answer; the useful output is the failure diagnosis."
        next_actions.append(preflight_user_action(classify_preflight_failure_code(error_msg)))
        next_actions.append("Run provider preflight before starting another full analysis.")
    elif score >= 0.75 and chains and evidences and has_anchored_evidence and has_source_trace:
        status = "ready_for_review"
        summary = "The result has enough structure for a user to review reasons, sources, and gaps."
    elif chains:
        status = "needs_more_evidence"
        summary = "The result has a causal shape, but evidence or challenge coverage is still thin."
    else:
        status = "not_reviewable"
        summary = "The result is not yet reviewable as a causal explanation."

    if not retrieval_trace:
        next_actions.append("Expose source trace rows so the user can see where evidence came from.")
    if not challenge_checks:
        next_actions.append("Run targeted challenge retrieval for the strongest causal edges.")
    if not analysis_brief:
        next_actions.append("Generate an analysis brief with top reasons and missing evidence.")
    if not evidences:
        next_actions.append("Collect or attach evidence before presenting causal conclusions.")
    if chains and evidences and not has_anchored_evidence:
        next_actions.append("Attach retrieved evidence to the causal chain before review.")
    if not next_actions:
        next_actions.append("Review the top reasons and inspect the cited evidence before trusting the conclusion.")

    return {
        "score": score,
        "status": status,
        "user_value_summary": summary,
        "checks": checks,
        "next_actions": next_actions[:4],
    }


def _production_check_payload(
    name: str,
    passed: bool,
    severity: str,
    message: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "severity": severity,
        "message": message,
    }


def _has_anchored_evidence(chains: list[object]) -> bool:
    for chain in chains:
        if _field(chain, "supporting_evidence_ids", []) or _field(chain, "refuting_evidence_ids", []):
            return True
        for edge in list(_field(chain, "edges", []) or []):
            if _field(edge, "supporting_evidence_ids", []) or _field(
                edge,
                "refuting_evidence_ids",
                [],
            ):
                return True
        for node in list(_field(chain, "nodes", []) or []):
            if _field(node, "supporting_evidence_ids", []) or _field(
                node,
                "refuting_evidence_ids",
                [],
            ):
                return True
    return False


def _check_freshness_gate(response: object) -> dict[str, Any]:
    scenario = _field(response, "scenario", None)
    scenario_key = str(_field(scenario, "key", "general") or "general")
    needs_freshness = scenario_key in {"market", "policy_geopolitics"} and _field(
        response,
        "time_range",
        "",
    ) in {"today", "yesterday", "this_week", "this month"}
    if not needs_freshness:
        return _production_check_payload(
            "freshness_gate",
            True,
            "info",
            "This scenario/query does not require a strict latest-information gate.",
        )
    fresh_enough = _field(response, "freshness_status", "") in {"fresh", "recent"}
    return _production_check_payload(
        "freshness_gate",
        fresh_enough,
        "warning",
        "Latest-information query has fresh/recent evidence."
        if fresh_enough
        else "Latest-information query needs fresh evidence before the brief is ready.",
    )


def _check_evidence_anchor_gate(response: object) -> dict[str, Any]:
    production_brief = _field(response, "production_brief", None)
    anchored_items = [
        item
        for section in list(_field(production_brief, "sections", []) or [])
        for item in list(_field(section, "items", []) or [])
        if _field(section, "kind", "") not in {"limits", "verification"}
        and _field(item, "evidence_ids", [])
    ]
    return _production_check_payload(
        "evidence_anchor",
        bool(anchored_items),
        "blocker",
        "Production claims include evidence IDs."
        if anchored_items
        else "No evidence-anchored production claim is available.",
    )


def _check_source_risk_gate(response: object) -> dict[str, Any]:
    scenario = _field(response, "scenario", None)
    scenario_key = str(_field(scenario, "key", "general") or "general")
    if scenario_key not in {"market", "policy_geopolitics"}:
        return _production_check_payload(
            "source_risk",
            True,
            "info",
            "No policy/market source-risk gate is required for this scenario.",
        )
    retrieval_trace = list(_field(response, "retrieval_trace", []) or [])
    if not retrieval_trace:
        return _production_check_payload(
            "source_risk",
            False,
            "warning",
            "No source trace is attached, so source quality cannot be inspected.",
        )
    stable_rows = [
        item
        for item in retrieval_trace
        if _field(item, "stability", "") in {"high", "medium"}
        and not _field(item, "error", None)
        and int(_field(item, "result_count", 0) or 0) > 0
    ]
    passed = bool(stable_rows)
    return _production_check_payload(
        "source_risk",
        passed,
        "warning",
        "At least one stable source returned evidence."
        if passed
        else "Only weak or empty source traces are attached.",
    )


def _check_challenge_gate(response: object) -> dict[str, Any]:
    challenge_checks = list(_field(response, "challenge_checks", []) or [])
    passed = bool(challenge_checks)
    return _production_check_payload(
        "challenge_coverage",
        passed,
        "warning",
        f"{len(challenge_checks)} challenge check(s) are attached."
        if passed
        else "No targeted challenge checks are attached.",
    )


def _check_internal_evidence_gate(response: object) -> dict[str, Any]:
    scenario = _field(response, "scenario", None)
    scenario_key = str(_field(scenario, "key", "general") or "general")
    if scenario_key != "postmortem":
        return _production_check_payload(
            "internal_evidence",
            True,
            "info",
            "Internal operational evidence is not required for this scenario.",
        )
    internal_markers = ("log", "ticket", "metric", "customer", "incident", "internal")
    has_internal = any(
        any(marker in _evidence_marker_text(item) for marker in internal_markers)
        for item in list(_field(response, "evidences", []) or [])
    )
    return _production_check_payload(
        "internal_evidence",
        has_internal,
        "warning",
        "Internal postmortem evidence is attached."
        if has_internal
        else "Postmortem brief needs logs, tickets, metrics, or customer/internal evidence.",
    )


def _harness_check_payload(
    check_id: str,
    label: str,
    status: str,
    detail: object = "",
) -> dict[str, Any]:
    return {"id": check_id, "label": label, "status": status, "detail": str(detail or "")}


def _evidence_marker_text(item: object) -> str:
    return " ".join(
        str(_field(item, field_name, "") or "")
        for field_name in ("source", "extraction_method", "content")
    ).lower()


def _field(item: object, key: str, default: object = None) -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)
