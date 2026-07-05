---
name: [be] ui-concept-first
description: "Используется перед building или redesign frontend UI, когда важна визуальная direction; фиксирует visual reference из ImageGen, Figma, screenshot, Lazyweb evidence или existing design system перед implementation и visual QA."
---

# UI Concept First

Establish the visual target before implementation.

## Workflow

1. Read `ui-router` and classify the UI request.
2. Gather evidence first when needed through `ui-research`.
3. Use `frontend-app-builder`, Product Design `ideate`, Figma, ImageGen, or an
   existing screenshot/design system to establish the visual reference.
4. Extract tokens, typography, layout, components, states, and responsive rules
   with `design-system-extractor`.
5. Implement only after the visual direction is clear.
6. Validate with `playwright-visual-qa`.

## Rules

- Do not start major UI implementation from text-only vibes.
- Do not add unapproved large UI sections after concept selection.
- If concept generation is blocked, state the blocker and use the strongest
  available reference.
