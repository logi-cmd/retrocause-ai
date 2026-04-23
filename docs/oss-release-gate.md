# OSS Release Gate

Last updated: 2026-04-24

This document defines the bar for promoting RetroCause from a stable-deliverable local alpha to a non-alpha OSS `v0.1.0` release.

## Current Truth

- The latest public GitHub release is `v0.1.0-alpha.5`.
- There is **no** public `v0.1.0` tag or GitHub release yet.
- The project currently qualifies as a **stable-deliverable local OSS alpha** because:
  - the active workspace passes the full root `npm test` workflow, and
  - a fresh local copy also passed the documented install steps plus the full root `npm test` workflow on Windows on 2026-04-23.

That status is stronger than "alpha demo works", but weaker than "stable `v0.1.0` release shipped".

## Definitions

### Stable-deliverable local alpha

Use this label when all of the following are true:

1. `README.md` setup instructions work from a fresh local copy.
2. The root `npm test` workflow passes in the active workspace.
3. The root `npm test` workflow passes in a fresh local copy at least once after meaningful onboarding changes.
4. Demo mode, partial-live failure mode, and source-trace transparency remain honest.
5. Public docs do not promise hosted/Pro behavior that does not exist.

### Non-alpha OSS `v0.1.0`

Use this label only when the release gates below are explicitly satisfied and recorded.

## Mandatory Gates For `v0.1.0`

Every item below must be satisfied before creating a public non-alpha `v0.1.0` tag or GitHub release.

### 1. Local verification gate

- Pass the full root `npm test` workflow in the release workspace.
- Record the exact command and result in `.agent-guardrails/evidence/current-task.md`.

Status today: met for the current local alpha.

### 2. Fresh-copy onboarding gate

- From a fresh local copy, run the documented install steps from `README.md`.
- Then run the full root `npm test` workflow successfully.
- Repeat this after any meaningful onboarding, dependency, or startup-flow rewrite.

Status today: met for the current local alpha on Windows.

### 3. Provider-backed live validation gate

- Run at least one provider-backed live validation with real keys using the current recommended provider path.
- Include Chinese finance coverage because that path has been a recurrent regression hotspot.
- Record source quality, analysis mode, evidence count, source-trace quality, and reviewability outcome.
- If OpenRouter remains documented as a fallback path, confirm whether it still works well enough to keep in docs and UI.

Recommended path today:

- Primary: `OFOXAI_API_KEY` with the current default provider path
- Search layer: real Tavily and/or Brave keys
- Probe harness: `scripts/live_stability_probe.py`

Status today: not fully met. Source-layer smoke exists, but the provider-backed Chinese finance run still needs to be recorded after the current fast-path changes.

### 4. User-facing documentation gate

- `README.md` must describe only real public behavior.
- `docs/PROJECT_STATE.md` must match actual release status and known gaps.
- `docs/INDEX.md` must point contributors to the current source-of-truth docs.
- OSS vs future Pro wording must stay consistent.

Status today: met for the current local alpha after the 2026-04-24 sync.

### 5. Release-state consistency gate

- No document may claim `v0.1.0` shipped unless:
  - a `v0.1.0` tag exists, and
  - a matching public GitHub release exists.
- `docs/PROJECT_STATE.md`, `README.md`, release notes, and tags must agree.

Status today: not met, because `v0.1.0` has not been published.

### 6. Manual product smoke gate

- Run the representative scenarios in `docs/manual-smoke-test.md`.
- Include:
  - demo mode
  - partial-live / failure transparency
  - source trace visibility
  - Chinese A-share sample query flow
  - panel controls and narrow viewport behavior
- Record notable results or regressions in the evidence note.

Status today: partly met through automated E2E, but not yet freshly recorded as a dedicated manual release smoke for a non-alpha launch.

### 7. Release hygiene gate

- No tracked secrets, local runtime stores, or ignored cache artifacts are included.
- Release notes are prepared.
- The target tag exists only after the above gates pass.

Status today: alpha hygiene is acceptable, but the non-alpha release package has not been prepared.

## Evidence Required Before Tagging `v0.1.0`

Before tagging `v0.1.0`, the evidence note should include:

1. the exact `npm test` result for the release workspace
2. the exact fresh-copy install + `npm test` result
3. the provider-backed live probe result with real keys
4. manual smoke notes or links to saved artifacts
5. guardrails result for the release-prep change
6. any residual risks accepted for launch

## What This Document Prevents

This gate exists to stop three failure modes:

1. promoting "stable local alpha" into "stable release" without a real release package
2. letting docs drift into claiming `v0.1.0` shipped before the tag and release exist
3. calling the product ready without a real provider-backed live validation on the highest-risk query paths

## Next Release-Focused Actions

1. Run `scripts/live_stability_probe.py` with real provider/search keys and record the Chinese finance result.
2. Re-run a targeted manual release smoke using `docs/manual-smoke-test.md`.
3. If those pass, prepare the explicit `v0.1.0` release-prep change and re-run guardrails on that release branch or commit.
