# Design Principles Reference

Status: legacy/deprecated compatibility reference. Prefer authoritative
standards under `engineering/`, especially `engineering/05_design_principles.md`
and `engineering/06_responsibility_model.md`.

## Principles as Behavior, Not Slogans

Do not merely mention SOLID, KISS, DRY, YAGNI, Clean Architecture, DDD, or TDD.

Apply their practical meaning.

## SOLID

### Single Responsibility

Every unit should have one reason to change.

Apply at:

- function;
- class/type;
- file/module;
- package/component;
- service/use case;
- layer;
- bounded context.

### Open/Closed

Prefer designs where new behavior can be added without modifying unrelated existing behavior.

Do not over-abstract for imaginary extensions.

### Liskov Substitution

Subtypes/implementations must preserve the expectations of their contracts.

Do not create polymorphism where implementations have incompatible behavior.

### Interface Segregation

Prefer small focused interfaces over broad capability bags.

Consumers should not depend on methods they do not use.

### Dependency Inversion

Depend on stable abstractions when it reduces coupling and clarifies boundaries.

Do not introduce interfaces as decoration.

## KISS

The simplest correct solution wins.

Simple does not mean sloppy.

Simple means:

- fewer moving parts;
- explicit behavior;
- clear boundaries;
- local reasoning;
- fewer hidden side effects;
- fewer magical abstractions.

## DRY

Avoid duplication of knowledge.

Duplicated lines are not always duplicated knowledge.

Do not create a bad abstraction merely to remove two similar snippets.

## YAGNI

Do not build features, abstractions, layers, configuration systems, or extension points before there is evidence they are needed.

## Clean Architecture

Business rules should be independent from frameworks, transport, persistence, and external systems.

Use boundaries where they reduce coupling and protect domain logic.

## DDD

Use domain language.

Keep invariants close to domain concepts.

Respect bounded contexts.

Do not apply DDD ceremony to simple scripts or CRUD code without domain complexity.

## TDD

Tests are a design feedback tool.

Prefer tests that describe behavior before or alongside implementation.

Bug fixes should have regression tests whenever possible.
