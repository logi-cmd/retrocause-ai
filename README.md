# RetroCause

**Ask any “Why did this happen?” question and get an evidence-backed causal map.**

RetroCause is an open-source causal explainer for complex events.

It helps you move beyond a single AI answer by generating:

- evidence-backed causal variables
- competing explanation chains
- intervention / what-if comparisons
- counterfactual-style reasoning signals
- an interactive causal graph you can inspect visually

Examples:

- Why did dinosaurs go extinct?
- Why did the 2008 financial crisis happen?
- Why did SVB collapse?
- Why is rent so high in New York?

---

## Why RetroCause

Most AI tools summarize information.

RetroCause is designed to explain **why** something happened:

- not just one answer, but competing explanations
- not just opinions, but evidence-linked reasoning
- not just static summaries, but intervention-style analysis

This makes it useful for developers, researchers, and early users exploring a new kind of **causal explanation interface**.

---

## Current status

RetroCause is currently a **research-grade alpha**:

- end-to-end pipeline is working
- browser-based evidence-board UI (FastAPI + Next.js)
- Streamlit demo is available as a fallback
- factor impact analysis MVP is available
- homepage now supports a minimal live `/api/analyze/v2` query flow
- demo fallback vs real analysis is explicitly labeled in the UI
- tests and frontend build are passing

Already implemented:

1. evidence collection orchestration
2. causal graph construction
3. hypothesis chain generation
4. evidence anchoring
5. counterfactual verification
6. factor impact analysis
7. interactive visualization
8. multi-hop causal tracing (API v2)
9. evidence-board web UI (Next.js frontend)

Still evolving:

- debate agents are still early
- sensitivity analysis is being expanded
- consumer-facing product polish is ongoing
- real-time streaming updates from the pipeline to the browser UI

---

## Quick start

### Browser UI (recommended)

The simplest way to run the full app is the unified launcher, which starts both the FastAPI backend and the Next.js frontend:

```bash
pip install -e ".[dev]"
cd frontend && npm install && cd ..
python start.py
```

This opens:

- **Frontend**: http://localhost:3005 (evidence-board UI)
- **Backend API**: http://localhost:8000 (FastAPI, with `/api/analyze/v2`)

The homepage can now send your question to the v2 API and render the recommended chain as an interactive evidence board. When real analysis is unavailable, the UI explicitly falls back to demo mode instead of silently pretending the result is live.

The fuller three-panel console workflow still exists in the codebase and remains a useful internal/reference UI path, but the current public OSS homepage is the primary entry point.

Without an API key, the UI may load demo data so you can explore the interface. This fallback is now explicitly labeled.

### CLI

```bash
pip install -e ".[dev,demo]"
retrocause "恐龙为什么灭绝？"
```

### Streamlit demo (fallback)

If you prefer the Streamlit-based demo:

```bash
pip install -e ".[dev,demo]"
streamlit run retrocause/app/entry.py
```

The demo mode works without an API key.

To use real analysis, provide your own API key in the UI.

Supported provider modes:

- OpenRouter
- OpenAI
- DashScope / 阿里百炼
- Zhipu / 智谱
- Moonshot / Kimi
- DeepSeek

This means the OSS demo now supports both:

- official domestic model endpoints
- global model endpoints
- OpenRouter as a model relay for mixed domestic + international access

---

## Example questions

Try questions like these:

### science / history

- Why did dinosaurs go extinct?
- Why did the Roman Empire collapse?
- Why did the Black Death spread so fast?

### business / tech

- Why did SVB collapse?
- Why did WeWork fail?
- Why did OpenAI's board crisis happen?

### economics / society

- Why is rent so high in New York?
- Why did the 2008 financial crisis happen?
- Why are semiconductor supply chains so fragile?

These examples are useful for demo screenshots, GitHub sharing, and early user onboarding.

---

## What the pipeline does

```text
Question
  → query decomposition
  → evidence collection from multiple sources
  → causal graph construction
  → competing hypothesis generation
  → evidence anchoring
  → counterfactual verification
  → factor intervention / impact comparison
  → multi-hop causal tracing
  → interactive explanation output (browser UI or CLI)
```

---

## Example product interaction

You ask:

> Why did dinosaurs go extinct?

The evidence-board UI shows a three-panel layout:

**Left panel**: hypothesis chains and evidence items for the current query. Each chain is listed with its probability and supporting evidence count.

**Center canvas**: the causal graph (or chain view) rendered as an interactive visualization. You can switch between graph view, chain view, and a data table. Nodes are colored by type (cause, mediator, effect) and edges show strength.

**Right panel**: when you click a node, this panel shows its detail: description, probability bar, upstream causes (clickable for multi-hop tracing), attached evidence, counterfactual analysis, and agent reports.

You can also:

- click any upstream cause to trace the chain deeper (multi-hop)
- inspect how hypothesis probabilities shift
- view counterfactual what-if scenarios for each chain
- switch between competing explanation chains

---

## What makes this different from a normal AI answer?

Typical chat tools give you a plausible explanation.

RetroCause tries to give you a more structured explanation by combining:

- causal variables
- explanation chains
- evidence links
- intervention-style comparisons

It is not claiming perfect causal truth, and it does not guarantee scientifically validated causal correctness.

It is designed to provide a **clearer and more inspectable explanation interface** with more visible uncertainty and evidence structure than a typical chat answer.

---

## Open source scope

The open-source repo is intended to be:

- runnable
- inspectable
- useful for experimentation
- good enough to demonstrate the product idea clearly

The open-source version focuses on the causal reasoning workflow itself.

Some commercial and planning documents are intentionally kept local and are not pushed to the remote repository.

---

## Public docs

- `docs/market-analysis-overseas-c.md` — overseas consumer market analysis
- `docs/open-source-growth-strategy.md` — GitHub open-source growth strategy
- `docs/engineering-audit.md` — engineering strengths, weak points, and optimization roadmap
- `docs/DECISIONS.md` — technical and product decisions
- `docs/manual-smoke-test.md` — manual smoke checklist for the OSS demo
- `docs/roadmap-and-limitations.md` — current roadmap and known limitations

---

## FAQ

### Is this a production-ready causal inference system?

No. It is currently a research-grade alpha and open-source demo product.

### Does the OSS UI clearly distinguish demo vs real analysis?

Yes. The homepage now explicitly marks whether the current board is showing a real API result or a demo fallback.

### Does it need an API key?

Only for real analysis. The browser UI and Streamlit demo can run without an API key, showing demo data.

### What is already working today?

- evidence collection orchestration
- causal graph construction
- hypothesis generation
- evidence anchoring
- counterfactual verification
- factor impact analysis MVP
- sensitivity profile MVP
- interactive visualization
- multi-hop causal tracing (API v2)
- evidence-board web UI (Next.js frontend)

### What is still early?

- debate agents
- stronger intervention math
- deeper sensitivity analysis
- consumer product polish

### Is this open source?

Yes. The code in this repository is open source under MIT.

Some business and planning documents are intentionally kept local and are not pushed to the remote repository.

---

## For GitHub visitors

If you are landing here from X, Reddit, Hacker News, or Product Hunt:

1. run `python start.py` to launch the browser UI
2. try one of the example questions above
3. click a node, then trace upstream causes (multi-hop)
4. switch between hypothesis chains to compare explanations
5. open an issue if you want a new example or feature

---

## Tech stack

| Area | Tech |
|---|---|
| causal graph | NetworkX |
| LLM orchestration | OpenAI SDK / OpenRouter-compatible API |
| pipeline | custom pipeline abstraction |
| probabilistic reasoning groundwork | NumPyro / JAX |
| backend API | FastAPI (Python) with `/api/analyze/v2` |
| frontend | Next.js + Tailwind CSS (evidence-board UI) |
| interface (fallback) | Streamlit + streamlit-agraph |

---

## Validation

Current local validation includes:

- `pytest tests/` passing
- `ruff check` on changed files
- diagnostics clean on source files
- frontend build (`npm run build`) passing in `frontend/`

---

## Vision

RetroCause is moving toward a consumer-facing product where people can ask:

> Why did this happen?

and receive a clearer, more structured, more evidence-aware explanation than a normal chat response.

---

## License

MIT
