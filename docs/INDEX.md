# RetroCause Documentation Index

Last updated: 2026-04-24

This index is the map for the tracked project documentation. It separates current operating docs from historical planning notes so new contributors do not have to infer the source of truth from file timestamps.

## Start Here

| Doc | Use it for | Status |
| --- | --- | --- |
| [`README.md`](../README.md) | Product overview, first-time setup, local API usage, OSS/Future Pro boundary | Current entry point |
| [`docs/PROJECT_STATE.md`](PROJECT_STATE.md) | Current shipped state, active focus, known gaps, next step | Current operating state |
| [`docs/oss-release-gate.md`](oss-release-gate.md) | Explicit bar for promoting the current local alpha into a non-alpha OSS `v0.1.0` release | Current release-state source of truth |
| [`AGENTS.md`](../AGENTS.md) | Required agent workflow, guardrails, verification definition | Current contributor/agent rules |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Local setup, validation commands, project structure, contribution expectations | Current contributor guide |

## Current Product And Architecture Docs

| Doc | What it covers | Notes |
| --- | --- | --- |
| [`docs/retrieval-and-output-strategy.md`](retrieval-and-output-strategy.md) | SourceBroker retrieval policy, source states, cache behavior, output contract | Current retrieval/output source of truth |
| [`docs/pro-workflow-spec.md`](pro-workflow-spec.md) | Future Pro workflow shape, explicitly deferred from current OSS alpha | Current boundary doc for future Pro |
| [`docs/pro-planning-kickoff.md`](pro-planning-kickoff.md) | First Pro planning entrypoint after OSS `v0.1.0`, including scope, workstreams, and required planning artifacts | Current Pro planning kickoff |
| [`docs/pro-prd.md`](pro-prd.md) | Product requirements draft for Solo Pro, including graph-first UX, scope, and success metrics | Current Pro kickoff PRD |
| [`docs/pro-rust-architecture.md`](pro-rust-architecture.md) | Rust workspace kickoff architecture for the separate Pro rewrite | Current Pro implementation starting point |
| [`docs/roadmap-and-limitations.md`](roadmap-and-limitations.md) | OSS strengths, limitations, roadmap, release-readiness heuristics | Strategic but partly historical |
| [`docs/operational-plan.md`](operational-plan.md) | Query classes, retrieval budgets, caching, source health, rate-limit strategy | Strategic operating plan |
| [`docs/mature-product-plan.md`](mature-product-plan.md) | Longer-term product quality contract and phased roadmap | Strategic, not an implementation promise |
| [`docs/oss-pro-positioning.md`](oss-pro-positioning.md) | OSS vs Future Pro positioning, target users, payment triggers, moat candidates | Strategic positioning |

## Audits, Checklists, And Smoke Tests

| Doc | What it covers | Notes |
| --- | --- | --- |
| [`docs/codebase-audit.md`](codebase-audit.md) | Current audit of undocumented capabilities and duplication/maintenance risks | Created for the 2026-04-17 documentation pass |
| [`docs/engineering-audit.md`](engineering-audit.md) | Older engineering audit, strengths, weak points, recommended sequence | Partly superseded by current state docs |
| [`docs/manual-smoke-test.md`](manual-smoke-test.md) | Manual browser/API smoke scenarios and real-analysis validation notes | Useful for release QA |
| [`scripts/live_stability_probe.py`](../scripts/live_stability_probe.py) | Repeatable keyless OSS stability probe for representative local/demo scenarios | Writes a secret-free JSON report |
| [`docs/PR_CHECKLIST.md`](PR_CHECKLIST.md) | Pull request review checklist | Lightweight checklist |

## Decision And Reference Records

| Doc | What it covers | Notes |
| --- | --- | --- |
| [`docs/DECISIONS.md`](DECISIONS.md) | Chronological technical/product decisions | Large historical log |
| [`docs/references.md`](references.md) | Papers, causal frameworks, and implementation references | Research reference |
| [`STATE.md`](../STATE.md) | Older session-state notes through 2026-04-10 | Historical, superseded by `docs/PROJECT_STATE.md` |

## Growth And Market Docs

| Doc | What it covers | Notes |
| --- | --- | --- |
| [`docs/open-source-growth-strategy.md`](open-source-growth-strategy.md) | GitHub/open-source growth strategy | Strategic |
| [`docs/market-analysis-overseas-c.md`](market-analysis-overseas-c.md) | Overseas consumer market analysis and commercialization framing | Strategic, partly historical |

## Implementation Plans And Specs

| Doc | What it covers | Notes |
| --- | --- | --- |
| [`docs/superpowers/plans/2026-04-14-production-brief-harness.md`](superpowers/plans/2026-04-14-production-brief-harness.md) | Executed Production Brief Harness plan | Historical implementation plan |
| [`docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`](superpowers/plans/2026-04-15-sourcebroker-plan.md) | Executed SourceBroker reliability plan | Historical implementation plan |
| [`docs/superpowers/specs/2026-04-12-frontend-analyst-desk-design.md`](superpowers/specs/2026-04-12-frontend-analyst-desk-design.md) | Frontend analyst desk design direction | Historical design spec |
| [`docs/superpowers/specs/2026-04-13-harness-value-design.md`](superpowers/specs/2026-04-13-harness-value-design.md) | Provider preflight and product value harness design | Historical design spec |
| [`docs/superpowers/specs/2026-04-14-production-brief-harness-design.md`](superpowers/specs/2026-04-14-production-brief-harness-design.md) | Production Brief Harness design | Historical design spec |

## Frontend-Specific Docs

| Doc | What it covers | Notes |
| --- | --- | --- |
| [`frontend/UI_DESIGN_SPEC.md`](../frontend/UI_DESIGN_SPEC.md) | Original frontend design system and interaction spec | Partly stale against the current evidence-board UI |
| [`frontend/AGENTS.md`](../frontend/AGENTS.md) | Next.js-specific agent warning | Current local instruction |
| [`frontend/CLAUDE.md`](../frontend/CLAUDE.md) | Empty or placeholder Claude context | Low value until filled |
| [`frontend/README.md`](../frontend/README.md) | Frontend dev notes, local UI run path, key files, validation commands | Current frontend-specific guide; root `README.md` remains setup source of truth |

## Local-Only Private Docs

The repository ignores `docs-private/`. If present locally, treat it as private planning material and do not link it as a public source of truth. Public OSS guidance should live in tracked docs under `docs/`.

## Maintenance Rules

- Update `docs/PROJECT_STATE.md` when shipped behavior, release status, known gaps, or next steps change.
- Update `README.md` when first-time setup, public API usage, or user-visible capability changes.
- Update `docs/retrieval-and-output-strategy.md` when retrieval routing, source policy, cache, or output contract changes.
- Update `docs/codebase-audit.md` after any substantial refactor, new product surface, or duplicate-code cleanup.
- Keep future Pro language in `docs/pro-workflow-spec.md` and `docs/oss-pro-positioning.md`; do not imply hosted Pro is available in the OSS alpha.
