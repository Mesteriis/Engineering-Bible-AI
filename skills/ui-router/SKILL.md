---
name: [be] ui-router
description: Thin entrypoint for any product UI prompt. Classify the request, choose the smallest coherent set of downstream UI skills, and read their SKILL.md files before acting. Use for product UI design, redesign, critique, frontend implementation, Figma, image-to-code, and visual QA workflows.
---

# UI Router

Use this skill as the first stop for any product UI request.

## Workflow

1. Classify the prompt.
2. Pick the smallest coherent set of downstream skills.
3. Read every selected skill's `SKILL.md` before taking action.
4. State which skill(s) are active and which additional skill(s) still need
   to be read if the prompt spans multiple UI modes.
5. Prefer the order: evidence/research -> design direction -> implementation
   -> QA.

## Routing

- New UI, redesign, landing page, dashboard, mobile concept, or any prompt
  where visual direction matters -> `ui-concept-first`.
- Evidence, critique, compare, improve, or "what do other apps do" ->
  `ui-research`.
- Extract tokens, typography, components, or responsive rules from a reference
  -> `design-system-extractor`.
- Figma selection/frame/component to frontend code -> `figma-to-code`.
- Existing code/live UI back to Figma or Code Connect -> `code-to-figma`.
- Landing pages, portfolios, editorial sites, redesigns, image-led website
  concepts, mobile app concepts, image-to-code work, general frontend UI,
  or style-constrained builds -> `ui-build`.
- Figma work -> `ui-figma`.
- Rendered frontend QA, visual diff, browser testing, perf review, or code
  review ->
  `ui-qa`.

## Rule

If the prompt spans multiple UI modes, name the primary skill and the next
skill to read. Do not skip the reading step.
