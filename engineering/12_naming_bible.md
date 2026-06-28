# Naming Bible

Names are architecture. Bad names hide bad boundaries.

## General rules

- Name by domain role, not implementation trivia.
- Prefer specific nouns and verbs.
- Avoid `manager`, `helper`, `utils`, `processor`, `common`, `misc`, `stuff`, `data`, `object`, `thing` unless already established and precise in the project.
- A name should make invalid usage look suspicious.
- A name should answer: what does this own, decide, or transform?

## Common suffixes and when to use them

### Command

Use for an explicit request to perform an action.

### Handler

Use for code that handles one command, event, message, or request type.

### Policy

Use for a decision rule that may vary.

### Strategy

Use when multiple interchangeable algorithms exist.

### Repository

Use for a persistence-facing collection-like contract around domain/application concepts.

### Gateway

Use for an external system boundary.

### Client

Use for a concrete protocol/API integration.

### Provider

Use for supplying values from a source, especially when source may vary.

### Factory

Use only when object creation has meaningful rules or multiple implementations.

### Builder

Use only for staged or complex construction, not normal constructors.

### Parser

Use for text/bytes/structured input to internal representation.

### Mapper

Use for mechanical conversion between representations.

### Codec

Use for encode/decode pairs.

### Projection

Use for read-optimized representation derived from source data.

### Snapshot

Use for captured state at a point in time.

### Aggregate

Use only in DDD contexts with real consistency boundaries.

### Entity

Use for identity-bearing domain object.

### Value Object

Use for immutable value with validation/invariants and no identity.

## Naming smell response

If a name is vague, first identify the hidden responsibility. Rename only after understanding the role.
