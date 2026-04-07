# RetroCause Engineering Audit

> Updated: 2026-04-02
> Scope: active repository `retrocause-ai`

---

## 1. Why this audit exists

The project is moving from a research-style prototype toward an open-source product that must be:

- easier to run
- easier to verify
- easier to evolve
- easier to present publicly on GitHub

This document captures the main engineering strengths, current weak points, and the highest-leverage optimization opportunities.

---

## 2. Current engineering strengths

### 2.1 Clear pipeline architecture

The project already has a strong structural foundation:

- `Pipeline`
- `PipelineStep`
- `PipelineContext`
- protocol-based interfaces

This makes the core reasoning flow easier to extend and test.

Relevant files:

- `retrocause/pipeline.py`
- `retrocause/engine.py`
- `retrocause/protocols.py`

### 2.2 Good test direction

The project already includes:

- unit-style tests
- integration tests
- counterfactual tests
- factor impact tests
- graceful fallback tests for no-LLM mode

This is a strong base for open-source evolution.

Relevant files:

- `tests/test_engine.py`
- `tests/test_integration.py`
- `tests/test_counterfactual.py`
- `tests/test_factor_impact.py`

### 2.3 Technical decisions are documented

Architecture and roadmap decisions are not only in code; they are written down.

Relevant files:

- `docs/DECISIONS.md`
- `docs/references.md`

---

## 3. Main engineering weak points

### 3.1 Runtime dependencies are incomplete

The Streamlit demo depends on packages that are not declared in `pyproject.toml`.

Impact:

- users may install the project successfully
- but still fail to run the visual demo

Relevant files:

- `pyproject.toml`
- `retrocause/app.py`

### 3.2 `app.py` is too large

The Streamlit application has grown into a large, mixed-responsibility file.

Current issues:

- UI rendering + demo data + state handling in one place
- duplicated demo data definitions
- harder long-term maintenance

Relevant file:

- `retrocause/app.py`

### 3.3 Existing validation infrastructure is underused

The project already has HookEngine and rule definitions, but they are not yet integrated into the main pipeline.

That means part of the engineering harness exists, but is not yet active in the product path.

Relevant files:

- `retrocause/hooks.py`
- `retrocause/rules.py`
- `retrocause/engine.py`

### 3.4 Some advanced modules are not yet wired into the main flow

Examples:

- `bayesian.py` exists but is not a first-class pipeline stage
- some configuration paths are split between code constants and config dataclass

Relevant files:

- `retrocause/bayesian.py`
- `retrocause/config.py`
- `retrocause/app.py`

---

## 4. Highest-priority optimization points

## P0 — do soon

### P0.1 Add missing runtime dependency groups

Add explicit optional dependency groups for demo / UI usage.

Why:

- improves first-run experience
- reduces GitHub friction
- makes README setup trustworthy

### P0.2 Split `app.py`

Break the Streamlit app into smaller modules such as:

- demo data
- graph panel
- hypotheses panel
- counterfactual panel
- factor impact panel

Why:

- reduces coupling
- makes UI evolution safer
- improves reviewability

### P0.3 Activate HookEngine in the main pipeline

The project already has a rule system. It should become part of the normal run path.

Why:

- converts passive validation into active validation
- strengthens engineering harness behavior
- improves trust in outputs

---

## P1 — next wave

### P1.1 Add CI

The project should have a GitHub Actions workflow that runs:

- `ruff`
- `pytest`

### P1.2 Unify test mocks

Several tests define their own fake LLM/source objects. These can be unified into shared fixtures.

### P1.3 Improve CLI ergonomics

The CLI should support:

- `--help`
- demo mode
- clearer usage messages

---

## P2 — strategic engineering improvements

### P2.1 Decide the role of `bayesian.py`

Current state:

- useful module exists
- not central to the pipeline yet

Decision needed:

- either integrate it more directly
- or move heavy probabilistic dependencies behind optional install groups

### P2.2 Strengthen config management

The config story should be unified across:

- environment variables
- app provider/model selection
- timeout behavior
- optional runtime modes

### P2.3 Open-source release quality improvements

Still worth adding:

- `LICENSE`
- `CONTRIBUTING.md`
- issue templates
- PR template

---

## 5. Recommended engineering sequence

### Phase A

1. fix dependency declaration gaps
2. split `app.py`
3. activate HookEngine in the pipeline

### Phase B

1. add CI
2. unify mocks and test helpers
3. improve CLI usability

### Phase C

1. decide how Bayesian inference fits into the main product story
2. improve configuration boundaries
3. finish open-source release support files

---

## 6. Practical interpretation

The project does **not** have a weak foundation.

The main issue is not architecture collapse. The main issue is that some good engineering pieces already exist but are not fully connected yet.

That is good news:

- this is mostly a wiring and hardening phase
- not a rewrite phase

---

## 7. Immediate next actions

If only three engineering optimizations are chosen next, they should be:

1. dependency declaration cleanup
2. `app.py` modularization
3. HookEngine integration into the main pipeline

These three changes would give the biggest engineering leverage for the least architectural disruption.

---

## 8. Harness Engineering Perspective

This section applies the structured harness engineering audit based on the Anthropic-inspired harness layer model.

The harness layer sits between the model and the business logic. It covers: orchestration, evaluation, context management, guardrails, and failure recovery.

### 8.1 Execution loop assessment

The project uses a linear `Pipeline.run()` (pipeline.py:55-62) — a Plan-and-Execute loop.

This is appropriate for the 6-step causal reasoning task, However:

- There is no feedback loop between steps
- Each step produces output but no step verifies the previous step's output
- The pipeline runs once and never revisits earlier decisions

This is a valid choice for MVP, As the pipeline matures, consider a GAN-style loop where a separate evaluator reviews pipeline output.

### 8.2 Generator / evaluator separation

The most critical gap: **the pipeline has no separate evaluator.**

Current state:

- Each step both generates and implicitly self-validates its own output
- `HookEngine` (hooks.py:42-64) exists with rules but is never called from `Pipeline.run()` or `engine.py`
- This is equivalent to "the generator evaluating its own output" — a known anti-pattern

The project already has the foundation to fix this:

- `HookEngine` + `HookRule` infrastructure is well-designed
- `ProbabilityBoundRule`, `EvidenceCoverageRule`, `CounterfactualBoundRule` exist in `rules.py`
- They just need to be wired into `Pipeline.run()` (pipeline.py:55-62)

### 8.3 Failure recovery assessment

The pipeline has **no failure recovery** at any level:

- `Pipeline.run()` (pipeline.py:55-62) has no try/except around step execution
- If any step raises an exception, the entire pipeline crashes
- `LLMClient` methods (llm.py) silently catch all `openai.OpenAIError` and return empty defaults
- This means failures are invisible: the pipeline appears to succeed but produces empty results

From harness-engineering: "When a step fails, the silently return empty defaults, this is worse than crashing — it broken pipeline silently produces broken output."

### 8.4 Context management assessment

The is no cross-session context management:

- `PipelineContext` is in-memory only, no persistence
- No handoff artifact format for resuming work across sessions
- No context reset strategy for long analyses

For a tool that may run multi-minute LLM calls, this is acceptable for MVP but will need attention as complexity grows.

### 8.5 Guardrails assessment

The project has guardrail infrastructure but it is inactive:

- `HookEngine` (hooks.py:42-64): exists, never called
- `HookRule` (hooks.py:25-40): abstract base, never used in production
- `ProbabilityBoundRule` (rules.py): checks probability bounds, never triggered
- `EvidenceCoverageRule` (rules.py): checks evidence coverage, never triggered
- `CounterfactualBoundRule` (rules.py): checks counterfactual bounds, never triggered

From harness-engineering: "Hooks must cover intent, not just tool names."

### 8.6 LLM call resilience assessment

All LLM methods in `llm.py` share the same anti-pattern:

```python
except (openai.OpenAIError, json.JSONDecodeError):
    return {}  # or return [] or return 0.5
```

Problems:

- No retry (transient API errors are permanent failures)
- No timeout enforcement (config has `request_timeout_seconds` but it is never passed to the OpenAI client)
- No rate limiting
- Silent failure: empty output is indistinguishable from "no results found"

From harness-engineering: "Silent failure is worse than loud failure."

---

## 9. Harness-specific optimization priorities

ordered by impact:
| # | Optimization | Harness dimension | Evidence | Effort |
|---|---|---|---|---|
| H1 | Wire HookEngine into Pipeline.run() | Guardrails | hooks.py, rules.py exist but pipeline.py:55-62 never calls them | **Done** — pipeline.py now calls hook_engine.evaluate after each step |
| H2 | Add try/except to Pipeline.run() | Failure recovery | pipeline.py:55-62 has no error handling | **Done** — step errors captured in ctx.step_errors |
| H3 | Add retry to LLM calls | Failure recovery | llm.py every method silently catches errors | **Done** — _call_with_retry with exponential backoff (3 retries) |
| H4 | Add timeout to OpenAI client | Failure recovery | config.py has timeout but llm.py never uses it | **Done** — LLMClient accepts timeout param, run_real_analysis passes config timeout |
| H5 | Separate evaluator from generator | Evaluation | engine.py evaluates its own output | 2h |

---

## 10. Recommended harness engineering sequence

### Phase A: Wire existing infrastructure
1. Wire `HookEngine` into `Pipeline.run()` so rules actually fire
2. Add try/except to `Pipeline.run()` with step-level error isolation
3. Pass `request_timeout_seconds` to the OpenAI client constructor

### Phase B: Add resilience
1. Add retry (tenacity or exponential backoff) to LLM calls
2. Add structured logging (JSON) for observability
3. Add handoff artifact format for cross-session continuity

### Phase C: Evaluation upgrade
1. Consider a separate evaluator step that reviews pipeline output
2. Add loop detection if the evaluator finds issues
3. Add sprint contracts for multi-session analyses
