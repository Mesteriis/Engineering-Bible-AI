---
name: [be] fix-security-finding
description: "Исправляет один подтверждённый или правдоподобный security finding минимальными изменениями, regression coverage и доказательством исправления."
---

# Fix Security Finding

Fix one finding without broad refactors.

## Workflow

1. Read `fix-finding` from Codex Security if available.
2. Confirm source, sink, control point, affected asset, and attacker input.
3. Reproduce, encode, or reason through the failure path.
4. Apply the smallest correct fix.
5. Add regression coverage when the repo supports tests.
6. Validate that the old path is blocked and normal behavior still works.

## Output

- finding fixed
- files changed
- regression coverage
- validation commands
- remaining proof gaps

## Rules

- Do not fix unrelated findings.
- Do not hide uncertainty.
- Do not weaken validation or authorization for convenience.
