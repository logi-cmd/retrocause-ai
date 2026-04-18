from __future__ import annotations

from retrocause.api.briefs import build_markdown_research_brief
from retrocause.api.harness import build_product_harness_payload, build_production_harness_payload
from retrocause.api.production_brief import build_production_brief_payload
from retrocause.api.scenarios import detect_production_scenario_payload
from retrocause.api.schemas import (
    AnalyzeResponseV2,
    ProductHarnessReportV2,
    ProductionBriefV2,
    ProductionHarnessReportV2,
    ScenarioV2,
    UpstreamMapV2,
)
from retrocause.parser import parse_input


def build_empty_live_failure_response(
    query: str,
    error_msg: str,
    scenario_override: str | None = None,
) -> AnalyzeResponseV2:
    parsed_query = parse_input(query)
    response = AnalyzeResponseV2(
        query=query,
        is_demo=False,
        demo_topic=None,
        analysis_mode="partial_live",
        freshness_status="unknown",
        time_range=parsed_query.time_range,
        partial_live_reasons=[error_msg],
        recommended_chain_id=None,
        chains=[],
        evidences=[],
        upstream_map=UpstreamMapV2(entries=[]),
        evaluation=None,
        retrieval_trace=[],
        uncertainty_report=None,
        error=error_msg,
    )
    scenario_payload = detect_production_scenario_payload(
        query,
        domain="general",
        override=scenario_override,
    )
    scenario = ScenarioV2(
        key=scenario_payload.key,
        label=scenario_payload.label,
        confidence=scenario_payload.confidence,
        detection_method=scenario_payload.detection_method,
        user_value=scenario_payload.user_value,
    )
    response.scenario = scenario
    response.production_brief = ProductionBriefV2(
        **build_production_brief_payload(response, scenario)
    )
    response.production_harness = ProductionHarnessReportV2(
        **build_production_harness_payload(response)
    )
    response.markdown_brief = build_markdown_research_brief(response)
    response.product_harness = ProductHarnessReportV2(
        **build_product_harness_payload(response)
    )
    return response
