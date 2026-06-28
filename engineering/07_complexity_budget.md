# Complexity Budget

These thresholds are not aesthetic preferences. They are early warning systems.

## Logical size thresholds

For human-authored source code:

| Unit | Warning | Strong refactor candidate | Unacceptable without explicit justification |
|---|---:|---:|---:|
| Function/method | > 60 logical lines | > 100 logical lines | > 150 logical lines |
| Class/type | > 300 logical lines | > 500 logical lines | > 800 logical lines |
| File/module | > 800 logical lines | > 1,500 logical lines | > 10,000 logical lines |
| Package/component | unclear public surface | repeated unrelated changes | dumping ground |

Human-authored 10,000-line files are unacceptable except for extraordinary legacy containment work with an explicit migration plan.

Generated, vendored, lock, snapshot, and large migration files may be exceptions when the repository expects them.

## Shape thresholds

Treat these as suspicious and justify or refactor:

- nesting deeper than 3 levels;
- more than 5 parameters without a clear value object/config object;
- more than 8 meaningful branches in one function;
- more than 20 public methods on one class/type;
- more than 20 imports in one module;
- repeated conditionals over the same type/status/mode;
- broad switch/match blocks that keep growing;
- functions that both decide and perform external side effects.

## Split rules

Split by:

- responsibility;
- domain concept;
- lifecycle;
- side-effect boundary;
- dependency boundary;
- volatility;
- public API boundary.

Do not split by:

- arbitrary line count alone;
- alphabetical grouping;
- “misc” categories;
- technical layer when the project intentionally uses a simpler structure.

## Complexity response

When a threshold is exceeded:

1. Name the smell.
2. Explain the responsibility overload.
3. Propose the smallest useful split.
4. Preserve behavior.
5. Add or preserve validation.
