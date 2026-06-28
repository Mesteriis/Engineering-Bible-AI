---
name: testing-tdd
description: "Apply practical TDD, regression testing, and validation discipline for behavior changes."
---

# Skill: testing-tdd

## Purpose

Apply practical TDD and validation discipline without turning every task into ritualized suffering.

## Core Rules

- Every meaningful behavior change needs a validation strategy.
- Prefer automated tests when practical.
- Bug fixes should include regression tests whenever feasible.
- Tests should verify externally observable behavior, not implementation trivia.
- Do not claim tests passed unless actually run.
- If tests cannot be run, report exactly why.

## TDD Workflow

Use TDD when feasible:

1. Define expected behavior.
2. Write or update a focused failing test.
3. Implement the smallest code change.
4. Run the test and make it pass.
5. Refactor while keeping tests green.

TDD is preferred for:

- bug fixes;
- domain rules;
- parsing;
- validation;
- edge cases;
- state machines;
- business workflows;
- hardware safety behavior;
- security-sensitive behavior.

If writing the test first is impractical, still add or update tests before reporting done.

## Test Scope

Choose the smallest test level that proves behavior:

- unit test for pure logic and small components;
- integration test for persistence, external boundaries, framework wiring;
- contract test for adapters and APIs;
- regression test for a reproduced bug;
- smoke/build test for compile or packaging behavior;
- manual validation only when automation is unavailable or disproportionate.

## What to Cover

Tests should cover relevant:

- happy paths;
- edge cases;
- invalid input;
- failure paths;
- boundary conditions;
- cancellation/timeouts where applicable;
- persistence transaction behavior where applicable;
- restart/reconnect behavior where applicable;
- regression scenario that triggered the bug.

## Mocking Rules

Mocks are useful for boundaries, not for proving that implementation details were called.

Avoid tests that only assert:

- method X was called;
- private helper Y was invoked;
- implementation sequence Z happened.

Prefer asserting:

- returned value;
- persisted state;
- emitted event;
- error behavior;
- side effect at a boundary;
- user-visible behavior;
- hardware-safe final state.

## Fixtures and Test Style

Follow the existing test framework and fixture style.

Do not introduce a new test framework unless explicitly requested or clearly required.

Keep tests readable and deterministic.

Avoid:

- sleeps without time control;
- external network calls unless explicitly integration-tested;
- order-dependent tests;
- random data without deterministic seeds;
- over-broad snapshots;
- brittle assertions on formatting unless formatting is the behavior.

## Validation Reporting

Report exact commands:

```markdown
Validation:
- Ran: <command>
- Result: passed
```

If failed:

```markdown
Validation:
- Ran: <command>
- Result: failed
- Failure: <short relevant failure>
```

If not run:

```markdown
Validation:
- Not run.
- Reason: <specific reason>
```
## Extended References

For deeper work, read:

- `engineering/13_testing_philosophy.md`
