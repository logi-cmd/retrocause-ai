# Project State

Last updated: 2026-04-24

## Goal

RetroCause is a runnable, inspectable causal explanation product for "why did this happen?" questions. It should help users see reasons, sources, uncertainty, and gaps instead of a single opaque answer.

## Current Status

The OSS version remains the only near-term implementation focus. The SourceBroker retrieval reliability pass is implemented locally, and the current local app also has small inspectability-oriented workflow slices: run metadata, a usage ledger, minimal uploaded evidence, saved-run history, browser dogfood for degraded source rows, an analysis-stage provider preflight smoke beyond the tiny JSON check, explicit recovery labeling for zero-hit Chinese time-sensitive live searches, stale-result trace labeling, and postmortem/outage live-source routing. As of 2026-04-24, the current workspace and a fresh local copy both passed the full root `npm test` workflow on Windows, and a release-state audit confirmed that the latest public GitHub release is still `v0.1.0-alpha.5`. This means the project currently meets the bar for a **stable-deliverable local OSS alpha**, not a hosted service and not yet a non-alpha `v0.1.0` release.

What is done:

- unified local app startup
- FastAPI + Next.js evidence-board workflow
- explicit demo / partial-live / live result labeling
- provider preflight harness for API key and model checks
- product value harness for whether a result is reviewable
- scenario-aware OSS Production Brief Harness for market, policy/geopolitics, and postmortem workflows
- copyable Markdown research brief in the V2 API and browser UI
- structured in-app readable brief so Markdown is the copy/export format rather than the only reading surface
- polished Markdown brief wording for challenge coverage, including readable source labels and clear no-refuting-evidence language instead of ambiguous `0 challenge` phrasing
- live US/Iran Islamabad talks golden-case validation with OpenRouter DeepSeek V3
- refreshed live golden-case screenshot under `docs/images/golden-us-iran-live-ui.png`
- automated validation through the root `npm test` command
- clean public GitHub repo published at `https://github.com/logi-cmd/retrocause-ai`
- GitHub prerelease `v0.1.0-alpha.5`
- SourceBroker reliability pass: source profiles, scenario/language/time-aware cache keys, degraded-source classification, API/brief/UI source-health status, optional user-key Tavily/Brave adapters, and search-source preflight
- lightweight local run workflow: `run_id`, run status/steps, source/provider usage ledger, saved-run endpoints/UI, and minimal pasted uploaded evidence stored as user-owned evidence
- OSS stabilization follow-up: narrow-viewport panel controls are browser-tested, graph path layout guards against `NaN`, demo/no-key source trace absence is explicit, API schema models, V2 result conversion, uploaded-evidence route handling, saved-run route handling, provider route/preflight handling, live-failure V2 response assembly, retrieval-trace V2 conversion, live-analysis model settings, run response finalization, Markdown brief generation, structured analysis brief assembly, production brief assembly, production/product harness payload assembly, production-scenario detection, provider preflight classification, saved-run persistence, run metadata assembly, and API timeout runtime helpers have been split out of the large route module, the legacy canvas graph now reuses the shared sticky-card renderer plus red-string path builder, and the E2E harness cleans up Windows frontend process trees while reporting 500 resource URLs

What is not done:

- stable `v0.1.0` release
- first-time OSS release polish beyond the current cleaned bilingual README and alpha prerelease
- hosted Solo Pro / Team Lite workflows such as durable cloud queues, team libraries, PDF/DOCX export, scheduled watch topics, review links, and saved-run comparison
- Pro implementation work in this codebase; future Pro should be planned as a separate full-stack Rust rewrite after the OSS version is solid

## Current Focus

Maintain the stable-deliverable local OSS alpha, fix real user regressions conservatively, and start formal Pro planning without growing hosted Pro behavior in this codebase. The stabilization pass addressed the first mobile/source-trace regressions locally, started backend route-module extraction, made the homepage evidence board the canonical graph/card path while keeping older canvas components as legacy secondary surfaces, added a homepage Chinese A-share intraday sample that fills `芯原股份今天盘中为什么下跌？` while selecting the Market scenario, tightened provider preflight with an analysis-stage query-planning smoke, added a recovery retry plus visible `recovered` trace status for zero-hit Chinese time-sensitive live searches, switched the default local model path to OfoxAI, and cleaned the root README back into readable bilingual OSS onboarding. The clean-clone first-run validation was rerun successfully on 2026-04-23. The next OSS work should focus on provider-backed live Chinese finance query behavior with real keys, continued maintainability cleanup around remaining legacy canvas layout/state logic plus the large API route module, and keeping the explicit `v0.1.0` release gate in sync with real verification results.

Current UX focus: keep the OSS version useful and inspectable before adding more Pro behavior. Validate the general Production Brief Harness across real market, policy/geopolitics, postmortem, and Chinese finance questions. Future Pro workflow depth should be designed after OSS stabilization and should be a separate full-stack Rust rewrite rather than an incremental hosted extension of this alpha codebase.

Current live-source status: a Tavily-backed source-layer smoke now verifies market, policy, postmortem/outage, and Chinese A-share source routes. Postmortem/outage queries route to live web/news sources instead of academic defaults, and time-filtered Chinese finance rows are surfaced as `stale_filtered`. Hosted search keys can now be supplied either through process environment variables or per-run browser/API fields, so users do not need to restart the local server just to test Tavily or Brave Search. The search-source preflight uses the same request-first, environment-fallback key resolution as live analysis, without echoing key values. The latest live-stability follow-up tightened reviewability so a causal chain with no evidence or no evidence anchors cannot be marked `ready_for_review`, lets Chinese evidence text match Chinese variable names when anchoring retrieved source summaries, shortens the Chinese time-sensitive market source path when Tavily/Brave is available, accepts undated hosted-search rows as inspectable fresh candidates instead of discarding every row, reduces default LLM retry amplification, and can build a conservative evidence-anchored fallback market graph when LLM graph extraction returns empty. OfoxAI is now the default local provider path (`https://api.ofox.ai/v1`) with `openai/gpt-5.4-mini` selected first. OpenRouter remains available as a fallback provider; legacy `deepseek/deepseek-chat-v3-0324` requests still normalize to `deepseek/deepseek-chat`. Full live analysis is now serialized by a local process gate by default (`RETROCAUSE_LIVE_MAX_CONCURRENT=1`), provider 429/rate-limit errors use capped backoff with `Retry-After` when present, and rate-limit failures include model-recovery actions for retrying later or trying another provider-accessible model. `scripts/live_stability_probe.py` is now the repeatable provider/search probe for real-key runs; it defaults to OfoxAI and only retests extra models when `RETROCAUSE_LIVE_MODELS` is set. Use `RETROCAUSE_LIVE_PROVIDER=openrouter` plus `OPENROUTER_API_KEY` to retest the older OpenRouter path.

Current planning status: the Production Brief Harness implementation plan is saved at `docs/superpowers/plans/2026-04-14-production-brief-harness.md` and has been executed through code, frontend, export, and regression cleanup. The retrieval/output strategy is captured in `docs/retrieval-and-output-strategy.md`. The SourceBroker reliability implementation plan is saved at `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md` and has been executed through documentation/full verification. The explicit non-alpha release bar now lives in `docs/oss-release-gate.md`. Pro planning now starts from `docs/pro-planning-kickoff.md` and `docs/pro-workflow-spec.md`. The local workflow slice is intentionally OSS inspectability work, not a commitment to build hosted Pro on this stack.

## Working Rules

- Keep project documentation synchronized with every behavior, API, UI, or pipeline change. At minimum, update the current task evidence note; when user-visible behavior changes, also update README or the relevant docs page.
- Keep the shipped OSS alpha stable, and treat Pro work as planning-only unless a new task explicitly reopens OSS runtime changes.
- Treat future Pro as a separate full-stack Rust rewrite. Do not grow this Python/Next alpha into the future hosted Pro architecture without an explicit planning reset.

## Done Recently

- Initialized project guardrails with the `generic` preset.
- Added absolute calendar buckets and pre-extraction stale-result filtering for relative time-sensitive evidence retrieval.
- Added stance-aware refutation coverage, analysis brief output, and challenge coverage UI.
- Added provider preflight and product value harness behavior so users can see whether model setup is blocking analysis and whether a returned result is reviewable.
- Updated OSS readiness docs to distinguish local alpha completeness from polished public release completeness.
- Completed the 2026-04-13 US/Iran Islamabad talks golden case through API and browser UI with OpenRouter DeepSeek V3.
- Fixed an over-broad Chinese localization regex that turned `nuclear` into `nucl出口管理条例`.
- Published the clean OSS alpha package to `logi-cmd/retrocause-ai` and created prerelease `v0.1.0-alpha.1`.
- Prepared `v0.1.0-alpha.2` with README status polish, zero-warning frontend lint, and explicit Turbopack root config.
- Decided the OSS/Pro product boundary: OSS gets copyable Markdown research briefs; Pro gets hosted, PDF/DOCX, team, scheduled, branded, source-policy, and saved-comparison workflows.
- Fixed the local WSL default distro for gstack-style tooling by installing `Ubuntu-24.04`, setting it as default instead of Docker Desktop's internal `docker-desktop` distro, and configuring a non-root default user `retrocause` with passwordless sudo for development tooling.
- Added OSS Markdown research brief output to `/api/analyze/v2` and the browser analysis card.
- Re-ran the US/Iran Islamabad talks golden case on 2026-04-14 with OpenRouter DeepSeek V3: live, fresh, 20 evidence items, 5 chains, 3 challenge checks, product harness `ready_for_review`, and a 4k+ character Markdown brief.
- Prepared `v0.1.0-alpha.3` as the first public alpha that includes the copyable Markdown research brief.
- Added `docs/pro-workflow-spec.md` to keep future paid workflows scoped around repeatable value instead of adding vague "more AI" features.
- Polished the Markdown research brief so top reasons use human-readable source/edge labels and checked edges with no attached refuting evidence explain that state directly.
- Upgraded the browser analysis card into a structured readable brief with top reasons, what-to-check, evidence coverage, and a `Copy report` action that still exports Markdown.
- Dogfooded the readable brief live path and removed the Chinese-mode fallback that collapsed specific live causal-map node labels into generic `市场影响因素` notes.
- Added a manual-copy fallback for blocked clipboard permissions, a source-health summary inside the readable brief, and targeted Chinese localization for the US/Iran golden-case graph labels.
- Published `v0.1.0-alpha.4` with readable-brief UX polish, copy fallback, source-health summary, Markdown challenge wording, and graph-label fixes.
- Designed the next OSS direction as a general Production Brief Harness for market, policy/geopolitics, and postmortem workflows, explicitly moving single-case US/Iran optimizations into regression-test territory rather than product logic.
- Wrote the implementation plan for the Production Brief Harness, covering scenario detection, scenario override, evidence-anchored production sections, freshness/actionability gates, frontend rendering, Markdown export, single-case cleanup, docs, tests, and guardrails verification.
- Added the OSS Production Brief Harness for market, policy/geopolitics, and postmortem workflows.
- Removed single-case US/Iran product labeling from frontend logic and kept it as regression context only.
- Reframed the paid direction away from enterprise/private deployment and toward Solo Pro / Team Lite hosted reliability for individuals and small teams.
- Added `docs/retrieval-and-output-strategy.md` to define the retrieval-to-output pipeline, source adapter rate-limit risks, candidate hosted sources, source policies, cache requirements, run orchestration direction, and development-skill usage.
- Wrote the SourceBroker retrieval reliability implementation plan, covering source profiles, scenario/source-policy cache keys, degraded source status classification, API/UI source trace metadata, optional Tavily/Brave adapters, docs, tests, and guardrails verification.
- Stabilized the local Windows Next.js build by enabling Next worker threads, avoiding `spawn EPERM` during type-checking in this environment.
- Implemented SourceBroker Task 1: source profiles now centralize labels, source kinds, stability, cache policies, default budgets/RPM, API-key requirements, and optional hosted-source ordering.
- Implemented SourceBroker Task 2: retrieval cache keys now include source policy, scenario, language, absolute time bucket, normalized scoped query, adapter name, and result count, with collector paths passing scenario/language metadata into live searches.
- Implemented SourceBroker Task 3: source attempts now classify `ok`, `cached`, `rate_limited`, `forbidden`, `timeout`, `source_error`, and `source_limited` states with retry-after and source-profile metadata.
- Implemented SourceBroker Task 4: V2 retrieval trace and Markdown/readable brief paths now preserve and expose source status, retry-after seconds, cache policy, source kind, and stability, including real pipeline output from `SourceAttempt`.
- Implemented SourceBroker Task 5: optional Tavily hosted search adapter is key-gated by `TAVILY_API_KEY`, maps Tavily results into `SearchResult`, and stays absent from OSS source registration when the key is not configured.
- Implemented SourceBroker Task 6: optional Brave Search adapter is key-gated by `BRAVE_SEARCH_API_KEY`, maps Brave web results into `SearchResult`, and marks result metadata with `cache_policy=transient_results_only`.
- Implemented SourceBroker Task 7: frontend source trace rows now show localized retrieval-health statuses, retry-after hints, and readable brief source-health summary counts for successful, cached, degraded, and reviewability state.
- Implemented SourceBroker Task 8: README and retrieval docs now explain SourceBroker source states, optional hosted adapters, OSS inspectable retrieval, and OSS/Pro boundary in user-facing language.
- Dogfooded the completed SourceBroker reliability pass across market, policy/geopolitics, and postmortem live scenarios with OpenRouter DeepSeek V3: all three returned live reviewable results with source trace rows, evidence counts, Markdown briefs, and harness `ready_for_review`.
- Added a degraded-source drill regression covering `rate_limited`, `forbidden`, `timeout`, `source_error`, `source_limited`, and `cached` source trace rows in the same reviewable output.
- Added multi-user/persona regression coverage for user-value outputs: no-key new users get a demo/readable brief path, invalid-key users get `blocked_by_model` with preflight next action, and reviewer users can audit degraded source states such as `rate_limited` and `forbidden` in the source trace and Markdown brief.
- Stabilized the browser E2E harness to wait for hydrated demo cards and an enabled submit button before interacting with the page, preventing false failures from stale or not-yet-hydrated local app state.
- Documented the OpenCLI source-adapter lesson for RetroCause: OpenCLI avoids shared hosted bottlenecks mostly through local/browser/user-owned execution and bounded deterministic adapters, while RetroCause still needs run orchestration, quota ownership labeling, cache, source policies, and transparent partial results for multi-user reliability.
- Added lightweight local run orchestration metadata to V2 analysis responses, including run id/status, run steps, saved-run persistence, and a provider/source usage ledger.
- Added minimal uploaded evidence support through a local evidence-store endpoint and homepage panel for pasted evidence, source names, and user-owned quota labeling.
- Added saved-runs listing/reopen support through `/api/runs`, `/api/runs/{run_id}`, and a homepage saved-runs panel.
- Added browser-level degraded-source dogfood in the E2E harness by rendering simulated `rate_limited` and `cached` source trace rows and asserting the visible browser labels.
- Decided to finish the OSS version first and defer further Pro implementation; future Pro should be a separate full-stack Rust rewrite, with every behavior/API/UI/pipeline change continuing to update docs and the current-task evidence note.
- Started the OSS release-readiness pass by rewriting `README.md` as clean bilingual first-time user documentation, adding the missing root `npm install`, documenting local saved runs/uploaded evidence accurately, and saving `docs/superpowers/plans/2026-04-16-oss-release-readiness.md`.
- Verified the first-time OSS path from a clean temporary copy: copied Git-managed files only, ran README install commands, started backend/frontend from the copy, passed clean-copy `npm test`, passed explicit browser E2E, and passed focused no-key / invalid-key preflight tests.
- Fixed a Chinese intraday A-share live-analysis failure path: CJK finance fallback retrieval now preserves company anchors such as `芯原股份`, adds searchable stock-price/plunge terms, rejects generic rewrites that drop the company, and routes Chinese time-sensitive market/news queries to web-first sources before GDELT/AP fallbacks.
- Published `v0.1.0-alpha.5` as a GitHub prerelease with local run metadata, saved runs, pasted uploaded evidence, degraded-source browser dogfood, README/Pro-boundary cleanup, and the Chinese A-share retrieval fix.
- Completed a post-release full functionality QA pass: focused query/evidence pytest passed, root `npm test` passed, guardrails passed, desktop demo/API/local inspectability worked, and mobile/narrow viewport defects were recorded for the next stabilization pass.
- Added `docs/INDEX.md` and `docs/codebase-audit.md` so maintainers have one documentation map plus a living audit of public surfaces, undocumented capabilities, similar-code hotspots, and cleanup priorities.
- Began reducing the large Next.js homepage by moving API/UI types, source-trace formatting, evidence formatting, the production brief card, the saved-runs panel, the uploaded-evidence panel, the rendered source-trace list, the readable brief panel, the source progress panel, the challenge coverage panel, the evidence filter panel, sticky card rendering, and sticky graph layout/red-string path math into focused `frontend/src/lib/` modules while keeping behavior covered by static tests and full `npm test`.
- Normalized several fragile Chinese homepage strings to Unicode escapes while extracting the source-trace panel, preventing Windows console encoding rewrites from turning localized copy into invalid TypeScript.
- Added browser regression coverage for narrow viewport panel controls, fixed the mobile panel stacking/width issue, and hardened sticky graph layout/path generation against non-finite values that previously produced SVG `NaN` console errors.
- Made empty demo/no-key source traces explicit in the browser UI instead of hiding the source-trace panel when `retrieval_trace=[]`.
- Started backend maintainability cleanup by moving the API timeout helper into `retrocause/api/runtime.py`, leaving `retrocause/api/main.py` focused slightly more on routes and response assembly.
- Moved Markdown research brief text generation into `retrocause/api/briefs.py` and made legacy `CausalGraphView` reuse the shared sticky-card renderer and sticky graph red-string path builder.
- Hardened the browser E2E harness by avoiding `networkidle` waits for a page with background requests, reporting 500 resource URLs in console-health failures, and cleaning up Windows `npm`/`next` process trees after autostart.
- Added a homepage Chinese A-share intraday sample query for `芯原股份今天盘中为什么下跌？`; the browser now dogfoods that the sample preserves the company anchor and selects the Market scenario before submission.
- Fixed remaining homepage mojibake in visible Chinese labels around preflight, run orchestration, source coverage, chain comparison, and reason summaries; older requests that still send `deepseek/deepseek-chat-v3-0324` are normalized to the stable DeepSeek alias before live analysis even though the current OpenRouter picker is now curated away from the DeepSeek entries.
- Refreshed OpenRouter picker model IDs for current public catalog availability by replacing `google/gemini-2.5-flash-preview` with `google/gemini-2.5-flash` and `anthropic/claude-haiku-4` with `anthropic/claude-haiku-4.5`; added an opt-in `RETROCAUSE_LIVE_OPENROUTER_CATALOG=1` pytest smoke that compares the local catalog to OpenRouter's public `/api/v1/models` list.
- Added an E2E guard for the running backend provider catalog so stale local `python start.py` processes fail visibly when `/api/providers` still serves old OpenRouter IDs.
- Curated the OpenRouter picker down to models that passed current alpha preflight/live checks in RetroCause with a real user key; removed the DeepSeek variants plus failing preview/invalid-payload entries from the picker while keeping legacy `deepseek/deepseek-chat-v3-0324` request normalization for backward compatibility.
- Live `partial_live` failure responses now include explicit recommended actions derived from the provider failure class, and the product harness surfaces those actions alongside the existing preflight retry guidance; added regression coverage for real Chinese stock-query demo detection and clean provider-label copy.
- Rebuilt `retrocause/app/demo_data.py` with clean bundled demo evidence, clean provider labels, and topic-aware sample outputs so demo-only flows no longer depend on older mojibake sample strings.
- Hardened live provider/search stability for the next OSS pass: provider preflight now requires an analysis-stage query-planning smoke after the tiny JSON check, Chinese time-sensitive market/policy searches retry a recovery query on zero-hit source attempts, and source trace plus the product harness surface recovered retry rows explicitly.
- Ran a real source-layer live smoke with the configured Tavily key: market, policy, postmortem/outage, and Chinese A-share source routes all executed; postmortem now uses Tavily/Web instead of arXiv/Semantic Scholar, and stale Chinese finance material is surfaced as `stale_filtered` instead of being mistaken for a source outage.
- Added `scripts/live_stability_probe.py` as a repeatable real-key provider/search stability probe, with tests that keep its provider/model defaults aligned to the current OfoxAI-first picker and verify missing-key reports do not contain secret values.
- Pinned root `npm test` pytest temp files under ignored `.tmp-tests/pytest` after local Windows ACL issues made both `.pytest-tmp` and the user Temp pytest root unreliable.
- Added per-run Tavily and Brave Search key fields to the local homepage/API analysis request path, while keeping environment variables as the restart-time fallback.
- Added `/api/sources/preflight` and a homepage **Run search preflight** action so Tavily/Brave keys can be checked before running a full model-backed analysis.
- Tightened live result reviewability after real-key probes: product harness now requires evidence and evidence anchors before `ready_for_review`, source summaries are preserved when LLM extraction produces no stored evidence, and Chinese evidence text can anchor against Chinese variable names.
- Shortened the Chinese time-sensitive market live path: hosted search rows from Tavily/Brave can survive strict same-day filtering even when undated, optional hosted sources keep the broker from falling through to slower GDELT/AP by default, CausalRAG/refutation retrieval are skipped for this fast path, and an evidence-anchored fallback market graph is used when LLM graph extraction returns empty.
- Rewrote the root README as readable English/Chinese OSS onboarding again after Windows mojibake reappeared, including OfoxAI default-provider setup, per-run Tavily/Brave keys, local-only saved runs/uploaded evidence, API examples, and the OSS/Future Pro boundary.
- Cleaned root OSS metadata by restoring readable `AGENTS.md` contributor rules and replacing the mojibake `pyproject.toml` package description with an English package summary, with regression coverage for both files.

## Known Gaps

- The OSS product can now export a Markdown research brief, show retrieval-health states, reopen local saved runs, has a clean bilingual README, and has now passed a fresh clean-clone install/test smoke again after the latest README cleanup. This closes the first-run local-delivery gate for the current local alpha and is one input into the future non-alpha release bar.
- Degraded-source states now have deterministic API/brief regression coverage plus browser-level source-trace dogfood for representative rate-limited/cached rows; wider visual QA across all bad-path states remains useful.
- Direct monetization design should be deferred until OSS is solid; future Pro should be revisited as a full-stack Rust architecture rather than incremental hosted work in the current alpha stack.
- A true provider-backed live Chinese finance run still needs verification with `OFOXAI_API_KEY` configured after the latest fast-path changes. Source-layer smoke with the configured Tavily key verifies the market/Chinese finance/postmortem source routes, and `scripts/live_stability_probe.py` is the repeatable path for the provider-backed run. Use `RETROCAUSE_LIVE_PROVIDER=openrouter` plus `OPENROUTER_API_KEY` only when retesting the older OpenRouter path.
- The current OpenRouter picker is intentionally smaller than the full public catalog. It includes `deepseek/deepseek-chat` again for user-key compatibility, but every selected model still needs provider preflight and representative live-probe checks because model access and JSON reliability vary by account/provider.
- The repository may still contain mojibake in legacy bilingual docs, test comments, and historical notes on Windows consoles, but the root README, `AGENTS.md`, package metadata, bundled demo data, provider labels, and current homepage/live-failure copy paths have now been cleaned or guarded by tests.
- Local browser/API E2E now verifies that the currently running backend exposes current OpenRouter picker IDs. This catches stale local services, but it is not a substitute for a real-key provider run; `OPENROUTER_API_KEY` must be provided by the operator and any key pasted into chat should be rotated.
- The API route module is still large even after the schema, uploaded-evidence route, saved-run route, provider route/preflight, live-failure V2 response, retrieval-trace V2 conversion, timeout, Markdown-brief, structured-analysis-brief, production-brief, production/product harness, production-scenario, provider-preflight, saved-run, and run-metadata helper extractions; streaming and the remaining main result-to-V2 conversion remain backend split candidates.
- Legacy canvas layout/state logic remains separate from the canonical homepage evidence board, but sticky-card rendering and red-string path math now reuse shared modules.

## Next Step

Start a new OSS stabilization task from the post-release QA findings:

1. exercise a live Chinese finance query with `OFOXAI_API_KEY` plus real search keys and record source quality after the current fast-path/provider-stability changes
2. continue the maintainability cleanup from `docs/codebase-audit.md`, next targeting legacy canvas layout/state retirement or the remaining homepage panel layout/query-flow split
3. continue backend cleanup by moving route orchestration out of `retrocause/api/main.py` in small verified slices
4. keep the `v0.1.0` release bar explicit in `docs/oss-release-gate.md` if new regressions or new release criteria appear
