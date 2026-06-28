# Architectural Smells

Architectural smells usually indicate boundary damage.

## Layer leaks

- Business logic in handlers/controllers.
- HTTP details inside domain logic.
- ORM models used as domain models without explicit project intent.
- SQL/storage concerns inside application policy.
- Infrastructure exceptions leaking through public API responses.
- Configuration objects passed everywhere.
- Presentation state influencing hardware control logic.

## Dependency damage

- Domain depends on infrastructure.
- Application layer imports concrete adapters unnecessarily.
- Infrastructure owns business rules.
- Cross-layer cycles.
- Shared mutable global state across layers.
- Framework lifecycle controls domain behavior.

## Domain damage

- Anemic domain where all rules live in services despite rich invariants.
- Over-modeled domain where simple CRUD became a ceremonial aggregate festival.
- Bounded contexts share models with different meanings.
- Domain events used as async function calls in disguise.
- Value objects skipped where invalid primitive states are common.

## Persistence damage

- Transactions hidden in low-level helpers.
- Multi-step writes without transaction boundaries.
- N+1 query patterns.
- Migrations containing business behavior.
- Schema fields assumed but not verified.
- Repositories that are just generic database access with no business-facing contract.

## Integration damage

- External API specifics leaking into domain code.
- Retry policies scattered across call sites.
- Timeouts missing on external calls.
- Idempotency ignored for retryable operations.
- Error mapping duplicated inconsistently.

## Response rule

Do not impose architecture purity for its own sake.

Fix architectural smells only when they affect correctness, maintainability, testability, safety, or the user's explicit goal.
