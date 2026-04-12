# Current Task Evidence

## Task

Fix strong time-sensitive evidence retrieval so queries such as `昨天比特币价格跳水` do not collect or build graphs from explicitly stale dated evidence.

## Root Cause

- Relative time windows were reused as plain strings such as `yesterday`, so local caches/stores could mix different calendar days.
- Search queries did not consistently carry absolute date context for relative Chinese market/news questions.
- Search results with explicit stale `published` metadata were allowed into merged extraction text before the LLM evidence extraction step.

## Files Touched

- `retrocause/evidence_access.py`
- `retrocause/collector.py`
- `retrocause/engine.py`
- `retrocause/evidence_store.py`
- `retrocause/llm.py`
- `tests/test_evidence_access.py`
- `tests/test_auto_collect.py`
- `tests/test_evidence_store.py`
- `README.md`
- `docs/operational-plan.md`
- `docs/manual-smoke-test.md`
- `docs/PROJECT_STATE.md`

## Changes

- Added absolute time-scope keys such as `yesterday:2026-04-12` and `today:2026-04-13`.
- Added concrete date enrichment for live search queries, including ISO date and English month-date text.
- Added pre-extraction filtering for explicitly dated stale search results.
- Routed time-sensitive market/news queries away from academic fallback sources in the default broker.
- Made the local evidence store strict for explicit time scopes so different relative days cannot reuse the same event evidence.
- Added regression tests for stale dated result filtering, absolute time buckets, date-enriched retrieval queries, and store reuse boundaries.
- Updated README and operational/manual docs with the freshness rule.

## Commands Run

- `pytest tests/test_evidence_access.py tests/test_auto_collect.py tests/test_evidence_store.py --basetemp=.pytest-tmp`
  - First run failed before implementation because new expected functions did not exist.
  - Final result: 29 passed.
- `npm test`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Python tests: 197 passed.
  - E2E: 604 passed, 0 failed, 0 skipped.

## Residual Risks

- If a source result has no `published` or equivalent date metadata, the system cannot prove it is stale. Those results are still allowed but remain freshness-limited by downstream freshness status and should not upgrade a time-sensitive run to strong `live` without fresh evidence.
- Public search engines may still return incomplete results. This fix prevents known-stale dated evidence from contaminating extraction/graph construction; it does not guarantee complete market/news coverage.
- Frontend lint still reports 7 existing warnings in unrelated component files, but no lint errors.
