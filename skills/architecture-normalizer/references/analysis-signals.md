# Analysis Signals

Use these signals to produce deterministic findings. They guide analysis; policy decides thresholds.

## Responsibility Violations

Look for files or packages that combine unrelated reasons to change:

- transport, parsing, persistence, domain rules, and presentation in one file
- unrelated public types in one module
- mixed naming domains in symbols, tests, or imports
- broad modules with forbidden generic names
- import sets spanning unrelated subsystems

Every split recommendation must name the target responsibilities and evidence.

## Coupling Signals

Detect and report:

- cyclic imports or include cycles
- bidirectional dependencies between packages
- imports of internal modules across package boundaries
- public API consumers importing moved internals directly
- feature envy: a module operating mostly on another module's data
- layer inversion, such as infrastructure importing UI or domain importing transport

Use graph edges from imports/includes/package dependencies where available.

## Cohesion Signals

High cohesion evidence:

- symbols share domain vocabulary
- tests exercise the same responsibility
- imports support one concern
- public API surface is small and explicit

Low cohesion evidence:

- unrelated exported types
- high fan-in/fan-out without a clear facade role
- functions changing for different feature areas
- constants, DTOs, errors, and transport code grouped by convenience rather than domain

## Duplicate Concept Signals

Report likely duplicates when names, fields, enum variants, or errors overlap across modules:

- duplicate DTO/model names with similar fields
- repeated enums representing the same state
- copied error types/messages
- parallel request/response types for the same external API

Do not merge duplicates during execution unless a reviewed artifact explicitly approves it.

## Entropy Scoring

Score each metric from 0 to 100:

- 90-100: clear structure, low coupling, explicit APIs, minimal exceptions
- 70-89: mostly healthy, localized issues
- 40-69: mixed responsibilities or dependency issues in important areas
- 0-39: architecture actively resists safe change

Every score must include evidence in `why`.

## Proposed Layout Heuristics

Prefer domain-first hierarchy:

```text
api/
  google/
    client.py
    requests/
    responses/
    errors/
    auth/
    transport/
    pagination/
```

Avoid flat or generic structures:

```text
google.py
helpers.py
utils.py
common.py
```

The proposed layout must preserve public APIs through explicit exports or compatibility artifacts.
