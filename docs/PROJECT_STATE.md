# Project State

Last updated: 2026-04-16

## Goal

RetroCause is a runnable, inspectable causal explanation product for "why did this happen?" questions. It should help users see reasons, sources, uncertainty, and gaps instead of a single opaque answer.

## Current Status

The OSS version is **published as an alpha prerelease** and the SourceBroker retrieval reliability pass is implemented locally.

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
- GitHub prerelease `v0.1.0-alpha.4`
- SourceBroker reliability pass: source profiles, scenario/language/time-aware cache keys, degraded-source classification, API/brief/UI source-health status, and optional user-key Tavily/Brave adapters

What is not done:

- stable `v0.1.0` release
- first-time OSS release polish beyond the current bilingual README and alpha prerelease
- Solo Pro / Team Lite hosted workflows that would make the product directly useful in repeated paid workflows

## Current Focus

Stabilize quality-first live evidence retrieval, especially for time-sensitive market/news queries where relative windows such as `today` and `yesterday` must not reuse stale evidence.

Current UX focus: validate the general Production Brief Harness across real market, policy/geopolitics, and postmortem questions. OSS now supports scenario-aware single-run briefs with freshness/source-quality gating; Pro workflow depth should focus on individuals and small teams: run queues, quota management, cache reuse, saved runs, uploaded evidence, scheduled watch topics, PDF/DOCX export, and lightweight team review. Enterprise private deployment is not a near-term target.

Current planning status: the Production Brief Harness implementation plan is saved at `docs/superpowers/plans/2026-04-14-production-brief-harness.md` and has been executed through code, frontend, export, and regression cleanup. The retrieval/output strategy is captured in `docs/retrieval-and-output-strategy.md`. The SourceBroker reliability implementation plan is saved at `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md` and has been executed through documentation/full verification.

## Working Rules

- Keep project documentation synchronized with every behavior, API, UI, or pipeline change. At minimum, update the current task evidence note; when user-visible behavior changes, also update README or the relevant docs page.

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

## Blockers

- The OSS product can now export a Markdown research brief and show retrieval-health states, but the brief format still needs real-user polish across more live domains.
- Degraded-source states now have deterministic API/brief regression coverage, but the remaining gap is visual/browser dogfood of those bad-path states in the right-side source trace.
- Direct monetization should stay Pro-oriented but lightweight: hosted operation, run queues, quota management, cache reuse, uploaded evidence, saved runs, PDF/DOCX, scheduled watch topics, lightweight team review, source controls, and saved comparisons.

## Next Step

Run visual/browser dogfood for degraded-source states, then decide whether the next implementation slice should be lightweight run orchestration, uploaded evidence, or saved-run history.

Release-readiness pass from the user journey:

1. new GitHub visitor can install and launch without ambiguity
2. first live run has a clear preflight path
3. degraded output tells the user what to fix next
4. a strong output makes the reasons, evidence, counterpoints, and gaps obvious
5. docs state honestly that OSS is an inspectable alpha / release candidate, with Markdown research brief export planned for OSS and higher-end report/share/team depth reserved for Pro
