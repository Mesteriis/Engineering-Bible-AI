---
name: debugging
description: "Reproduces failures, gathers evidence, tests hypotheses, fixes root causes, and adds regression coverage."
---

# Skill: debugging

## Purpose

Debug failures by evidence, not by randomly poking code until the CI lights stop blinking.

## Protocol

1. Reproduce or identify the failure.
2. Locate the smallest relevant code path.
3. Form explicit hypotheses.
4. Verify each hypothesis against code, logs, tests, or runtime behavior.
5. Fix the root cause, not only the symptom.
6. Add or update validation.
7. Report what failed, why, what changed, and how it was validated.

## Rules

- Do not patch blindly.
- Do not suppress errors to make tests pass.
- Do not broaden exception handling unless it is the correct domain behavior.
- Do not delete failing tests unless they are invalid and the reason is documented.
- Do not assume the stack trace is the root cause; it is evidence.
- Do not invent logs or command output.

## Failure Analysis

When investigating, collect:

- exact command or user action that fails;
- exact error message;
- relevant stack trace;
- recent changes if available;
- relevant configuration;
- dependency versions if relevant;
- environment differences if relevant.

## Hypothesis Format

Use concise hypotheses:

```markdown
Hypothesis: <what may be wrong>
Evidence: <what supports it>
Check: <how to verify>
Result: <confirmed/rejected>
```

Do not expose private chain-of-thought. Provide concise evidence summaries.

## Root Cause Fixes

Prefer fixes that:

- preserve intended behavior;
- add regression coverage;
- keep boundaries clean;
- make invalid states less likely;
- improve error messages when useful;
- avoid hidden side effects.

## Reporting

Final debugging report should include:

- symptom;
- root cause;
- changed files;
- validation;
- remaining risks.
## Extended References


For deeper work, read:

- `../../engineering/14_debugging_philosophy.md`
