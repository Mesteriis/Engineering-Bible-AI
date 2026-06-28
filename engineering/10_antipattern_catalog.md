# Anti-pattern Catalog

Use this catalog to recognize recurring bad designs.

## Common anti-patterns

### AbstractFactoryFactory

Too many abstract layers exist before real variation exists.

Fix: collapse unnecessary abstractions and keep the first useful seam.

### Singleton Abuse

Global instance controls behavior and hides dependencies.

Fix: pass dependencies explicitly or isolate lifecycle at composition root.

### Repository Everywhere

Every operation gets a repository even when it adds no boundary or language.

Fix: use repositories only where they express a persistence-facing contract.

### Service Locator

Code asks a global container for dependencies.

Fix: inject explicit dependencies where practical.

### MegaConfig

One configuration object leaks across the codebase.

Fix: pass focused settings to the component that needs them.

### MegaEnum

One enum grows to represent unrelated concepts.

Fix: split by domain meaning and lifecycle.

### Global Event Bus Abuse

Events are used to hide control flow.

Fix: keep direct calls for local orchestration; use events for real decoupling.

### Base Class Trap

A base class shares convenience code without a true substitution relationship.

Fix: prefer composition or focused helpers with explicit names.

### Magic Context

Behavior depends on implicit request/session/task context.

Fix: pass required data explicitly or constrain context usage to boundaries.

### Everything Utility

A utility module becomes the unofficial architecture.

Fix: move functions to domain-specific modules with clear ownership.

### Over-clean Architecture

A small feature gets too many layers, DTOs, interfaces, factories, and mappers.

Fix: keep architecture proportional to the problem and repository style.

## Rule

An anti-pattern label is useful only if it leads to a smaller, safer, clearer design.
