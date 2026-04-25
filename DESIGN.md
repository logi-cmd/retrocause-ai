# Design System Inspired by xAI

This document is a local RetroCause Pro design reference inspired by xAI's stark monochrome, futuristic minimalism. It is not an official xAI design system and does not imply affiliation.

## Visual Direction

- The product opens as a dialogue-first intelligence workspace: the first action is asking a precise causal question.
- The knowledge graph should feel like a star map: black space, thin constellation lines, bright labeled nodes, and cinematic depth.
- The interface should feel quiet, severe, research-grade, and high-trust rather than decorative.
- Use monochrome surfaces, restrained transparency, and scale contrast instead of colorful panels.

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

- Dialogue box: large, sparse, centered or upper-left over the graph field; it is the homepage entry point.
- Star-map graph: black scene, constellation lines, bright point labels, node focus through border/opacity and smooth transform feedback.
- HUD rails: transparent monochrome panels for sources, quota, execution gates, evidence, and review deltas.
- Buttons: ghost surfaces with rounded pill corners, strong text contrast, and subtle hover transitions.
- Inputs: dark ghost fields with visible borders and generous padding.

## Motion

- Use short, cinematic entrance transitions on opacity and transform only.
- Hover feedback should feel smooth and restrained: slight lift, clearer border, no layout shift.
- Respect `prefers-reduced-motion`.
- Do not add looping decorative animations, heavy blurs, or full-screen glow effects.

## Product Boundary

The current Pro shell is still preview-only for hosted execution. UI language must not imply real provider calls, credential vault reads, quota reservation, worker execution, durable intent persistence, billing mutation, or result commits until those backend gates exist.

## RetroCause Pro Adaptation Notes

- Treat this document as visual direction only, not brand affiliation.
- Use the causal graph itself as the cinematic scene; do not introduce remote imagery, decorative blobs, or a marketing hero.
- Keep operator controls as transparent HUD rails around the graph so the product remains usable rather than merely atmospheric.
- Keep preview-only gates visibly blocked until the Rust backend has real tenant auth, vault handles, quota reservation, worker leases, durable intents, and idempotent result commits.
- Do not add font, icon, image, JavaScript framework, provider, or credential dependencies for this visual system.
