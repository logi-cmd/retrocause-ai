from __future__ import annotations

from fastapi import APIRouter

from retrocause.api.provider_preflight import (
    classify_preflight_failure_code,
    preflight_user_action,
    resolve_provider_model,
)
from retrocause.api.runtime import TimeoutError, run_with_timeout
from retrocause.api.schemas import HarnessCheckV2, ProviderPreflightRequest, ProviderPreflightResponse
from retrocause.app.demo_data import PROVIDERS


router = APIRouter()


def _harness_check(check_id: str, label: str, status: str, detail: str = "") -> HarnessCheckV2:
    return HarnessCheckV2(id=check_id, label=label, status=status, detail=detail)


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


@router.post("/api/providers/preflight", response_model=ProviderPreflightResponse)
async def preflight_provider(request: ProviderPreflightRequest):
    provider_cfg, model_name = resolve_provider_model(PROVIDERS, request.model, request.explicit_model)
    checks: list[HarnessCheckV2] = []

    if provider_cfg is None:
        checks.append(
            _harness_check(
                "provider_config",
                "Provider configured",
                "fail",
                f"Provider {request.model!r} is not configured.",
            )
        )
        return ProviderPreflightResponse(
            provider=request.model,
            model_name=model_name,
            status="error",
            can_run_analysis=False,
            failure_code="unknown_provider",
            diagnosis="Provider is not configured in this RetroCause instance.",
            user_action=preflight_user_action("unknown_provider"),
            checks=checks,
        )

    checks.append(
        _harness_check(
            "provider_config",
            "Provider configured",
            "pass",
            f"{request.model} resolves to {provider_cfg.get('base_url') or 'default OpenAI endpoint'}.",
        )
    )

    if not request.api_key:
        checks.append(
            _harness_check(
                "api_key_present",
                "API key present",
                "fail",
                "No API key was provided.",
            )
        )
        return ProviderPreflightResponse(
            provider=request.model,
            model_name=model_name,
            status="error",
            can_run_analysis=False,
            failure_code="missing_api_key",
            diagnosis="Live analysis needs a provider API key.",
            user_action=preflight_user_action("missing_api_key"),
            checks=checks,
        )

    checks.append(
        _harness_check("api_key_present", "API key present", "pass", "API key was provided.")
    )

    configured_models = provider_cfg.get("models", {})
    catalog_status = "pass" if model_name in configured_models else "warn"
    catalog_detail = (
        "Model is listed in the configured provider catalog."
        if catalog_status == "pass"
        else "Model is not in the local catalog; preflight will still test provider access."
    )
    checks.append(
        _harness_check("model_catalog", "Model listed locally", catalog_status, catalog_detail)
    )

    try:
        from retrocause.config import RetroCauseConfig
        from retrocause.llm import LLMClient

        cfg = RetroCauseConfig.from_env()
        llm = LLMClient(
            api_key=request.api_key,
            model=model_name,
            base_url=provider_cfg.get("base_url"),
            timeout=min(cfg.request_timeout_seconds, 45),
        )
        ok, error_msg = run_with_timeout(llm.preflight_model_access, 50)
    except TimeoutError:
        ok = False
        error_msg = "Model preflight timed out."
    except Exception as exc:
        ok = False
        error_msg = f"{type(exc).__name__}: {exc}"

    if ok:
        checks.append(
            _harness_check(
                "model_access",
                "Model returns JSON",
                "pass",
                "Provider returned the expected tiny JSON payload.",
            )
        )
        return ProviderPreflightResponse(
            provider=request.model,
            model_name=model_name,
            status="ok",
            can_run_analysis=True,
            failure_code=None,
            diagnosis="Provider, key, and model passed the lightweight JSON preflight.",
            user_action="Run the full analysis.",
            checks=checks,
        )

    failure_code = classify_preflight_failure_code(error_msg)
    checks.append(
        _harness_check(
            "model_access",
            "Model returns JSON",
            "fail",
            error_msg or "Model preflight failed.",
        )
    )
    return ProviderPreflightResponse(
        provider=request.model,
        model_name=model_name,
        status="error",
        can_run_analysis=False,
        failure_code=failure_code,
        diagnosis=error_msg or "Model preflight failed.",
        user_action=preflight_user_action(failure_code),
        checks=checks,
    )
