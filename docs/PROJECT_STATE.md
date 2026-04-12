# Project State

Last updated: 2026-04-12

## Goal

描述这个项目要长期达成的目标。

## Current focus

Stabilize quality-first live evidence retrieval, especially for time-sensitive market/news queries where relative windows such as `today` and `yesterday` must not reuse stale evidence.

## Done recently

- 已使用 preset `generic` 初始化项目 guardrails
- Added absolute calendar buckets and pre-extraction stale-result filtering for relative time-sensitive evidence retrieval.

## Blockers

- Unknown

## Next step

Re-test live browser/API runs for `昨天比特币价格跳水` and other strong-freshness queries with OpenRouter DeepSeek, then inspect retrieval trace dates and evidence timestamps.
