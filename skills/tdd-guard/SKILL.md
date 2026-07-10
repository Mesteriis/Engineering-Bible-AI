---
name: tdd-guard
description: "Strict test-first gate only when explicitly requested or required by repository policy. Do not use for ordinary practical testing."
---

# TDD Guard

Use this skill when a task changes behavior and there is a realistic way to
write or update tests before implementation.

This is a Codex-native adaptation of TDD guardrail ideas. It does not install
Claude Code hooks or reporters. It enforces sequencing through task gates,
evidence, and explicit validation.

## When To Use

Use for:

- bug fixes;
- features;
- parser or API behavior changes;
- business logic;
- security fixes where regression coverage is possible;
- refactors that must preserve behavior.

Do not force TDD for:

- docs-only changes;
- formatting-only changes;
- generated files;
- exploratory read-only analysis;
- emergency repair where the user explicitly accepts a no-test path.

## Workflow

1. Identify the behavior under change.
2. Find the nearest existing test style and command.
3. Add or update the smallest failing test first.
4. Run the focused test and record the failing result.
5. Implement the minimal code needed to pass.
6. Run the focused test again.
7. Run broader validation if the blast radius is shared.
8. Refactor only after the test passes.

## Guard Rules

- Do not edit production behavior before a test plan exists.
- If a failing test cannot be added, state why and choose the strongest
  alternative validation.
- Do not add broad abstractions before the test demands them.
- Do not hide behind snapshots when explicit assertions are practical.
- Keep one behavior per test unless the existing suite uses scenario tests.
- Preserve existing test runner, fixture, factory, and assertion conventions.

## Escape Hatch

If TDD is not appropriate, write a short exception:

```markdown
TDD exception:
- Reason:
- Alternative validation:
- Residual risk:
```

## Output

Report:

- test added or updated;
- first failing command and result, when available;
- implementation summary;
- passing validation command;
- exception reason if no failing test was created.
