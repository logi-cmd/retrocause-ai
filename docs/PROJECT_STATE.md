# Project State

Last updated: 2026-04-13

## Goal

RetroCause is a runnable, inspectable causal explanation product for "why did this happen?" questions. It should help users see reasons, sources, uncertainty, and gaps instead of a single opaque answer.

## Current Status

The OSS version is **published as an alpha prerelease**.

What is done:

- unified local app startup
- FastAPI + Next.js evidence-board workflow
- explicit demo / partial-live / live result labeling
- provider preflight harness for API key and model checks
- product value harness for whether a result is reviewable
- live US/Iran Islamabad talks golden-case validation with OpenRouter DeepSeek V3
- refreshed live golden-case screenshot under `docs/images/golden-us-iran-live-ui.png`
- automated validation through the root `npm test` command
- clean public GitHub repo published at `https://github.com/logi-cmd/retrocause-ai`
- GitHub prerelease `v0.1.0-alpha.2`

What is not done:

- stable `v0.1.0` release
- first-time OSS release polish beyond the current bilingual README
- export/share/report workflows that would make the product directly useful in repeated paid workflows

## Current Focus

Stabilize quality-first live evidence retrieval, especially for time-sensitive market/news queries where relative windows such as `today` and `yesterday` must not reuse stale evidence.

Current UX focus: make live analysis failures and thin outputs actionable through provider preflight and a result value harness.

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

## Blockers

- The product can explain and inspect causal evidence, but it does not yet package outputs into a report/share/export workflow that directly supports client, team, or market-intelligence monetization.

## Next Step

Post-release polish for the alpha: reduce first-run friction, clean remaining lint warnings, and design the report/share/export workflow that would create clearer repeated-use value.

Release-readiness pass from the user journey:

1. new GitHub visitor can install and launch without ambiguity
2. first live run has a clear preflight path
3. degraded output tells the user what to fix next
4. a strong output makes the reasons, evidence, counterpoints, and gaps obvious
5. docs state honestly that OSS is an inspectable alpha / release candidate, while Pro value would come from reliable repeated workflows and report/share/export depth
