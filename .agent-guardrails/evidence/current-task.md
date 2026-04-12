# Current Task Evidence

## Task

Fix the frontend causal canvas so sticky notes are not clipped by the bottom overlay and can use the available canvas height, including upward dragging in low-height viewports.

## Files Touched

- `package.json`
- `frontend/src/app/page.tsx`
- `scripts/e2e_test.py`
- `README.md`
- `docs/manual-smoke-test.md`
- `docs/superpowers/specs/2026-04-12-frontend-analyst-desk-design.md`

## Root Cause

- Sticky note coordinates are stored relative to `.main-canvas`, but the layout and drag bounds mixed canvas-relative coordinates with viewport/header-relative bounds.
- The bottom drag guard used an estimated note height instead of the rendered card height, so real cards could still be clipped in short viewports.

## Changes

- Made layout bounds canvas-relative and reserved only a compact bottom safe area.
- Used rendered sticky-card height during drag bound calculation.
- Spread multi-row layouts across the usable canvas height instead of clustering the top row too low.
- Kept zoom, panel collapse, and bottom-drag E2E coverage aligned with the updated UI.

## Commands Run

- `npm test`
  - Result: initially failed because root `package.json` had no `test` script; fixed by adding a root aggregate test script.
  - Final result: passed.
- `cmd /c npm.cmd run lint` from `frontend`
  - Result: passed with existing warnings in unrelated files.
- `cmd /c npm.cmd run build` from `frontend`
  - Result: passed.
- `ruff check retrocause/`
  - Result: passed.
- `pytest tests/ --basetemp=.pytest-tmp`
  - Result: 191 passed.
- `python scripts\e2e_test.py`
  - Result: 604 passed, 0 failed, 0 skipped.
- Low-height Playwright measurement at `1675x768`
  - Result: bottom cards kept approximately 46.8px and 54.8px visible bottom gap; drag-up reached approximately top 83.3px; drag-down kept approximately 46.7px bottom gap.

## Residual Risks

- Root `npm test` is now available and maps to the practical validation path: frontend lint/build, Python ruff/pytest, and the custom E2E script.
- The generated guardrails task contract has mojibake in the task text, but the guard rules and required command were still captured and followed as far as the repository allowed.
- Frontend lint still reports 7 existing warnings in unrelated component files; no lint errors were reported.
