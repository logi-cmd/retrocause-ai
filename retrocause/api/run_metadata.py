from __future__ import annotations

from collections.abc import Mapping, Sequence


def build_run_step_payloads(
    *,
    error: str | None,
    chain_count: int,
    has_markdown_brief: bool,
    has_analysis_brief: bool,
    saved: bool,
) -> list[dict]:
    analysis_status = "failed" if error and chain_count == 0 else "completed"
    brief_status = "completed" if has_markdown_brief or has_analysis_brief else "skipped"
    return [
        {
            "id": "queued",
            "label": "Run accepted",
            "status": "completed",
            "detail": "Local run record was created.",
        },
        {
            "id": "analysis",
            "label": "Analysis pipeline",
            "status": analysis_status,
            "detail": error or f"{chain_count} causal chain(s) returned.",
        },
        {
            "id": "brief",
            "label": "Reviewable brief",
            "status": brief_status,
            "detail": (
                "Markdown/readable brief available."
                if brief_status == "completed"
                else "No brief output."
            ),
        },
        {
            "id": "saved",
            "label": "Saved run",
            "status": "completed" if saved else "failed",
            "detail": "Run payload persisted locally." if saved else "Run payload was not saved.",
        },
    ]


def quota_owner_for_source_payload(item: object) -> str:
    cache_hit = bool(_field(item, "cache_hit", False))
    status = str(_field(item, "status", ""))
    source = str(_field(item, "source", ""))
    source_kind = str(_field(item, "source_kind", ""))
    if cache_hit or status == "cached":
        return "cache_reuse"
    if source.startswith("uploaded") or source_kind == "uploaded":
        return "user_owned"
    return "source_specific"


def build_usage_ledger_payloads(
    *,
    provider_label: str,
    model_name: str,
    uses_hosted_provider: bool,
    analysis_mode: str,
    chain_count: int,
    retrieval_trace: Sequence[object],
    evidences: Sequence[object],
) -> list[dict]:
    ledger = [
        {
            "category": "model_provider",
            "name": model_name,
            "quota_owner": "hosted_provider" if uses_hosted_provider else "local_demo",
            "status": analysis_mode,
            "count": chain_count,
            "detail": provider_label,
        }
    ]
    ledger.extend(
        {
            "category": "retrieval_source",
            "name": str(_field(item, "source_label", "")) or str(_field(item, "source", "")),
            "quota_owner": quota_owner_for_source_payload(item),
            "status": str(_field(item, "status", "")),
            "count": int(_field(item, "result_count", 0) or 0),
            "detail": str(_field(item, "cache_policy", "")),
        }
        for item in retrieval_trace
    )

    uploaded_count = sum(1 for item in evidences if _field(item, "source_tier", "") == "uploaded")
    if uploaded_count:
        ledger.append(
            {
                "category": "uploaded_evidence",
                "name": "Uploaded evidence library",
                "quota_owner": "user_owned",
                "status": "attached",
                "count": uploaded_count,
                "detail": "User-provided evidence is stored locally.",
            }
        )
    return ledger


def _field(item: object, key: str, default: object = None) -> object:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)
