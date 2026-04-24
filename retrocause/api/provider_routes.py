from __future__ import annotations

from fastapi import APIRouter

from retrocause.api.schemas import (
    HarnessCheckV2,
    ProviderPreflightRequest,
    ProviderPreflightResponse,
    SourcePreflightItemV2,
    SourcePreflightRequest,
    SourcePreflightResponse,
)
from retrocause.app.demo_data import PROVIDERS


router = APIRouter()


def _harness_check(check_id: str, label: str, status: str, detail: str = "") -> HarnessCheckV2:
    return HarnessCheckV2(id=check_id, label=label, status=status, detail=detail)


def _source_preflight_item(
    source: str,
    source_label: str,
    status: str,
    can_search: bool,
    result_count: int = 0,
    diagnosis: str = "",
    user_action: str = "",
) -> SourcePreflightItemV2:
    return SourcePreflightItemV2(
        source=source,
        source_label=source_label,
        status=status,
        can_search=can_search,
        result_count=result_count,
        diagnosis=diagnosis,
        user_action=user_action,
    )


@router.get("/api/providers")
async def list_providers():
    return {
        "providers": {
            key: {
                "label": cfg["label"],
                "models": {mid: mcfg["label"] for mid, mcfg in cfg["models"].items()},
            }
            for key, cfg in PROVIDERS.items()
        }
    }


@router.post("/api/sources/preflight", response_model=SourcePreflightResponse)
async def preflight_sources(request: SourcePreflightRequest):
    query = request.query.strip() or "RetroCause source preflight latest market news"
    checks = [
        _source_preflight_item(
            "built_in_sources",
            "Built-in OSS sources",
            "ok",
            True,
            diagnosis=f"Keyless OSS source path is available for: {query}",
            user_action="Run the local analysis and inspect source health in the result.",
        )
    ]
    return SourcePreflightResponse(status="ok", can_search=True, checks=checks)


@router.post("/api/providers/preflight", response_model=ProviderPreflightResponse)
async def preflight_provider(request: ProviderPreflightRequest):
    provider_cfg = PROVIDERS.get(request.model)
    model_name = request.explicit_model or (
        next(iter(provider_cfg["models"])) if provider_cfg else request.model
    )
    checks = [
        _harness_check(
            "oss_keyless_boundary",
            "OSS keyless boundary",
            "warn",
            "The OSS browser/API surface does not accept provider keys.",
        )
    ]
    return ProviderPreflightResponse(
        provider=request.model,
        model_name=model_name,
        status="disabled",
        can_run_analysis=False,
        failure_code="oss_keyless",
        diagnosis="Provider preflight is disabled in the keyless OSS surface.",
        user_action="Use demo/local analysis in OSS, or use the separate Rust Pro service for hosted runs.",
        checks=checks,
    )
