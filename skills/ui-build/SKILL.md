---
name: [be] ui-build
description: "UI design и implementation router для landing pages, portfolios, redesigns, general frontend UI, image-led website concepts и style-constrained builds; выбирает нужный build skill и требует прочитать его SKILL.md перед работой."
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
