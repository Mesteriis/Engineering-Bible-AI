---
name: [be] figma-to-code
description: "Реализует Figma frame, selection, component или design-system screen в коде; извлекает Figma context, сохраняет variants/assets/tokens и валидирует рендер против Figma reference."
---

# Figma To Code

Translate Figma into repo-native frontend code.

## Workflow

1. Read `ui-figma`.
2. Read `figma-use` before any Figma tool/API work when available.
3. Pull only the selected frame/component context needed for the task.
4. Extract tokens and component anatomy with `design-system-extractor`.
5. Implement using existing repo conventions.
6. Validate rendered output with `playwright-visual-qa`.

## Rules

- Do not call Figma tools before reading the required Figma skill.
- Do not treat a Figma screenshot as enough when structured Figma context is
  available.
- Return affected Figma node IDs or the reason they were unavailable.
