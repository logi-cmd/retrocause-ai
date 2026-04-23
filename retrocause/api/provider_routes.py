from __future__ import annotations

import os

from fastapi import APIRouter

from retrocause.api.provider_preflight import (
    classify_preflight_failure_code,
    provider_recovery_action,
    preflight_user_action,
    resolve_provider_model,
)
from retrocause.api.runtime import TimeoutError, run_with_timeout
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


def _source_failure_status(exc: Exception) -> tuple[str, str]:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code == 429:
        return "rate_limited", "Search provider rate limit was reached."
    if status_code in {401, 403}:
        return "forbidden", "Search provider rejected the key or permissions."
    return "source_error", f"{type(exc).__name__}: {exc}"


def _configured_source_key(request_key: str | None, env_name: str) -> str:
    return (request_key or os.environ.get(env_name, "")).strip()


def _check_source_adapter(source: str, source_label: str, adapter: object, query: str):
    try:
        results = run_with_timeout(lambda: adapter.search(query, max_results=1), 25)
    except TimeoutError:
        return _source_preflight_item(
            source,
            source_label,
            "timeout",
            False,
            diagnosis="Search provider preflight timed out.",
            user_action="Retry later or use the built-in OSS sources for this run.",
        )
    except Exception as exc:
        status, diagnosis = _source_failure_status(exc)
        action = (
            "Wait for quota reset or use another search provider."
            if status == "rate_limited"
            else "Check the search API key, permissions, and provider account status."
        )
        return _source_preflight_item(
            source,
            source_label,
            status,
            False,
            diagnosis=diagnosis,
            user_action=action,
        )

    result_count = len(results or [])
    return _source_preflight_item(
        source,
        source_label,
        "ok",
        True,
        result_count=result_count,
        diagnosis=f"Search provider returned {result_count} result(s).",
        user_action="Run the full analysis.",
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
    checks: list[SourcePreflightItemV2] = []
    query = request.query.strip() or "RetroCause source preflight latest market news"
    tavily_key = _configured_source_key(request.tavily_api_key, "TAVILY_API_KEY")
    brave_key = _configured_source_key(request.brave_search_api_key, "BRAVE_SEARCH_API_KEY")

    if tavily_key:
        from retrocause.sources.tavily import TavilySourceAdapter

        checks.append(
            _check_source_adapter(
                "tavily",
                "Tavily Search",
                TavilySourceAdapter(tavily_key),
                query,
            )
        )
    else:
        checks.append(
            _source_preflight_item(
                "tavily",
                "Tavily Search",
                "missing_api_key",
                False,
                diagnosis="No Tavily key was provided in the request or process environment.",
                user_action="Paste a Tavily key, set TAVILY_API_KEY, or leave Tavily disabled.",
            )
        )

    if brave_key:
        from retrocause.sources.brave import BraveSearchSourceAdapter

        checks.append(
            _check_source_adapter(
                "brave",
                "Brave Search API",
                BraveSearchSourceAdapter(brave_key),
                query,
            )
        )
    else:
        checks.append(
            _source_preflight_item(
                "brave",
                "Brave Search API",
                "missing_api_key",
                False,
                diagnosis="No Brave Search key was provided in the request or process environment.",
                user_action=(
                    "Paste a Brave Search key, set BRAVE_SEARCH_API_KEY, or leave Brave disabled."
                ),
            )
        )

    can_search = any(item.can_search for item in checks)
    status = "ok" if can_search else "error"
    return SourcePreflightResponse(status=status, can_search=can_search, checks=checks)


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
        try:
            smoke_ok, smoke_error = run_with_timeout(llm.preflight_analysis_smoke, 50)
        except TimeoutError:
            smoke_ok = False
            smoke_error = "Analysis-stage smoke timed out."
        except Exception as exc:
            smoke_ok = False
            smoke_error = f"{type(exc).__name__}: {exc}"

        if smoke_ok:
            checks.append(
                _harness_check(
                    "analysis_smoke",
                    "Model can plan analysis queries",
                    "pass",
                    "Provider passed a query-planning smoke for a real live-analysis prompt.",
                )
            )
            return ProviderPreflightResponse(
                provider=request.model,
                model_name=model_name,
                status="ok",
                can_run_analysis=True,
                failure_code=None,
                diagnosis="Provider, key, model, and analysis planning smoke all passed.",
                user_action="Run the full analysis.",
                checks=checks,
            )

        failure_code = classify_preflight_failure_code(smoke_error)
        checks.append(
            _harness_check(
                "analysis_smoke",
                "Model can plan analysis queries",
                "fail",
                smoke_error or "Analysis-stage smoke failed.",
            )
        )
        return ProviderPreflightResponse(
            provider=request.model,
            model_name=model_name,
            status="error",
            can_run_analysis=False,
            failure_code=failure_code,
            diagnosis=smoke_error or "Analysis-stage smoke failed.",
            user_action=provider_recovery_action(
                PROVIDERS, request.model, model_name, failure_code
            ),
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
        user_action=provider_recovery_action(PROVIDERS, request.model, model_name, failure_code),
        checks=checks,
    )
