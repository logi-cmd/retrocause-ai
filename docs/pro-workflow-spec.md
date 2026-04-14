# RetroCause Pro Workflow Spec

## Purpose

RetroCause OSS proves the inspectable core: a user can ask why an event happened, inspect causal chains, review evidence, check challenge coverage, and copy a Markdown research brief.

RetroCause Pro should monetize the repeated workflow around that core. The paid value is not "more AI text." The paid value is faster trusted delivery, saved context, stakeholder-ready outputs, and operating reliability for people who must explain events more than once.

## Target Users

- Market intelligence analysts who need to explain price, policy, supply-chain, or competitor events.
- Policy and geopolitical analysts who need source-backed briefings under time pressure.
- Strategy, consulting, and investment teams that need repeatable written explanations for colleagues or clients.
- Builders and researchers who want the OSS inspectability locally, then need hosted runs and export workflows for teams.

## Jobs To Be Done

- "When a market, policy, or geopolitical event happens, help me quickly produce a source-backed causal brief I can review and forward."
- "When new evidence arrives, help me compare what changed from the previous explanation."
- "When I need to brief a team or client, help me package reasons, evidence, counterpoints, and caveats without rewriting the whole result."
- "When a source or model fails, tell me what broke and what to trust less."

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
- team sharing
- scheduled briefings
- PDF/DOCX/branded exports
- saved comparison history
- source-policy controls for organizations
- paid domain packs

## Pro MVP

The smallest credible Pro version should ship one complete repeated workflow:

1. Saved runs
   - Store the query, model/provider metadata, retrieval trace, evidence, challenge checks, analysis brief, Markdown brief, and run status.
   - Let users reopen, duplicate, and compare previous runs.

2. Report export
   - Generate PDF and DOCX from the same grounded fields used by the Markdown brief.
   - Include question, likely explanation, top reasons, evidence table, challenge coverage, source trace, gaps, and use caveat.
   - Preserve citations and source labels in the exported artifact.

3. Team review
   - Share a run with read-only review links.
   - Let reviewers mark evidence as useful, weak, stale, or disputed.
   - Keep reviewer comments separate from model-generated claims.

4. Scheduled briefings
   - Run saved templates on a daily or weekly cadence.
   - Alert only when evidence, top explanation, confidence, or challenge coverage changes materially.
   - Record failure states instead of silently sending weak reports.

5. Source policy controls
   - Let a workspace choose source packs such as wire news, official policy, academic, market, or web.
   - Show the policy used on every report.
   - Require primary-source confirmation for high-stakes templates.

## User-Facing Output

Every Pro output should answer five user questions clearly:

- What is the most likely explanation?
- What concrete reasons support it?
- What evidence anchors those reasons?
- What counterpoints or refutations were checked?
- What is still missing or risky?

The UI should treat this as a workflow, not a dashboard. A good Pro run ends with a deliverable the user can send, archive, compare, or schedule.

## Trust Rules

- Causal conclusions must cite evidence or point to a missing-evidence caveat.
- Probability values must stay within `[0,1]`.
- Challenge coverage must distinguish `has_refutation`, `no_refutation_in_retrieved_evidence`, and `not_checked`.
- Reports must never hide demo, partial-live, provider failure, or stale evidence states.
- Source trace and retrieval policy must be visible in every saved run and export.

## Success Metrics

- Time from query to reviewable brief is under 3 minutes for a normal live run.
- At least 80% of successful Pro runs produce a report the user can forward with minor edits.
- Saved comparison highlights changed explanations, changed evidence, and changed caveats without manual diffing.
- Scheduled briefings avoid sending weak output when provider, source, or evidence coverage is blocked.
- Users can explain why they trust or distrust the result by pointing to evidence, challenge coverage, and gaps.

## Implementation Phases

### Phase 1: Saved Runs

- Add persistence for run payloads and metadata.
- Add a run history page.
- Add duplicate and compare actions.

### Phase 2: Report Export

- Convert the current Markdown brief schema into a report schema.
- Add PDF and DOCX generation.
- Add branded headers only after the unbranded report is useful.

### Phase 3: Team Review

- Add share links and read-only review.
- Add evidence annotations and reviewer notes.
- Add audit trail for human edits versus model output.

### Phase 4: Scheduled Briefings

- Add templates and schedules.
- Add change detection between runs.
- Add failure gating so poor runs become alerts, not reports.

### Phase 5: Source Policies And Domain Packs

- Add workspace source policy settings.
- Add domain-specific source presets.
- Add stronger primary-source requirements for high-stakes templates.

## Non-Goals

- Do not make Pro a generic chatbot.
- Do not hide uncertainty to make reports look more confident.
- Do not expose model chain-of-thought as a product promise.
- Do not add heavy multi-agent orchestration unless it improves evidence, refutation, or delivery quality.
- Do not move features into Pro if they are necessary for OSS users to inspect the core causal explanation honestly.

## Current Decision

For `v0.1.0-alpha.3`, keep Pro as a documented product direction only. Do not write Pro code until the OSS Markdown brief has been dogfooded across more domains and at least one repeated paid workflow is validated with real users.
