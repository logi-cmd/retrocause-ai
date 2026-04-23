#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from retrocause.api.main import app
from retrocause.app.demo_data import PROVIDERS


DEFAULT_PROVIDER = os.environ.get("RETROCAUSE_LIVE_PROVIDER", "ofoxai").strip() or "ofoxai"
DEFAULT_KEY_ENV = {
    "ofoxai": "OFOXAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}.get(DEFAULT_PROVIDER, f"{DEFAULT_PROVIDER.upper()}_API_KEY")
DEFAULT_MODEL_CANDIDATES = list(PROVIDERS[DEFAULT_PROVIDER]["models"].keys())

SCENARIOS = [
    {
        "id": "market_zh_a_share",
        "persona": "Chinese retail investor checking a same-day A-share move",
        "query": "\u82af\u539f\u80a1\u4efd\u4eca\u5929\u76d8\u4e2d\u4e3a\u4ec0\u4e48\u4e0b\u8dcc\uff1f",
        "scenario_override": "market",
    },
    {
        "id": "policy_geopolitics_semiconductors",
        "persona": "Policy analyst checking current semiconductor export-control causes",
        "query": "Why did the US announce new semiconductor export controls today?",
        "scenario_override": "policy_geopolitics",
    },
    {
        "id": "postmortem_public_incident",
        "persona": "Engineering lead reviewing a public software incident postmortem",
        "query": "Why did the CrowdStrike Falcon update cause Windows outages?",
        "scenario_override": "postmortem",
    },
]


def _models_from_env() -> list[str]:
    raw = os.environ.get("RETROCAUSE_LIVE_MODELS", "")
    configured = [item.strip() for item in raw.split(",") if item.strip()]
    if configured:
        return configured
    return DEFAULT_MODEL_CANDIDATES


def _key_status(name: str) -> str:
    return "present" if os.environ.get(name) else "missing"


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
        "recovered_rows": statuses.get("recovered", 0),
        "degraded_rows": sum(
            statuses.get(status, 0)
            for status in ["rate_limited", "source_limited", "forbidden", "timeout", "source_error"]
        ),
    }


def _reviewability(payload: dict[str, Any]) -> dict[str, Any]:
    product = payload.get("product_harness") or {}
    production = payload.get("production_harness") or {}
    trace = payload.get("retrieval_trace") or []
    evidences = payload.get("evidences") or []
    chains = payload.get("chains") or []
    trace_summary = _trace_summary(trace)
    is_reviewable = (
        payload.get("is_demo") is False
        and payload.get("analysis_mode") in {"live", "partial_live"}
        and len(chains) > 0
        and len(evidences) > 0
        and trace_summary["hits"] > 0
        and product.get("status") in {"ready_for_review", "needs_more_evidence"}
    )
    return {
        "is_reviewable": is_reviewable,
        "analysis_mode": payload.get("analysis_mode"),
        "is_demo": payload.get("is_demo"),
        "chain_count": len(chains),
        "evidence_count": len(evidences),
        "challenge_count": len(payload.get("challenge_checks") or []),
        "product_status": product.get("status"),
        "production_status": production.get("status"),
        "trace": trace_summary,
        "error": payload.get("error"),
        "partial_live_reasons": payload.get("partial_live_reasons") or [],
        "recommended_actions": (payload.get("evaluation") or {}).get("recommended_actions") or [],
    }


def _preflight_model(client: TestClient, api_key: str, provider: str, model: str) -> dict[str, Any]:
    started = time.time()
    response = client.post(
        "/api/providers/preflight",
        json={
            "model": provider,
            "explicit_model": model,
            "api_key": api_key,
        },
    )
    payload = response.json()
    return {
        "model": model,
        "http_status": response.status_code,
        "elapsed_seconds": round(time.time() - started, 2),
        "status": payload.get("status"),
        "can_run_analysis": payload.get("can_run_analysis"),
        "failure_code": payload.get("failure_code"),
        "diagnosis": payload.get("diagnosis"),
        "checks": [
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "detail": item.get("detail"),
            }
            for item in payload.get("checks", [])
        ],
    }


def _run_scenario(
    client: TestClient,
    api_key: str,
    provider: str,
    model: str,
    scenario: dict[str, str],
) -> dict[str, Any]:
    started = time.time()
    response = client.post(
        "/api/analyze/v2",
        json={
            "query": scenario["query"],
            "model": provider,
            "explicit_model": model,
            "api_key": api_key,
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
    provider = DEFAULT_PROVIDER
    key_env = DEFAULT_KEY_ENV
    api_key = os.environ.get(key_env, "").strip()
    output_path = Path(
        os.environ.get(
            "RETROCAUSE_LIVE_PROBE_OUTPUT",
            ".agent-guardrails/evidence/live-stability-probe.json",
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "provider": provider,
        "keys": {
            "OFOXAI_API_KEY": _key_status("OFOXAI_API_KEY"),
            "OPENROUTER_API_KEY": _key_status("OPENROUTER_API_KEY"),
            "TAVILY_API_KEY": _key_status("TAVILY_API_KEY"),
            "BRAVE_SEARCH_API_KEY": _key_status("BRAVE_SEARCH_API_KEY"),
        },
        "model_candidates": _models_from_env(),
        "preflight_results": [],
        "selected_model": None,
        "scenarios": [],
        "verdict": "blocked",
    }

    if not api_key:
        report["blocker"] = f"{key_env} is missing."
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    client = TestClient(app)
    for model in report["model_candidates"]:
        preflight = _preflight_model(client, api_key, provider, str(model))
        report["preflight_results"].append(preflight)
        if preflight["http_status"] == 200 and preflight["can_run_analysis"] is True:
            report["selected_model"] = model
            break

    if not report["selected_model"]:
        report["blocker"] = (
            f"No {provider} candidate passed provider preflight and analysis smoke."
        )
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    for scenario in SCENARIOS:
        report["scenarios"].append(
            _run_scenario(client, api_key, provider, str(report["selected_model"]), scenario)
        )

    reviewable_count = sum(1 for item in report["scenarios"] if item.get("is_reviewable"))
    recovered_count = sum(
        int((item.get("trace") or {}).get("recovered_rows") or 0)
        for item in report["scenarios"]
    )
    report["summary"] = {
        "reviewable_count": reviewable_count,
        "scenario_count": len(report["scenarios"]),
        "recovered_rows": recovered_count,
    }
    report["verdict"] = (
        "pass" if reviewable_count == len(report["scenarios"]) else "needs_followup"
    )

    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
