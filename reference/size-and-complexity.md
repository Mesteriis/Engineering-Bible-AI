# Size and Complexity Reference

Status: legacy/deprecated compatibility reference. Prefer authoritative
standards under `engineering/`, especially `engineering/07_complexity_budget.md`
and `engineering/08_engineering_smells.md`.

## Goal

Prevent code from growing into giant files, god objects, accidental frameworks, and other evidence that civilization was a mistake.

## Default Limits for Human-Authored Source

These are defaults, not laws of physics. Project-local rules may override them.

| Unit | Suspicious | Split or justify | Hard failure |
|---|---:|---:|---:|
| Function | >60 logical lines | >100 logical lines | Project-specific |
| Class/type | >300 logical lines | >500 logical lines | Project-specific |
| File/module | >800 logical lines | >1,500 logical lines | >10,000 logical lines |
| Package/component | unclear public API | mixed responsibilities | repository becomes a junk drawer |

Generated, vendored, lock, and machine-produced migration files may be exceptions.

## Splitting Rules

Split by responsibility, not by arbitrary size.

Good split reasons:

- separate domain concepts;
- separate layer boundary;
- separate infrastructure adapter;
- separate validation/parsing from execution;
- separate public API from internals;
- separate hardware responsibilities;
- separate state machine from transport.

Bad split reasons:

- every 200 lines regardless of cohesion;
- random alphabetical grouping;
- moving everything into `utils`;
- hiding complexity behind vague managers.

## Complexity Smells

A unit is too complex when:

- it needs many unrelated comments/sections;
- it has multiple reasons to change;
- tests require huge setup;
- adding one case breaks unrelated behavior;
- errors are handled inconsistently;
- dependencies point in every direction;
- the name must be vague because the responsibility is vague.

## Refactoring Large Files

1. Identify responsibilities.
2. Identify public API.
3. Identify tests and behavior contracts.
4. Extract cohesive units.
5. Preserve dependency direction.
6. Validate after each meaningful slice.
7. Avoid unrelated behavior changes.
