# Harness Value Design

Date: 2026-04-13

## Goal

RetroCause should help a user understand two things before they trust a live causal result:

- whether the selected provider key and model can produce valid JSON analysis output
- whether the returned result is useful enough to review as an evidence-backed causal explanation

This is driven by the live query:

> US Iran Islamabad talks ended without agreement

The product should not make the user wait through a full run only to discover that the model id, key, quota, or JSON behavior was the real blocker.

## Harness 1: Provider Preflight

The provider preflight harness runs before a full analysis. It checks:

- provider configuration
- API key presence
- selected model catalog status
- model access and tiny JSON response behavior

It returns an actionable diagnosis such as missing key, invalid model, auth/permission issue, quota issue, timeout, or invalid/empty JSON payload.

The UI exposes this in the advanced provider settings so the user can test the model before spending a full analysis budget.

## Harness 2: Result Value Harness

Every v2 analysis response includes a lightweight `product_harness` report. It scores whether the run produced reviewable value for a user:

- causal chain present
- analysis summary present
- source trace visible
- evidence stance visible
- challenge coverage checked
- failure state actionable

The report classifies the result as:

- `ready_for_review`
- `needs_more_evidence`
- `blocked_by_model`
- `not_reviewable`

This makes empty or partial-live runs honest. A model-blocked run can still be useful if it tells the user exactly what to fix next.

## User Value

For a real geopolitics/news question, the user wants a reasoned brief, not a raw evidence dump. A good output should show:

- top causal reasons with evidence anchors
- source trace and source stability
- support vs challenge evidence
- missing-evidence notes
- a clear next action when the run is blocked

## Testing

The harnesses are covered by backend tests for:

- missing API key preflight classification
- invalid model preflight classification
- model-blocked empty result scoring
- useful evidence-backed result scoring

The frontend is verified through lint and build.
