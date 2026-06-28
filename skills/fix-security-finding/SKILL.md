---
name: fix-security-finding
description: "Fix one validated or plausible security finding with minimal code changes, regression coverage, and proof. Use when the user provides a vulnerability, scan finding, exploit path, or security review item to remediate."
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
