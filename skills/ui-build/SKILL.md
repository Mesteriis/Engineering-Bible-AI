---
name: ui-build
description: UI design and implementation router. Use after ui-router for landing pages, portfolios, redesigns, general frontend UI, image-led website concepts, or style-constrained builds. Routes to the matching build skill and requires reading that skill's SKILL.md before acting.
---

# UI Build Router

Use this skill for UI prompts that need design direction or implementation.

## Workflow

1. Read the brief.
2. Pick the smallest matching build skill.
3. Read that skill's `SKILL.md`.
4. Implement from the chosen direction without adding unrelated UI patterns.

## Routing

- Major new UI/redesign before code -> `ui-concept-first`
- Extracting implementation constraints from a visual reference ->
  `design-system-extractor`
- Figma frame/selection/component implementation -> `figma-to-code`
- Landing pages, portfolios, editorial sites, redesigns -> `design-taste-frontend`
- General frontend pages/components -> `frontend-design`
- Image-led website concepts -> `imagegen-frontend-web`
- Mobile app concepts -> `imagegen-frontend-mobile`
- Translate a selected visual into code -> `image-to-code`
- New complex frontend app, dashboard, or implementation -> `frontend-app-builder`
- Strong style constraints -> `minimalist-ui`, `industrial-brutalist-ui`,
  `high-end-visual-design`, `gpt-taste`, or `stitch-design-taste`
- shadcn/component composition -> `shadcn`

## Rule

If the prompt also needs validation or performance review, name `ui-qa` as
the next skill to read after this one. For visual fidelity, name
`playwright-visual-qa` specifically.
