# Current Task Evidence

## Task

Fix the OSS homepage flashing reported by the user. Keep the OSS local alpha behavior unchanged and remove only the continuous visual flash from the homepage header status indicator.

## Scope

- `frontend/src/app/page.tsx`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

## What Changed

- Confirmed the OSS checkout was on clean `main` before this fix, not on the Pro PR branch.
- Diagnosed the running OSS homepage with Playwright before editing. The only continuous animation was `pulse` on a 6x6 header status `span` with inline `animation: "2s infinite pulse"`.
- Removed `animation: "pulse 2s infinite"` from the header status dot in `frontend/src/app/page.tsx`.
- Removed the now-unused page-local `@keyframes pulse` definition from `frontend/src/app/page.tsx`.
- Replaced the stale Pro durability-gate guardrails contract with a narrowed OSS flicker-fix contract.
- Did not change backend/API/provider/worker/quota/billing behavior and did not touch Pro files.

## Commands Run

- Read-before-edit context:
  - `Get-Content AGENTS.md -TotalCount 220`
  - `Get-Content docs\PROJECT_STATE.md -TotalCount 220`
  - `Get-Content README.md -TotalCount 180`
  - `Get-Content pyproject.toml -TotalCount 180`
  - `Get-Content .agent-guardrails\task-contract.json -TotalCount 240`
  - targeted reads of `frontend\src\app\page.tsx`

- Baseline state and diagnosis:
  - `git status --short --branch`
    - Result: `## main...origin/main`
  - `Get-NetTCPConnection -LocalPort 3005 -State Listen`
    - Result: Next frontend process was already listening on port `3005`.
  - Playwright pre-fix smoke on `http://127.0.0.1:3005`
    - Result: page title was `RetroCause — Evidence-Backed Causal Explorer`.
    - Result: exactly one running continuous animation was observed: `pulse` on a header `SPAN`, duration `2000`, infinite iterations, inline animation `"2s infinite pulse"`.
    - Result: console errors `0`.

- Guardrails planning:
  - `agent-guardrails plan --task "Fix the OSS homepage flashing status indicator by removing the continuous pulse animation from the keyless local alpha header, keeping behavior and status copy unchanged, limiting product changes to frontend/src/app/page.tsx plus guardrails evidence, and not touching Pro/backend/API/provider/worker/quota/billing behavior."`
  - Result: the automatic detector inferred an over-broad bugfix scope that included docs, backend files, and `pro/target` build artifacts. I did not accept it. The contract was manually narrowed to the actual OSS homepage animation fix.

- Source search:
  - `Get-ChildItem -Path frontend\src -Recurse -Include *.tsx,*.css | Select-String -Pattern "pulse"`
  - Result before fix: found `frontend\src\app\page.tsx` status-dot animation and page-local keyframes.
  - Result after fix: no remaining `pulse` references in `frontend\src\app\page.tsx`; unrelated `gentlePulse`/selected glow CSS and a separate layout header `animate-pulse` remain outside this page scope.

- `npm --prefix frontend run lint`
  - Result: passed.

- `npm --prefix frontend run build`
  - Result: passed.
  - Next.js compiled successfully, TypeScript finished, and the root route prerendered.

- Browser smoke:
  - First Playwright attempt against existing `http://127.0.0.1:3005` timed out waiting for `networkidle`; follow-up attempts saw navigation context churn, likely from the existing production process after the local build.
  - Started a temporary independent production frontend on port `3015` with `npm --prefix frontend run start -- -p 3015`.
  - Playwright opened `http://127.0.0.1:3015`.
  - Result: HTTP status `200`.
  - Result: title `RetroCause — Evidence-Backed Causal Explorer`.
  - Result: animation count `17`, infinite animation count `0`.
  - Result: console errors `0`.
  - Result: horizontal overflow `false`.
  - Result: external runtime requests `0`.
  - Stopped the temporary port `3015` process tree after the smoke.

- `git diff --check`
  - Result: passed.
  - Git emitted expected CRLF conversion warnings for touched text files only.

## Risk / Tradeoff Notes

- This removes the continuous flash from the OSS homepage header status dot while keeping finite entrance/string drawing animations intact.
- The separate `frontend/src/components/layout/Header.tsx` `animate-pulse` usage was not changed because it is outside the active homepage page file and was not the animation observed on the reported OSS page.
- No backend, API, Pro, provider, worker, quota, or billing behavior changed.

## Observability

- No production metrics, logging, tracing, telemetry, or runtime monitoring hooks were added or changed.
- The observable acceptance signal for this UI-only fix is browser-level animation inspection:
  - Pre-fix Playwright observation: one infinite `pulse` animation on the homepage header status `SPAN`.
  - Post-fix Playwright observation: infinite animation count `0` on the production-built OSS homepage.

## Remaining Risks

- The already-running port `3005` process may need a browser refresh or process restart to pick up the rebuilt static asset immediately in an existing tab.
- The repository still contains unrelated historical mojibake in some docs visible through Windows console output; this task did not change documentation text outside guardrails evidence.
