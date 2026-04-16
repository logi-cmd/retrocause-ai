# RetroCause Pro Workflow Spec

## Purpose

RetroCause OSS proves the inspectable core: a user can ask why an event happened, inspect causal chains, review evidence, check challenge coverage, and copy a Markdown research brief.

RetroCause Pro should monetize the repeated workflow around that core for individuals and small teams. The paid value is not "more AI text." The paid value is faster trusted delivery, saved context, uploaded evidence, source reliability, stakeholder-ready outputs, and operating reliability for people who must explain events more than once.

Pro is not an enterprise private-deployment product in the near term. Enterprise deployment, SSO, document-level ACLs, custom connectors, and data-residency commitments should remain out of scope unless a concrete paid customer justifies that maintenance burden.

## Target Users

- Independent researchers, creators, and analysts who need source-backed briefs without rebuilding the same workflow for every event.
- Market, policy, geopolitical, and startup operators who need to explain price, policy, supply-chain, competitor, or incident events.
- Solo consultants, small funds, research studios, and small teams that need repeatable written explanations for colleagues or clients.
- Builders and researchers who want the OSS inspectability locally, then need hosted runs, saved history, uploaded evidence, and export workflows.

## Jobs To Be Done

- "When a market, policy, or geopolitical event happens, help me quickly produce a source-backed causal brief I can review and forward."
- "When new evidence arrives, help me compare what changed from the previous explanation."
- "When I need to brief a team or client, help me package reasons, evidence, counterpoints, and caveats without rewriting the whole result."
- "When a source or model fails, tell me what broke and what to trust less."
- "When a provider is rate-limited, queue or degrade the run honestly instead of failing silently."
- "When I upload my own evidence, use it as a cited source without turning RetroCause into a heavy enterprise knowledge system."

## OSS Boundary

OSS should keep these capabilities:

- local FastAPI and Next.js app
- provider preflight
- live/demo/partial-live labeling
- evidence board and causal chains
- retrieval trace and challenge coverage
- product value harness
- copyable Markdown research brief
- tests and inspectable code paths

OSS should not default to:

- persistent hosted workspaces
- team sharing or shared hosted credits
- scheduled briefings
- PDF/DOCX/branded exports
- saved comparison history
- source-policy controls beyond local inspectability
- paid domain/source packs
- enterprise private deployment
- SSO, document-level ACLs, custom enterprise connectors, or data-residency commitments

## Pro MVP

The smallest credible Pro version should ship one complete repeated workflow:

1. Run queue and quota management
   - Create a run record instead of forcing the full analysis through one synchronous request.
   - Track run steps, provider usage, retry/fallback state, and partial-live degradation.
   - Enforce user and workspace quotas for runs, deep checks, LLM calls, search calls, and concurrent jobs.
   - Separate central hosted quota from user-owned quota such as user API keys, browser/account-backed sources, and uploaded evidence.
   - Show queued, cooling-down, rate-limited, cached, and partial-live states as product states, not hidden backend errors.

2. Source policy and cache
   - Route each scenario through source packs such as market research, policy/geopolitics, and postmortem.
   - Cache search results, fetched content, extracted evidence, and source trace where provider terms allow it.
   - Include normalized topic, scenario, locale, source policy, freshness requirement, and absolute date bucket in cache keys.
   - Show rate-limited, stale, cached, and skipped sources in the run trace.

3. Uploaded evidence
   - Let users upload PDF, Markdown, TXT, CSV, or pasted notes into a personal/small-team evidence library.
   - Preserve source name, upload time, document title, and cited snippets.
   - Keep the first version simple: personal library and Team Lite workspace library, not document-level enterprise ACL.

4. Saved runs
   - Store the query, model/provider metadata, retrieval trace, evidence, challenge checks, analysis brief, Markdown brief, and run status.
   - Let users reopen, duplicate, and compare previous runs.

5. Report export
   - Generate PDF and DOCX from the same grounded fields used by the Markdown brief.
   - Include question, likely explanation, top reasons, evidence table, challenge coverage, source trace, gaps, and use caveat.
   - Preserve citations and source labels in the exported artifact.

6. Team Lite review
   - Share a run with read-only review links for a small workspace.
   - Let reviewers mark evidence as useful, weak, stale, or disputed.
   - Keep reviewer comments separate from model-generated claims.

7. Scheduled watch topics
   - Run saved templates on a daily or weekly cadence.
   - Alert only when evidence, top explanation, confidence, or challenge coverage changes materially.
   - Record failure states instead of silently sending weak reports.

## User-Facing Output

Every Pro output should answer five user questions clearly:

- What is the most likely explanation?
- What concrete reasons support it?
- What evidence anchors those reasons?
- What counterpoints or refutations were checked?
- What is still missing or risky?

The UI should treat this as a workflow, not a dashboard. A good Pro run ends with a deliverable the user can send, archive, compare, or schedule.

## Rate-Limit And Source Ownership Model

OpenCLI is a useful comparison point because it avoids a large class of shared rate-limit failures by running deterministic adapters through the user's local browser, cookies, account, and IP. It is not "limit free"; it moves many limits from a central service to the user's own source session and keeps each adapter bounded.

RetroCause cannot remove limits the same way because the product depends on retrieval plus LLM-backed extraction, synthesis, causal graphing, and challenge coverage. Pro should therefore make quota ownership explicit:

- Central hosted quota: RetroCause-managed LLM calls, hosted search, extraction, report rendering, and scheduled jobs.
- User-owned quota: user-supplied LLM/search keys, browser-backed source sessions where supported, and uploaded evidence libraries.
- Source-specific quota: public websites, official APIs, news APIs, academic APIs, and search providers with their own RPM, daily, storage, or access rules.

The Pro promise should be reliability under limits, not unlimited usage. A paid run should queue, reuse allowed cache, fall back to safer sources, pause on retry-after, preserve partial results, and tell the user exactly which source or provider was constrained. This is the direct monetization value for individuals and small teams: they pay for a repeatable operating workflow that turns fragile provider calls into a reviewable deliverable.

This also defines the OSS/Pro boundary:

- OSS: local inspectable runs, explicit source trace, optional user-supplied keys, bounded adapters, and Markdown export.
- Pro: hosted run records, usage ledger, queue, cache reuse, saved runs, exports, uploaded evidence, scheduled watch topics, lightweight team review, and source-policy controls.
- Not near-term: private enterprise deployment, hidden scraping, account rotation, or promises that bypass provider terms.

## Trust Rules

- Causal conclusions must cite evidence or point to a missing-evidence caveat.
- Probability values must stay within `[0,1]`.
- Challenge coverage must distinguish `has_refutation`, `no_refutation_in_retrieved_evidence`, and `not_checked`.
- Reports must never hide demo, partial-live, provider failure, or stale evidence states.
- Source trace and retrieval policy must be visible in every saved run and export.
- Source ownership and quota status must be visible enough that users can tell whether a failure came from RetroCause-hosted quota, their own key/session, or a third-party source.

## Success Metrics

- Time from query to reviewable brief is under 3 minutes for a normal live run.
- At least 80% of successful Pro runs produce a report the user can forward with minor edits.
- Saved comparison highlights changed explanations, changed evidence, and changed caveats without manual diffing.
- Scheduled briefings avoid sending weak output when provider, source, or evidence coverage is blocked.
- Users can explain why they trust or distrust the result by pointing to evidence, challenge coverage, and gaps.
- Rate-limited providers result in queued, retried, cached, fallback, or partial-live runs with visible status rather than silent thin evidence.

## Implementation Phases

### Phase 1: Run Queue, Quota, And Source Policy

- Add `run_id`, run status, run steps, and usage ledger.
- Add provider budget metadata and source fallback/cooldown behavior.
- Add source policy presets for market, policy/geopolitics, and postmortem.
- Add cache keys that include scenario and absolute time buckets.

### Phase 2: Saved Runs

- Add persistence for run payloads and metadata.
- Add a run history page.
- Add duplicate and compare actions.

### Phase 3: Uploaded Evidence

- Add personal uploaded evidence.
- Add a simple small-team workspace library.
- Keep enterprise connectors and document-level ACL out of scope.

### Phase 4: Report Export

- Convert the current Markdown brief schema into a report schema.
- Add PDF and DOCX generation.
- Add branded headers only after the unbranded report is useful.

### Phase 5: Team Lite Review

- Add share links and read-only review.
- Add evidence annotations and reviewer notes.
- Add audit trail for human edits versus model output.

### Phase 6: Scheduled Watch Topics

- Add templates and schedules.
- Add change detection between runs.
- Add failure gating so poor runs become alerts, not reports.

## Non-Goals

- Do not make Pro a generic chatbot.
- Do not hide uncertainty to make reports look more confident.
- Do not expose model chain-of-thought as a product promise.
- Do not add heavy multi-agent orchestration unless it improves evidence, refutation, or delivery quality.
- Do not move features into Pro if they are necessary for OSS users to inspect the core causal explanation honestly.
- Do not promise unlimited usage.
- Do not make enterprise private deployment, SSO, document-level ACL, or custom enterprise connector work a near-term requirement.
- Do not bypass provider rate limits or storage terms.

## Current Decision

For the current alpha, keep Pro as a documented product direction only. The next Pro-facing implementation should start with lightweight run orchestration, provider budgets, source policies, cache, and uploaded evidence for personal/small-team use. Do not write enterprise private-deployment code until a concrete paid customer justifies the maintenance cost.
