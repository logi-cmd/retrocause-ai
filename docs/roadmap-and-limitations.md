# RetroCause OSS Roadmap and Limitations

## Current OSS Strengths

- evidence-backed causal explanation pipeline
- competing hypothesis chains
- counterfactual summary support
- FastAPI backend with `/api/analyze/v2`
- browser-based evidence-board UI
- multi-hop causal tracing in the frontend
- unified local startup via `python start.py`

## Current Limitations

### 1. Demo fallback is still important

Without a configured real model / evidence collection path, the browser experience can fall back to demo data.

This is now **explicitly labeled in the UI**, but it still means:

- not every user query yields a truly query-specific causal chain
- the OSS demo is reliable for interaction testing, not guaranteed real analysis quality

### 2. Real-time streaming is not finished

The pipeline does not yet stream intermediate reasoning into the browser in a polished way.

### 3. Debate visualization is still early

The debate / multi-agent reasoning view is present, but still less mature than the main chain / graph / right-panel experience.

### 4. Browser automation environment may vary

Automated browser QA depends on local Chrome / Playwright availability.

### 5. Product polish is still ongoing

The current OSS is a strong demoable alpha, not a production-grade end-user application.

## Near-Term Roadmap

### P1 — Make real analysis mode clearer

- show stronger distinction between real analysis and demo mode
- optionally surface model / source availability in the UI

### P2 — Improve node and evidence workflows

- evidence filtering by source / support / confidence
- better chain comparison workflows
- stronger edge explanation affordances

### P3 — Strengthen query-specific fallback behavior

- move from generic demo chain fallback toward topic-aware or query-shaped demo responses

### P4 — Better OSS onboarding

- add screenshots / GIFs
- add issue templates
- add contributor setup notes

### P5 — Deeper reasoning fidelity

- stronger intervention math
- richer sensitivity analysis
- more robust evidence grounding and uncertainty communication

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
