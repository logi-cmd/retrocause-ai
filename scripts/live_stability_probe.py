#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from retrocause.api.main import app


SCENARIOS = [
    {
        "id": "market_zh_a_share",
        "persona": "Chinese retail investor checking an A-share move",
        "query": "\u82af\u539f\u80a1\u4efd\u4eca\u5929\u76d8\u4e2d\u4e3a\u4ec0\u4e48\u4e0b\u8dcc\uff1f",
        "scenario_override": "market",
    },
    {
        "id": "policy_geopolitics_semiconductors",
        "persona": "Policy analyst checking semiconductor export-control causes",
        "query": "Why did the US announce new semiconductor export controls?",
        "scenario_override": "policy_geopolitics",
    },
    {
        "id": "postmortem_public_incident",
        "persona": "Engineering lead reviewing a public software incident postmortem",
        "query": "Why did the CrowdStrike Falcon update cause Windows outages?",
        "scenario_override": "postmortem",
    },
]


def _trace_summary(trace: list[dict[str, Any]]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    total_hits = 0
    for item in trace:
        status = str(item.get("status") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
        total_hits += max(0, int(item.get("result_count") or 0))
    return {
        "rows": len(trace),
        "hits": total_hits,
        "statuses": statuses,
    }


def _reviewability(payload: dict[str, Any]) -> dict[str, Any]:
    product = payload.get("product_harness") or {}
    trace = payload.get("retrieval_trace") or []
    evidences = payload.get("evidences") or []
    chains = payload.get("chains") or []
    trace_summary = _trace_summary(trace)
    return {
        "is_reviewable": len(chains) > 0 and len(evidences) > 0,
        "analysis_mode": payload.get("analysis_mode"),
        "is_demo": payload.get("is_demo"),
        "chain_count": len(chains),
        "evidence_count": len(evidences),
        "challenge_count": len(payload.get("challenge_checks") or []),
        "product_status": product.get("status"),
        "trace": trace_summary,
        "error": payload.get("error"),
    }


def _run_scenario(client: TestClient, scenario: dict[str, str]) -> dict[str, Any]:
    started = time.time()
    response = client.post(
        "/api/analyze/v2",
        json={
            "query": scenario["query"],
            "scenario_override": scenario["scenario_override"],
        },
    )
    try:
        payload = response.json()
    except Exception as exc:
        return {
            "id": scenario["id"],
            "persona": scenario["persona"],
            "http_status": response.status_code,
            "elapsed_seconds": round(time.time() - started, 2),
            "parse_error": f"{type(exc).__name__}: {exc}",
            "is_reviewable": False,
        }
    return {
        "id": scenario["id"],
        "persona": scenario["persona"],
        "query": scenario["query"],
        "scenario_override": scenario["scenario_override"],
        "http_status": response.status_code,
        "elapsed_seconds": round(time.time() - started, 2),
        **_reviewability(payload),
    }


def main() -> int:
    output_path = Path(
        ".agent-guardrails/evidence/local-stability-probe.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "mode": "keyless_oss",
        "scenarios": [],
        "verdict": "blocked",
    }

    client = TestClient(app)
    for scenario in SCENARIOS:
        report["scenarios"].append(_run_scenario(client, scenario))

    reviewable_count = sum(1 for item in report["scenarios"] if item.get("is_reviewable"))
    report["summary"] = {
        "reviewable_count": reviewable_count,
        "scenario_count": len(report["scenarios"]),
    }
    report["verdict"] = (
        "pass" if reviewable_count == len(report["scenarios"]) else "needs_followup"
    )

    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
