# RetroCause Frontend Analyst Desk Design

## Direction

Use an **Analyst Desk** visual system with selective **Case Room Command** accents.

The interface should feel like a serious evidence workstation: warm paper, precise typography, visible source quality, and a small amount of investigative drama only where the system is actively retrieving or comparing evidence.

## DFII

- Aesthetic Impact: 4
- Context Fit: 5
- Implementation Feasibility: 5
- Performance Safety: 4
- Consistency Risk: 1
- DFII: 17 minus 1 = 16

## Product Goals

- Make the query area feel like the primary action, not a cramped utility panel.
- Make live/partial/demo status, evidence coverage, and retrieval health visible at a glance.
- Keep chain comparison and node selection stable and keyboard-accessible.
- Reduce cognitive clutter by collapsing provider/API settings behind an advanced control.
- Preserve the existing evidence-board metaphor while making the UI feel more premium and usable.

## Interaction Changes

- The left panel becomes an investigation brief with a larger textarea, stronger submit button, and collapsed advanced settings.
- The OSS provider selector is intentionally narrowed to OpenRouter-first to reduce setup confusion while keeping explicit model selection available.
- The header becomes a command bar with status, freshness, coverage, source-hit, and trace-failure chips.
- Subtle embedded side-panel buttons own hide behavior while low-emphasis edge tabs restore hidden panels without competing with the investigation board.
- Chain buttons keep explicit `aria-pressed` state so users and tests can verify the active chain.
- Sticky cards expose `role=button`, keyboard activation, and `aria-pressed`.
- The right panel remains the evidence/detail inspector, but panel styling is upgraded to a denser analyst-desk surface.
- View instructions move into a top, pointer-events-disabled hint using low-friction wording, the bottom help pill is removed, and the note layout begins lower so dragged evidence cards are not covered by help text.
- Canvas zoom controls provide minus/reset/plus actions near the top of the board so users can inspect dense evidence maps without relying on browser zoom.
- Sticky-note layout and drag bounds reserve a compact rendered-height-aware bottom safety area so a single note cannot be dragged into the clipped/covered bottom edge while the lower canvas remains usable.

## Implementation Notes

- Use `Fraunces` for headings and `IBM Plex Sans` for body/UI text to move away from the previous generic product-dashboard feel.
- Keep all quality signals visible: `live`, `partial_live`, `demo`, freshness, coverage, retrieval trace, cache/cooldown, and source errors remain exposed.
- Avoid mixed shorthand and per-side border styles on interactive chain buttons; use explicit `borderWidth`, `borderStyle`, and `borderColor` only.
- Advanced provider controls must not reset query state, selected chain state, language state, or current evidence state.
- Hiding either side panel must recompute note layout margins instead of leaving an unnecessary empty gutter.
- The upgrade is presentation-only: no backend retrieval/scoring behavior is changed in this design pass.

## Constraints

- No backend behavior changes.
- No hidden quality degradation: demo, partial_live, source cooldown, cache, and fallback evidence remain visible.
- No decorative motion beyond focused entrance and active retrieval cues.
- Keep E2E coverage for chain B -> A switching, language toggle, and console/page errors.
