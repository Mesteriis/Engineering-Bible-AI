# Domain Modeling

Domain modeling is the discipline of making business meaning explicit in code. It is not a costume party where every CRUD table receives a ceremonial aggregate because someone read a blog post in 2017.

## Use domain modeling when

Use explicit domain modeling when the problem contains:

- business invariants;
- state transitions;
- rules that must be protected from transport or persistence details;
- meaningful terminology shared by engineers and domain experts;
- behavior that will evolve independently from infrastructure;
- workflows with consequences beyond simple data entry.

Do not force domain modeling when the project is a small script, basic CRUD admin, one-off migration, or simple integration glue.

## Vocabulary

| Concept | Use when | Avoid when |
|---|---|---|
| Entity | Identity persists while attributes change | The value is fully described by its fields |
| Value Object | Equality comes from value, not identity | It has lifecycle, ownership, or mutable identity |
| Aggregate | A cluster of objects must protect invariants atomically | You only want a folder for related classes |
| Command | A caller requests a change | You are describing something that already happened |
| Domain Event | A domain fact happened | You need a request, intention, or future action |
| Policy | A rule selects behavior based on domain conditions | The rule is simple enough to stay near the caller |
| Domain Service | Behavior spans multiple concepts and does not belong to one entity/value | You need a dumping ground named `Manager` |
| Repository | Domain code needs collection-like persistence access | It becomes a generic database utility |
| Projection | Read model optimized for queries | It becomes the source of truth by accident |

## Invariants

An invariant is a rule that must remain true for the domain to be valid.

Examples:

- an order cannot be paid twice;
- a booking cannot overlap another booking for the same resource;
- a device command cannot be sent when the device is disabled;
- a user cannot grant permissions they do not hold.

Rules:

- Put invariants near the state they protect.
- Validate invariants before side effects.
- Make invalid states hard to represent.
- Do not spread the same invariant across controllers, jobs, UI, tests, and database triggers without a single source of truth.

## Boundaries

A domain boundary should separate language and responsibility.

Strong signs that a boundary exists:

- teams use different vocabulary;
- data changes for different reasons;
- rules conflict or evolve independently;
- lifecycle differs;
- consistency needs differ;
- the same word means different things in different areas.

When boundaries are unclear, prefer smaller modules and explicit translation over a large shared model that becomes a diplomatic disaster with imports.

## Entities

An entity should:

- own its identity;
- protect its invariants;
- expose meaningful behavior;
- avoid becoming a bag of mutable fields;
- avoid knowing about transport, persistence, UI, or framework details.

Bad sign:

- all entity behavior lives in services while the entity only stores data.

## Value objects

A value object should:

- be immutable where the language allows it;
- validate itself at construction;
- use names from the domain;
- make illegal combinations unrepresentable when practical.

Examples:

- `Money`;
- `EmailAddress`;
- `TemperatureRange`;
- `DeviceId`;
- `DateRange`.

Do not create value objects for every primitive by ritual. The ceremony is not the architecture.

## Aggregates

Use an aggregate when:

- several objects must change together;
- invariants span those objects;
- a consistency boundary matters;
- concurrent modification must be controlled.

Rules:

- Keep aggregate boundaries small.
- Reference other aggregates by identity, not object graph, unless the project intentionally uses a different persistence model.
- Do not use aggregates as arbitrary module folders.
- Avoid loading the universe to change one field.

## Commands and events

A command is an intention:

- `ApproveInvoice`;
- `ScheduleDeviceCommand`;
- `ChangeUserRole`.

An event is a fact:

- `InvoiceApproved`;
- `DeviceCommandScheduled`;
- `UserRoleChanged`.

Rules:

- Commands may be rejected.
- Events happened and must not be phrased as instructions.
- Events should contain enough stable information for consumers without exposing internal persistence shape.
- Persisted events need versioning and migration strategy.

## Domain services

Use a domain service only when behavior:

- is domain behavior;
- spans multiple entities or value objects;
- does not naturally belong to one of them;
- is not infrastructure orchestration.

A service named `Manager`, `Helper`, `Utils`, or `Processor` is presumed guilty until it proves a clear responsibility. Barbaric, but effective.

## Application services

Application services coordinate use cases:

- load domain objects;
- call domain behavior;
- persist changes;
- publish events;
- coordinate transactions;
- translate boundary errors.

They should not become the place where domain rules hide from the domain model.

## Review checklist

Before accepting a domain model change, verify:

- vocabulary matches the problem domain;
- invariants are named and protected;
- invalid states are rejected or made unrepresentable;
- boundaries are explicit;
- persistence and transport details do not leak inward;
- commands and events are not confused;
- services have specific responsibilities;
- tests cover invariant preservation and rejection paths.
