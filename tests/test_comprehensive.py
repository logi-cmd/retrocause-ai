"""全面边界测试 — API schema、空输入、极端值、类型安全、demo topic 覆盖"""

from __future__ import annotations

import json
import os
import pytest
import tomllib
import urllib.request
from uuid import uuid4
from pathlib import Path

from retrocause.api.main import (
    AnalyzeRequest,
    AnalyzeResponseV2,
    EvidenceBindingV2,
    GraphNodeV2,
    GraphEdgeV2,
    HypothesisChainV2,
    PipelineEvaluationV2,
    analyze_query_v2,
    _detect_production_scenario,
    _result_to_v2,
    app,
)
from retrocause.api.harness import build_product_harness_payload
from retrocause.api.live_failure_response import build_empty_live_failure_response
from retrocause.api.provider_routes import preflight_provider, preflight_sources
from retrocause.api.provider_preflight import resolve_provider_model
from retrocause.api.schemas import ProviderPreflightRequest, SourcePreflightRequest
from retrocause.app.demo_data import (
    PROVIDERS,
    detect_demo_topic,
    topic_aware_demo_result,
)
from retrocause.evaluation import (
    EvaluationStep,
    PipelineEvaluation,
    _assess_probability_coherence,
    _assess_chain_diversity,
)
from retrocause.evidence_access import SourceAttempt
from retrocause.evidence_store import EvidenceStore
from retrocause.models import (
    AnalysisResult,
    CausalEdge,
    CausalVariable,
    Evidence,
    EvidenceType,
    HypothesisChain,
    HypothesisStatus,
)
from retrocause.pipeline import Pipeline, PipelineContext


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_STORE_ROOT = REPO_ROOT / ".tmp-tests"


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _isolated_test_store_path(filename: str) -> Path:
    TEST_STORE_ROOT.mkdir(exist_ok=True)
    return TEST_STORE_ROOT / f"{uuid4().hex}_{filename}"


def test_run_orchestration_metadata_and_saved_run_round_trip(monkeypatch):
    from fastapi.testclient import TestClient

    run_store_path = _isolated_test_store_path("saved_runs.json")
    monkeypatch.setenv("RETROCAUSE_RUN_STORE_PATH", str(run_store_path))

    client = TestClient(app)
    response = client.post("/api/analyze/v2", json={"query": "Why did SVB collapse?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"].startswith("run_")
    assert payload["run_status"] == "completed"
    assert {step["id"] for step in payload["run_steps"]} >= {
        "queued",
        "analysis",
        "brief",
        "saved",
    }
    assert any(
        item["category"] == "model_provider"
        and item["quota_owner"] in {"local_demo", "user_owned"}
        for item in payload["usage_ledger"]
    )

    saved_list = client.get("/api/runs")
    assert saved_list.status_code == 200
    runs = saved_list.json()["runs"]
    assert runs[0]["run_id"] == payload["run_id"]
    assert runs[0]["query"] == "Why did SVB collapse?"

    saved_detail = client.get(f"/api/runs/{payload['run_id']}")
    assert saved_detail.status_code == 200
    assert saved_detail.json()["response"]["query"] == "Why did SVB collapse?"


def test_uploaded_evidence_minimal_store_round_trip(monkeypatch):
    from fastapi.testclient import TestClient

    store_path = _isolated_test_store_path("evidence_store.json")
    monkeypatch.setenv("RETROCAUSE_EVIDENCE_STORE_PATH", str(store_path))

    client = TestClient(app)
    response = client.post(
        "/api/evidence/upload",
        json={
            "query": "Why did trial users fail to convert after launch?",
            "domain": "postmortem",
            "title": "Launch notes",
            "source_name": "internal launch review",
            "content": "Trial users hit onboarding errors after the launch and support tickets doubled.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["evidence_id"].startswith("uploaded_")
    assert payload["stored"] is True

    results = EvidenceStore(path=store_path).search(
        "trial users onboarding errors launch conversion",
        "postmortem",
    )
    assert len(results) == 1
    assert results[0].extraction_method == "uploaded_evidence"
    assert results[0].source_tier == "uploaded"
    assert results[0].stance_basis == "user_upload"


def test_frontend_and_e2e_expose_pro_workflow_slices():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    uploaded_evidence_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "uploaded-evidence-panel.tsx"
    ).read_text(encoding="utf-8")
    saved_runs_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "saved-runs-panel.tsx"
    ).read_text(encoding="utf-8")
    e2e_source = (REPO_ROOT / "scripts" / "e2e_test.py").read_text(encoding="utf-8")

    assert 'data-testid="run-orchestration-status"' in page_source
    assert "@/lib/uploaded-evidence-panel" in page_source
    assert 'data-testid="upload-evidence-panel"' in uploaded_evidence_source
    assert "@/lib/saved-runs-panel" in page_source
    assert 'data-testid="saved-runs-panel"' in saved_runs_source
    assert "/api/evidence/upload" in page_source
    assert "/api/runs" in page_source
    assert "Degraded Source Browser Dogfood" in e2e_source
    assert "source-trace-status" in e2e_source


def test_frontend_usage_ledger_rows_use_collision_safe_keys():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert "usageLedger.slice(0, 3).map((item, index) => (" in page_source
    assert 'key={`${item.category}-${item.name}-${item.quota_owner}-${item.status}-${index}`}' in page_source


def test_frontend_dev_server_allows_local_hydration_origins():
    frontend_package = json.loads(
        (REPO_ROOT / "frontend" / "package.json").read_text(encoding="utf-8")
    )
    next_config = (REPO_ROOT / "frontend" / "next.config.ts").read_text(encoding="utf-8")
    start_script = (REPO_ROOT / "start.py").read_text(encoding="utf-8")

    assert frontend_package["scripts"]["dev"] == "next dev --hostname 127.0.0.1"
    assert 'allowedDevOrigins: ["127.0.0.1", "localhost"]' in next_config
    assert "Frontend: http://127.0.0.1:3005" in start_script


def test_frontend_exposes_chinese_a_share_market_sample():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    en_source = (REPO_ROOT / "frontend" / "src" / "lib" / "i18n" / "en.ts").read_text(
        encoding="utf-8"
    )
    zh_source = (REPO_ROOT / "frontend" / "src" / "lib" / "i18n" / "zh.ts").read_text(
        encoding="utf-8"
    )
    e2e_source = (REPO_ROOT / "scripts" / "e2e_test.py").read_text(encoding="utf-8")

    assert 'data-testid="sample-a-share-query"' in page_source
    assert "setScenarioOverride(\"market\")" in page_source
    assert "芯原股份今天盘中为什么下跌" in page_source
    assert "query.sampleAshare" in en_source
    assert "query.sampleAshare" in zh_source
    assert "sample-a-share-query" in e2e_source


def test_frontend_page_has_no_known_mojibake_strings():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    forbidden_fragments = [
        "姝ｅ湪",
        "杩愯",
        "棰勬",
        "涓嬩竴",
        "鎺ㄨ",
        "鍘熷",
        "閾捐矾",
        "鈥?",
        "閳?",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in page_source

    assert '"\\u8986\\u76d6"' in page_source
    assert '"\\u6765\\u6e90"' in page_source
    assert '"\\u6765\\u6e90\\u95ee\\u9898"' in page_source


def test_frontend_brief_localization_strings_are_clean():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert "缃俊淇″彿" not in page_source
    assert "鍙戠幇" not in page_source
    assert "鏉″叧閿洜鏋滆竟" not in page_source
    assert "鏉￠珮璐ㄩ噺璇佹嵁" not in page_source
    assert '"\\u7f6e\\u4fe1\\u4fe1\\u53f7"' in page_source
    assert '"\\u53d1\\u73b0"' in page_source
    assert '"\\u6761\\u5173\\u952e\\u8fb9"' in page_source
    assert '"\\u6761\\u9ad8\\u8d28\\u91cf\\u8bc1\\u636e"' in page_source
    assert "localizeBriefText(uncertaintyReport.summary, locale)" in page_source
    assert "localizeUncertaintyType" in page_source


def test_api_live_failure_messages_have_no_known_mojibake_strings():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert "閳?" not in api_source
    assert "鈥?" not in api_source
    assert " - empty result" in api_source
    assert " 路 " not in page_source


def test_openrouter_catalog_keeps_curated_models_that_work_in_retrocause():
    model_ids = list(PROVIDERS["openrouter"]["models"].keys())

    assert model_ids[0] == "deepseek/deepseek-chat"
    assert "google/gemini-2.5-flash" in model_ids
    assert "anthropic/claude-haiku-4.5" in model_ids
    assert "deepseek/deepseek-chat" in model_ids
    assert "deepseek/deepseek-v3.2" not in model_ids
    assert "deepseek/deepseek-chat-v3-0324" not in model_ids
    assert "deepseek/deepseek-r1" not in model_ids
    assert "google/gemini-2.5-pro-preview" not in model_ids
    assert "qwen/qwen3-235b-a22b" not in model_ids


def test_ofoxai_is_default_provider_catalog():
    assert AnalyzeRequest(query="Why did Bitcoin move today?").model == "ofoxai"
    assert ProviderPreflightRequest().model == "ofoxai"
    assert list(PROVIDERS.keys())[0] == "ofoxai"
    assert PROVIDERS["ofoxai"]["base_url"] == "https://api.ofox.ai/v1"
    assert list(PROVIDERS["ofoxai"]["models"].keys())[0] == "openai/gpt-5.4-mini"


def test_readme_has_clean_bilingual_oss_onboarding():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    forbidden_fragments = [
        "涓枃",
        "鍥犳灉",
        "锛",
        "鈥",
        "鏄",
        "杩",
        "绠",
        "歚",
        "乽",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in readme

    assert "输入一个“为什么会这样？”的问题" in readme
    assert "OfoxAI 是默认的本地模型提供商路径" in readme
    assert "芯原股份今天盘中为什么下跌？" in readme
    assert "These are local inspectability features. They are not hosted Pro infrastructure." in readme


def test_root_project_metadata_has_no_known_mojibake_strings():
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pyproject = tomllib.loads(pyproject_text)

    forbidden_fragments = [
        "鍏",
        "璇",
        "锛",
        "鈥",
        "鏄",
        "閫",
        "绠",
        "浠",
    ]
    for document in [agents, pyproject_text]:
        for fragment in forbidden_fragments:
            assert fragment not in document

    assert "先阅读" in agents
    assert "Agent 规则" in agents
    assert pyproject["project"]["description"].startswith("Evidence-backed causal explanation")


def test_openrouter_catalog_uses_current_flash_and_haiku_model_ids():
    model_ids = set(PROVIDERS["openrouter"]["models"].keys())

    assert "google/gemini-2.5-flash" in model_ids
    assert "anthropic/claude-haiku-4.5" in model_ids
    assert "google/gemini-2.5-flash-preview" not in model_ids
    assert "anthropic/claude-haiku-4" not in model_ids
    assert "google/gemini-2.5-pro-preview" not in model_ids
    assert "qwen/qwen3-235b-a22b" not in model_ids


def test_provider_catalog_labels_have_no_known_mojibake_strings():
    forbidden_fragments = ["锛", "闃块噷", "鏅鸿氨", "鏂癸級", "涓婁笅鏂"]

    for provider_cfg in PROVIDERS.values():
        assert not any(fragment in provider_cfg["label"] for fragment in forbidden_fragments)
        for model_cfg in provider_cfg["models"].values():
            assert not any(fragment in model_cfg["label"] for fragment in forbidden_fragments)


def test_openrouter_catalog_live_public_model_smoke():
    if os.environ.get("RETROCAUSE_LIVE_OPENROUTER_CATALOG") != "1":
        pytest.skip("Set RETROCAUSE_LIVE_OPENROUTER_CATALOG=1 to hit OpenRouter's public catalog.")

    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as response:
        payload = json.load(response)

    public_model_ids = {item["id"] for item in payload.get("data", []) if item.get("id")}
    missing = sorted(set(PROVIDERS["openrouter"]["models"]) - public_model_ids)

    assert missing == []


def test_legacy_openrouter_deepseek_snapshot_resolves_to_stable_alias():
    _, model_name = resolve_provider_model(
        PROVIDERS,
        "openrouter",
        "deepseek/deepseek-chat-v3-0324",
    )

    assert model_name == "deepseek/deepseek-chat"


def test_analyze_v2_uses_stable_deepseek_alias_for_legacy_snapshot(monkeypatch):
    from fastapi.testclient import TestClient

    captured: dict[str, str | None] = {}

    def fake_run_real_analysis(
        query,
        api_key,
        model,
        base_url,
        tavily_api_key=None,
        brave_search_api_key=None,
    ):
        captured["query"] = query
        captured["api_key"] = api_key
        captured["model"] = model
        captured["base_url"] = base_url
        captured["tavily_api_key"] = tavily_api_key
        captured["brave_search_api_key"] = brave_search_api_key
        return _sample_result_with_one_supported_chain(query)

    monkeypatch.setattr("retrocause.app.demo_data.run_real_analysis", fake_run_real_analysis)

    response = TestClient(app).post(
        "/api/analyze/v2",
        json={
            "query": "芯原股份今天盘中为什么下跌？",
            "model": "openrouter",
            "explicit_model": "deepseek/deepseek-chat-v3-0324",
            "api_key": "sk-test",
            "scenario_override": "market",
        },
    )

    assert response.status_code == 200
    assert captured["model"] == "deepseek/deepseek-chat"
    payload = response.json()
    assert payload["analysis_mode"] == "live"
    assert payload["chains"]


def test_frontend_and_api_expose_per_run_hosted_search_keys():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    api_source = (REPO_ROOT / "retrocause" / "api" / "schemas.py").read_text(
        encoding="utf-8"
    )

    assert "tavilyApiKey" in page_source
    assert "braveSearchApiKey" in page_source
    assert "tavily_api_key" in page_source
    assert "brave_search_api_key" in page_source
    assert "tavily_api_key" in api_source
    assert "brave_search_api_key" in api_source
    assert "/api/sources/preflight" in page_source
    assert "Run search preflight" in page_source


@pytest.mark.anyio
async def test_analyze_v2_passes_user_search_keys_to_live_analysis(monkeypatch):
    captured: dict[str, str | None] = {}

    def fake_run_real_analysis(
        query,
        api_key,
        model,
        base_url,
        tavily_api_key=None,
        brave_search_api_key=None,
    ):
        captured["query"] = query
        captured["api_key"] = api_key
        captured["model"] = model
        captured["base_url"] = base_url
        captured["tavily_api_key"] = tavily_api_key
        captured["brave_search_api_key"] = brave_search_api_key
        return _sample_result_with_one_supported_chain(query)

    monkeypatch.setattr("retrocause.app.demo_data.run_real_analysis", fake_run_real_analysis)

    response = await analyze_query_v2(
        AnalyzeRequest(
            query="Why did Bitcoin move today?",
            model="openrouter",
            api_key="sk-test",
            explicit_model="openai/gpt-4o-mini",
            tavily_api_key="tvly-test",
            brave_search_api_key="brave-test",
            scenario_override="market",
        )
    )

    assert response.analysis_mode == "live"
    assert captured["tavily_api_key"] == "tvly-test"
    assert captured["brave_search_api_key"] == "brave-test"


@pytest.mark.anyio
async def test_source_preflight_reports_missing_search_keys(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    response = await preflight_sources(SourcePreflightRequest())

    assert response.status == "error"
    assert response.can_search is False
    assert {check.source: check.status for check in response.checks} == {
        "tavily": "missing_api_key",
        "brave": "missing_api_key",
    }


@pytest.mark.anyio
async def test_source_preflight_checks_tavily_without_leaking_key(monkeypatch):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    def fake_search(self, query, max_results=5):
        assert query == "RetroCause source preflight latest market news"
        assert max_results == 1
        return [object()]

    monkeypatch.setattr("retrocause.sources.tavily.TavilySourceAdapter.search", fake_search)

    response = await preflight_sources(SourcePreflightRequest(tavily_api_key="tvly-test"))

    tavily = next(check for check in response.checks if check.source == "tavily")
    brave = next(check for check in response.checks if check.source == "brave")

    assert response.status == "ok"
    assert response.can_search is True
    assert tavily.status == "ok"
    assert tavily.can_search is True
    assert tavily.result_count == 1
    assert "tvly-test" not in tavily.diagnosis
    assert brave.status == "missing_api_key"


@pytest.mark.anyio
async def test_source_preflight_uses_environment_search_key_without_leaking(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-env-test")
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    def fake_search(self, query, max_results=5):
        assert query == "RetroCause source preflight latest market news"
        assert max_results == 1
        return [object()]

    monkeypatch.setattr("retrocause.sources.tavily.TavilySourceAdapter.search", fake_search)

    response = await preflight_sources(SourcePreflightRequest())

    tavily = next(check for check in response.checks if check.source == "tavily")
    brave = next(check for check in response.checks if check.source == "brave")

    assert response.status == "ok"
    assert response.can_search is True
    assert tavily.status == "ok"
    assert tavily.can_search is True
    assert tavily.result_count == 1
    assert "tvly-env-test" not in tavily.diagnosis
    assert "tvly-env-test" not in tavily.user_action
    assert brave.status == "missing_api_key"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Demo topic 覆盖测试
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "query, expected_topic",
    [
        ("Why did SVB collapse?", "svb"),
        ("What caused the SVB bank failure?", "svb"),
        ("SVB倒闭的原因是什么？", "svb"),
        ("为什么某股票暴跌？", "stock"),
        ("What caused the stock market crash?", "stock"),
        ("Why did the 2008 financial crisis happen?", "crisis"),
        ("2008年金融危机的原因", "crisis"),
        ("Why is rent so high in New York?", "rent"),
        ("纽约房租为什么这么贵", "rent"),
        ("Why did dinosaurs go extinct?", None),  # default → None
        ("Some random unrelated question", None),
    ],
)
def test_detect_demo_topic_all_cases(query, expected_topic):
    topic = detect_demo_topic(query)
    assert topic == expected_topic, f"query={query!r}: expected {expected_topic}, got {topic}"


def test_topic_aware_demo_result_svb():
    result = topic_aware_demo_result("Why did SVB collapse?")
    assert result.domain == "finance"
    assert result.hypotheses[0].id == "demo_svb_primary"
    assert any(v.name == "svb_collapse" for v in result.variables)


def test_topic_aware_demo_result_stock():
    result = topic_aware_demo_result("为什么某股票暴跌？")
    assert result.domain == "finance"
    assert result.hypotheses[0].id == "demo_stock_primary"


def test_topic_aware_demo_result_crisis():
    result = topic_aware_demo_result("2008 financial crisis causes")
    assert result.domain == "finance"
    assert result.hypotheses[0].id == "demo_crisis_primary"


def test_topic_aware_demo_result_rent():
    result = topic_aware_demo_result("Why is rent so high?")
    assert result.domain == "economics"
    assert result.hypotheses[0].id == "demo_rent_primary"


def test_topic_aware_demo_result_default():
    result = topic_aware_demo_result("Why did dinosaurs go extinct?")
    assert result.domain == "paleontology"
    # default demo should still produce valid result
    assert len(result.hypotheses) >= 1
    assert len(result.variables) > 0
    assert len(result.edges) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. API Schema 验证 — V2 转换
# ═══════════════════════════════════════════════════════════════════════════════


def _make_minimal_result() -> AnalysisResult:
    """构造最小有效 AnalysisResult"""
    return AnalysisResult(
        query="test query",
        domain="general",
        variables=[
            CausalVariable(name="var_a", description="Cause A", posterior_support=0.8),
            CausalVariable(name="var_b", description="Effect B", posterior_support=0.6),
        ],
        edges=[
            CausalEdge(source="var_a", target="var_b", conditional_prob=0.7),
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Test Chain",
                description="A test chain",
                variables=[
                    CausalVariable(name="var_a", description="Cause A", posterior_support=0.8),
                    CausalVariable(name="var_b", description="Effect B", posterior_support=0.6),
                ],
                edges=[
                    CausalEdge(source="var_a", target="var_b", conditional_prob=0.7),
                ],
                path_probability=0.7,
                posterior_probability=0.6,
                evidence_coverage=0.5,
                counterfactual_score=0.4,
            ),
        ],
    )


def _sample_result_with_one_supported_chain(query: str) -> AnalysisResult:
    return AnalysisResult(
        query=query,
        domain="general",
        variables=[
            CausalVariable(name="primary_driver", description="Primary driver"),
            CausalVariable(name="observed_outcome", description="Observed outcome"),
        ],
        edges=[
            CausalEdge(
                source="primary_driver",
                target="observed_outcome",
                conditional_prob=0.72,
                supporting_evidence_ids=["ev-support"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Primary supported explanation",
                description="A supported driver explains the observed outcome.",
                variables=[
                    CausalVariable(name="primary_driver", description="Primary driver"),
                    CausalVariable(name="observed_outcome", description="Observed outcome"),
                ],
                edges=[
                    CausalEdge(
                        source="primary_driver",
                        target="observed_outcome",
                        conditional_prob=0.72,
                        supporting_evidence_ids=["ev-support"],
                    )
                ],
                posterior_probability=0.66,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Source evidence links the primary driver to the observed outcome.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            )
        ],
    )


def test_result_to_v2_minimal():
    result = _make_minimal_result()
    v2 = _result_to_v2(result, is_demo=True, demo_topic="test")

    assert v2.query == "test query"
    assert v2.is_demo is True
    assert v2.demo_topic == "test"
    assert v2.analysis_mode == "demo"
    assert v2.freshness_status == "unknown"
    assert len(v2.chains) == 1
    assert v2.chains[0].chain_id == "chain-1"
    assert v2.chains[0].probability == 0.6
    assert v2.recommended_chain_id == "chain-1"
    assert v2.evaluation is None  # no evaluation on minimal result


def test_result_to_v2_with_evaluation():
    result = _make_minimal_result()
    result.evaluation = PipelineEvaluation(
        evidence_sufficiency=0.7,
        probability_coherence=0.85,
        chain_diversity=0.6,
        overall_confidence=0.72,
        weaknesses=["weak evidence"],
        recommended_actions=["add more sources"],
    )
    v2 = _result_to_v2(result, is_demo=False)

    assert v2.is_demo is False
    assert v2.evaluation is not None
    assert v2.evaluation.evidence_sufficiency == 0.7
    assert v2.evaluation.probability_coherence == 0.85
    assert v2.evaluation.chain_diversity == 0.6
    assert v2.evaluation.overall_confidence == 0.72
    assert "weak evidence" in v2.evaluation.weaknesses
    assert "add more sources" in v2.evaluation.recommended_actions


def test_result_to_v2_empty_hypotheses():
    result = AnalysisResult(
        query="empty test",
        domain="general",
        variables=[],
        edges=[],
        hypotheses=[],
    )
    v2 = _result_to_v2(result, is_demo=True, demo_topic="default")

    assert v2.query == "empty test"
    assert len(v2.chains) == 0
    assert v2.recommended_chain_id is None
    assert len(v2.evidences) == 0


def test_result_to_v2_multiple_chains():
    result = AnalysisResult(
        query="multi chain",
        domain="general",
        variables=[
            CausalVariable(name="a", description="A"),
            CausalVariable(name="b", description="B"),
            CausalVariable(name="c", description="C"),
        ],
        edges=[
            CausalEdge(source="a", target="b", conditional_prob=0.8),
            CausalEdge(source="a", target="c", conditional_prob=0.5),
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-low",
                name="Low Prob Chain",
                description="Low",
                variables=[
                    CausalVariable(name="a", description="A"),
                    CausalVariable(name="b", description="B"),
                ],
                edges=[CausalEdge(source="a", target="b", conditional_prob=0.8)],
                path_probability=0.3,
                posterior_probability=0.3,
            ),
            HypothesisChain(
                id="chain-high",
                name="High Prob Chain",
                description="High",
                variables=[
                    CausalVariable(name="a", description="A"),
                    CausalVariable(name="c", description="C"),
                ],
                edges=[CausalEdge(source="a", target="c", conditional_prob=0.5)],
                path_probability=0.8,
                posterior_probability=0.7,
            ),
        ],
    )
    v2 = _result_to_v2(result, is_demo=False)
    assert v2.recommended_chain_id == "chain-high"


def test_detects_market_production_scenario():
    scenario = _detect_production_scenario(
        "Why did bitcoin fall today after ETF outflows and rate headlines?"
    )

    assert scenario.key == "market"
    assert 0 <= scenario.confidence <= 1
    assert "market" in scenario.user_value.lower()


def test_detects_policy_geopolitics_production_scenario():
    scenario = _detect_production_scenario(
        "Why did the ceasefire talks fail after the latest sanctions announcement?"
    )

    assert scenario.key == "policy_geopolitics"
    assert 0 <= scenario.confidence <= 1
    assert "policy" in scenario.user_value.lower() or "geopolitical" in scenario.user_value.lower()


def test_detects_postmortem_production_scenario():
    scenario = _detect_production_scenario(
        "Why did our checkout conversion drop after the release incident?"
    )

    assert scenario.key == "postmortem"
    assert 0 <= scenario.confidence <= 1
    assert "incident" in scenario.user_value.lower() or "postmortem" in scenario.user_value.lower()


def test_scenario_override_wins_over_auto_detection():
    scenario = _detect_production_scenario(
        "Why did bitcoin fall today?",
        override="postmortem",
    )

    assert scenario.key == "postmortem"
    assert scenario.detection_method == "override"


def test_market_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)

    assert response.scenario is not None
    assert response.scenario.key == "market"
    assert response.production_brief is not None
    titles = [section.title for section in response.production_brief.sections]
    assert "Market Drivers" in titles
    assert "What Would Change The View" in titles
    assert all(
        item.evidence_ids
        for section in response.production_brief.sections
        for item in section.items
        if section.kind not in {"limits", "verification"}
    )


def test_policy_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain("Why did the ceasefire talks fail?")
    response = _result_to_v2(result, is_demo=False)

    assert response.scenario is not None
    assert response.scenario.key == "policy_geopolitics"
    assert response.production_brief is not None
    assert "Negotiation Constraints" in [
        section.title for section in response.production_brief.sections
    ]


def test_postmortem_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain(
        "Why did our checkout conversion drop after the release incident?"
    )
    response = _result_to_v2(result, is_demo=False)

    assert response.scenario is not None
    assert response.scenario.key == "postmortem"
    assert response.production_brief is not None
    assert "Operational Causes" in [section.title for section in response.production_brief.sections]


def test_market_production_brief_uses_evidence_excerpt_and_next_steps():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)

    assert response.production_brief is not None
    drivers = next(
        section for section in response.production_brief.sections if section.kind == "drivers"
    )
    assert drivers.items
    assert "Supporting clue:" in drivers.items[0].summary
    assert "Source evidence links the primary driver to the observed outcome." in drivers.items[0].summary
    assert response.production_brief.next_verification_steps


def test_recent_market_result_needs_fresh_evidence_before_ready():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    result.freshness_status = "stale"
    response = _result_to_v2(result, is_demo=False)

    assert response.production_harness is not None
    assert response.production_harness.status == "needs_more_evidence"
    assert any(
        check.name == "freshness_gate" and not check.passed
        for check in response.production_harness.checks
    )


def test_policy_result_with_weak_source_trace_surfaces_source_risk():
    result = _sample_result_with_one_supported_chain("Why did sanctions talks fail today?")
    result.retrieval_trace = [
        {
            "source": "web_search",
            "query": "sanctions talks failed",
            "result_count": 1,
            "cache_hit": False,
        }
    ]
    response = _result_to_v2(result, is_demo=False)

    assert response.production_harness is not None
    assert any(check.name == "source_risk" for check in response.production_harness.checks)


def test_retrieval_trace_exposes_degraded_source_metadata():
    result = _sample_result_with_one_supported_chain(
        "Why did US Iran talks in Islamabad end without agreement?"
    )
    result.retrieval_trace = [
        SourceAttempt(
            name="ap_news",
            query="US Iran Islamabad talks no agreement AP",
            result_count=0,
            cache_hit=False,
            error="rate_limited",
            status="rate_limited",
            retry_after_seconds=7,
            source_label="AP News",
            source_kind="wire_news",
            stability="high",
            cache_policy="short_lived_cache_allowed",
        ),
        {
            "source": "web",
            "query": "US Iran Islamabad talks no agreement",
            "result_count": 2,
            "cache_hit": True,
            "status": "cached",
            "source_label": "Trusted web search",
            "source_kind": "web_search",
            "stability": "medium",
            "cache_policy": "derived_cache_allowed",
        },
    ]

    response = _result_to_v2(result, is_demo=False)

    degraded = response.retrieval_trace[0]
    assert degraded.source == "ap_news"
    assert degraded.status == "rate_limited"
    assert degraded.retry_after_seconds == 7
    assert degraded.source_kind == "wire_news"
    assert degraded.stability == "high"
    assert degraded.cache_policy == "short_lived_cache_allowed"

    cached = response.retrieval_trace[1]
    assert cached.status == "cached"
    assert cached.cache_policy == "derived_cache_allowed"
    assert cached.cache_hit is True

    assert response.markdown_brief is not None
    assert "status: rate-limited" in response.markdown_brief
    assert "retry after 7s" in response.markdown_brief
    assert "cache policy: short_lived_cache_allowed" in response.markdown_brief


def test_degraded_source_drill_surfaces_all_limited_states_for_review():
    result = _sample_result_with_one_supported_chain(
        "Why did US Iran talks in Islamabad end without agreement?"
    )
    result.retrieval_trace = [
        {
            "source": "ap_news",
            "query": "US Iran Islamabad talks AP",
            "result_count": 0,
            "cache_hit": False,
            "status": "rate_limited",
            "retry_after_seconds": 30,
            "source_label": "AP News",
            "source_kind": "wire_news",
            "stability": "high",
            "cache_policy": "short_lived_cache_allowed",
        },
        {
            "source": "federal_register",
            "query": "US Iran official sanctions register",
            "result_count": 0,
            "cache_hit": False,
            "status": "forbidden",
            "source_label": "Federal Register",
            "source_kind": "official_record",
            "stability": "high",
            "cache_policy": "public_record_cache_allowed",
        },
        {
            "source": "gdelt",
            "query": "US Iran talks timeout",
            "result_count": 0,
            "cache_hit": False,
            "status": "timeout",
            "source_label": "GDELT",
            "source_kind": "news_index",
            "stability": "medium",
            "cache_policy": "short_lived_cache_allowed",
        },
        {
            "source": "brave",
            "query": "US Iran talks broad web",
            "result_count": 0,
            "cache_hit": False,
            "status": "source_error",
            "source_label": "Brave Search",
            "source_kind": "web_search",
            "stability": "medium",
            "cache_policy": "transient_results_only",
        },
        {
            "source": "tavily",
            "query": "US Iran talks fallback",
            "result_count": 0,
            "cache_hit": False,
            "status": "source_limited",
            "source_label": "Tavily Search",
            "source_kind": "hosted_search",
            "stability": "medium",
            "cache_policy": "derived_cache_allowed",
        },
        {
            "source": "web",
            "query": "US Iran talks cached evidence",
            "result_count": 3,
            "cache_hit": True,
            "status": "cached",
            "source_label": "Trusted web search",
            "source_kind": "web_search",
            "stability": "medium",
            "cache_policy": "derived_cache_allowed",
        },
    ]

    response = _result_to_v2(result, is_demo=False)

    assert response.analysis_brief is not None
    assert "6 source attempt(s), 5 degraded or limited" in response.analysis_brief.source_coverage
    assert response.markdown_brief is not None
    for status in [
        "status: rate-limited",
        "status: forbidden",
        "status: timeout",
        "status: source-error",
        "status: source-limited",
        "status: cached",
    ]:
        assert status in response.markdown_brief
    assert "retry after 30s" in response.markdown_brief
    assert "cache policy: transient_results_only" in response.markdown_brief


def test_postmortem_without_internal_evidence_is_not_actionable():
    result = _sample_result_with_one_supported_chain(
        "Why did our checkout conversion drop after the release incident?"
    )
    response = _result_to_v2(result, is_demo=False)

    assert response.production_harness is not None
    assert response.production_harness.status in {"needs_more_evidence", "not_actionable"}
    assert any(
        check.name == "internal_evidence" and not check.passed
        for check in response.production_harness.checks
    )


def test_result_to_v2_surfaces_refutation_status_and_stance():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="hardline_demands", description="Hardline demands"),
            CausalVariable(name="failed_talks", description="Failed talks"),
        ],
        edges=[
            CausalEdge(
                source="hardline_demands",
                target="failed_talks",
                conditional_prob=0.7,
                supporting_evidence_ids=["ev-support"],
                refuting_evidence_ids=["ev-refute"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-refute",
                name="Refuted chain",
                description="A chain with a challenge",
                variables=[
                    CausalVariable(name="hardline_demands", description="Hardline demands"),
                    CausalVariable(name="failed_talks", description="Failed talks"),
                ],
                edges=[
                    CausalEdge(
                        source="hardline_demands",
                        target="failed_talks",
                        conditional_prob=0.7,
                        supporting_evidence_ids=["ev-support"],
                        refuting_evidence_ids=["ev-refute"],
                    )
                ],
                posterior_probability=0.6,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Officials cited hardline demands as a cause.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
            ),
            Evidence(
                id="ev-refute",
                content="Officials denied that hardline demands caused the failure.",
                source_type=EvidenceType.NEWS,
                stance="refuting",
                stance_basis="llm_extraction",
            ),
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.chains[0].refutation_status == "has_refutation"
    assert v2.chains[0].edges[0].refutation_status == "has_refutation"
    refuting = next(item for item in v2.evidences if item.id == "ev-refute")
    assert refuting.is_supporting is False
    assert refuting.stance == "refuting"
    assert refuting.stance_basis == "llm_extraction"


def test_result_to_v2_marks_missing_refutation_coverage_honestly():
    result = _make_minimal_result()
    result.evidences = [
        Evidence(
            id="ev-support",
            content="A retrieved claim supports the explanation.",
            source_type=EvidenceType.NEWS,
            stance="supporting",
            stance_basis="llm_extraction",
        )
    ]
    result.hypotheses[0].edges[0].supporting_evidence_ids = ["ev-support"]

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.chains[0].refutation_status == "no_refutation_in_retrieved_evidence"


def test_result_to_v2_surfaces_challenge_checks_and_analysis_brief():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
            CausalVariable(name="talks_failed", description="Talks failed"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_pressure",
                target="talks_failed",
                conditional_prob=0.72,
                supporting_evidence_ids=["ev-support"],
                refuting_evidence_ids=["ev-refute"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions explanation",
                description="Sanctions pressure contributed to failure",
                variables=[
                    CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
                    CausalVariable(name="talks_failed", description="Talks failed"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_pressure",
                        target="talks_failed",
                        conditional_prob=0.72,
                        supporting_evidence_ids=["ev-support"],
                        refuting_evidence_ids=["ev-refute"],
                    )
                ],
                posterior_probability=0.64,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Diplomats linked sanctions pressure to the failed talks.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
            ),
            Evidence(
                id="ev-refute",
                content="Officials denied sanctions pressure was the reason talks failed.",
                source_type=EvidenceType.NEWS,
                stance="refuting",
                stance_basis="challenge_retrieval",
            ),
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_pressure->talks_failed",
                "source": "sanctions_pressure",
                "target": "talks_failed",
                "query": "why did talks fail evidence against sanctions pressure causing talks failed",
                "result_count": 1,
                "refuting_count": 1,
                "status": "has_refutation",
            }
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.challenge_checks[0].status == "has_refutation"
    assert v2.analysis_brief is not None
    assert "Sanctions explanation" in v2.analysis_brief.answer
    assert v2.analysis_brief.top_reasons
    assert v2.analysis_brief.challenge_summary.startswith("Found")
    assert v2.analysis_brief.missing_evidence


def test_result_to_v2_builds_copyable_markdown_research_brief():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
            CausalVariable(name="talks_failed", description="Talks failed"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_pressure",
                target="talks_failed",
                conditional_prob=0.72,
                supporting_evidence_ids=["ev-support"],
                refuting_evidence_ids=["ev-refute"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions explanation",
                description="Sanctions pressure contributed to failure",
                variables=[
                    CausalVariable(name="sanctions_pressure", description="Sanctions pressure"),
                    CausalVariable(name="talks_failed", description="Talks failed"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_pressure",
                        target="talks_failed",
                        conditional_prob=0.72,
                        supporting_evidence_ids=["ev-support"],
                        refuting_evidence_ids=["ev-refute"],
                    )
                ],
                posterior_probability=0.64,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Diplomats linked sanctions pressure to the failed talks.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            ),
            Evidence(
                id="ev-refute",
                content="Officials denied sanctions pressure was the reason talks failed.",
                source_type=EvidenceType.NEWS,
                stance="refuting",
                stance_basis="challenge_retrieval",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            ),
        ],
        retrieval_trace=[
            {
                "source": "ap_news",
                "query": "talks failed sanctions pressure",
                "result_count": 2,
                "cache_hit": False,
            }
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_pressure->talks_failed",
                "source": "sanctions_pressure",
                "target": "talks_failed",
                "query": "evidence against sanctions pressure causing talks failed",
                "result_count": 1,
                "refuting_count": 1,
                "status": "has_refutation",
            }
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.markdown_brief is not None
    assert v2.markdown_brief.startswith("# Policy / Geopolitics Brief")
    assert "## Question" in v2.markdown_brief
    assert "why did talks fail" in v2.markdown_brief
    assert "## Likely Explanation" in v2.markdown_brief
    assert "Sanctions explanation" in v2.markdown_brief
    assert "## Top Reasons" in v2.markdown_brief
    assert "Sanctions pressure -> Talks failed" in v2.markdown_brief
    assert "Challenge evidence on this edge: 1" in v2.markdown_brief
    assert "## Challenge Coverage" in v2.markdown_brief
    assert "Found 1 challenge evidence" in v2.markdown_brief
    assert "## Evidence" in v2.markdown_brief
    assert "[ev-support] Supports. Source: News." in v2.markdown_brief
    assert "[ev-refute] Challenges. Source: News." in v2.markdown_brief
    assert "EvidenceType.NEWS" not in v2.markdown_brief
    assert "## Source Trace" in v2.markdown_brief
    assert "AP News" in v2.markdown_brief


def test_markdown_brief_title_uses_detected_market_scenario():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)

    assert response.markdown_brief is not None
    assert response.markdown_brief.startswith("# Market / Investment Brief")


def test_markdown_brief_includes_production_verification_steps():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)

    assert response.markdown_brief is not None
    assert "## Production Brief" in response.markdown_brief
    assert "## Next Verification Steps" in response.markdown_brief
    assert "## Production Limits" in response.markdown_brief


def test_markdown_brief_explains_checked_edges_without_refuting_evidence():
    result = AnalysisResult(
        query="why did talks fail",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
            CausalVariable(name="failed_agreement", description="No agreement"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_dispute",
                target="failed_agreement",
                conditional_prob=0.74,
                supporting_evidence_ids=["ev-support"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions and sequencing gap",
                description="Disagreement over sanctions relief and sequencing blocked agreement.",
                variables=[
                    CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
                    CausalVariable(name="failed_agreement", description="No agreement"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_dispute",
                        target="failed_agreement",
                        conditional_prob=0.74,
                        supporting_evidence_ids=["ev-support"],
                    )
                ],
                posterior_probability=0.68,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Officials said sanctions relief sequencing remained unresolved.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            )
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_dispute->failed_agreement",
                "source": "sanctions_dispute",
                "target": "failed_agreement",
                "query": "evidence against sanctions sequencing causing failed talks",
                "result_count": 2,
                "refuting_count": 0,
                "status": "checked_no_refuting_claims",
            }
        ],
    )

    v2 = _result_to_v2(result, is_demo=False)

    assert v2.markdown_brief is not None
    assert "No challenge evidence attached to this edge after targeted retrieval" in v2.markdown_brief
    assert "Challenge evidence on this edge: 0" not in v2.markdown_brief
    assert "0 challenge" not in v2.markdown_brief


def test_frontend_renders_readable_brief_instead_of_raw_markdown_copy():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    readable_brief_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "readable-brief-panel.tsx"
    ).read_text(encoding="utf-8")

    assert "@/lib/readable-brief-panel" in page_source
    assert 'data-testid="readable-brief"' in readable_brief_source
    assert "Readable brief" in readable_brief_source
    assert "Top reasons" in readable_brief_source
    assert "What to check" in readable_brief_source
    assert 'data-testid="copy-report-button"' in readable_brief_source
    assert "Copy report" in readable_brief_source
    assert "Copy Markdown" not in page_source


def test_frontend_offers_manual_report_copy_fallback():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    readable_brief_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "readable-brief-panel.tsx"
    ).read_text(encoding="utf-8")

    assert 'data-testid="manual-copy-report"' in readable_brief_source
    assert "Manual copy" in readable_brief_source
    assert "selectManualCopyReport" in page_source
    assert "onSelectManualCopyReport" in readable_brief_source
    assert "readOnly" in readable_brief_source


def test_frontend_summarizes_source_transparency_in_readable_brief():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    readable_brief_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "readable-brief-panel.tsx"
    ).read_text(encoding="utf-8")

    assert "sourceTransparencySummary" in page_source
    assert 'data-testid="source-health-summary"' in readable_brief_source
    assert "Sources checked" in readable_brief_source
    assert "Stable sources" in readable_brief_source
    assert "Failed sources" in readable_brief_source


def test_frontend_surfaces_rate_limited_source_trace_language():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    source_trace_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "source-trace.ts"
    ).read_text(encoding="utf-8")
    source_trace_panel_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "source-trace-panel.tsx"
    ).read_text(encoding="utf-8")
    readable_brief_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "readable-brief-panel.tsx"
    ).read_text(encoding="utf-8")

    assert "@/lib/source-trace-panel" in page_source
    assert "formatSourceStatusLabel" in source_trace_panel_source
    assert "Rate limited" in source_trace_source
    assert "Recovered" in source_trace_source
    assert "Stale filtered" in source_trace_source
    assert "Source limited" in source_trace_source
    assert "Timed out" in source_trace_source
    assert "Source error" in source_trace_source
    assert "retry_after_seconds" in source_trace_panel_source
    assert "data-testid=\"source-trace-status\"" in source_trace_panel_source
    assert "Reviewability" in readable_brief_source
    assert "Needs source attention" in page_source


def test_frontend_extracts_source_progress_panel():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    source_progress_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "source-progress-panel.tsx"
    ).read_text(encoding="utf-8")

    assert "@/lib/source-progress-panel" in page_source
    assert "SourceProgressPanel" in page_source
    assert "Retrieval trace" in source_progress_source
    assert "Why partial live" in source_progress_source
    assert "EvidenceCollectionStep" in source_progress_source
    assert "Finding and reading evidence" in source_progress_source


def test_frontend_extracts_challenge_coverage_panel():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    challenge_panel_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "challenge-coverage-panel.tsx"
    ).read_text(encoding="utf-8")
    evidence_formatting_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "evidence-formatting.ts"
    ).read_text(encoding="utf-8")

    assert "@/lib/challenge-coverage-panel" in page_source
    assert "ChallengeCoveragePanel" in page_source
    assert "Challenge coverage" in challenge_panel_source
    assert "challenge item(s)" in challenge_panel_source
    assert "formatRefutationStatusLabel" in challenge_panel_source
    assert "checked, no explicit challenge" in evidence_formatting_source


def test_frontend_extracts_evidence_filter_panel():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    evidence_filter_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "evidence-filter-panel.tsx"
    ).read_text(encoding="utf-8")

    assert "@/lib/evidence-filter-panel" in page_source
    assert "EvidenceFilterPanel" in page_source
    assert "All evidence types" in evidence_filter_source
    assert "lower-priority evidence item(s)" in evidence_filter_source
    assert "formatEvidenceTierLabel" in evidence_filter_source
    assert "selectedNodeCitationByEvidenceId" in evidence_filter_source


def test_frontend_extracts_sticky_card_component():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    sticky_card_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "sticky-card.tsx"
    ).read_text(encoding="utf-8")

    assert "@/lib/sticky-card" in page_source
    assert "StickyCard" in page_source
    assert "function StickyCard" not in page_source
    assert "function Pushpin" not in page_source
    assert "export function StickyCard" in sticky_card_source
    assert "function Pushpin" in sticky_card_source
    assert "sticky-card-${note.id}" in sticky_card_source
    assert "paper-texture" in sticky_card_source
    assert "card-title" in sticky_card_source


def test_frontend_extracts_sticky_graph_layout_helpers():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    sticky_layout_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "sticky-graph-layout.ts"
    ).read_text(encoding="utf-8")

    assert "@/lib/sticky-graph-layout" in page_source
    assert "function computeLayout" not in page_source
    assert "function computeCausalStrings" not in page_source
    assert "export function computeLayout" in sticky_layout_source
    assert "export function computeCausalStrings" in sticky_layout_source
    assert "export function buildEdgePath" in sticky_layout_source
    assert "PANEL_SAFE_LEFT_OPEN" in sticky_layout_source
    assert "NOTE_VISUAL_HEIGHT_BUFFER" in sticky_layout_source


def test_api_timeout_runtime_helper_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    runtime_source = (REPO_ROOT / "retrocause" / "api" / "runtime.py").read_text(
        encoding="utf-8"
    )
    live_gate_source = (REPO_ROOT / "retrocause" / "api" / "live_gate.py").read_text(
        encoding="utf-8"
    )

    assert "from retrocause.api.runtime import TimeoutError" in api_source
    assert "def _run_with_timeout" not in api_source
    assert "class _TimeoutError" not in api_source
    assert "def run_with_timeout" in runtime_source
    assert "class TimeoutError" in runtime_source
    assert "from retrocause.api.runtime import run_with_timeout" in live_gate_source
    assert "def run_live_analysis_with_gate" in live_gate_source


def test_api_markdown_brief_builder_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    brief_source = (REPO_ROOT / "retrocause" / "api" / "briefs.py").read_text(
        encoding="utf-8"
    )
    result_conversion_source = (
        REPO_ROOT / "retrocause" / "api" / "result_conversion.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.briefs import" not in api_source
    assert "build_markdown_research_brief" not in api_source
    assert "build_markdown_research_brief" in result_conversion_source
    assert "_build_markdown_research_brief" not in api_source
    assert "def build_markdown_research_brief" in brief_source
    assert "def markdown_bullet" in brief_source


def test_api_production_scenario_detection_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    scenario_source = (REPO_ROOT / "retrocause" / "api" / "scenarios.py").read_text(
        encoding="utf-8"
    )
    result_conversion_source = (
        REPO_ROOT / "retrocause" / "api" / "result_conversion.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.scenarios import" not in api_source
    assert "detect_production_scenario_payload" not in api_source
    assert "detect_production_scenario_payload" in result_conversion_source
    assert "PRODUCTION_SCENARIOS" not in api_source
    assert "SCENARIO_SIGNALS" not in api_source
    assert "def detect_production_scenario_payload" in scenario_source
    assert "PRODUCTION_SCENARIOS" in scenario_source
    assert "SCENARIO_SIGNALS" in scenario_source


def test_api_provider_preflight_classification_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    provider_route_source = (
        REPO_ROOT / "retrocause" / "api" / "provider_routes.py"
    ).read_text(encoding="utf-8")
    provider_preflight_source = (
        REPO_ROOT / "retrocause" / "api" / "provider_preflight.py"
    ).read_text(encoding="utf-8")
    analysis_execution_source = (
        REPO_ROOT / "retrocause" / "api" / "analysis_execution.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.provider_preflight import" in api_source
    assert "is_live_failure" in api_source
    assert "resolve_provider_model" not in api_source
    assert "classify_preflight_failure_code" not in api_source
    assert "preflight_user_action" not in api_source
    assert "resolve_provider_model" in analysis_execution_source
    assert "classify_preflight_failure_code" in provider_route_source
    assert "preflight_user_action" in provider_route_source
    assert "def _preflight_failure_code" not in api_source
    assert "def _preflight_user_action" not in api_source
    assert "def _is_live_failure" not in api_source
    assert "def classify_preflight_failure_code" in provider_preflight_source
    assert "def preflight_user_action" in provider_preflight_source
    assert "def is_live_failure" in provider_preflight_source


def test_provider_routes_are_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    provider_route_source = (
        REPO_ROOT / "retrocause" / "api" / "provider_routes.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.provider_routes import" in api_source
    assert "app.include_router(provider_router)" in api_source
    assert "def list_providers" not in api_source
    assert "def preflight_provider" not in api_source
    assert '"/api/providers"' not in api_source
    assert "router = APIRouter()" in provider_route_source
    assert '@router.get("/api/providers")' in provider_route_source
    assert '@router.post("/api/providers/preflight"' in provider_route_source


def test_api_saved_run_persistence_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    run_route_source = (REPO_ROOT / "retrocause" / "api" / "run_routes.py").read_text(
        encoding="utf-8"
    )
    run_store_source = (REPO_ROOT / "retrocause" / "api" / "run_store.py").read_text(
        encoding="utf-8"
    )
    run_finalization_source = (
        REPO_ROOT / "retrocause" / "api" / "run_finalization.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.run_store import" in api_source
    assert "create_run_id" in api_source
    assert "persist_saved_run_payload" not in api_source
    assert "persist_saved_run_payload" in run_finalization_source
    assert "load_saved_run_records" not in api_source
    assert "load_saved_run_records" in run_route_source
    assert "def _create_run_id" not in api_source
    assert "def _run_store_path" not in api_source
    assert "def _load_saved_run_records" not in api_source
    assert "def _save_saved_run_records" not in api_source
    assert "def _persist_saved_run" not in api_source
    assert "def create_run_id" in run_store_source
    assert "def load_saved_run_records" in run_store_source
    assert "def persist_saved_run_payload" in run_store_source


def test_api_run_metadata_assembly_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    run_metadata_source = (
        REPO_ROOT / "retrocause" / "api" / "run_metadata.py"
    ).read_text(encoding="utf-8")
    run_finalization_source = (
        REPO_ROOT / "retrocause" / "api" / "run_finalization.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.run_metadata import" not in api_source
    assert "build_run_step_payloads" not in api_source
    assert "build_usage_ledger_payloads" not in api_source
    assert "build_run_step_payloads" in run_finalization_source
    assert "build_usage_ledger_payloads" in run_finalization_source
    assert "def _run_step" not in api_source
    assert "def _build_run_steps" not in api_source
    assert "def _quota_owner_for_source" not in api_source
    assert "def _build_usage_ledger" not in api_source
    assert "def build_run_step_payloads" in run_metadata_source
    assert "def build_usage_ledger_payloads" in run_metadata_source
    assert "def quota_owner_for_source_payload" in run_metadata_source


def test_api_run_finalization_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    run_finalization_source = (
        REPO_ROOT / "retrocause" / "api" / "run_finalization.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.run_finalization import" in api_source
    assert "finalize_run_response" in api_source
    assert "def _finalize_run_response" not in api_source
    assert "def _write_saved_run_response" not in api_source
    assert "def finalize_run_response" in run_finalization_source
    assert "persist_saved_run_payload" in run_finalization_source


def test_api_live_failure_response_builder_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    live_failure_source = (
        REPO_ROOT / "retrocause" / "api" / "live_failure_response.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.live_failure_response import" in api_source
    assert "build_empty_live_failure_response" in api_source
    assert "def _empty_live_failure_response" not in api_source
    assert "def build_empty_live_failure_response" in live_failure_source
    assert "build_markdown_research_brief" in live_failure_source
    assert "build_product_harness_payload" in live_failure_source


def test_api_retrieval_trace_conversion_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    retrieval_trace_source = (
        REPO_ROOT / "retrocause" / "api" / "retrieval_trace.py"
    ).read_text(encoding="utf-8")
    result_conversion_source = (
        REPO_ROOT / "retrocause" / "api" / "result_conversion.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.retrieval_trace import" not in api_source
    assert "build_retrieval_trace_item_v2" not in api_source
    assert "build_retrieval_trace_item_v2" in result_conversion_source
    assert "def _retrieval_trace_item_v2" not in api_source
    assert "def _retrieval_status_from_trace" not in api_source
    assert "def build_retrieval_trace_item_v2" in retrieval_trace_source
    assert "describe_source_name" in retrieval_trace_source


def test_api_live_analysis_settings_are_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    analysis_execution_source = (
        REPO_ROOT / "retrocause" / "api" / "analysis_execution.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.analysis_execution import" in api_source
    assert "resolve_live_analysis_settings" in api_source
    assert "PROVIDERS.get(request.model)" not in api_source
    assert 'list(provider_cfg["models"].keys())[0]' not in api_source
    assert "def resolve_live_analysis_settings" in analysis_execution_source
    assert "resolve_provider_model" in analysis_execution_source


def test_api_result_v2_conversion_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    result_conversion_source = (
        REPO_ROOT / "retrocause" / "api" / "result_conversion.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.result_conversion import" in api_source
    assert "result_to_v2 as _result_to_v2" in api_source
    assert "detect_production_scenario as _detect_production_scenario" in api_source
    assert "def _result_to_v2" not in api_source
    assert "def _collect_evidence_bindings" not in api_source
    assert "def _refutation_status" not in api_source
    assert "def result_to_v2" in result_conversion_source
    assert "def collect_evidence_bindings" in result_conversion_source


def test_api_analysis_brief_builder_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    analysis_brief_source = (
        REPO_ROOT / "retrocause" / "api" / "analysis_brief.py"
    ).read_text(encoding="utf-8")
    result_conversion_source = (
        REPO_ROOT / "retrocause" / "api" / "result_conversion.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.analysis_brief import" not in api_source
    assert "build_analysis_brief_payload" not in api_source
    assert "build_analysis_brief_payload" in result_conversion_source
    assert "def _build_analysis_brief" not in api_source
    assert "def _edge_challenge_phrase" not in api_source
    assert "def build_analysis_brief_payload" in analysis_brief_source
    assert "def edge_challenge_phrase" in analysis_brief_source


def test_api_production_brief_builder_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    production_brief_source = (
        REPO_ROOT / "retrocause" / "api" / "production_brief.py"
    ).read_text(encoding="utf-8")
    result_conversion_source = (
        REPO_ROOT / "retrocause" / "api" / "result_conversion.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.production_brief import" not in api_source
    assert "build_production_brief_payload" not in api_source
    assert "build_production_brief_payload" in result_conversion_source
    assert "def _build_production_brief" not in api_source
    assert "def _brief_item_from_edge" not in api_source
    assert "def _top_edge_items" not in api_source
    assert "def _verification_items" not in api_source
    assert "def _production_executive_summary" not in api_source
    assert "def build_production_brief_payload" in production_brief_source
    assert "def production_brief_item_from_edge_payload" in production_brief_source


def test_api_product_harness_builders_are_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    harness_source = (REPO_ROOT / "retrocause" / "api" / "harness.py").read_text(
        encoding="utf-8"
    )
    result_conversion_source = (
        REPO_ROOT / "retrocause" / "api" / "result_conversion.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.harness import" not in api_source
    assert "build_production_harness_payload" not in api_source
    assert "build_product_harness_payload" not in api_source
    assert "build_production_harness_payload" in result_conversion_source
    assert "build_product_harness_payload" in result_conversion_source
    assert "def _build_production_harness" not in api_source
    assert "def _build_product_harness" not in api_source
    assert "def _production_check" not in api_source
    assert "def _check_freshness_gate" not in api_source
    assert "def build_production_harness_payload" in harness_source
    assert "def build_product_harness_payload" in harness_source


def test_api_schema_models_are_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    schemas_source = (REPO_ROOT / "retrocause" / "api" / "schemas.py").read_text(
        encoding="utf-8"
    )

    assert "from retrocause.api.schemas import" in api_source
    assert "AnalyzeRequest" in api_source
    assert "AnalyzeResponseV2" in api_source
    assert "class AnalyzeRequest(BaseModel)" not in api_source
    assert "class AnalyzeResponseV2(BaseModel)" not in api_source
    assert "class ProductionHarnessReportV2(BaseModel)" not in api_source
    assert "class AnalyzeRequest(BaseModel)" in schemas_source
    assert "class AnalyzeResponseV2(BaseModel)" in schemas_source
    assert "class ProductionHarnessReportV2(BaseModel)" in schemas_source


def test_uploaded_evidence_route_is_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    evidence_route_source = (
        REPO_ROOT / "retrocause" / "api" / "evidence_routes.py"
    ).read_text(encoding="utf-8")

    assert "from retrocause.api.evidence_routes import" in api_source
    assert "app.include_router(evidence_router)" in api_source
    assert "def upload_evidence" not in api_source
    assert '"/api/evidence/upload"' not in api_source
    assert "router = APIRouter()" in evidence_route_source
    assert '@router.post("/api/evidence/upload"' in evidence_route_source
    assert "def upload_evidence" in evidence_route_source


def test_saved_run_routes_are_extracted():
    api_source = (REPO_ROOT / "retrocause" / "api" / "main.py").read_text(encoding="utf-8")
    run_route_source = (REPO_ROOT / "retrocause" / "api" / "run_routes.py").read_text(
        encoding="utf-8"
    )

    assert "from retrocause.api.run_routes import" in api_source
    assert "app.include_router(run_router)" in api_source
    assert "def list_saved_runs" not in api_source
    assert "def get_saved_run" not in api_source
    assert '"/api/runs"' not in api_source
    assert "router = APIRouter()" in run_route_source
    assert '@router.get("/api/runs"' in run_route_source
    assert '@router.get("/api/runs/{run_id}")' in run_route_source


def test_legacy_canvas_graph_uses_shared_red_string_path_builder():
    legacy_graph_source = (
        REPO_ROOT / "frontend" / "src" / "components" / "canvas" / "CausalGraphView.tsx"
    ).read_text(encoding="utf-8")

    assert "@/lib/sticky-graph-layout" in legacy_graph_source
    assert "buildEdgePath" in legacy_graph_source
    assert "function computeRedStringPath" not in legacy_graph_source
    assert "Legacy canvas view" in legacy_graph_source


def test_legacy_canvas_graph_uses_canonical_sticky_card_component():
    legacy_graph_source = (
        REPO_ROOT / "frontend" / "src" / "components" / "canvas" / "CausalGraphView.tsx"
    ).read_text(encoding="utf-8")

    assert "@/lib/sticky-card" in legacy_graph_source
    assert "StickyCardNote" in legacy_graph_source
    assert "const StickyCard = ({" not in legacy_graph_source
    assert "const PushpinSVG" not in legacy_graph_source
    assert "TAG_COLORS" not in legacy_graph_source
    assert "toLegacyStickyNote" in legacy_graph_source


def test_frontend_localizes_source_trace_status():
    source_trace_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "source-trace.ts"
    ).read_text(encoding="utf-8")

    assert "\\u53ef\\u7528" in source_trace_source
    assert "\\u7f13\\u5b58" in source_trace_source
    assert "\\u6765\\u6e90\\u53d7\\u9650" in source_trace_source
    assert "\\u9650\\u6d41" in source_trace_source
    assert "\\u65e0\\u6743\\u9650" in source_trace_source
    assert "\\u8d85\\u65f6" in source_trace_source
    assert "\\u6765\\u6e90\\u9519\\u8bef" in source_trace_source
    assert "\\u901a\\u8baf\\u793e\\u65b0\\u95fb" in source_trace_source
    assert "\\u7f51\\u9875\\u68c0\\u7d22" in source_trace_source
    assert "\\u5b98\\u65b9\\u8bb0\\u5f55" in source_trace_source
    assert "\\u7a33\\u5b9a" in source_trace_source
    assert "\\u4e0d\\u7a33\\u5b9a" in source_trace_source


def test_frontend_empty_source_trace_is_explicit_for_demo_mode():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    source_trace_panel_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "source-trace-panel.tsx"
    ).read_text(encoding="utf-8")

    assert "mode={analysisMode.mode}" in page_source
    assert "No live retrieval trace" in source_trace_panel_source
    assert "\\u65e0\\u5b9e\\u65f6\\u68c0\\u7d22\\u8f68\\u8ff9" in source_trace_panel_source
    assert "retrievalTrace.length === 0" in source_trace_panel_source


def test_frontend_evidence_formatting_helpers_are_extracted():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    evidence_formatting_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "evidence-formatting.ts"
    ).read_text(encoding="utf-8")

    assert "@/lib/evidence-formatting" in page_source
    assert "export function formatEvidenceTierLabel" in evidence_formatting_source
    assert "export function evidenceQualityCategory" in evidence_formatting_source
    assert "export function formatFreshnessLabel" in evidence_formatting_source
    assert "export function formatAnalysisBadge" in evidence_formatting_source
    assert "function formatEvidenceTierLabel" not in page_source


def test_frontend_renders_production_brief_and_use_case_selector():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )
    production_brief_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "production-brief-panel.tsx"
    ).read_text(encoding="utf-8")

    assert 'data-testid="scenario-selector"' in page_source
    assert "@/lib/production-brief-panel" in page_source
    assert 'data-testid="production-brief"' in production_brief_source
    assert "scenario_override" in page_source
    assert "Production brief" in production_brief_source


def test_frontend_production_brief_panel_surfaces_next_steps_and_limits():
    production_brief_source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "production-brief-panel.tsx"
    ).read_text(encoding="utf-8")

    assert "brief.next_verification_steps" in production_brief_source
    assert "brief.limits" in production_brief_source
    assert "Next verification steps" in production_brief_source
    assert "Current limits" in production_brief_source


def test_frontend_offers_three_production_use_cases():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert "Market / Investment" in page_source
    assert "Policy / Geopolitics" in page_source
    assert "Postmortem" in page_source


def test_frontend_does_not_hardcode_single_case_product_labels():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    forbidden_terms = [
        "nuclear program",
        "negotiation refusal",
        "no deal reached",
        "iran",
        "united states",
    ]
    lowered = page_source.lower()
    for term in forbidden_terms:
        assert term not in lowered
    assert 'return "市场影响因素"' not in page_source
    assert "hasUnlocalizedEnglishLabel(localized)" not in page_source


def test_frontend_keeps_specific_live_node_labels():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert 'return "市场影响因素"' not in page_source
    assert "hasUnlocalizedEnglishLabel(localized)" not in page_source


def test_result_to_v2_node_types():
    result = _make_minimal_result()
    v2 = _result_to_v2(result)
    nodes = v2.chains[0].nodes
    node_types = {n.id: n.type for n in nodes}
    # var_a has no upstream → "cause"
    # var_b has no downstream → "effect"
    assert node_types["var_a"] == "cause"
    assert node_types["var_b"] == "effect"


def test_result_to_v2_infers_time_range_from_query():
    result = _make_minimal_result()
    result.query = "Why did this stock fall today?"
    v2 = _result_to_v2(result)
    assert v2.time_range == "today"


def test_result_to_v2_partial_live_reasons_follow_evaluation():
    result = _make_minimal_result()
    result.analysis_mode = "partial_live"
    result.freshness_status = "stable"
    result.evaluation = PipelineEvaluationV2.model_validate(
        {
            "evidence_sufficiency": 0.4,
            "probability_coherence": 0.8,
            "chain_diversity": 0.5,
            "overall_confidence": 0.55,
            "weaknesses": ["Fallback-summary evidence dominates the run (3/4 items)."],
            "recommended_actions": ["Reduce fallback-summary evidence."],
        }
    )
    # Convert back to the dataclass-like shape expected by _result_to_v2.
    from retrocause.evaluation import PipelineEvaluation

    result.evaluation = PipelineEvaluation(
        evidence_sufficiency=result.evaluation.evidence_sufficiency,
        probability_coherence=result.evaluation.probability_coherence,
        chain_diversity=result.evaluation.chain_diversity,
        overall_confidence=result.evaluation.overall_confidence,
        weaknesses=result.evaluation.weaknesses,
        recommended_actions=result.evaluation.recommended_actions,
    )
    v2 = _result_to_v2(result)
    assert v2.partial_live_reasons
    assert "Fallback-summary evidence dominates the run" in v2.partial_live_reasons[0]


@pytest.mark.anyio
async def test_analyze_query_v2_returns_partial_live_instead_of_demo_on_live_failure(monkeypatch):
    def _fail_run_real_analysis(*args, **kwargs):
        raise RuntimeError("401 User not found.")

    monkeypatch.setattr("retrocause.app.demo_data.run_real_analysis", _fail_run_real_analysis)

    request = AnalyzeRequest(
        query="为什么美国会同意与伊朗进行首轮谈判？",
        model="openrouter",
        api_key="sk-test",
        explicit_model="openai/gpt-4o-mini",
    )
    response = await analyze_query_v2(request)
    assert response.is_demo is False
    assert response.analysis_mode == "partial_live"
    assert response.error is not None
    assert response.chains == []
    assert response.evaluation is not None
    assert any("api key" in action.lower() for action in response.evaluation.recommended_actions)


@pytest.mark.anyio
async def test_analyze_v2_accepts_scenario_override_without_live_key():
    response = await analyze_query_v2(
        AnalyzeRequest(
            query="Why did bitcoin fall today?",
            scenario_override="postmortem",
        )
    )

    assert response.scenario is not None
    assert response.scenario.key == "postmortem"
    assert response.scenario.detection_method == "override"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Pydantic Schema 验证 — 确保 API 模型能正确序列化
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_multi_user_persona_outputs_are_actionable(monkeypatch):
    novice_response = await analyze_query_v2(
        AnalyzeRequest(query="Why did a product launch fail to convert trial users?")
    )

    assert novice_response.analysis_mode == "demo"
    assert novice_response.product_harness is not None
    assert novice_response.product_harness.status in {"ready_for_review", "needs_more_evidence"}
    assert novice_response.analysis_brief is not None
    assert novice_response.markdown_brief
    assert novice_response.product_harness.next_actions

    def _fail_run_real_analysis(*args, **kwargs):
        raise RuntimeError("401 invalid API key")

    monkeypatch.setattr("retrocause.app.demo_data.run_real_analysis", _fail_run_real_analysis)

    blocked_response = await analyze_query_v2(
        AnalyzeRequest(
            query="Why did Bitcoin move today?",
            model="openrouter",
            api_key="sk-test",
            explicit_model="deepseek/deepseek-chat-v3-0324",
        )
    )

    assert blocked_response.is_demo is False
    assert blocked_response.analysis_mode == "partial_live"
    assert blocked_response.product_harness is not None
    assert blocked_response.product_harness.status == "blocked_by_model"
    assert blocked_response.error is not None
    assert blocked_response.markdown_brief
    assert any("preflight" in action.lower() for action in blocked_response.product_harness.next_actions)


def test_multi_user_reviewer_can_audit_degraded_source_states():
    result = _sample_result_with_one_supported_chain(
        "Why did US Iran talks in Islamabad end without agreement?"
    )
    result.retrieval_trace = [
        {
            "source": "ap_news",
            "query": "US Iran Islamabad talks AP",
            "result_count": 0,
            "cache_hit": False,
            "status": "rate_limited",
            "retry_after_seconds": 30,
            "source_kind": "wire_news",
            "stability": "high",
            "cache_policy": "short_lived_cache_allowed",
        },
        {
            "source": "brave_search",
            "query": "US Iran talks sanctions disagreement",
            "result_count": 0,
            "cache_hit": False,
            "status": "forbidden",
            "source_kind": "hosted_search",
            "stability": "medium",
            "cache_policy": "transient_results_only",
        },
        {
            "source": "web_search",
            "query": "US Iran negotiations failed reasons",
            "result_count": 2,
            "cache_hit": False,
            "status": "ok",
            "source_kind": "general_search",
            "stability": "medium",
            "cache_policy": "short_lived_cache_allowed",
        },
    ]
    result.refutation_checks = [
        {
            "edge_id": "primary_driver->observed_outcome",
            "source": "primary_driver",
            "target": "observed_outcome",
            "query": "evidence against primary driver causing observed outcome",
            "result_count": 1,
            "refuting_count": 0,
            "status": "checked_no_refuting_claims",
        }
    ]

    response = _result_to_v2(result, is_demo=False)

    statuses = {item.source: item.status for item in response.retrieval_trace}
    assert statuses == {
        "ap_news": "rate_limited",
        "brave_search": "forbidden",
        "web_search": "ok",
    }
    assert response.product_harness is not None
    assert response.product_harness.status in {"ready_for_review", "needs_more_evidence"}
    assert response.analysis_brief is not None
    assert "3 source attempt(s), 2 degraded or limited" in response.analysis_brief.source_coverage
    assert response.markdown_brief is not None
    assert "status: rate-limited" in response.markdown_brief
    assert "status: forbidden" in response.markdown_brief
    assert "retry after 30s" in response.markdown_brief


def test_v2_schema_round_trip():
    """验证 V2 schema 可以正确序列化/反序列化"""
    v2 = AnalyzeResponseV2(
        query="test",
        is_demo=True,
        demo_topic="svb",
        time_range="today",
        partial_live_reasons=[],
        recommended_chain_id="chain-1",
        chains=[
            HypothesisChainV2(
                chain_id="chain-1",
                label="Test",
                description="A test chain",
                probability=0.8,
                nodes=[
                    GraphNodeV2(
                        id="a",
                        label="A",
                        description="Cause A",
                        probability=0.9,
                        type="cause",
                        depth=0,
                        upstream_ids=[],
                        supporting_evidence_ids=[],
                        refuting_evidence_ids=[],
                    ),
                ],
                edges=[
                    GraphEdgeV2(
                        id="a_b",
                        source="a",
                        target="b",
                        strength=0.7,
                        type="causes",
                        supporting_evidence_ids=[],
                        refuting_evidence_ids=[],
                    ),
                ],
                supporting_evidence_ids=[],
                refuting_evidence_ids=[],
                counterfactual={"items": [], "overall_confidence": 0.0},
                depth=1,
            ),
        ],
        evidences=[
            EvidenceBindingV2(
                id="ev1",
                content="Test evidence",
                source="test",
                reliability="0.80",
                is_supporting=True,
                source_tier="base",
                freshness="stable",
                extraction_method="manual",
            ),
        ],
        upstream_map={"entries": []},
        evaluation=PipelineEvaluationV2(
            evidence_sufficiency=0.6,
            probability_coherence=0.8,
            chain_diversity=0.5,
            overall_confidence=0.63,
            weaknesses=["low diversity"],
            recommended_actions=["generate more chains"],
        ),
    )
    # Should serialize without error
    json_str = v2.model_dump_json()
    parsed = AnalyzeResponseV2.model_validate_json(json_str)
    assert parsed.query == "test"
    assert parsed.time_range == "today"
    assert parsed.partial_live_reasons == []
    assert parsed.evaluation.overall_confidence == 0.63
    assert parsed.evidences[0].source_tier == "base"
    assert parsed.evidences[0].freshness == "stable"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Pipeline Evaluation 边界
# ═══════════════════════════════════════════════════════════════════════════════


def test_evaluation_all_scores_bounded():
    """All evaluation scores must be in [0.0, 1.0]"""
    step = EvaluationStep()
    ctx = PipelineContext(query="test")
    ctx = step.execute(ctx)

    ev = ctx.evaluation
    assert ev is not None
    assert 0.0 <= ev.evidence_sufficiency <= 1.0
    assert 0.0 <= ev.probability_coherence <= 1.0
    assert 0.0 <= ev.chain_diversity <= 1.0
    assert 0.0 <= ev.overall_confidence <= 1.0


def test_evaluation_step_errors_penalty():
    """step_errors should reduce overall_confidence"""
    ctx_good = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=[CausalVariable(name="a", description="A")],
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
                evidence_coverage=0.8,
            ),
        ],
        total_evidence_count=5,
    )
    step = EvaluationStep()
    ctx_good = step.execute(ctx_good)
    score_good = ctx_good.evaluation.overall_confidence

    ctx_bad = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=[CausalVariable(name="a", description="A")],
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
                evidence_coverage=0.8,
            ),
        ],
        total_evidence_count=5,
        step_errors=[{"step": "x", "error": "fail"}],
    )
    ctx_bad = step.execute(ctx_bad)
    score_bad = ctx_bad.evaluation.overall_confidence

    assert score_bad < score_good, f"Errors should reduce confidence: {score_bad} >= {score_good}"


def test_probability_coherence_rejects_negative_ci():
    ctx = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=[],
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
                confidence_interval=(0.8, 0.2),  # lo > hi → incoherent
            ),
        ],
    )
    score, weaknesses = _assess_probability_coherence(ctx)
    assert score < 1.0
    assert any("异常" in w or "不自洽" in w for w in weaknesses)


def test_chain_diversity_identical_chains():
    vars_a = [CausalVariable(name=f"v{i}", description=f"V{i}") for i in range(3)]
    ctx = PipelineContext(
        query="test",
        hypotheses=[
            HypothesisChain(
                id="h1",
                name="H1",
                description="Test",
                variables=vars_a,
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
            ),
            HypothesisChain(
                id="h2",
                name="H2",
                description="Test",
                variables=vars_a,
                edges=[],
                path_probability=0.5,
                posterior_probability=0.5,
            ),
        ],
    )
    score, weaknesses = _assess_chain_diversity(ctx)
    assert score == 0.0, f"Identical chains should have 0 diversity, got {score}"
    assert len(weaknesses) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Providers 配置验证
# ═══════════════════════════════════════════════════════════════════════════════


def test_providers_have_required_keys():
    assert "openrouter" in PROVIDERS
    assert "openai" in PROVIDERS
    assert "dashscope" in PROVIDERS
    for name, cfg in PROVIDERS.items():
        assert "base_url" in cfg, f"Provider {name} missing base_url"
        assert "models" in cfg, f"Provider {name} missing models"
        assert isinstance(cfg["models"], dict), f"Provider {name} models must be dict"
        assert len(cfg["models"]) > 0, f"Provider {name} has no models"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Models 数据类验证
# ═══════════════════════════════════════════════════════════════════════════════


def test_analysis_result_defaults():
    r = AnalysisResult(
        query="test",
        domain="general",
        variables=[],
        edges=[],
        hypotheses=[],
    )
    assert r.is_demo is False
    assert r.demo_topic is None
    assert r.evaluation is None
    assert r.analysis_mode == "live"
    assert r.freshness_status == "unknown"
    assert r.total_evidence_count == 0
    assert r.total_uncertainty == 0.0
    assert r.recommended_next_steps == []


def test_hypothesis_chain_defaults():
    h = HypothesisChain(
        id="h1",
        name="Test",
        description="A test chain",
    )
    assert h.status == HypothesisStatus.ACTIVE
    assert h.counterfactual_score == 0.0
    assert h.evidence_coverage == 0.0
    assert h.debate_rounds == []


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Pipeline 空运行
# ═══════════════════════════════════════════════════════════════════════════════


def test_pipeline_empty_steps():
    p = Pipeline()
    ctx = p.run()
    assert ctx.query == ""
    assert ctx.step_errors == []


def test_pipeline_step_failure_captured():
    class FailStep:
        @property
        def name(self):
            return "FailStep"

        @property
        def checkpoint(self):
            return False

        def execute(self, ctx):
            raise RuntimeError("intentional failure")

    p = Pipeline(steps=[FailStep()])
    ctx = p.run(PipelineContext(query="fail test"))
    assert len(ctx.step_errors) == 1
    assert ctx.step_errors[0]["step"] == "FailStep"
    assert "intentional failure" in ctx.step_errors[0]["error"]


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Demo 结果完整性和一致性
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "query",
    [
        "Why did SVB collapse?",
        "为什么某股票暴跌？",
        "2008 financial crisis",
        "Why is rent so high?",
        "Why did dinosaurs go extinct?",
    ],
)
def test_demo_result_completeness(query):
    """Every demo result must have non-empty hypotheses, variables, and edges"""
    result = topic_aware_demo_result(query)
    assert result.query == query
    assert len(result.hypotheses) >= 1, f"No hypotheses for: {query}"
    assert len(result.variables) >= 2, f"Too few variables for: {query}"
    assert len(result.edges) >= 1, f"No edges for: {query}"

    for h in result.hypotheses:
        assert h.id, "Hypothesis must have an id"
        assert h.name, "Hypothesis must have a name"
        assert len(h.variables) > 0, f"Chain {h.id} has no variables"
        assert len(h.edges) > 0, f"Chain {h.id} has no edges"
        assert 0.0 <= h.path_probability <= 1.0
        assert 0.0 <= h.posterior_probability <= 1.0


def test_demo_result_edges_reference_valid_variables():
    """All edge source/target must reference existing variables"""
    result = topic_aware_demo_result("Why did SVB collapse?")
    var_names = {v.name for v in result.variables}
    for edge in result.edges:
        assert edge.source in var_names, f"Edge source {edge.source} not in variables"
        assert edge.target in var_names, f"Edge target {edge.target} not in variables"


def test_demo_result_hypothesis_variables_match_result_variables():
    """Hypothesis chain variables must be a subset of result variables"""
    result = topic_aware_demo_result("Why did SVB collapse?")
    result_var_names = {v.name for v in result.variables}
    for h in result.hypotheses:
        hyp_var_names = {v.name for v in h.variables}
        assert hyp_var_names.issubset(result_var_names), (
            f"Chain {h.id} has variables not in result: {hyp_var_names - result_var_names}"
        )


@pytest.mark.anyio
async def test_provider_preflight_classifies_missing_api_key():
    response = await preflight_provider(
        ProviderPreflightRequest(model="openrouter", api_key=None, explicit_model=None)
    )

    assert response.status == "error"
    assert response.can_run_analysis is False
    assert response.failure_code == "missing_api_key"
    assert any(check.id == "api_key_present" and check.status == "fail" for check in response.checks)
    assert "API key" in response.user_action


@pytest.mark.anyio
async def test_provider_preflight_runs_model_health_check(monkeypatch):
    class FakeLLM:
        def __init__(self, api_key, model, base_url, timeout):
            self.api_key = api_key
            self.model = model
            self.base_url = base_url
            self.timeout = timeout

        def preflight_model_access(self):
            return False, "BadRequestError: invalid model ID"

    monkeypatch.setattr("retrocause.llm.LLMClient", FakeLLM)

    response = await preflight_provider(
        ProviderPreflightRequest(
            model="openrouter",
            api_key="sk-test",
            explicit_model="not-a-real-model",
        )
    )

    assert response.status == "error"
    assert response.can_run_analysis is False
    assert response.failure_code == "invalid_model"
    assert response.model_name == "not-a-real-model"
    assert any(check.id == "model_access" and check.status == "fail" for check in response.checks)
    assert "model" in response.user_action.lower()


@pytest.mark.anyio
async def test_provider_preflight_requires_analysis_stage_smoke(monkeypatch):
    class FakeLLM:
        def __init__(self, api_key, model, base_url, timeout):
            self.api_key = api_key
            self.model = model
            self.base_url = base_url
            self.timeout = timeout

        def preflight_model_access(self):
            return True, None

        def preflight_analysis_smoke(self):
            return False, "Analysis-stage smoke returned empty search queries."

    monkeypatch.setattr("retrocause.llm.LLMClient", FakeLLM)

    response = await preflight_provider(
        ProviderPreflightRequest(
            model="openrouter",
            api_key="sk-test",
            explicit_model="openai/gpt-4o-mini",
        )
    )

    assert response.status == "error"
    assert response.can_run_analysis is False
    assert response.failure_code == "invalid_or_empty_payload"
    assert any(check.id == "model_access" and check.status == "pass" for check in response.checks)
    assert any(check.id == "analysis_smoke" and check.status == "fail" for check in response.checks)
    assert "reliable json output" in response.user_action.lower()


def test_product_harness_marks_model_blocked_empty_result_as_actionable():
    response = AnalyzeResponseV2(
        query="US Iran Islamabad talks ended without agreement",
        is_demo=False,
        demo_topic=None,
        analysis_mode="partial_live",
        freshness_status="unknown",
        time_range=None,
        partial_live_reasons=["LLM calls failed for deepseek/deepseek-chat-v3-0324 - empty result"],
        recommended_chain_id=None,
        chains=[],
        evidences=[],
        upstream_map={"entries": []},
        retrieval_trace=[],
        challenge_checks=[],
        analysis_brief=None,
        error="LLM calls failed for deepseek/deepseek-chat-v3-0324 - empty result",
    )

    report = build_product_harness_payload(response)

    assert report["status"] == "blocked_by_model"
    assert report["score"] < 0.5
    assert any(
        check["id"] == "actionable_failure" and check["status"] == "pass"
        for check in report["checks"]
    )
    assert any("preflight" in action.lower() for action in report["next_actions"])


def test_empty_live_failure_response_includes_specific_user_action():
    response = build_empty_live_failure_response(
        "Why did Bitcoin move today?",
        "LLM calls failed for deepseek/deepseek-chat - empty result",
    )

    assert response.analysis_mode == "partial_live"
    assert response.evaluation is not None
    assert response.evaluation.weaknesses == [
        "LLM calls failed for deepseek/deepseek-chat - empty result"
    ]
    assert any(
        "reliable json output" in action.lower() for action in response.evaluation.recommended_actions
    )
    assert any("preflight" in action.lower() for action in response.evaluation.recommended_actions)


def test_provider_failure_classifier_detects_rate_limits():
    from retrocause.api.provider_preflight import (
        classify_preflight_failure_code,
        provider_recovery_actions,
        preflight_user_action,
    )

    failure_code = classify_preflight_failure_code(
        "RateLimitError: Error code: 429 - deepseek/deepseek-chat is temporarily rate-limited"
    )

    assert failure_code == "rate_limited"
    assert "rate-limited" in preflight_user_action(failure_code).lower()
    recovery_actions = provider_recovery_actions(
        PROVIDERS,
        "openrouter",
        "deepseek/deepseek-chat",
        failure_code,
    )
    joined = " ".join(recovery_actions)
    assert "Try another openrouter model" in joined
    assert "retry DeepSeek later" in joined


def test_empty_live_failure_response_includes_model_recovery_actions():
    response = build_empty_live_failure_response(
        "Why did Bitcoin move today?",
        "RateLimitError: Error code: 429 - deepseek/deepseek-chat is temporarily rate-limited",
        providers=PROVIDERS,
        provider_key="openrouter",
        model_name="deepseek/deepseek-chat",
    )

    evaluation_actions = response.evaluation.recommended_actions if response.evaluation else []
    product_actions = response.product_harness.next_actions if response.product_harness else []
    joined = " ".join([*evaluation_actions, *product_actions])
    assert "rate-limit window" in joined
    assert "Try another openrouter model" in joined


def test_live_analysis_gate_reports_busy_when_local_analysis_is_already_running(monkeypatch):
    from retrocause.api.provider_preflight import classify_preflight_failure_code, is_live_failure
    from retrocause.api.live_gate import (
        LiveAnalysisQueueTimeout,
        _LIVE_ANALYSIS_SEMAPHORE,
        run_live_analysis_with_gate,
    )

    monkeypatch.setenv("RETROCAUSE_LIVE_QUEUE_WAIT_SECONDS", "0.01")
    acquired = _LIVE_ANALYSIS_SEMAPHORE.acquire(timeout=0.1)
    assert acquired is True
    try:
        with pytest.raises(LiveAnalysisQueueTimeout):
            run_live_analysis_with_gate(lambda: "unused", 1)
    finally:
        _LIVE_ANALYSIS_SEMAPHORE.release()
    assert is_live_failure("Live analysis queue is busy: another run is already running")
    assert (
        classify_preflight_failure_code("Live analysis queue is busy: another run is already running")
        == "queue_busy"
    )


def test_llm_retry_after_parser_clamps_provider_delay():
    from retrocause.llm import _retry_after_seconds

    class _Response:
        headers = {"retry-after": "99"}

    class _ProviderError(Exception):
        response = _Response()

    assert _retry_after_seconds(_ProviderError()) == 8


def test_product_harness_mentions_recovered_source_trace_rows():
    response = AnalyzeResponseV2(
        query="Why did Bitcoin move today?",
        is_demo=False,
        demo_topic=None,
        analysis_mode="live",
        freshness_status="fresh",
        time_range="today",
        partial_live_reasons=[],
        recommended_chain_id=None,
        chains=[],
        evidences=[],
        upstream_map={"entries": []},
        retrieval_trace=[
            {
                "source": "web",
                "source_label": "Trusted web search",
                "query": "Bitcoin move today stock price selloff",
                "result_count": 2,
                "cache_hit": False,
                "status": "recovered",
                "source_kind": "web_search",
                "stability": "medium",
                "cache_policy": "short_lived_cache_allowed",
            }
        ],
        challenge_checks=[],
        evaluation=PipelineEvaluationV2(
            evidence_sufficiency=0.5,
            probability_coherence=0.5,
            chain_diversity=0.5,
            overall_confidence=0.5,
            weaknesses=[],
            recommended_actions=[],
        ),
    )

    payload = build_product_harness_payload(response)
    source_trace_check = next(check for check in payload["checks"] if check["id"] == "source_trace")

    assert "recovered" in source_trace_check["detail"].lower()


def test_product_harness_does_not_mark_chain_without_evidence_ready():
    result = _sample_result_with_one_supported_chain("芯原股份今天盘中为什么下跌？")
    response = _result_to_v2(result, is_demo=False)
    response.evidences = []

    payload = build_product_harness_payload(response)

    assert payload["status"] == "needs_more_evidence"
    assert any(
        check["id"] == "evidence_stance" and check["status"] == "fail"
        for check in payload["checks"]
    )
    assert any("evidence" in action.lower() for action in payload["next_actions"])


def test_product_harness_does_not_mark_live_result_without_source_trace_ready():
    result = _sample_result_with_one_supported_chain("芯原股份今天盘中为什么下跌？")
    response = _result_to_v2(result, is_demo=False)
    response.retrieval_trace = []

    payload = build_product_harness_payload(response)

    assert payload["status"] == "needs_more_evidence"
    assert any(
        check["id"] == "source_trace" and check["status"] == "fail"
        for check in payload["checks"]
    )
    assert any("source trace" in action.lower() for action in payload["next_actions"])


def test_detect_demo_topic_accepts_real_chinese_stock_query():
    assert detect_demo_topic("为什么某股票暴跌？") == "stock"


def test_provider_labels_expose_clean_chinese_copy():
    assert PROVIDERS["openrouter"]["label"] == "OpenRouter（多模型中转）"
    assert PROVIDERS["openrouter"]["models"]["anthropic/claude-haiku-4.5"]["label"] == "Claude Haiku 4.5（快速）"


def test_product_harness_rewards_useful_evidence_backed_result():
    result = AnalysisResult(
        query="US Iran Islamabad talks ended without agreement",
        domain="geopolitics",
        variables=[
            CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
            CausalVariable(name="failed_agreement", description="No agreement"),
        ],
        edges=[
            CausalEdge(
                source="sanctions_dispute",
                target="failed_agreement",
                conditional_prob=0.74,
                supporting_evidence_ids=["ev-support"],
            )
        ],
        hypotheses=[
            HypothesisChain(
                id="chain-1",
                name="Sanctions and sequencing gap",
                description="Disagreement over sanctions relief and sequencing blocked agreement.",
                variables=[
                    CausalVariable(name="sanctions_dispute", description="Sanctions dispute"),
                    CausalVariable(name="failed_agreement", description="No agreement"),
                ],
                edges=[
                    CausalEdge(
                        source="sanctions_dispute",
                        target="failed_agreement",
                        conditional_prob=0.74,
                        supporting_evidence_ids=["ev-support"],
                    )
                ],
                posterior_probability=0.68,
            )
        ],
        evidences=[
            Evidence(
                id="ev-support",
                content="Officials said sanctions relief sequencing remained unresolved.",
                source_type=EvidenceType.NEWS,
                stance="supporting",
                stance_basis="llm_extraction",
                source_tier="fresh",
                extraction_method="llm_fulltext",
            )
        ],
        retrieval_trace=[
            {
                "source": "ap_news",
                "query": "US Iran Islamabad talks no agreement sanctions sequencing",
                "result_count": 2,
                "cache_hit": False,
            }
        ],
        refutation_checks=[
            {
                "edge_id": "sanctions_dispute->failed_agreement",
                "source": "sanctions_dispute",
                "target": "failed_agreement",
                "query": "evidence against sanctions sequencing causing failed talks",
                "result_count": 1,
                "refuting_count": 0,
                "status": "checked_no_refuting_claims",
            }
        ],
    )
    response = _result_to_v2(result, is_demo=False)

    assert response.product_harness is not None
    assert response.product_harness.status == "ready_for_review"
    assert response.product_harness.score >= 0.7
    assert any(
        check.id == "analysis_summary" and check.status == "pass"
        for check in response.product_harness.checks
    )
