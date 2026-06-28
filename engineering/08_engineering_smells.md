# Engineering Smells

A smell is not automatically a bug. It is evidence that demands inspection.

## Structural smells

- God Function: one function owns multiple decisions and side effects.
- God Class: one type owns unrelated state and behavior.
- God File: one file changes for unrelated reasons.
- God Package: one package exposes unrelated capabilities.
- Long Function: control flow is too large to reason about locally.
- Deep Nesting: the happy path is buried under conditions.
- Boolean Parameter: one function secretly contains multiple behaviors.
- Parameter Train: many parameters move together and want a value object.
- Primitive Obsession: domain concepts are represented as raw strings, ints, or dicts everywhere.
- Magic Numbers/Strings: undocumented constants encode policy.
- Duplicate Knowledge: the same business rule exists in multiple places.
- Shotgun Surgery: one change requires editing many unrelated places.
- Divergent Change: one unit changes for many unrelated reasons.

## Dependency smells

- Hidden I/O: a function performs network, disk, DB, or hardware operations without making that clear.
- Hidden State: behavior depends on globals, contextvars, singletons, or mutable module state.
- Temporal Coupling: calls must happen in a specific undocumented order.
- Circular Dependency: modules/packages depend on each other in both directions.
- Service Locator: dependencies are pulled from a global container instead of being explicit.
- Static State: shared mutable state controls behavior across calls.

## Naming smells

- Utility Hell: `utils` becomes a graveyard of unrelated helpers.
- Helper Hell: `helpers` hides missing domain vocabulary.
- Manager Hell: `Manager` owns everything because nobody named the real responsibilities.
- Processor Hell: `Processor` means “something happens here, good luck.”
- BaseClass Abuse: inheritance exists to share code, not model substitutable behavior.

## Testing smells

- Mock Theater: tests only verify calls to mocks.
- Snapshot Abuse: large snapshots hide behavior instead of explaining it.
- Brittle Test: tests break on harmless refactors.
- No Failure Tests: only happy path is validated.
- Test Knows Too Much: test mirrors implementation details.

## Response rule

When a smell is relevant, name it, explain why it matters, and propose a targeted fix. Do not invent smells just to sound clever.
