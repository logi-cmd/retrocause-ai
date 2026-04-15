# SourceBroker Retrieval Reliability Implementation Plan

> **For <PRIVATE_PERSON>:** REQUIRED SUB-SKILL: Use `executing-plans` to execute this plan task-by-task.

**Goal:** turn the current retrieval strategy into a small, testable SourceBroker reliability pass. The work should help a user answer: which sources were checked, which were fresh enough, which were limited or degraded, whether cache was used, and whether the output is still reviewable.

**Architecture:** keep this inside the existing `retrocause.evidence_access` boundary first. Do not add a queue, database, or enterprise connector in this pass. The first implementation should make the current local OSS run more honest and inspectable, while leaving room for Solo Pro / Team Lite run orchestration later.

**Primary files:**

- `retrocause/evidence_access.py`
- `retrocause/api/main.py`
- `retrocause/app/demo_data.py`
- `retrocause/sources/tavily.py`
- `retrocause/sources/brave.py`
- `frontend/src/app/page.tsx`
- `tests/test_evidence_access.py`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/retrieval-and-output-strategy.md`
- `.agent-guardrails/evidence/current-task.md`

## Task 1: Source Profiles And Policy Selection

**Files:** `retrocause/evidence_access.py`, `tests/test_evidence_access.py`

- [x] Add tests first:
  - `test_source_profiles_expose_budget_and_storage_policy`
  - `test_broker_source_names_can_include_optional_hosted_sources_when_enabled`
- [x] Add a frozen `SourceProfile` dataclass with fields:
  - `name`
  - `source_label`
  - `source_kind`
  - `stability`
  - `cache_policy`
  - `default_monthly_budget`
  - `default_rpm`
  - `requires_api_key`
- [x] Add `SOURCE_PROFILES` for:
  - `ap_news`
  - `gdelt`
  - `gdelt_news`
  - `web`
  - `federal_register`
  - `arxiv`
  - `semantic_scholar`
  - `tavily`
  - `brave`
- [x] Add `source_profile(source_name: str) -> SourceProfile`.
- [x] Update `describe_source_name` to use `source_profile` and include `cache_policy`.
- [x] Extend `broker_source_names(configured_sources, plan, *, optional_sources=None)`:
  - preserve explicit `configured_sources` override exactly
  - for fresh market/news queries, prepend enabled hosted sources such as `tavily` or `brave`
  - for policy queries, prefer official and wire/news sources before broad web
- [x] Run `pytest tests/test_evidence_access.py -q`.
- [x] Commit: `feat: add source profiles for retrieval policy`.

## Task 2: Cache Keys Include Scenario, Language, Source Policy, And Absolute Time

**Files:** `retrocause/evidence_access.py`, `tests/test_evidence_access.py`

- [x] Add tests first:
  - `test_access_cache_key_separates_scenario_and_language`
  - `test_access_cache_key_reuses_same_absolute_time_bucket`
- [x] Extend `EvidenceAccessLayer.search` keyword-only parameters:
  - `scenario: str = "unknown"`
  - `language: str = "unknown"`
  - `source_policy: str = "default"`
- [x] Replace the cache key with a tuple shaped like:
  - adapter name
  - source policy
  - scenario
  - language
  - absolute time scope key
  - normalized scoped query
  - max results
- [x] Keep existing callers compatible by using defaults.
- [x] Where a `QueryPlan` is already available in collection code, pass scenario, language, and source policy into `search`.
- [x] Run `pytest tests/test_evidence_access.py -q`.
- [x] Commit: `feat: scope retrieval cache by source policy`.

## Task 3: Rate-Limit And Degraded Source Classification

**Files:** `retrocause/evidence_access.py`, `tests/test_evidence_access.py`

- [ ] Add tests first:
  - `test_access_layer_classifies_rate_limited_sources`
  - `test_access_layer_classifies_forbidden_sources`
  - `test_access_layer_marks_cooldown_as_source_limited`
- [ ] Extend `SourceAttempt` with:
  - `status`
  - `retry_after_seconds`
  - `source_label`
  - `source_kind`
  - `stability`
  - `cache_policy`
- [ ] Add `classify_source_error(exc: Exception) -> tuple[str, str | None, int | None]`.
- [ ] Classify stable statuses:
  - `ok`
  - `cached`
  - `rate_limited`
  - `forbidden`
  - `timeout`
  - `source_error`
  - `source_limited`
- [ ] Extract retry-after seconds from common exception attributes and response headers when present.
- [ ] Store stable status categories in `EvidenceAccessBatch.errors` instead of raw class names for newly classified cases.
- [ ] Keep old general `ConnectionError` behavior readable by mapping it to `source_error`.
- [ ] Run `pytest tests/test_evidence_access.py -q`.
- [ ] Commit: `feat: classify degraded retrieval sources`.

## Task 4: Surface Degraded Source Trace In API And Briefs

**Files:** `retrocause/api/main.py`, `tests/test_comprehensive.py`

- [ ] Add test first:
  - `test_retrieval_trace_exposes_degraded_source_metadata`
- [ ] Extend the V2 retrieval trace schema with:
  - `status`
  - `retry_after_seconds`
  - `cache_policy`
  - `source_kind`
  - `stability`
- [ ] Preserve the new `SourceAttempt` metadata when converting results in `_result_to_v2`.
- [ ] Update Markdown source trace wording so limited sources read as source-limited or rate-limited, not as silent zero-result sources.
- [ ] Ensure no new causal claim is introduced by this mapping. It only exposes retrieval health.
- [ ] Run `pytest tests/test_comprehensive.py::test_retrieval_trace_exposes_degraded_source_metadata -q`.
- [ ] Commit: `feat: expose degraded source trace metadata`.

## Task 5: Optional Tavily Adapter

**Files:** `retrocause/sources/tavily.py`, `retrocause/app/demo_data.py`, `tests/test_evidence_access.py`

- [ ] Add tests first:
  - `test_optional_tavily_adapter_requires_api_key`
  - `test_tavily_adapter_maps_results_to_search_result`
- [ ] Implement `TavilySourceAdapter`.
- [ ] Read the key from `TAVILY_API_KEY`.
- [ ] Return no adapter from app source registration when the key is absent.
- [ ] Map Tavily result title, URL, content/snippet, score, and published date metadata into `SearchResult`.
- [ ] Mark metadata with `content_quality`, provider name, and cache policy.
- [ ] Run the focused adapter tests without requiring a real API key by mocking HTTP.
- [ ] Commit: `feat: add optional Tavily retrieval adapter`.

## Task 6: Optional Brave Search Adapter

**Files:** `retrocause/sources/brave.py`, `retrocause/app/demo_data.py`, `tests/test_evidence_access.py`

- [ ] Add tests first:
  - `test_optional_brave_adapter_requires_api_key`
  - `test_brave_adapter_marks_transient_cache_policy`
- [ ] Implement `BraveSearchSourceAdapter`.
- [ ] Read the key from `BRAVE_SEARCH_API_KEY`.
- [ ] Return no adapter from app source registration when the key is absent.
- [ ] Map web results to `SearchResult`.
- [ ] Mark Brave metadata with transient result-storage policy so downstream cache handling can respect provider terms.
- [ ] Run the focused adapter tests without requiring a real API key by mocking HTTP.
- [ ] Commit: `feat: add optional Brave retrieval adapter`.

## Task 7: UI And Markdown Source Degradation Language

**Files:** `frontend/src/app/page.tsx`, `tests/test_comprehensive.py`

- [ ] Add tests first:
  - `test_frontend_surfaces_rate_limited_source_trace_language`
  - `test_frontend_localizes_source_trace_status`
- [ ] Add a small frontend helper for status labels:
  - English: `Ready`, `Cached`, `Source limited`, `Rate limited`, `Forbidden`, `Timed out`, `Source error`
  - Chinese: `可用`, `缓存`, `来源受限`, `限流`, `无权限`, `超时`, `来源错误`
- [ ] Show source status in the right-side trace and readable brief source-health summary.
- [ ] Keep the summary useful for a user:
  - checked sources
  - successful sources
  - cached sources
  - limited/degraded sources
  - whether the result is still reviewable
- [ ] Run `pytest tests/test_comprehensive.py::test_frontend_surfaces_rate_limited_source_trace_language -q`.
- [ ] Run `npm --prefix frontend run lint`.
- [ ] Commit: `feat: show degraded source trace status`.

## Task 8: Documentation And Full Verification

**Files:** `README.md`, `docs/PROJECT_STATE.md`, `docs/retrieval-and-output-strategy.md`, `.agent-guardrails/evidence/current-task.md`

- [ ] Update README bilingual usage notes to explain:
  - users may see source-limited or rate-limited states
  - OSS supports local inspectable retrieval
  - optional hosted search adapters require user-provided keys
- [ ] Update `docs/retrieval-and-output-strategy.md` with the implemented source profile, cache, and degradation behavior.
- [ ] Update `docs/PROJECT_STATE.md` current status, done-recently, blockers, and next step.
- [ ] Update guardrails evidence with files touched, commands, behavior notes, and residual risks.
- [ ] Run `npm test`.
- [ ] Run `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`.
- [ ] Commit: `docs: document sourcebroker reliability pass`.

## Self-Review

- This plan enhances existing retrieval boundaries before adding hosted workflow infrastructure.
- Every behavior change has a named test target.
- Source adapters are optional and key-gated, so OSS remains runnable without external search accounts.
- Degraded-source language is a product output requirement, not only a backend retry detail.
- The plan keeps enterprise/private deployment out of scope and supports the Solo Pro / Team Lite direction through provider budgets, cache policy, and visible limits.
