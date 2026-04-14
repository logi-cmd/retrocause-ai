# RetroCause OSS Roadmap and Limitations

## Current OSS Strengths

- evidence-backed causal explanation pipeline
- competing hypothesis chains
- counterfactual summary support
- FastAPI backend with `/api/analyze/v2`
- browser-based evidence-board UI
- multi-hop causal tracing in the frontend
- unified local startup via `python start.py`
- independent pipeline evaluation step (evidence sufficiency, probability coherence, chain diversity)
- LLM call retry with exponential backoff
- config-driven request timeout
- 148 automated tests (unit + integration + comprehensive boundary + CausalRAG / uncertainty / citation)
- API smoke test (38/38 PASS) and UI smoke test (21/21 PASS, Playwright/Chromium)
- real data sources: ArXiv, Semantic Scholar, DuckDuckGo (all live HTTP, not stubs)
- topic-aware demo fallback (SVB, stock, crisis, rent, default)
- explicit demo vs real analysis labeling across browser UI, API, and Streamlit
- graph-guided retrieval / CausalRAG second pass for thin-coverage graph regions
- span-level citation grounding on edges
- structured uncertainty report (per-node / per-edge) and evidence conflict classification
- homepage evidence filtering by source / stance / confidence
- homepage chain comparison snapshot and richer right-panel rendering for live API evidence
- Evidence Access Layer for query planning, source brokering, multi-source aggregation, evidence quality ordering, short-lived caching, source cooldown, and API/UI retrieval trace transparency
- provider preflight harness that checks whether the selected provider key/model can return valid JSON before spending a full run
- product value harness that tells users whether a result is reviewable, evidence-backed, challenged, or blocked by model/provider setup

## Current OSS Completion Status

The OSS version is **alpha-complete for local demonstration and inspection**, and now has one live golden-case validation:

- it can be installed locally
- it can start the backend and frontend together
- it can show demo, partial-live, and live states honestly
- it can run the evidence-board workflow end to end
- it has automated coverage through the root `npm test` path
- the 2026-04-13 US/Iran Islamabad talks golden case passed with OpenRouter DeepSeek V3 as a non-demo live result

It is **not yet release-complete as a polished public OSS launch** until release packaging is done:

- first-run onboarding should be reviewed once more as if the user has never seen the project
- release notes, tag/commit, and known-limit messaging should be finalized
- the output still needs report/share/export packaging before it has obvious direct monetization value for repeated client, market-intelligence, or strategy workflows

## Current Limitations

### 1. Demo fallback is still important

Without a configured real model / evidence collection path, the browser or Streamlit experience can fall back to demo data.

This is now **explicitly labeled in the UI**, the homepage can call `/api/analyze/v2` directly, and Browser UI users can supply a local API key, but it still means:

- not every user query yields a truly query-specific causal chain
- the OSS demo is reliable for interaction testing, not guaranteed real analysis quality
- evidence coverage, confidence, and uncertainty should be treated as guidance signals rather than proof of causal truth

### 2. Real-time streaming is not finished

The pipeline does not yet stream intermediate reasoning into the browser in a polished way.

### 3. Debate visualization is still early

The debate / multi-agent reasoning view is present, but still less mature than the main chain / graph / right-panel experience.

### 4. Browser automation environment may vary

Automated browser QA depends on local Chrome / Playwright availability.

### 5. Product polish is still ongoing

The current OSS is a strong demoable alpha, not a production-grade end-user application.

### 6. The release bar is higher than “demo works”

The OSS version should not be published just because the main demo flow looks good.

Before public release, the project should also have:

- setup clarity (`.env.example`, clear provider expectations)
- honest fallback behavior across browser UI and CLI
- coherent docs and route structure
- a stable main workflow that does not feel partially stitched together

### 7. Future Pro value depends on trust and workflow depth

The likely Pro opportunity is not “more AI output.”

It is:

- better real-analysis quality
- better explanation reuse and comparison workflows
- stronger team / report / stakeholder communication outputs
- domain-specific higher-trust workflows where being wrong is costly

### 8. Direct monetization needs a packaged workflow

The current OSS product helps users inspect causal explanations, but direct monetization usually requires an output that can be reused in a business workflow.

The most credible near-term wedge is not generic "why answers." It is a repeatable brief/report workflow for users who need to explain market, policy, geopolitical, or competitive events to themselves first, and then to other people.

The OSS/Pro boundary should be:

- **OSS:** copyable Markdown research brief for individual judgment, personal research notes, policy/market/geopolitical analysis, and transparent review.
- **Pro:** hosted, scheduled, team-ready, client-ready delivery workflows with PDF/DOCX, saved comparisons, branded templates, source policy controls, and operational reliability.

To support that, the product still needs:

- a clear Markdown research brief output format in OSS
- Pro-grade export/share/report generation
- saved comparison runs or reusable templates
- stronger source reliability defaults for the chosen vertical
- clear confidence, gaps, and counterpoint sections that a user can forward without rewriting

## Near-Term Roadmap

### P0.5 - Finish public OSS release readiness

- select a preflight-passing OpenRouter model for the default live demo path ✅
- re-run the US/Iran Islamabad talks golden case through API and browser UI ✅
- confirm the final output includes source trace, analysis brief, challenge coverage, and `product_harness` status ✅
- refresh screenshots and public docs after that golden case ✅
- document one "good output" example and one "blocked/degraded output" example so users know what the system can and cannot currently do

### P0 — Reach the minimum usable OSS release bar ✅

- add `.env.example` and clarify required / optional provider configuration ✅
- add `LICENSE` file to match the MIT declaration already present in metadata ✅
- make CLI fallback behavior honest when no real analysis is available ✅
- resolve confusing dead paths / route references (for example old console expectations) ✅
- ensure README / CONTRIBUTING / issue templates describe the actual current product and ports ✅

### P1 — Make real analysis mode clearer ✅

- show stronger distinction between real analysis and demo mode ✅
- allow local Browser UI key entry while keeping trust-preserving copy ✅
- unify `is_demo` / `demo_topic` signaling across Browser UI, API, CLI, and Streamlit ✅
- surface model / source availability in the UI ✅
- surface evidence coverage / support-vs-refutation balance ✅

### P1.5 — Engineering hardening ✅

- HookEngine wired into Pipeline.run() ✅
- Pipeline step error isolation (try/except) ✅
- LLM call retry with exponential backoff ✅
- Config timeout passed to OpenAI client ✅
- Independent evaluation step (generator/evaluator separation) ✅
- Evaluation data surfaced in API V2 response ✅

### P1.6 — CI and release infrastructure ✅

- GitHub Actions CI (ruff + pytest + frontend build) ✅

### P2 — Improve node and evidence workflows

- evidence filtering by source / support / confidence ✅
- better chain comparison workflows (homepage compare snapshot) ✅
- stronger edge explanation affordances ✅
- richer right-panel rendering of real API evidence pools ✅

### P3 — Strengthen query-specific fallback behavior ✅

- move from generic demo chain fallback toward topic-aware or query-shaped demo responses ✅

### P4 — Better OSS onboarding

- add screenshots / GIFs ✅
- add issue templates ✅
- add contributor setup notes ✅

### P5 — Deeper reasoning fidelity

- stronger intervention math
- richer sensitivity analysis
- more robust evidence grounding and uncertainty communication
- clearer failure states so the product never overstates confidence when real analysis is weak
- evaluate groundedness / factual consistency metrics with tools such as RAGAS / TruLens / FCS-style scoring

### P5.5 — Frontier techniques that fit OSS

- add citation-grounded outputs so chains and edges can point back to evidence more explicitly ✅
- add support-vs-refutation balance and provenance completeness into the evaluation layer ✅
- add lightweight graph-guided retrieval / CausalRAG-style retrieval on top of the existing pipeline and optional vector store ✅
- add uncertainty communication that distinguishes thin evidence, conflicting evidence, and low-confidence reasoning ✅
- add reasoning-trace summaries only where they improve inspectability without pretending to expose ground-truth model cognition

### P6 — Shape the future Pro tier around real jobs-to-be-done

- keep the OSS wedge useful: evidence board plus copyable Markdown research brief
- identify one repeated workflow where explanation quality is materially more valuable than generic chat answers
- build Pro-grade comparison / report / stakeholder-facing workflows
- invest in trust-preserving domain packs before broad feature expansion

## Not planned for OSS by default

The following directions are intentionally treated as **Pro-first** unless the OSS mission changes:

- persistent workspaces and saved analysis history
- shareable report workflows for teams / clients / stakeholders
- PDF / DOCX / branded report generation
- scheduled or monitored briefing runs
- streaming-first long-running analysis UX
- strong provenance ledger / audit trail for repeated operational use
- heavy multi-agent orchestration as a core product promise
- domain packs designed for high-stakes repeated workflows
- infrastructure changes whose main value is operating scale rather than OSS inspectability

## Release Readiness Heuristic

The current OSS is suitable for:

- GitHub demos
- architecture inspection
- interface testing
- early user feedback

It is not yet suitable for:

- guaranteed real-world causal correctness
- production decision support
- claims of validated causal inference at scientific or enterprise reliability levels

## OSS vs Pro Heuristic

OSS should provide the full product idea clearly:

- evidence-backed why-question exploration
- competing chains
- explicit uncertainty and demo labeling
- a usable evidence-board interface
- copyable Markdown research brief output

Pro should justify payment by improving workflow outcomes:

- higher-trust real analysis
- better explanation comparison and reuse
- stronger scenario / intervention workflows
- outputs that help users explain causality to teams, clients, or decision-makers
- hosted operation, scheduled runs, team sharing, source policy controls, and branded deliverables

The operational policy for rate-limit resilience, caching, concurrency budgets, and source tiers now lives in [`docs/operational-plan.md`](./operational-plan.md) so roadmap decisions can stay aligned with real operating constraints.

The broader product and OSS/Pro strategy for quality-first operation now lives in [`docs/mature-product-plan.md`](./mature-product-plan.md).

## OSS vs Pro architecture heuristic

- **OSS** keeps the current Python + FastAPI + Next.js stack and should prioritize visible quality, explicit limits, and contribution friendliness.
- **Pro** may diverge into a separate Rust full-stack runtime where the payoff is in strong typing, streaming workflows, graph/runtime performance, shared models, and operational cost.
- Rust should not be treated as the magic source of better causal correctness. Better correctness should mostly come from stronger evaluation, evidence grounding, calibration, and refutation patterns.
