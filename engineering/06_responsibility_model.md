# Responsibility Model

Single Responsibility is a scale-independent principle.

## Function responsibility

A function should do one coherent operation.

A function is suspicious when it:

- validates input;
- performs business decisions;
- talks to external systems;
- mutates persistence;
- formats presentation;
- handles retries;
- logs operational events;
- and returns transport-specific responses all at once.

Split by decision boundary, not by arbitrary line count.

## Class/type responsibility

A class or type should represent one cohesive concept:

- domain state;
- lifecycle;
- policy;
- adapter;
- protocol implementation;
- dependency grouping with a clear reason.

A class is suspicious when it is named `Manager`, `Service`, `Helper`, or `Processor` without a more precise domain role.

## File/module responsibility

A file should contain a small set of closely related concepts.

A file is suspicious when unrelated changes repeatedly touch it.

A file is unacceptable when it becomes a dumping ground for utilities, handlers, DTOs, constants, and business rules together.

## Package/component responsibility

A package should expose one coherent capability.

A package is suspicious when its public API is a random inventory of unrelated helpers.

## Service/use-case responsibility

A service or use case should coordinate one application-level action.

It may orchestrate dependencies, transactions, policies, and domain operations, but should not become a domain model, repository, HTTP handler, and serializer at the same time.

## Layer responsibility

Each layer owns a kind of decision:

- transport layer: protocol details;
- application layer: orchestration;
- domain layer: rules and invariants;
- infrastructure layer: external systems;
- persistence layer: storage mechanics;
- configuration layer: runtime settings;
- presentation layer: user-facing representation.

Do not leak one layer's concerns into another unless the project intentionally uses a simpler architecture.

## Bounded context responsibility

A bounded context owns a language and model.

Do not share domain objects across contexts when the words look similar but mean different things.

## Change-reason test

Ask:

> What future change would require editing this unit?

If the answer lists unrelated reasons, split the unit.
