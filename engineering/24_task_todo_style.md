# Task and TODO Style

Even temporary plans and TODO lists should follow the same engineering discipline as production code.

## Rule

A 100-line TODO must still be structured, testable, and responsibility-oriented.

Do not write chaotic task dumps.

## Good TODO structure

```markdown
# Task: <outcome>

## Goal

## Constraints

## Current State

## Target State

## Slices

### Slice 1: <small deliverable>
- Files:
- Change:
- Validation:
- Risks:

### Slice 2: <small deliverable>
- Files:
- Change:
- Validation:
- Risks:

## Definition of Done

## Open Questions
```

## Rules for task plans

- Split by deliverable, not by vague activity.
- Each slice should be independently understandable.
- Each slice should have validation.
- Risks must be visible.
- Avoid “cleanup later” unless there is an explicit follow-up.
- Do not use TODOs as fake implementation.

## Code TODOs

A code TODO is allowed only when:

- it is not required for correctness now;
- it names the missing behavior;
- it explains why it is deferred;
- it has enough context to act later;
- it does not hide a production failure.

Bad:

```text
TODO: fix later
```

Good:

```text
TODO(authz): replace temporary role check after policy engine lands; current behavior matches existing admin-only endpoint contract.
```
