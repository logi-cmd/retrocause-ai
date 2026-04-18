# RetroCause Codebase Audit

Last updated: 2026-04-18

This is a maintenance audit, not a feature spec. It records code surfaces that are easy to miss in docs and code areas that are becoming too similar or too large.

## Scope

Reviewed tracked docs and code under:

- `README.md`, `CONTRIBUTING.md`, `STATE.md`, `docs/`, and frontend Markdown files
- `retrocause/`
- `frontend/src/`
- `scripts/`
- `tests/`

Excluded ignored runtime/vendor data such as `.venv/`, `.retrocause/`, `.tmp/`, `.pytest-tmp/`, `.tmp-tests/`, `.pip-tmp/`, `node_modules/`, and `.next/`.

## Public Surfaces Found In Code

### FastAPI endpoints

`retrocause/api/main.py` exposes:

| Endpoint | Handler | Documentation status |
| --- | --- | --- |
| `GET /` | `root` | Documented indirectly as backend health |
| `GET /api/providers` | `list_providers` | Partly documented through provider setup |
| `POST /api/providers/preflight` | `preflight_provider` | Documented in README API usage |
| `POST /api/analyze` | `analyze_query` | Legacy compatibility endpoint, not emphasized in README |
| `POST /api/analyze/v2` | `analyze_query_v2` | Documented in README API usage |
| `POST /api/analyze/v2/stream` | `analyze_query_v2_stream` | Mentioned in project history, not shown in README examples |
| `GET /api/runs` | `list_saved_runs` | Documented in README API usage |
| `GET /api/runs/{run_id}` | `get_saved_run` | Documented in README API usage |
| `POST /api/evidence/upload` | `upload_evidence` | Documented in README API usage |

Finding: `/api/analyze/v2/stream` and legacy `/api/analyze` are real surfaces but are less discoverable than `/api/analyze/v2`. That is acceptable for alpha, but the docs should keep labeling `/api/analyze/v2` as the preferred API.

### Other runnable surfaces

| Surface | Code evidence | Documentation status |
| --- | --- | --- |
| CLI command `retrocause` | `pyproject.toml` has `[project.scripts] retrocause = "retrocause.cli:main"` | Under-documented in README |
| Streamlit demo | `pyproject.toml` optional group `demo`, `retrocause/app/entry.py`, `retrocause/app/panels/` | Mentioned in CONTRIBUTING/manual smoke, not positioned in README |
| Optional Bayesian/vector extras | `pyproject.toml` optional groups `bayesian` and `vector` | Not prominent in README; probably fine because they are not primary OSS workflow |
| Browser UI local run workflow | `frontend/src/app/page.tsx`, `/api/runs`, `/api/evidence/upload` | Documented in README and project state |
| SourceBroker optional adapters | `retrocause/sources/tavily.py`, `retrocause/sources/brave.py`, env keys | Documented in README and retrieval strategy |

Decision after this audit: the browser evidence board started by `python start.py` is the supported first-run path. The CLI is a secondary local smoke-check/scripting surface, and the Streamlit app is a legacy/development demo path. README now labels both accordingly.

## Undocumented Or Easy-To-Miss Capabilities

1. CLI fallback behavior

   `retrocause/cli.py` returns a topic-matched demo fallback when no model key is configured. README now lists the CLI as a secondary entry point for local smoke checks and scripting, not the primary OSS product surface.

2. Streamlit path still exists

   `retrocause/app/entry.py` and `retrocause/app/panels/` are still present. README now labels Streamlit as a legacy/development demo path. The Next.js evidence board remains the current main app.

3. V1 API compatibility

   `/api/analyze` still exists and maps to the older response shape. It should stay quiet in user docs unless backward compatibility becomes important.

4. Optional extras in `pyproject.toml`

   `demo`, `bayesian`, and `vector` extras exist. They are contributor/developer affordances, not current alpha product promises.

## Similar-Code And Maintainability Hotspots

### 1. `frontend/src/app/page.tsx` is the biggest risk

Current size after the source-trace, evidence-formatting, production-brief, saved-runs, uploaded-evidence, source-trace-panel, readable-brief-panel, source-progress-panel, challenge-coverage-panel, evidence-filter-panel, sticky-card, and sticky-graph-layout refactor slices: about 124 KB and 3,195 lines. API response/UI state types now live in `frontend/src/lib/api-types.ts`, source-trace status/source-kind/source-stability label helpers now live in `frontend/src/lib/source-trace.ts`, the rendered source trace list and empty demo/no-key trace note now live in `frontend/src/lib/source-trace-panel.tsx`, readable brief/manual-copy/source-health rendering now lives in `frontend/src/lib/readable-brief-panel.tsx`, partial-live reason and in-flight retrieval progress rendering now lives in `frontend/src/lib/source-progress-panel.tsx`, challenge/refutation coverage rendering now lives in `frontend/src/lib/challenge-coverage-panel.tsx`, related-evidence filter/list rendering now lives in `frontend/src/lib/evidence-filter-panel.tsx`, sticky note card rendering now lives in `frontend/src/lib/sticky-card.tsx`, sticky graph layout and red-string path math now live in `frontend/src/lib/sticky-graph-layout.ts`, evidence quality/freshness/badge/refutation formatting helpers now live in `frontend/src/lib/evidence-formatting.ts`, the production brief card now lives in `frontend/src/lib/production-brief-panel.tsx`, the saved-runs panel now lives in `frontend/src/lib/saved-runs-panel.tsx`, and the uploaded-evidence panel now lives in `frontend/src/lib/uploaded-evidence-panel.tsx`. The homepage evidence board is now the canonical graph/card path.

It still contains localization helpers, panel layout, query flow, and global CSS in one file.

Risk:

- New UI changes are likely to create accidental duplicate helpers instead of reusing existing components.
- Existing component files under `frontend/src/components/` overlap with homepage logic but are not the main rendering path.
- Small viewport bugs are now covered by browser E2E for representative panel controls, but layout, graph math, panels, and CSS still live close together.

Recommended cleanup sequence:

1. Continue extracting pure formatting helpers from `page.tsx` into `frontend/src/lib/`. The source-trace static tests now follow `frontend/src/lib/source-trace.ts`, so future helper extraction should update tests to track the canonical helper module instead of forcing literals to remain in the homepage.
2. Continue resolving duplicated graph/card implementation by moving legacy canvas card rendering toward shared homepage modules or explicitly retiring unused legacy views.
3. Keep `page.tsx` as state orchestration only.

### 2. Duplicate frontend graph/card concepts

Decision after the current cleanup: the homepage evidence board is canonical. `frontend/src/components/canvas/*` is a legacy secondary surface unless a future task revives it deliberately.

Evidence:

- `frontend/src/app/page.tsx` uses the canonical `frontend/src/lib/sticky-card.tsx` and `frontend/src/lib/sticky-graph-layout.ts` modules.
- `frontend/src/components/canvas/CausalGraphView.tsx` now reuses the shared `StickyCard` renderer and red-string path builder, but still has separate legacy position, drag, and view-switching state.
- `frontend/src/components/canvas/ChainView.tsx`, `DebateTreeView.tsx`, and `DataTableView.tsx` still exist as componentized views.

Risk:

- The same UI concept can diverge in behavior, visual language, and bug fixes.
- A fix in legacy `CausalGraphView.tsx` may not fix the current homepage unless it touches the shared `frontend/src/lib/*` graph/card modules.

Recommendation: keep `page.tsx` plus `frontend/src/lib/sticky-card.tsx` / `sticky-graph-layout.ts` as the canonical evidence board path. Next, either retire the unused legacy canvas views or migrate their remaining position/drag/view-state logic toward the canonical modules. Do not grow two graph implementations.

### 3. Backend API assembly is too concentrated

Current size: `retrocause/api/main.py` is still large after extracting timeout/runtime execution to `retrocause/api/runtime.py`, Markdown research brief generation to `retrocause/api/briefs.py`, production scenario metadata/keyword scoring to `retrocause/api/scenarios.py`, and provider preflight classification/model-resolution helpers to `retrocause/api/provider_preflight.py`.

It contains request/response models, V2 conversion, analysis brief builder, production brief builder, product harness, saved-run persistence, uploaded evidence, provider preflight route orchestration, and streaming. Timeout/runtime execution now lives in `retrocause/api/runtime.py`, Markdown research brief text generation now lives in `retrocause/api/briefs.py`, production scenario detection metadata now lives in `retrocause/api/scenarios.py`, and provider/preflight string classification now lives in `retrocause/api/provider_preflight.py`.

Risk:

- API schema changes and product-copy changes are coupled.
- Brief/harness behavior becomes harder to test without importing the full API module.

Recommended cleanup sequence:

1. Move V2 schema models into `retrocause/api/schemas.py`.
2. Continue moving analysis and production brief builders into `retrocause/api/briefs.py`.
3. Move product/production harness checks into `retrocause/api/harness.py`.
4. Keep `retrocause/api/main.py` mostly as routing and request orchestration.

### 4. Retrieval quality helpers appear in multiple modules

Evidence:

- `retrocause/collector.py` has `_result_quality`, fallback extraction, freshness inference, and source-tier inference.
- `retrocause/evidence_access.py` has `_result_quality`, source profiles, result sorting, time matching, and source-error classification.
- `retrocause/engine.py` and `retrocause/evaluation.py` both reason about fallback-summary dominance.

Risk:

- A future change to fallback-summary scoring or freshness semantics may update one module but leave another inconsistent.

Recommendation: keep source-profile and result-quality semantics centralized in `retrocause/evidence_access.py`, then gradually make collector/evaluation call the shared policy rather than duplicating thresholds.

### 5. Source adapters intentionally share a shape

Evidence:

- `retrocause/sources/*.py` classes repeat `name`, `source_type`, and `search` methods.
- The duplicate method names are expected because they implement the same adapter protocol.

Risk:

- Boilerplate is acceptable now. The real risk is inconsistent metadata fields such as `content_quality`, cache policy, provider name, and published date.

Recommendation: do not abstract adapters too early. Instead, add a small adapter contract test that each source returns `SearchResult` metadata needed by SourceBroker.

### 6. Tests contain many repeated mocks

Evidence:

- Mock LLM/source classes appear in `tests/test_engine.py`, `tests/test_integration.py`, `tests/test_auto_collect.py`, and `tests/test_evidence_access.py`.

Risk:

- Repeated mocks make behavior changes noisy and can preserve stale assumptions.

Recommendation: introduce shared test fixtures only after the next refactor target is clear. Avoid a broad test-utils migration until the API/collector boundaries settle.

## Stale Or Conflicting Docs

| Doc | Issue | Suggested action |
| --- | --- | --- |
| `frontend/README.md` | Replaced with RetroCause-specific frontend notes during this audit follow-up | Keep it short and defer product/setup truth to root README |
| `frontend/UI_DESIGN_SPEC.md` | Documents earlier dimensions and layout; current homepage has grown beyond it | Treat as historical design intent until updated |
| `STATE.md` | Older running log through 2026-04-10 | Keep historical, but use `docs/PROJECT_STATE.md` for current state |
| `docs/engineering-audit.md` | Older audit still says some runtime/dependency and app-size issues from an earlier phase | Keep as historical, but do not treat all items as current blockers without rechecking |
| `docs/roadmap-and-limitations.md` | Contains completed and historical roadmap items | Useful, but current next step should come from `docs/PROJECT_STATE.md` |

## Current Non-Code Cleanup Backlog

1. Continue splitting `frontend/src/app/page.tsx` by product section, next targeting remaining homepage panel layout/query-flow split or retiring the legacy canvas state path.
2. Split `retrocause/api/main.py` by schema, brief builders, harnesses, and route handlers.
3. Consolidate retrieval quality/fallback semantics around SourceBroker policy.
4. Add adapter contract tests for source metadata consistency.

## Test Harness Notes

- `scripts/e2e_test.py` is the canonical browser dogfood script for the local OSS app. It autostarts backend/frontend services when needed.
- On Windows, the cleanup path must terminate the process tree, not only the `npm.cmd` parent, or `next start` can keep serving stale `.next` chunks after a later build.
- The Playwright page load checks intentionally wait for DOM content plus product elements instead of `networkidle`; the homepage can issue background requests while still being ready for user interaction.

## Guardrails Notes

- No secrets or runtime data are documented here.
- No package dependencies are added by this audit.
- No product behavior changes are made by this audit.
- Performance impact is documentation-only; the identified performance-sensitive areas are API assembly, retrieval fan-out, and frontend hydration/layout in large files.
