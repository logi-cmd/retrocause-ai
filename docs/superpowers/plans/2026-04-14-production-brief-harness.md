# Production Brief Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an OSS production brief layer that turns evidence-backed causal analysis into scenario-aware market, policy/geopolitics, and postmortem outputs with freshness, source-quality, and actionability gates.

**Architecture:** Keep the first version inside the existing V2 API and homepage path instead of introducing a new service. The backend detects a scenario, builds deterministic sections from existing evidence/chains/challenge/source-trace fields, and exposes a production harness explaining whether the result is ready to use. The frontend renders a scenario selector and a readable production brief while Markdown remains the portable copy/export format.

**Tech Stack:** Python 3.10, FastAPI/Pydantic, existing RetroCause result models, Next.js/React/Tailwind, pytest static/API tests, root `npm test`, `agent-guardrails`.

---

## Files And Responsibilities

- `retrocause/api/main.py`: add request override, scenario detection, production brief schemas, harness gates, V2 wiring, Markdown export sections.
- `frontend/src/app/page.tsx`: add scenario selector, request payload wiring, response types, production brief rendering, bilingual labels.
- `tests/test_comprehensive.py`: add TDD coverage for detection, scenario output, freshness gates, frontend static assertions, and Markdown export.
- `README.md`: document the three OSS production brief modes in English and Chinese.
- `docs/PROJECT_STATE.md`: record that implementation moved from design to planned execution and later to shipped behavior.
- `.agent-guardrails/evidence/current-task.md`: record commands, checks, residual risks, and plan/implementation status.

## Behavior Contract

- Every production brief claim must be backed by at least one `evidence_id`, or it must be placed in a limits/verification section instead of as a conclusion.
- Probabilities and scores remain in `[0,1]`.
- `scenario_override` is optional and backward compatible; when absent, deterministic scenario detection runs from the query and domain.
- "Latest", "today", "yesterday", "this week", and market/policy breaking-news queries cannot be marked ready unless freshness/source-trace gates pass.
- US/Iran-specific label substitutions are regression-test material only; product logic should be general.
- OSS includes single-run production brief usefulness; Pro remains hosted/scheduled/team/PDF/DOCX/saved/source-policy/branded workflow depth.

## Tasks

### Task 1: Scenario Detection And Request Override

**Files:**
- Modify: `retrocause/api/main.py`
- Test: `tests/test_comprehensive.py`

- [x] **Step 1: Write failing tests**

Add these tests near existing V2 helper tests:

```python
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
```

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
pytest tests/test_comprehensive.py::test_detects_market_production_scenario tests/test_comprehensive.py::test_detects_policy_geopolitics_production_scenario tests/test_comprehensive.py::test_detects_postmortem_production_scenario tests/test_comprehensive.py::test_scenario_override_wins_over_auto_detection -q
```

Expected: failures because `_detect_production_scenario` and `ScenarioV2` do not exist.

- [x] **Step 3: Implement minimal schemas and detector**

In `retrocause/api/main.py`, add `scenario_override` to `AnalyzeRequest`:

```python
scenario_override: Optional[str] = None
```

Add a Pydantic schema near other V2 schemas:

```python
class ScenarioV2(BaseModel):
    key: str
    label: str
    confidence: float
    detection_method: str
    user_value: str
```

Add `_detect_production_scenario` near other V2 builder helpers:

```python
def _detect_production_scenario(
    query: str,
    domain: str = "general",
    override: Optional[str] = None,
) -> ScenarioV2:
    valid = {"market", "policy_geopolitics", "postmortem", "general"}
    if override in valid:
        return _scenario_from_key(override, 1.0, "override")

    normalized = f"{query} {domain}".lower()
    signals = {
        "market": ["market", "stock", "bitcoin", "crypto", "price", "yield", "rate", "earnings", "etf"],
        "policy_geopolitics": ["policy", "sanction", "talks", "ceasefire", "negotiation", "election", "treaty", "war"],
        "postmortem": ["our", "incident", "outage", "conversion", "release", "churn", "customer", "retention"],
    }
    scored = {
        key: sum(1 for token in tokens if token in normalized)
        for key, tokens in signals.items()
    }
    key, count = max(scored.items(), key=lambda item: item[1])
    if count <= 0:
        return _scenario_from_key("general", 0.35, "auto")
    return _scenario_from_key(key, min(0.95, 0.45 + count * 0.15), "auto")
```

Add `_scenario_from_key` with fixed labels and user values:

```python
def _scenario_from_key(key: str, confidence: float, detection_method: str) -> ScenarioV2:
    labels = {
        "market": "Market / Investment Brief",
        "policy_geopolitics": "Policy / Geopolitics Brief",
        "postmortem": "Postmortem Brief",
        "general": "General Causal Brief",
    }
    values = {
        "market": "Helps users inspect market-moving factors, evidence freshness, and trade/research risks.",
        "policy_geopolitics": "Helps users inspect policy or geopolitical drivers, source reliability, and negotiation constraints.",
        "postmortem": "Helps teams inspect incident, product, or business causes and the evidence needed before action.",
        "general": "Helps users inspect likely causes, evidence, counterpoints, and gaps.",
    }
    return ScenarioV2(
        key=key,
        label=labels[key],
        confidence=max(0.0, min(1.0, confidence)),
        detection_method=detection_method,
        user_value=values[key],
    )
```

- [x] **Step 4: Run focused tests and commit**

Run the four tests from Step 2. Expected: pass.

Commit:

```bash
git add retrocause/api/main.py tests/test_comprehensive.py
git commit -m "feat: detect production brief scenarios"
```

### Task 2: Production Brief Sections

**Files:**
- Modify: `retrocause/api/main.py`
- Test: `tests/test_comprehensive.py`

- [x] **Step 1: Write failing tests**

Add tests that call `_result_to_v2` with market, policy, and postmortem queries. Use existing helper patterns from `test_result_to_v2_builds_copyable_markdown_research_brief`.

```python
def test_market_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)
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
```

Repeat the same shape for:

```python
def test_policy_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain("Why did the ceasefire talks fail?")
    response = _result_to_v2(result, is_demo=False)
    assert response.scenario.key == "policy_geopolitics"
    assert "Negotiation Constraints" in [section.title for section in response.production_brief.sections]


def test_postmortem_production_brief_has_expected_sections():
    result = _sample_result_with_one_supported_chain("Why did our checkout conversion drop after the release incident?")
    response = _result_to_v2(result, is_demo=False)
    assert response.scenario.key == "postmortem"
    assert "Operational Causes" in [section.title for section in response.production_brief.sections]
```

Implement `_sample_result_with_one_supported_chain` as a local test helper using existing `AnalysisResult`, `Evidence`, `CausalHypothesis`, and `CausalEdge` imports.

- [x] **Step 2: Run focused tests and confirm red**

Run:

```bash
pytest tests/test_comprehensive.py::test_market_production_brief_has_expected_sections tests/test_comprehensive.py::test_policy_production_brief_has_expected_sections tests/test_comprehensive.py::test_postmortem_production_brief_has_expected_sections -q
```

Expected: failures because response fields and builders do not exist.

- [x] **Step 3: Add production brief schemas**

Add:

```python
class ProductionBriefItemV2(BaseModel):
    title: str
    summary: str
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class ProductionBriefSectionV2(BaseModel):
    kind: str
    title: str
    items: List[ProductionBriefItemV2] = Field(default_factory=list)


class ProductionBriefV2(BaseModel):
    title: str
    scenario_key: str
    executive_summary: str
    sections: List[ProductionBriefSectionV2] = Field(default_factory=list)
    limits: List[str] = Field(default_factory=list)
    next_verification_steps: List[str] = Field(default_factory=list)
```

Add to `AnalyzeResponseV2`:

```python
scenario: Optional[ScenarioV2] = None
production_brief: Optional[ProductionBriefV2] = None
```

- [x] **Step 4: Implement deterministic section builder**

Add `_build_production_brief(response, scenario)`:

```python
def _build_production_brief(
    response: AnalyzeResponseV2,
    scenario: ScenarioV2,
) -> ProductionBriefV2:
    items = _top_edge_items(response)
    section_titles = {
        "market": ["Market Drivers", "What Would Change The View"],
        "policy_geopolitics": ["Negotiation Constraints", "Source And Policy Risks"],
        "postmortem": ["Operational Causes", "Evidence Needed Before Action"],
        "general": ["Top Causes", "What To Check Next"],
    }
    primary_title, secondary_title = section_titles.get(scenario.key, section_titles["general"])
    limits = []
    if not items:
        limits.append("No evidence-anchored causal drivers were available in this run.")
    sections = [
        ProductionBriefSectionV2(kind="drivers", title=primary_title, items=items[:5]),
        ProductionBriefSectionV2(kind="verification", title=secondary_title, items=_verification_items(response, scenario)),
    ]
    return ProductionBriefV2(
        title=scenario.label,
        scenario_key=scenario.key,
        executive_summary=_production_executive_summary(response, scenario, items),
        sections=sections,
        limits=limits or response.analysis_brief.missing_evidence if response.analysis_brief else limits,
        next_verification_steps=[item.summary for item in sections[1].items],
    )
```

Add helpers `_top_edge_items`, `_brief_item_from_edge`, `_verification_items`, and `_production_executive_summary`. These helpers must only use existing edge/evidence IDs and `analysis_brief`; no new LLM conclusions.

- [x] **Step 5: Wire into `_result_to_v2` and commit**

Inside `_result_to_v2`, after `analysis_brief` exists:

```python
scenario = _detect_production_scenario(result.query, domain=result.domain, override=scenario_override)
response.scenario = scenario
response.production_brief = _build_production_brief(response, scenario)
```

Run focused tests. Expected: pass.

Commit:

```bash
git add retrocause/api/main.py tests/test_comprehensive.py
git commit -m "feat: build scenario production briefs"
```

### Task 3: Production Harness Freshness And Actionability Gates

**Files:**
- Modify: `retrocause/api/main.py`
- Test: `tests/test_comprehensive.py`

- [x] **Step 1: Write failing tests**

Add:

```python
def test_recent_market_result_needs_fresh_evidence_before_ready():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    result.freshness_status = "stale"
    result.time_range = {"is_time_sensitive": True, "bucket": "today"}
    response = _result_to_v2(result, is_demo=False)
    assert response.production_harness is not None
    assert response.production_harness.status == "needs_more_evidence"
    assert any(check.name == "freshness_gate" and not check.passed for check in response.production_harness.checks)


def test_policy_result_with_weak_source_trace_surfaces_source_risk():
    result = _sample_result_with_one_supported_chain("Why did sanctions talks fail today?")
    result.retrieval_trace = [{"source": "web_search", "status": "ok", "results": 1, "source_tier": "volatile"}]
    response = _result_to_v2(result, is_demo=False)
    assert any(check.name == "source_risk" for check in response.production_harness.checks)


def test_postmortem_without_internal_evidence_is_not_actionable():
    result = _sample_result_with_one_supported_chain("Why did our checkout conversion drop after the release incident?")
    response = _result_to_v2(result, is_demo=False)
    assert response.production_harness.status in {"needs_more_evidence", "not_actionable"}
    assert any(check.name == "internal_evidence" and not check.passed for check in response.production_harness.checks)
```

- [x] **Step 2: Run focused tests and confirm red**

```bash
pytest tests/test_comprehensive.py::test_recent_market_result_needs_fresh_evidence_before_ready tests/test_comprehensive.py::test_policy_result_with_weak_source_trace_surfaces_source_risk tests/test_comprehensive.py::test_postmortem_without_internal_evidence_is_not_actionable -q
```

Expected: failures because `production_harness` and new checks do not exist.

- [x] **Step 3: Add production harness schemas**

```python
class ProductionHarnessCheckV2(BaseModel):
    name: str
    passed: bool
    severity: str
    message: str


class ProductionHarnessReportV2(BaseModel):
    status: str
    score: float
    scenario_key: str
    checks: List[ProductionHarnessCheckV2] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
```

Add to `AnalyzeResponseV2`:

```python
production_harness: Optional[ProductionHarnessReportV2] = None
```

- [x] **Step 4: Implement `_build_production_harness` without replacing the existing value harness**

Keep the existing `product_harness` field intact. Add a separate `_build_production_harness(response)` that checks:

```python
checks = [
    _check_freshness_gate(response),
    _check_evidence_anchor_gate(response),
    _check_source_risk_gate(response),
    _check_challenge_gate(response),
    _check_internal_evidence_gate(response),
]
```

Status rules:

```python
if any(check.severity == "blocker" and not check.passed for check in checks):
    status = "blocked"
elif any(check.name == "internal_evidence" and not check.passed for check in checks):
    status = "not_actionable"
elif any(check.severity == "warning" and not check.passed for check in checks):
    status = "needs_more_evidence"
else:
    status = "ready_for_brief"
```

Score rule:

```python
score = sum(1 for check in checks if check.passed) / max(1, len(checks))
```

- [x] **Step 5: Wire into `_result_to_v2`, run tests, commit**

```python
response.production_harness = _build_production_harness(response)
```

Run focused tests plus existing product harness tests:

```bash
pytest tests/test_comprehensive.py::test_recent_market_result_needs_fresh_evidence_before_ready tests/test_comprehensive.py::test_policy_result_with_weak_source_trace_surfaces_source_risk tests/test_comprehensive.py::test_postmortem_without_internal_evidence_is_not_actionable tests/test_comprehensive.py::test_product_harness_rewards_useful_evidence_backed_result -q
```

Commit:

```bash
git add retrocause/api/main.py tests/test_comprehensive.py
git commit -m "feat: gate production briefs for freshness and evidence"
```

### Task 4: API Override Wiring

**Files:**
- Modify: `retrocause/api/main.py`
- Test: `tests/test_comprehensive.py`

- [x] **Step 1: Write failing API test**

Add an async test near provider/API tests:

```python
async def test_analyze_v2_accepts_scenario_override_without_live_key(async_client):
    response = await async_client.post(
        "/api/analyze/v2",
        json={
            "query": "Why did bitcoin fall today?",
            "scenario_override": "postmortem",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"]["key"] == "postmortem"
    assert payload["scenario"]["detection_method"] == "override"
```

- [x] **Step 2: Run and confirm red**

```bash
pytest tests/test_comprehensive.py::test_analyze_v2_accepts_scenario_override_without_live_key -q
```

Expected: fail because `_result_to_v2` does not accept/pass override yet.

- [x] **Step 3: Pass override through V2 response and stream paths**

Change signature:

```python
def _result_to_v2(..., scenario_override: Optional[str] = None) -> AnalyzeResponseV2:
```

In `/api/analyze/v2`:

```python
return _result_to_v2(result, is_demo=is_demo, demo_topic=demo_topic, scenario_override=request.scenario_override)
```

In `/api/analyze/v2/stream`, pass the same override when converting final payloads.

- [x] **Step 4: Run focused test and commit**

```bash
pytest tests/test_comprehensive.py::test_analyze_v2_accepts_scenario_override_without_live_key -q
```

Commit:

```bash
git add retrocause/api/main.py tests/test_comprehensive.py
git commit -m "feat: expose production scenario override"
```

### Task 5: Frontend Scenario Selector And Production Brief Rendering

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Test: `tests/test_comprehensive.py`

- [x] **Step 1: Write failing frontend static tests**

```python
def test_frontend_renders_production_brief_and_use_case_selector():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
    assert 'data-testid="scenario-selector"' in page_source
    assert 'data-testid="production-brief"' in page_source
    assert "scenario_override" in page_source
    assert "Production brief" in page_source


def test_frontend_offers_three_production_use_cases():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
    assert "Market / Investment" in page_source
    assert "Policy / Geopolitics" in page_source
    assert "Postmortem" in page_source
```

- [x] **Step 2: Run and confirm red**

```bash
pytest tests/test_comprehensive.py::test_frontend_renders_production_brief_and_use_case_selector tests/test_comprehensive.py::test_frontend_offers_three_production_use_cases -q
```

- [x] **Step 3: Add response types**

Add types near existing API types:

```ts
type ApiScenario = {
  key: string;
  label: string;
  confidence: number;
  detection_method: string;
  user_value: string;
};

type ApiProductionBriefItem = {
  title: string;
  summary: string;
  evidence_ids: string[];
  confidence: number;
};

type ApiProductionBriefSection = {
  kind: string;
  title: string;
  items: ApiProductionBriefItem[];
};

type ApiProductionBrief = {
  title: string;
  scenario_key: string;
  executive_summary: string;
  sections: ApiProductionBriefSection[];
  limits: string[];
  next_verification_steps: string[];
};
```

Extend `AnalyzeResponseV2` with `scenario`, `production_brief`, and `production_harness`.

- [x] **Step 4: Add selector state and payload field**

```ts
const [scenarioOverride, setScenarioOverride] = useState("auto");
const [scenario, setScenario] = useState<ApiScenario | null>(null);
const [productionBrief, setProductionBrief] = useState<ApiProductionBrief | null>(null);
```

When building analyze request body:

```ts
scenario_override: scenarioOverride === "auto" ? null : scenarioOverride,
```

- [x] **Step 5: Render selector and brief**

Add selector near the query controls:

```tsx
<select
  data-testid="scenario-selector"
  value={scenarioOverride}
  onChange={(event) => setScenarioOverride(event.target.value)}
>
  <option value="auto">Auto detect</option>
  <option value="market">Market / Investment</option>
  <option value="policy_geopolitics">Policy / Geopolitics</option>
  <option value="postmortem">Postmortem</option>
</select>
```

Render production brief near readable brief:

```tsx
{productionBrief && (
  <section data-testid="production-brief">
    <h3>{locale === "en" ? "Production brief" : "\u751f\u4ea7\u7ea7\u7b80\u62a5"}</h3>
    <p>{productionBrief.executive_summary}</p>
    {productionBrief.sections.map((section) => (
      <div key={section.kind}>
        <h4>{section.title}</h4>
        {section.items.map((item) => (
          <p key={`${section.kind}-${item.title}`}>{item.summary}</p>
        ))}
      </div>
    ))}
  </section>
)}
```

- [x] **Step 6: Run tests and commit**

```bash
pytest tests/test_comprehensive.py::test_frontend_renders_production_brief_and_use_case_selector tests/test_comprehensive.py::test_frontend_offers_three_production_use_cases -q
npm --prefix frontend run lint
```

Commit:

```bash
git add frontend/src/app/page.tsx tests/test_comprehensive.py
git commit -m "feat: render production brief workflow"
```

### Task 6: Scenario-Specific Markdown Export

**Files:**
- Modify: `retrocause/api/main.py`
- Test: `tests/test_comprehensive.py`

- [x] **Step 1: Write failing Markdown tests**

```python
def test_markdown_brief_title_uses_detected_market_scenario():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)
    assert response.markdown_brief is not None
    assert response.markdown_brief.startswith("# Market / Investment Brief")


def test_markdown_brief_includes_production_verification_steps():
    result = _sample_result_with_one_supported_chain("Why did bitcoin fall today?")
    response = _result_to_v2(result, is_demo=False)
    assert "## Production Brief" in response.markdown_brief
    assert "## Next Verification Steps" in response.markdown_brief
    assert "## Production Limits" in response.markdown_brief
```

- [x] **Step 2: Run and confirm red**

```bash
pytest tests/test_comprehensive.py::test_markdown_brief_title_uses_detected_market_scenario tests/test_comprehensive.py::test_markdown_brief_includes_production_verification_steps -q
```

- [x] **Step 3: Update `_build_markdown_research_brief`**

Use production brief title when present:

```python
title = response.production_brief.title if response.production_brief else "RetroCause Research Brief"
lines = [f"# {title}", ""]
```

Append sections after likely explanation and before evidence:

```python
if response.production_brief:
    lines.extend(["## Production Brief", "", response.production_brief.executive_summary, ""])
    for section in response.production_brief.sections:
        lines.extend([f"### {section.title}", ""])
        for item in section.items:
            evidence_note = ", ".join(item.evidence_ids) if item.evidence_ids else "verification needed"
            lines.append(f"- {item.summary} Evidence: {evidence_note}.")
        lines.append("")
    lines.extend(["## Next Verification Steps", ""])
    for step in response.production_brief.next_verification_steps:
        lines.append(f"- {step}")
    lines.extend(["", "## Production Limits", ""])
    for limit in response.production_brief.limits or ["No additional production limits were generated."]:
        lines.append(f"- {limit}")
    lines.append("")
```

- [x] **Step 4: Run Markdown tests and commit**

```bash
pytest tests/test_comprehensive.py::test_markdown_brief_title_uses_detected_market_scenario tests/test_comprehensive.py::test_markdown_brief_includes_production_verification_steps tests/test_comprehensive.py::test_result_to_v2_builds_copyable_markdown_research_brief -q
```

Commit:

```bash
git add retrocause/api/main.py tests/test_comprehensive.py
git commit -m "feat: export scenario production briefs"
```

### Task 7: Remove Single-Case Product Logic

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Test: `tests/test_comprehensive.py`

- [x] **Step 1: Replace the US/Iran localization test with a general regression**

Remove `test_frontend_localizes_us_iran_golden_case_labels`. Add:

```python
def test_frontend_does_not_hardcode_single_case_product_labels():
    page_source = (REPO_ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
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
```

- [x] **Step 2: Run and confirm red**

```bash
pytest tests/test_comprehensive.py::test_frontend_does_not_hardcode_single_case_product_labels -q
```

Expected: fail because `ZH_CAUSAL_LABELS` still contains single-case phrases.

- [x] **Step 3: Remove single-case entries from `ZH_CAUSAL_LABELS`**

Delete only entries matching:

```ts
[/\bnuclear program\b/gi, "\u6838\u8ba1\u5212"],
[/\bnegotiation refusal\b/gi, "\u8c08\u5224\u62d2\u7edd"],
[/\bno deal reached\b/gi, "\u672a\u8fbe\u6210\u534f\u8bae"],
[/\bIran\b/g, "\u4f0a\u6717"],
[/\bUnited States\b/g, "\u7f8e\u56fd"],
```

Keep general role/event labels such as sanctions, negotiation, market pressure, evidence, and talks only if they are not single-case entities.

- [x] **Step 4: Run test and commit**

```bash
pytest tests/test_comprehensive.py::test_frontend_does_not_hardcode_single_case_product_labels tests/test_comprehensive.py::test_frontend_keeps_specific_live_node_labels -q
```

Commit:

```bash
git add frontend/src/app/page.tsx tests/test_comprehensive.py
git commit -m "refactor: remove single-case graph label product logic"
```

### Task 8: Documentation And Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT_STATE.md`
- Modify: `.agent-guardrails/evidence/current-task.md`

- [x] **Step 1: Update README in both languages**

Add to `What You Get / 你会看到什么`:

```markdown
- **Production brief modes / 生产级简报模式**: auto-detect or choose Market / Investment, Policy / Geopolitics, or Postmortem so the output explains what a user can decide, what evidence supports it, what could change the view, and what is not ready yet.
```

Add to `OSS vs Pro Boundary`:

```markdown
OSS includes local single-run production briefs and Markdown export. Pro remains the place for hosted recurring runs, PDF/DOCX, saved comparisons, team review, source-policy controls, and branded delivery.
```

- [x] **Step 2: Update PROJECT_STATE**

Move current focus from planned implementation to shipped behavior once Tasks 1-7 pass:

```markdown
- Added the OSS Production Brief Harness for market, policy/geopolitics, and postmortem workflows.
- Removed single-case US/Iran product labeling from frontend logic and kept it as regression context only.
```

Set `Next Step` to release validation/public alpha sync.

- [x] **Step 3: Update evidence note**

Append:

```markdown
## 2026-04-14 Production Brief Harness Implementation

### Task
Implement the approved Production Brief Harness across API, frontend, Markdown export, tests, and docs.

### Files Touched
- `retrocause/api/main.py`
- `frontend/src/app/page.tsx`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run
- Focused pytest commands for scenario detection, production brief sections, production harness gates, API override, Markdown export, and frontend static checks.
- `npm test`
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`

### Residual Risks
- Scenario detection is deterministic keyword routing; deeper domain-specific source policies remain Pro/future work.
- Latest-info readiness still depends on available live retrieval sources and provider behavior.
```

- [x] **Step 4: Run full verification**

```bash
npm test
agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"
```

Expected:
- `npm test` passes frontend lint/build, `ruff check retrocause/`, pytest, and E2E.
- Guardrails reports no blocking issues. Non-blocking documentation-scope warnings are acceptable only if they match the documented task scope and evidence note.

- [x] **Step 5: Final commit**

```bash
git add README.md docs/PROJECT_STATE.md .agent-guardrails/evidence/current-task.md
git commit -m "docs: document production brief harness"
```

## Self-Review

- Spec coverage: the plan covers scenario-aware output, market/policy/postmortem modes, evidence anchoring, freshness gates, source-risk gates, Markdown export, frontend selector/rendering, single-case cleanup, docs, and guardrails evidence.
- Placeholder scan: the plan contains no placeholder markers or empty "add tests" instructions.
- Type consistency: `scenario`, `production_brief`, `production_harness`, and `scenario_override` are named consistently across backend, frontend, tests, and API payload wiring.
- Scope: all planned paths are inside the current task contract's allowed paths.
