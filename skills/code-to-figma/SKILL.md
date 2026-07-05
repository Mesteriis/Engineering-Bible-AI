---
name: [be] code-to-figma
description: "Переносит реализованный UI обратно в Figma: live UI в редактируемые слои, Code Connect, обновление component library, design handoff и синхронизация Figma с production components."
---

# Code To Figma

Bridge implemented UI back into Figma.

## Workflow

1. Read `ui-figma`.
2. Use `figma-code-connect` for component mappings when available.
3. Use `figma-generate-design` or Figma API workflow for editable screen output.
4. Preserve component names, variants, tokens, and source file references.
5. Return changed node IDs, mapping files, and validation gaps.

## Rules

- Do not create disconnected Figma art when Code Connect is the requested
  outcome.
- Do not inspect secret-bearing app state to generate design artifacts.
