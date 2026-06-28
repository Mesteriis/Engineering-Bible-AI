# Design Principles

This document translates common principles into concrete engineering behavior.

## SOLID

### Single Responsibility Principle

A unit should have one clear reason to change.

Apply this to functions, classes, files, packages, services, layers, and bounded contexts.

### Open/Closed Principle

Prefer extension points only where change is expected and justified.

Do not create abstract extension mechanisms for hypothetical future needs.

### Liskov Substitution Principle

A subtype or implementation must preserve the expectations of the interface it implements.

Do not narrow accepted inputs, surprise callers with new failure modes, or violate invariants.

### Interface Segregation Principle

Prefer focused interfaces that represent actual client needs.

Do not create large interfaces that force implementers to support behavior they do not own.

### Dependency Inversion Principle

High-level policy should not depend on low-level infrastructure details.

Use abstractions when they protect business logic from volatile infrastructure, not as decoration.

## KISS

Keep solutions simple by removing unnecessary moving parts.

Simple does not mean careless. A simple solution still handles errors, tests behavior, and respects boundaries.

## DRY

Avoid duplicated knowledge, not merely duplicated text.

Two similar code blocks may remain separate if they represent different concepts that can change independently.

Do not create shared abstractions that couple unrelated domains just to reduce line count.

## YAGNI

Do not build functionality, abstraction, configuration, extensibility, or infrastructure before there is evidence it is needed.

## Clean Architecture

Business rules should be independent from transport, persistence, frameworks, and external services where the project architecture supports that separation.

Dependencies should point toward stable policy and away from volatile details.

## DDD

Use domain modeling when the problem has meaningful business concepts and invariants.

Do not force DDD vocabulary into simple CRUD or script-like projects.

When DDD is appropriate, protect the ubiquitous language, aggregate boundaries, invariants, and domain events from infrastructure leakage.

## TDD

Use tests as design feedback when practical.

Bug fixes should start with or include a regression test whenever feasible.

Tests should verify behavior, not implementation trivia.
