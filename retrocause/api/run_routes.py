from __future__ import annotations

from fastapi import APIRouter, HTTPException

from retrocause.api.run_store import load_saved_run_records
from retrocause.api.schemas import SavedRunListResponse, SavedRunSummaryV2


router = APIRouter()


@router.get("/api/runs", response_model=SavedRunListResponse)
async def list_saved_runs():
    summaries = [
        SavedRunSummaryV2(
            run_id=str(record.get("run_id", "")),
            query=str(record.get("query", "")),
            run_status=str(record.get("run_status", "unknown")),
            analysis_mode=str(record.get("analysis_mode", "unknown")),
            created_at=str(record.get("created_at", "")),
            scenario_key=str(record.get("scenario_key", "general")),
        )
        for record in load_saved_run_records()
        if record.get("run_id")
    ]
    return SavedRunListResponse(runs=summaries)


@router.get("/api/runs/{run_id}")
async def get_saved_run(run_id: str):
    for record in load_saved_run_records():
        if record.get("run_id") == run_id:
            return record
    raise HTTPException(status_code=404, detail="Saved run not found")
