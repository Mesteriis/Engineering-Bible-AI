---
name: architecture-map
description: "Map a repository or subsystem architecture before changes, reviews, migrations, onboarding, or agent handoff. Use for bounded domains, ownership boundaries, dependency direction, entrypoints, test surfaces, runtime services, and risk hotspots."
---

# Architecture Map

Build a compact, verified architecture map from current files.

## Workflow

1. Read repo instructions and top-level dependency/build files.
2. Identify entrypoints, layers, data flow, external integrations, and tests.
3. Map dependency direction and boundary violations.
4. Record uncertainty separately from verified facts.
5. Keep the output short enough to guide implementation or review.

## Output

- repo shape
- main layers or bounded domains
- important entrypoints
- persistence/integration/config surfaces
- test and validation commands found
- risks and unknowns
- suggested next skill if applicable

## Rule

Do not invent architecture. Every claim must come from files, commands, or
explicit user-provided context.
