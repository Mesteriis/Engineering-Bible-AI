# Testing Philosophy

Tests are executable claims about behavior.

## Principles

- Test behavior, not implementation trivia.
- Prefer tests that fail for the right reason.
- Prefer integration tests at meaningful boundaries when unit tests require excessive mocking.
- Add regression tests for bug fixes whenever feasible.
- Cover failure paths, invalid input, edge cases, and boundary conditions.
- Keep tests readable as documentation.
- Do not weaken tests to make code pass.
- Do not assert mock calls unless the interaction is the behavior.

## TDD

Use TDD when it improves design feedback:

1. Express expected behavior with a failing test.
2. Implement the smallest correct behavior.
3. Refactor with tests green.

Do not perform fake TDD by writing tests after the fact and pretending they guided design.

## Test boundaries

Good test seams are often:

- public API behavior;
- service/use-case behavior;
- domain rules;
- parser/serializer contracts;
- database transaction behavior;
- external integration adapters using fakes/contracts;
- hardware safety behavior using simulations where possible.

## Mock discipline

Mock only what is outside the boundary under test.

Avoid mocking the thing whose behavior you are trying to verify.

## Validation reporting

Always report exact commands and results.
