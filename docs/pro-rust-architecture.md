# RetroCause Pro Rust Architecture

Last updated: 2026-04-24

## Why a separate Rust workspace

The OSS Python/FastAPI + Next.js app remains the inspectable local product. Pro needs a different runtime shape: queueable jobs, durable run records, explicit quota ownership, and more controlled latency under provider pressure. That is a good fit for a separate Rust codebase rather than accreting hosted concerns into the OSS stack.

The Rust rewrite lives under `pro/` inside this repository so the product and architecture can evolve in the open without destabilizing OSS runtime paths.

## Current architecture goals

1. Establish a clean Rust workspace boundary.
2. Define shared Pro domain types around graph-first runs, evidence anchors, challenge checks, source health, usage ledger entries, provider quota ownership, and cooldown state.
3. Stand up API endpoints that expose run summaries, run detail, graph payloads, file-backed local run creation, keyless provider/search quota status, routing previews, and preview-only execution jobs.
4. Render a graph-first web shell from the same shared Rust payload and wire it to the local API create/read flow plus provider-status view.
5. Keep Pro separate from the OSS Python/FastAPI + Next.js runtime.

## Workspace layout

```text
pro/
  Cargo.toml
  apps/
    api/
    web/
  crates/
    domain/
    provider-routing/
    queue/
    run-store/
```

## Stack choice

### API

- `axum`
- `tokio`
- `serde`

Reason: small, explicit, good fit for future queue, cache, and run-record services.

### Web

- `axum`
- `maud`
- shared Rust domain crate

Reason: the first Pro shell wants a graph-first surface that compiles quickly and keeps the Rust web path simple. Server-rendered HTML gives us a real interface immediately without committing to a WASM/hydration stack too early.

This is a deliberate tradeoff:

- good now: faster iteration, fewer moving parts, easier first compile/test path
- deferred: richer client-side graph interaction, drag behavior, zoom state persistence, incremental hydration

If the graph workspace proves out, the next phase can move the web shell toward Leptos or another Rust-heavy client strategy without changing the domain model or API boundary.

## Shared domain

The first shared crate now defines:

- a `ProRun` payload
- run summaries
- graph nodes
- graph edges
- evidence anchors
- challenge checks
- source status cards
- usage ledger entries
- provider/search quota ownership entries
- source cooldown state
- verification steps
- an owned `CreateRunRequest` builder for process-local alpha run creation
- a canonical seed run used by both the API and the web shell

This keeps the API and web kickoff honest: they render the same shape instead of drifting into two separate demos.

## Run store boundary

`crates/run-store` is the first Pro storage boundary. It currently provides a local JSON file-backed `FileRunStore` around `ProRun` records.

Current behavior:

- default path: `.retrocause/pro_runs.json`
- override: `RETROCAUSE_PRO_RUN_STORE_PATH`
- first open seeds the canonical sample run
- created runs are written to disk and survive API process restarts
- the API no longer owns raw `HashMap` or sequence state directly

This is intentionally an alpha local store. It is not encrypted storage, not a multi-tenant database, not a credential vault, and not the final hosted Pro persistence layer. The value is the boundary: future Postgres-backed storage should replace this crate's implementation without forcing the API routes to own storage details again.

## Provider routing boundary

`crates/provider-routing` is the first Pro provider/source routing boundary. It currently produces a route preview plan from the static keyless provider-status payload.

Current behavior:

- input: workspace id, query, optional scenario, optional source policy
- output: preview-only route plan with lane decisions, cooldown hints, selected local lane, and warnings
- execution: always disabled in this slice
- selected local fallback: uploaded-evidence lane when the source policy allows it
- explicit blocked/deferred lanes: managed Pro model pool, workspace search, BYOK-later search, and market-search cooldown

This is intentionally not a provider executor. It does not read provider keys, call models/search APIs, enqueue jobs, bill usage, or store credentials. The value is the decision vocabulary: future executors can consume the same lane and decision semantics instead of inventing hidden routing behavior inside provider adapters.

## Queue boundary

`crates/queue` is the first Pro execution-queue boundary. It currently provides an in-memory `ExecutionQueue` that turns a routing-preview request into a preview-only execution job.

Current behavior:

- input: the same workspace id, query, scenario, and source policy accepted by provider-routing preview
- output: execution job payload with id, workspace id, query, preview-only status, selected lane, and the full route plan
- storage: process-local memory only
- execution: always disabled in this slice

This is intentionally not a worker system. It does not read provider keys, call models/search APIs, persist queue state, bill usage, enforce tenant quotas, or schedule background work. The value is the API and state boundary: future Redis/Postgres-backed queue workers should replace the in-memory implementation without making API routes own job sequencing or route-plan coupling.

## Near-term service split

### `apps/api`

Initial responsibility:

- health endpoint
- seed graph endpoint retained for compatibility
- `GET /api/runs`
- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/graph`
- `GET /api/provider-status`
- `GET /api/provider-route/preview`
- `POST /api/provider-route/preview`
- `GET /api/execution-jobs`
- `POST /api/execution-jobs`
- `GET /api/execution-jobs/{job_id}`
- minimal local CORS headers for the separate Pro web port
- local JSON run storage through `crates/run-store`, shared by list/detail/graph reads and surviving API restarts
- local preview-only queue jobs through `crates/queue`, shared by list/detail reads while the API process is running
- future home for durable run status, queue control, provider routing, cooldown buckets, and saved-run access

The current store is intentionally local-file-backed. It is useful for proving the API behavior, graph payload contract, and restart continuity, but it should not be treated as the hosted Pro data layer. The provider-status, provider-route preview, and execution-job endpoints are static/keyless in this slice: they model ownership, cooldown, routing semantics, and queue shape without exposing credential fields or calling real providers. The CORS behavior is local-alpha plumbing for `127.0.0.1` API/web development, not a production auth or permission boundary.

### `apps/web`

Initial responsibility:

- render the graph-first Pro workspace
- visualize the canonical run, including evidence anchors, challenge checks, source health, and usage ledger state
- create new in-memory runs through `POST /api/runs`
- reload run summaries, run detail, and graph payloads from the Pro API
- show provider/search quota ownership, credential policy, and cooldown status through the local provider-status payload
- create and list preview-only execution jobs through the local execution-job API
- keep a browser-local selected-node state and graph inspector for evidence/challenge links, including focused evidence/challenge review items
- establish layout, palette, and information hierarchy for the knowledge-graph experience

## Future crates after the kickoff

- `crates/export`
- `crates/evidence-store`

`crates/run-store`, `crates/provider-routing`, and `crates/queue` exist today. The other crates are intentionally not created yet; each should appear only when it removes real duplication or isolates a concrete boundary.

## Operational architecture direction

### Planned control plane

- Postgres for durable runs, evidence metadata, exports, and quota ledger
- Redis for queue coordination, cooldown state, and rate-limit buckets
- Worker processes for retrieval, extraction, graph synthesis, export, and scheduled reruns

### Run lifecycle direction

- `queued`
- `running`
- `cooling_down`
- `partial_live`
- `needs_followup`
- `ready_for_review`
- `blocked`

### Key ownership direction

- managed Pro quota
- workspace-managed quota
- BYOK
- uploaded-evidence only / local-only data

Those semantics should remain explicit in both API payloads and the graph workspace UI.

The current `POST /api/runs` path uses `queued` runs and managed/user-provided quota labels without calling model or search providers. The current `GET /api/provider-status` path exposes static ownership lanes for managed Pro quota, workspace-managed search quota, BYOK-later search, uploaded-evidence-only input, and an example market-search cooldown bucket. The current `POST /api/execution-jobs` path records a preview-only queue job from the routing plan but still does not execute providers. Live provider credentials, BYOK storage, workspace quotas, real cooldown enforcement, and real worker execution remain future work.

## Knowledge-graph UI direction

The Pro UI should feel like a graph command room, not a generic SaaS dashboard and not a direct carry-over from the OSS evidence board.

- dark, calm, editorial surfaces
- graph canvas as the largest area
- supporting detail revealed through overlays, trays, and inspectors instead of inherited side rails
- visible source states and challenge status
- no gradient-heavy AI dashboard styling

The kickoff web shell encodes that direction with a graph workspace that now supports browser-local node selection, an inspector for the active node's evidence/challenge links, focused evidence/challenge review items, provider quota status, and preview-only execution-job status. Advanced interaction such as persisted layout state, graph editing, multi-select, and review workflows remains later work.

The current web shell is still intentionally lightweight: server-rendered HTML plus a small browser script for local API calls and DOM refresh. It is enough to prove the Pro run loop without committing to the eventual interactive graph client stack.

## Verification for this kickoff

- `cargo test --manifest-path pro/Cargo.toml`

That is enough for the kickoff because there is no deployment pipeline, persistence layer, or browser runtime yet.

The in-memory run-creation slice also uses:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`

The web/API wiring slice additionally uses a local browser smoke that starts `retrocause-pro-api.exe` and `retrocause-pro-web.exe`, submits the web create-run form, and verifies that the page reloads the API graph payload for the created run.

The provider-status slice adds focused unit coverage under:

- `cargo test --manifest-path pro/Cargo.toml`

The tests assert that quota ownership remains explicit, the static cooldown bucket is visible, and provider-status payloads do not contain API-key or secret-shaped fields.

The graph-interaction slice adds the same Rust test command plus a Playwright smoke that clicks a graph node and verifies that the inspector switches to the selected node while keeping only one node selected.

The run-store slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API restart smoke with `RETROCAUSE_PRO_RUN_STORE_PATH` proving a created run can be read after the API process restarts

The provider-routing slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/provider-route/preview` proving the response stays `preview_only`, does not allow execution, includes five lane decisions, and selects only the local uploaded-evidence lane

The queue-boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/execution-jobs`, `GET /api/execution-jobs`, and `GET /api/execution-jobs/{job_id}` proving created jobs stay preview-only, do not allow execution, and expose the selected local routing lane

The queue-status web slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- a browser smoke that starts the Pro API and web shell, clicks `Queue preview job`, and verifies that the execution queue panel shows a `job_local_*` preview job with execution off

The graph-review focus slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- a browser smoke that clicks an inspector evidence link and verifies that the corresponding evidence item receives browser-local focus state
