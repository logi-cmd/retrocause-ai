from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_run_id() -> str:
    return f"run_{uuid4().hex[:12]}"


def run_store_path() -> Path:
    configured_path = os.environ.get("RETROCAUSE_RUN_STORE_PATH")
    if configured_path:
        return Path(configured_path)
    return Path.cwd() / ".retrocause" / "saved_runs.json"


def load_saved_run_records() -> list[dict]:
    path = run_store_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def save_saved_run_records(records: list[dict]) -> None:
    path = run_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def persist_saved_run_payload(
    *,
    run_id: str,
    query: str,
    run_status: str,
    analysis_mode: str,
    scenario_key: str,
    response_payload: dict,
) -> bool:
    if not run_id:
        return False

    records = load_saved_run_records()
    records = [record for record in records if record.get("run_id") != run_id]
    records.insert(
        0,
        {
            "run_id": run_id,
            "query": query,
            "run_status": run_status,
            "analysis_mode": analysis_mode,
            "created_at": utc_now_iso(),
            "scenario_key": scenario_key,
            "response": response_payload,
        },
    )
    save_saved_run_records(records[:50])
    return True
