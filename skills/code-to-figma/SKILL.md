---
name: code-to-figma
description: "Send, recreate, or connect an implemented UI back into Figma. Use for live UI to editable Figma layers, Code Connect mapping, component library updates, design handoff, and keeping Figma in sync with production components."
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
