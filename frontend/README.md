# RetroCause Frontend Notes

This folder contains the Next.js browser evidence board for RetroCause. The root
[`README.md`](../README.md) remains the source of truth for first-time setup,
product positioning, API usage, and release status.

## Supported Run Path

Start the full local app from the repository root:

```bash
python start.py
```

Then open:

- Frontend: `http://localhost:3005`
- Backend API: `http://localhost:8000`

Running only the frontend with `npm --prefix frontend run dev` is useful for UI
development, but many flows depend on the local FastAPI backend.

## Main Files

- `src/app/page.tsx`: current evidence-board homepage and primary UI surface.
- `src/app/layout.tsx`: app shell metadata.
- `src/lib/`: extracted homepage types, formatting helpers, and focused panels
  for source trace/progress, readable briefs, production briefs, saved runs,
  uploaded evidence, and challenge coverage.
- `src/components/canvas/`: older/componentized graph and evidence views that
  still overlap with homepage concepts.
- `UI_DESIGN_SPEC.md`: historical design direction. Treat it as design intent,
  not an exact description of the current homepage.
- `AGENTS.md`: local Next.js warning. Read it before changing frontend code.

## Validation

From the repository root, run:

```bash
npm test
```

That command covers frontend lint/build, backend `ruff`, full Python tests, and
the full-stack browser E2E smoke test.

For frontend-only checks:

```bash
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Maintenance Notes

- Keep user-visible behavior and setup docs in the root `README.md`.
- Keep current project status in `docs/PROJECT_STATE.md`.
- The current homepage is large; prefer extracting focused components and pure
  helpers instead of adding more unrelated logic to `src/app/page.tsx`.
- Do not imply hosted Pro features exist in this frontend. Saved runs and
  uploaded evidence are local OSS alpha inspectability features.
