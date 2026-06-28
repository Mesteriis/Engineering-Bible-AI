# Evolution Rules

Software should become easier to change over time, not merely larger.

## Rules

- Every new abstraction must remove more complexity than it adds.
- Every dependency must justify its maintenance cost.
- Every layer must earn its existence.
- Every interface must protect a real boundary or represent real variation.
- Every public API should be smaller than the implementation behind it.
- Every module should have a clear owner responsibility.
- Every workaround needs either a removal path or a reason it is permanent.
- Every large legacy file needs containment and a gradual split strategy.
- Every repeated rule should move toward one source of truth.
- Every test should make future change safer.

## When adding code

Ask:

- Can existing code solve this cleanly?
- Is the new responsibility in the right place?
- What future change will this make easier?
- What future change will this make harder?
- How will this fail?
- How will this be tested?
- How will this be deleted?

## When removing code

Prefer removing:

- unused abstractions;
- dead flags;
- obsolete compatibility paths;
- duplicated conversion logic;
- generic helpers used once;
- test fixtures that hide behavior;
- documentation for behavior that no longer exists.
