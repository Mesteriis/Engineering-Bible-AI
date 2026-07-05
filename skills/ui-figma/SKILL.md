---
name: [be] ui-figma
description: "Figma router для UI prompts: создание, обновление, инспекция, connection или animation Figma screens/components; выбирает matching Figma skill и требует прочитать его SKILL.md перед работой."
---

# UI Figma Router

Use this skill for any Figma-related UI work.

## Workflow

1. Identify the Figma task.
2. Pick the smallest matching Figma skill.
3. Read that skill's `SKILL.md`.
4. Follow the Figma API or design-system workflow from that skill.

## Routing

- Implement Figma as code -> `figma-to-code`
- Sync implemented UI or component mappings back to Figma -> `code-to-figma`
- Create or update screen/view in Figma -> `figma-generate-design`
- Create or update design system/component library -> `figma-generate-library`
- Work directly with Figma Plugin API -> `figma-use`
- Add or inspect motion in Figma -> `figma-use-motion`
- Create or edit Code Connect mappings -> `figma-code-connect`
- Create a new blank Figma file -> `figma-create-new-file`

## Rule

If the prompt also needs evidence or implementation, name `ui-research` or
`ui-build` as the next skill to read after this one. If the prompt asks for
implementation fidelity, name `playwright-visual-qa` after build.
