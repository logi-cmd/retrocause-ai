from __future__ import annotations

from fastapi import APIRouter, HTTPException

from retrocause.api.schemas import UploadedEvidenceRequest, UploadedEvidenceResponse
from retrocause.evidence_store import EvidenceStore

router = APIRouter()


@router.post("/api/evidence/upload", response_model=UploadedEvidenceResponse)
async def upload_evidence(request: UploadedEvidenceRequest):
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded evidence content is empty")
    evidence = EvidenceStore().add_uploaded_evidence(
        query=request.query,
        domain=request.domain,
        title=request.title,
        content=content,
        source_name=request.source_name,
        time_scope=request.time_scope,
    )
    return UploadedEvidenceResponse(
        evidence_id=evidence.id,
        stored=True,
        source_tier=evidence.source_tier,
        extraction_method=evidence.extraction_method,
    )
