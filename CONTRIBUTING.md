# Contributing to RetroCause

RetroCause is a research-grade alpha project. Contributions are welcome, whether it's a bug fix, a docs improvement, or a feature that makes the causal reasoning workflow more useful.

This guide covers how to get set up locally, run validation, and submit a contribution.

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Git

## Local Setup

### 1. Backend (Python)

```bash
pip install -e ".[dev]"
```

This installs RetroCause and dev dependencies (pytest, ruff).

If you want the Streamlit demo or Bayesian extras:

```bash
pip install -e ".[dev,demo]"
pip install -e ".[bayesian]"
```

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
cd ..
```

### 3. Run the full app

```bash
python start.py
```

This starts both the FastAPI backend (port 8000) and the Next.js frontend (port 3000). The frontend loads demo data when no API key is configured, so you can explore the UI right away.

## Validation Commands

Run these before submitting a PR. All three should pass.

```bash
# Python tests
python -m pytest tests/ -v

# Lint
ruff check retrocause/

# Frontend build
cd frontend && npm run build
```

## Project Structure

```text
retrocause/          # Core Python package
  api/               # FastAPI backend (main.py, routes)
  app/               # Streamlit demo entry point
  core/              # Pipeline, graph, reasoning modules
frontend/            # Next.js evidence-board UI
tests/               # pytest test suite
docs/                # Project documentation
start.py             # Unified launcher (backend + frontend)
```

## Key Docs

| Document | What it covers |
|---|---|
| `README.md` | Project overview, quick start, tech stack |
| `docs/manual-smoke-test.md` | Step-by-step manual QA checklist for the browser UI |
| `docs/roadmap-and-limitations.md` | Current roadmap, known limitations, what's still early |
| `docs/DECISIONS.md` | Technical and product decisions |

## Making Changes

1. Fork the repo and create a branch.
2. Make your change. Keep it focused and small.
3. Run the validation commands above.
4. Open a pull request with a clear description of what changed and why.

### Style Notes

- Python: follow existing patterns. `ruff check` handles formatting enforcement.
- Frontend: follow the patterns in `frontend/src/`. Tailwind CSS for styling.
- Keep changes minimal. Don't refactor adjacent code unless it's directly related to your change.

## Reporting Issues

Use the GitHub issue templates:

- **Bug Report**: for something broken or unexpected. Include steps to reproduce, which interface you were using (browser UI, CLI, Streamlit, API), and whether you were in demo mode or real analysis mode.
- **Feature Request**: for ideas and improvements. Describe the problem you're trying to solve, not just the solution you imagine.

## What to Work On

Check the [open issues](../../issues) for things that are already tracked. The [roadmap](docs/roadmap-and-limitations.md) lists the current priorities and what's still early-stage.

Good first contributions:

- fixing a bug you found while running the demo
- improving docs or error messages
- adding a test for an untested edge case

## License

By contributing, you agree that your changes will be licensed under the same MIT license as the rest of the project.
