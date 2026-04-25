# Design System Inspired by xAI

This document is a local RetroCause Pro design reference inspired by the `awesome-design-md` xAI entry: stark monochrome, futuristic minimalism, and dialogue-first intelligence. It is not an official xAI design system and does not imply affiliation.

## Visual Direction

- The product opens as a dialogue-only intelligence surface: the root page should focus on asking a precise causal question, not on exposing operational panels.
- The knowledge graph lives on a separate workspace page and should feel like a star map: black space, thin constellation lines, bright labeled nodes, and cinematic depth.
- The interface should feel quiet, severe, research-grade, and high-trust rather than decorative.
- Use monochrome surfaces, restrained transparency, and scale contrast instead of colorful panels.
- Motion should feel like a film-grade system wake-up: prompt, graph, wires, and nodes resolve into place with a smooth scan rather than popping in.

## Color

- Void: `#050505`
- XAI graphite: `#1f2228`
- Near white: `#ededed`
- Muted text: `#a0a0a0`
- Hairline border: `rgba(237, 237, 237, 0.18)`
- Strong border: `rgba(237, 237, 237, 0.42)`
- Ghost surface: `rgba(237, 237, 237, 0.06)`
- Ghost hover: `rgba(237, 237, 237, 0.12)`

Avoid colorful gradients, purple-blue AI palettes, beige luxury palettes, and decorative glow-heavy surfaces.

## Typography

- Use a Geist/Universal Sans feel with local fallbacks: `Arial`, `Verdana`, `system-ui`, sans-serif.
- Use uppercase for labels, buttons, and telemetry.
- Use sentence case for user input and generated analytical text so the product remains readable.
- Use wide tracking only for small labels and controls. Do not apply negative letter spacing.
- Let the main prompt and graph labels carry the visual hierarchy.

## Components

- Dialogue box: large, sparse, centered in the root page; it is the homepage and should feel like the product's first-class intelligence surface, not a side form.
- Star-map graph: black galaxy scene on `/graph`, constellation lines, bright point labels, node focus through border/opacity and smooth transform feedback.
- HUD rails: transparent monochrome panels for sources, quota, execution gates, evidence, and review deltas.
- Buttons: ghost surfaces with rounded pill corners, strong text contrast, and subtle hover transitions.
- Inputs: dark ghost fields with visible borders and generous padding.

## Motion

- Use short, cinematic entrance transitions on opacity and transform only.
- Hover feedback should feel smooth and restrained: slight lift, clearer border, no layout shift.
- A single low-cost scan or wire-draw sequence is acceptable when it clarifies the graph waking up.
- Pointer-driven star-field parallax is acceptable when it is transform-only, bounded, and disabled by `prefers-reduced-motion`.
- Respect `prefers-reduced-motion`.
- Do not add heavy animation loops, large blur surfaces, full-screen glow effects, video backgrounds, remote assets, or framework dependencies.

## Product Boundary

The current Pro shell is still preview-only for hosted execution. UI language must not imply real provider calls, credential vault reads, quota reservation, worker execution, durable intent persistence, billing mutation, or result commits until those backend gates exist.

## RetroCause Pro Adaptation Notes

- Treat this document as visual direction only, not brand affiliation.
- Use the causal graph itself as the cinematic scene; do not introduce remote imagery, decorative blobs, or a marketing hero.
- Keep operator controls as transparent HUD rails around the `/graph` scene so the product remains usable rather than merely atmospheric.
- Keep the first screen dialogue-only: users should immediately know where to ask the causal question, while source, quota, gate, evidence, and review details live away from the homepage.
- Star-map effects should reinforce evidence inspection, not hide labels or turn the product into a decorative splash screen.
- Keep preview-only gates visibly blocked until the Rust backend has real tenant auth, vault handles, quota reservation, worker leases, durable intents, and idempotent result commits.
- Do not add font, icon, image, JavaScript framework, provider, or credential dependencies for this visual system.
