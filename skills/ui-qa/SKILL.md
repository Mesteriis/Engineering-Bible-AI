---
name: ui-qa
description: UI validation and review router. Use after ui-router for browser testing, visual QA, UI regressions, frontend performance review, or code review of rendered UI. Routes to the matching QA/review skill and requires reading that skill's SKILL.md before acting.
---

# UI QA Router

Use this skill for validation, debugging, and review of UI work.

## Workflow

1. Read the brief.
2. Pick the smallest matching QA or review skill.
3. Read that skill's `SKILL.md`.
4. Validate the rendered UI or review the implementation against evidence.

## Routing

- Visual fidelity, screenshot comparison, UI regression -> `playwright-visual-qa`
- Desktop/tablet/mobile layout verification -> `responsive-breakpoint-check`
- Keyboard, focus, semantics, contrast, or ARIA review ->
  `accessibility-ui-review`
- Rendered frontend testing / debugging -> `frontend-testing-debugging`
- React / Next.js perf review -> `react-best-practices`
- Principal code review for UI changes -> `principal-review`

## Rule

If the prompt also needs evidence before validation, name `ui-research` as
the next skill to read. If it needs more implementation changes, name
`ui-build`.
