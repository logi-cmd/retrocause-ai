# Project State

Last updated: 2026-04-24

## Goal

RetroCause is a runnable, inspectable causal explanation product for "why did this happen?" questions. It should help users see reasons, sources, uncertainty, and gaps instead of a single opaque answer.

## Current Status

The OSS version is a stable-deliverable local alpha and should remain keyless. The active OSS browser/API surface keeps the inspectability workflow slices (run metadata, usage ledger, uploaded evidence, saved-run history, degraded-source rows, local/demo causal maps, source trace structures, and reviewability checks) without accepting model or hosted-search credentials. As of 2026-04-24, the current workspace and a fresh local copy both passed the full root `npm test` workflow on Windows, and a release-state audit confirmed that the latest public GitHub release is still `v0.1.0-alpha.5`. The next implementation focus has moved to the separate Rust Pro workspace under `pro/`, while OSS maintenance stays conservative.

What is done:

- unified local app startup
- FastAPI + Next.js evidence-board workflow
- explicit demo / partial-live / live result labeling
- keyless provider catalog plus disabled preflight compatibility response
- product value harness for whether a result is reviewable
- scenario-aware OSS Production Brief Harness for market, policy/geopolitics, and postmortem workflows
- copyable Markdown research brief in the V2 API and browser UI
- structured in-app readable brief so Markdown is the copy/export format rather than the only reading surface
- polished Markdown brief wording for challenge coverage, including readable source labels and clear no-refuting-evidence language instead of ambiguous `0 challenge` phrasing
- live US/Iran Islamabad talks golden-case validation during the earlier multi-provider alpha phase
- refreshed live golden-case screenshot under `docs/images/golden-us-iran-live-ui.png`
- automated validation through the root `npm test` command
- clean public GitHub repo published at `https://github.com/logi-cmd/retrocause-ai`
- GitHub prerelease `v0.1.0-alpha.5`
- SourceBroker reliability pass: source profiles, scenario/language/time-aware cache keys, degraded-source classification, and API/brief/UI source-health status
- lightweight local run workflow: `run_id`, run status/steps, source/provider usage ledger, saved-run endpoints/UI, and minimal pasted uploaded evidence stored as user-owned evidence
- OSS stabilization follow-up: narrow-viewport panel controls are browser-tested, graph path layout guards against `NaN`, demo/no-key source trace absence is explicit, API schema models, V2 result conversion, uploaded-evidence route handling, saved-run route handling, provider route/preflight handling, live-failure V2 response assembly, retrieval-trace V2 conversion, live-analysis model settings, run response finalization, Markdown brief generation, structured analysis brief assembly, production brief assembly, production/product harness payload assembly, production-scenario detection, provider preflight classification, saved-run persistence, run metadata assembly, and API timeout runtime helpers have been split out of the large route module, the legacy canvas graph now reuses the shared sticky-card renderer plus red-string path builder, and the E2E harness cleans up Windows frontend process trees while reporting 500 resource URLs

What is not done:

- stable `v0.1.0` release
- first-time OSS release polish beyond the current cleaned bilingual README and alpha prerelease
- hosted Solo Pro / Team Lite workflows such as durable cloud queues, team libraries, PDF/DOCX export, scheduled watch topics, review links, and saved-run comparison
- hosted Solo Pro / Team Lite production features such as durable cloud queues, billing, exports, scheduled watch topics, review links, and saved-run comparison beyond the current Rust foundation

## Current Focus

Maintain the stable-deliverable local OSS alpha conservatively and build Pro in the separate Rust workspace. The stabilization pass addressed the first mobile/source-trace regressions locally, started backend route-module extraction, made the homepage evidence board the canonical graph/card path while keeping older canvas components as legacy secondary surfaces, added a homepage Chinese A-share intraday sample that fills `芯原股份今天盘中为什么下跌？` while selecting the Market scenario, removed active key entry/preflight flows from the OSS browser/API surface, deprecated OpenRouter from active support, and cleaned the root README back into readable bilingual OSS onboarding. The active Pro branch now starts from a graph-first Rust foundation with a richer shared run payload and API endpoints for run list/detail/graph inspection.

Current UX focus: Pro should keep the knowledge graph as the primary workspace. The first Rust web shell is server-rendered and graph-first; it can now create runs through the Rust API, reload run detail/graph payloads, update the graph workspace from API state, show keyless provider/search quota ownership plus cooldown semantics, let operators select graph nodes into a browser-local inspector, focus evidence/challenge items from inspector links, keep created runs across API restarts through a local JSON run-store boundary, preview provider/source routing plans without executing providers, create local preview-only execution jobs behind that routing plan, expose non-executing worker work orders for those jobs, render queue jobs plus route-step/work-order details, show planned hosted-worker lifecycle/failure-state and worker-lease/retry-scheduler contracts, show a planned hosted storage/tenant/worker-ownership migration contract, show planned credential-vault and quota-ledger/billing boundaries, show a planned provider-adapter quota/degradation/partial-result contract, run a non-executing provider-adapter dry-run from the graph workspace, show a non-enforcing workspace/auth preview context, render a non-durable run event timeline/status vocabulary derived from the current run record, show a derived review-comparison preview for evidence/challenge deltas, and show the first gated OfoxAI live-adapter candidate with denied gate checks until auth, quota, dry-run, event, vault, and worker gates exist. Future work should add real provider/search execution and deeper graph review without inheriting the OSS page layout.

Current source status: the active OSS browser/API surface is keyless. It returns local/demo analysis payloads, saved-run metadata, uploaded evidence, source-trace structures, and reviewability signals without asking users for model or search credentials. Earlier hosted-source and provider-preflight experiments remain historical context only; OpenRouter is deprecated and is not part of the supported OSS provider surface. The repeatable probe in `scripts/live_stability_probe.py` now exercises the keyless local OSS scenarios instead of requiring provider credentials.

Current planning status: the Production Brief Harness implementation plan is saved at `docs/superpowers/plans/2026-04-14-production-brief-harness.md` and has been executed through code, frontend, export, and regression cleanup. The retrieval/output strategy is captured in `docs/retrieval-and-output-strategy.md`. The SourceBroker reliability implementation plan is saved at `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md` and has been executed through documentation/full verification. The explicit non-alpha release bar now lives in `docs/oss-release-gate.md`. Pro planning starts from `docs/pro-planning-kickoff.md`, `docs/pro-workflow-spec.md`, `docs/pro-prd.md`, and `docs/pro-rust-architecture.md`; implementation now lives under `pro/`.

## Working Rules

- Keep project documentation synchronized with every behavior, API, UI, or pipeline change. At minimum, update the current task evidence note; when user-visible behavior changes, also update README or the relevant docs page.
- Keep the shipped OSS alpha stable. Pro work should stay under `pro/` unless a task explicitly reopens OSS runtime changes.
- Treat Pro as a separate full-stack Rust rewrite. Do not grow the Python/Next alpha into hosted Pro architecture.

## Done Recently

- Initialized project guardrails with the `generic` preset.
- Added absolute calendar buckets and pre-extraction stale-result filtering for relative time-sensitive evidence retrieval.
- Added stance-aware refutation coverage, analysis brief output, and challenge coverage UI.
- Added provider preflight and product value harness behavior so users can see whether model setup is blocking analysis and whether a returned result is reviewable.
- Updated OSS readiness docs to distinguish local alpha completeness from polished public release completeness.
- Completed the 2026-04-13 US/Iran Islamabad talks golden case through API and browser UI during the earlier multi-provider alpha phase.
- Fixed an over-broad Chinese localization regex that turned `nuclear` into `nucl出口管理条例`.
- Published the clean OSS alpha package to `logi-cmd/retrocause-ai` and created prerelease `v0.1.0-alpha.1`.
- Prepared `v0.1.0-alpha.2` with README status polish, zero-warning frontend lint, and explicit Turbopack root config.
- Decided the OSS/Pro product boundary: OSS gets copyable Markdown research briefs; Pro gets hosted, PDF/DOCX, team, scheduled, branded, source-policy, and saved-comparison workflows.
- Fixed the local WSL default distro for gstack-style tooling by installing `Ubuntu-24.04`, setting it as default instead of Docker Desktop's internal `docker-desktop` distro, and configuring a non-root default user `retrocause` with passwordless sudo for development tooling.
- Added OSS Markdown research brief output to `/api/analyze/v2` and the browser analysis card.
- Re-ran the US/Iran Islamabad talks golden case on 2026-04-14 during the earlier multi-provider alpha phase: live, fresh, 20 evidence items, 5 chains, 3 challenge checks, product harness `ready_for_review`, and a 4k+ character Markdown brief.
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
- Implemented SourceBroker Task 1: source profiles now centralize labels, source kinds, stability, cache policies, default budgets/RPM, credential requirements, and hosted-source ordering metadata.
- Implemented SourceBroker Task 2: retrieval cache keys now include source policy, scenario, language, absolute time bucket, normalized scoped query, adapter name, and result count, with collector paths passing scenario/language metadata into live searches.
- Implemented SourceBroker Task 3: source attempts now classify `ok`, `cached`, `rate_limited`, `forbidden`, `timeout`, `source_error`, and `source_limited` states with retry-after and source-profile metadata.
- Implemented SourceBroker Task 4: V2 retrieval trace and Markdown/readable brief paths now preserve and expose source status, retry-after seconds, cache policy, source kind, and stability, including real pipeline output from `SourceAttempt`.
- Implemented SourceBroker Task 5: a Tavily hosted-search experiment mapped Tavily results into `SearchResult`; the active OSS source factory no longer registers hosted-search credentials.
- Implemented SourceBroker Task 6: a Brave Search experiment mapped Brave web results into `SearchResult` with transient-result cache metadata; the active OSS source factory no longer registers hosted-search credentials.
- Implemented SourceBroker Task 7: frontend source trace rows now show localized retrieval-health statuses, retry-after hints, and readable brief source-health summary counts for successful, cached, degraded, and reviewability state.
- Implemented SourceBroker Task 8: README and retrieval docs now explain SourceBroker source states, optional hosted adapters, OSS inspectable retrieval, and OSS/Pro boundary in user-facing language.
- Dogfooded the completed SourceBroker reliability pass across market, policy/geopolitics, and postmortem live scenarios during the earlier multi-provider alpha phase: all three returned live reviewable results with source trace rows, evidence counts, Markdown briefs, and harness `ready_for_review`.
- Added a degraded-source drill regression covering `rate_limited`, `forbidden`, `timeout`, `source_error`, `source_limited`, and `cached` source trace rows in the same reviewable output.
- Added multi-user/persona regression coverage for user-value outputs: no-key new users get a demo/readable brief path, keyless OSS requests stay local/demo, and reviewer users can audit degraded source states such as `rate_limited` and `forbidden` in the source trace and Markdown brief.
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
- Fixed remaining homepage mojibake in visible Chinese labels around earlier preflight copy, run orchestration, source coverage, chain comparison, and reason summaries.
- Refreshed an earlier experimental provider catalog to current public model IDs during alpha probing, before later deprecating the OpenRouter path from active OSS support.
- Added an E2E guard for the running backend provider catalog so stale local `python start.py` processes fail visibly when `/api/providers` serves out-of-date provider IDs.
- Curated the earlier experimental multi-provider picker down to models that passed alpha preflight/live checks before later simplifying the active OSS path back to OfoxAI-first support.
- Earlier live `partial_live` failure responses included explicit recommended actions derived from provider failure classes; current OSS behavior now stays keyless/local while preserving reviewability signals.
- Rebuilt `retrocause/app/demo_data.py` with clean bundled demo evidence, clean provider labels, and topic-aware sample outputs so demo-only flows no longer depend on older mojibake sample strings.
- Hardened earlier live provider/search stability paths during alpha probing; current OSS behavior now keeps provider execution out of the browser/API surface and records keyless source-trace reviewability.
- Ran earlier hosted-source smokes for market, policy, postmortem/outage, and Chinese A-share routes; current OSS validation is the keyless local stability probe.
- Added `scripts/live_stability_probe.py` as a repeatable keyless OSS stability probe with tests that verify reports do not contain secret fields.
- Pinned root `npm test` pytest temp files under ignored `.tmp-tests/pytest` after local Windows ACL issues made both `.pytest-tmp` and the user Temp pytest root unreliable.
- Removed per-run hosted-search credential fields from the active local homepage/API analysis request path.
- Kept `/api/sources/preflight` as a compatibility endpoint that reports the keyless built-in OSS source path.
- Tightened live result reviewability after real-key probes: product harness now requires evidence and evidence anchors before `ready_for_review`, source summaries are preserved when LLM extraction produces no stored evidence, and Chinese evidence text can anchor against Chinese variable names.
- Shortened the Chinese time-sensitive market path during alpha probing; current OSS keeps the A-share path keyless/local and focused on reviewable demo behavior.
- Rewrote the root README as readable English/Chinese OSS onboarding again after Windows mojibake reappeared, including the keyless OSS boundary, local-only saved runs/uploaded evidence, API examples, and the OSS/Future Pro boundary.
- Cleaned root OSS metadata by restoring readable `AGENTS.md` contributor rules and replacing the mojibake `pyproject.toml` package description with an English package summary, with regression coverage for both files.
- Landed the Rust Pro foundation on `main` and opened `codex/pro-rust-product-core` for Pro implementation work.
- Added the first Pro product-core slice: richer shared Rust run/graph/evidence/challenge/source/usage payloads, `/api/runs`, `/api/runs/{run_id}`, `/api/runs/{run_id}/graph`, and a graph-first web shell that renders the richer payload.
- Added the next Pro product-core slice: owned Rust run payload strings, a `CreateRunRequest` builder, `POST /api/runs`, and process-local in-memory run storage so list/detail/graph reads share the same created-run state.
- Wired the graph-first Pro web shell to the Rust API create/list/detail/graph flow with a local create-run console, browser-side graph refresh from API payloads, and minimal local CORS support for the separate API/web ports.
- Added the next Pro product-core slice: shared provider/search quota ownership and cooldown status types, a keyless `GET /api/provider-status` endpoint, and a quota-routing panel in the graph-first web shell. This models managed Pro, workspace-managed, BYOK-later, user-evidence, and cooldown lanes without adding credentials or live provider calls.
- Added the next Pro graph-interaction slice: graph nodes are selectable, selected state stays browser-local, and the graph inspector shows the active node's confidence, evidence links, and challenge links.
- Added the next Pro run-store slice: `crates/run-store` provides a local JSON file-backed run-store boundary, the Pro API routes no longer hold a direct `HashMap`, and created runs survive API restarts through `RETROCAUSE_PRO_RUN_STORE_PATH` or the default `.retrocause/pro_runs.json`.
- Added the next Pro routing slice: `crates/provider-routing` turns keyless quota/cooldown status into a non-executing provider route preview, exposed through `POST /api/provider-route/preview` and `GET /api/provider-route/preview`.
- Added the next Pro queue-boundary slice: `crates/queue` creates in-memory preview-only execution jobs from routing-preview requests, exposed through `POST /api/execution-jobs`, `GET /api/execution-jobs`, and `GET /api/execution-jobs/{job_id}` without provider calls, credentials, billing, or worker execution.
- Added the next Pro web-shell slice: the graph-first Rust web app can now create preview-only queue jobs from the current run question, list queue jobs from the Pro API, and show selected lane plus execution-disabled state.
- Added the next Pro graph-review slice: inspector evidence/challenge links now focus the corresponding evidence-dock or challenge-strip item in the browser-local graph workspace.
- Added the next Pro executor-contract slice: preview-only queue jobs now expose a non-executing `work-order` payload with route steps, routing warnings, selected lane, and explicit safeguards for disabled provider execution, credential access, billing, and workers.
- Added the next Pro route-visibility slice: the graph-first web shell now fetches queued job work orders, auto-opens the route details after queueing a preview job, and renders route steps, routing warnings, selected lane, and safeguards without enabling provider execution.
- Added the next Pro worker-lifecycle slice: `crates/queue` now defines a non-executing hosted-worker lifecycle/failure-state contract, the Pro API exposes it through `GET /api/execution-lifecycle`, and the graph-first web shell renders a compact lifecycle/failure panel.
- Added the next Pro storage-boundary slice: `crates/run-store` now defines a no-connection hosted storage migration plan covering Postgres, Redis, tenant boundaries, and worker ownership; the Pro API exposes it through `GET /api/storage-plan`, and the web shell renders a compact storage-boundary panel.
- Added the next Pro provider-adapter contract slice: `crates/provider-routing` now defines dry request/result/degradation/quota/partial-result semantics, the Pro API exposes it through `GET /api/provider-adapter-contract`, and the web shell renders a compact adapter contract panel without enabling provider calls.
- Added the next Pro provider-adapter dry-run slice: `crates/provider-routing` now returns a keyless dry-run evidence/usage/degradation preview, the Pro API exposes it through `POST /api/provider-adapter/dry-run`, and the web shell can run it from the current graph question while keeping provider calls and billable usage disabled.
- Added the next Pro workspace/auth boundary slice: `crates/domain` now defines a non-enforcing workspace access context, the Pro API exposes it through `GET /api/workspace/access-context`, and the web shell renders preview permissions, gated future permissions, and auth safeguards without enabling real auth.
- Added the next Pro run-event/status slice: `crates/domain` now defines a non-durable run event timeline and status vocabulary derived from a `ProRun`, the Pro API exposes it through `GET /api/runs/{run_id}/events`, and the web shell renders a compact event timeline without adding an event store, workers, provider calls, or auth enforcement.
- Added the next Pro live-adapter candidate slice: `crates/provider-routing` now registers a gated OfoxAI model adapter candidate and gate-check payload, the Pro API exposes `GET /api/provider-adapter/candidates` and `POST /api/provider-adapter/gate-check`, and the web shell renders candidate/gate-check panels that keep live execution denied until auth, quota, dry-run, event, vault, and worker gates exist.
- Added the next Pro graph-review comparison slice: `crates/domain` now defines derived review-comparison payloads for evidence and challenge deltas, the Pro API exposes `GET /api/runs/{run_id}/review-comparison`, and the graph-first web shell renders a compact comparison panel without adding historical storage, auth enforcement, provider calls, or cross-workspace access.
- Added the next Pro credential-vault boundary slice: `crates/domain` now defines a keyless planned vault boundary, the Pro API exposes `GET /api/credential-vault-boundary`, and the graph-first web shell renders credential classes, access rules, and safeguards without accepting, storing, reading, logging, or returning provider credentials.
- Added the next Pro quota-ledger/billing boundary slice: `crates/domain` now defines a preview-only ledger/billing boundary, the Pro API exposes `GET /api/quota-ledger-boundary`, and the graph-first web shell renders quota lanes, metering rules, and safeguards without mutating ledger rows, connecting a payment provider, or emitting billable usage.
- Added the next Pro worker-lease/retry-scheduler boundary slice: `crates/queue` now defines preview-only worker lease, retry, and idempotency rules, the Pro API exposes `GET /api/worker-lease-boundary`, and the graph-first web shell renders lease rules, retry policies, and safeguards without starting workers, connecting a lease store, or enabling retries.

## Known Gaps

- The OSS product can now export a Markdown research brief, show retrieval-health states, reopen local saved runs, has a clean bilingual README, and has now passed a fresh clean-clone install/test smoke again after the latest README cleanup. This closes the first-run local-delivery gate for the current local alpha and is one input into the future non-alpha release bar.
- Degraded-source states now have deterministic API/brief regression coverage plus browser-level source-trace dogfood for representative rate-limited/cached rows; wider visual QA across all bad-path states remains useful.
- Direct monetization design should stay behind the Pro product core. The current Pro implementation is still a Rust foundation, not a hosted paid service.
- Provider-backed live Chinese finance validation has moved out of OSS and into the future hosted Pro line. The current OSS validation target is keyless local reviewability.
- The repository may still contain mojibake in legacy bilingual docs, test comments, and historical notes on Windows consoles, but the root README, `AGENTS.md`, package metadata, bundled demo data, provider labels, and current homepage/live-failure copy paths have now been cleaned or guarded by tests.
- Local browser/API E2E now verifies that the currently running backend exposes the current keyless provider catalog and does not expose OpenRouter as an active option.
- The API route module is still large even after the schema, uploaded-evidence route, saved-run route, provider route/preflight, live-failure V2 response, retrieval-trace V2 conversion, timeout, Markdown-brief, structured-analysis-brief, production-brief, production/product harness, production-scenario, provider-preflight, saved-run, and run-metadata helper extractions; streaming and the remaining main result-to-V2 conversion remain backend split candidates.
- Legacy canvas layout/state logic remains separate from the canonical homepage evidence board, but sticky-card rendering and red-string path math now reuse shared modules.

## Next Step

Continue Pro implementation on `codex/pro-rust-product-core`:

1. turn the derived review-comparison preview into a real cross-run selector only after durable run history and auth boundaries exist
2. add a result-commit/event-store boundary before any live adapter execution can persist provider outputs
3. keep the keyless OSS browser/API path stable and avoid changing OSS runtime unless a task explicitly asks for it
