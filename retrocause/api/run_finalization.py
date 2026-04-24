from __future__ import annotations

from retrocause.api.provider_preflight import resolve_provider_model
from retrocause.api.run_metadata import (
    build_run_step_payloads,
    build_usage_ledger_payloads,
)
from retrocause.api.run_store import persist_saved_run_payload
from retrocause.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponseV2,
    RunStepV2,
    UsageLedgerItemV2,
)


def write_saved_run_response(response: AnalyzeResponseV2) -> bool:
    run_id = response.run_id or ""
    scenario_key = response.scenario.key if response.scenario else "general"
    return persist_saved_run_payload(
        run_id=run_id,
        query=response.query,
        run_status=response.run_status,
        analysis_mode=response.analysis_mode,
        scenario_key=scenario_key,
        response_payload=response.model_dump(mode="json"),
    )


def finalize_run_response(
    response: AnalyzeResponseV2,
    request: AnalyzeRequest,
    run_id: str,
    providers: dict,
) -> AnalyzeResponseV2:
    response.run_id = run_id
    response.run_status = "failed" if response.error and not response.chains else "completed"
    provider_cfg, model_name = resolve_provider_model(
        providers,
        request.model,
        request.explicit_model,
    )
    provider_label = provider_cfg.get("label", request.model) if provider_cfg else request.model
    response.usage_ledger = [
        UsageLedgerItemV2(**payload)
        for payload in build_usage_ledger_payloads(
            provider_label=provider_label,
            model_name=model_name,
            uses_hosted_provider=False,
            analysis_mode=response.analysis_mode,
            chain_count=len(response.chains),
            retrieval_trace=response.retrieval_trace,
            evidences=response.evidences,
        )
    ]
    saved = write_saved_run_response(response)
    response.run_steps = [
        RunStepV2(**payload)
        for payload in build_run_step_payloads(
            error=response.error,
            chain_count=len(response.chains),
            has_markdown_brief=bool(response.markdown_brief),
            has_analysis_brief=bool(response.analysis_brief),
            saved=saved,
        )
    ]
    if saved:
        # Persist once more so the saved payload includes the completed saved step.
        write_saved_run_response(response)
    return response
