# Concurrency Philosophy

Concurrency is not a performance feature first. It is a correctness problem that occasionally makes things faster, presumably as an apology.

## Core principles

- Shared mutable state must have an owner.
- Every wait needs a timeout or cancellation path unless the process lifetime deliberately owns it.
- Every queue needs a bound or an explicit reason it is unbounded.
- Every retry needs idempotency or a clear proof that duplication is harmless.
- Every lock needs a small scope and an ordering rule when multiple locks exist.
- Every background task needs ownership, shutdown behavior, and error handling.
- Backpressure is design, not a surprise memory graph.

## Choose the concurrency model deliberately

| Need | Prefer | Watch for |
|---|---|---|
| Many waiting I/O operations | Async I/O | Blocking calls inside event loop |
| CPU parallelism | Workers/processes/threads depending on runtime | Shared mutation and serialization cost |
| Ordered per-resource behavior | Actor or keyed queue | Hot keys and starvation |
| Short critical section | Lock/mutex | Lock ordering and deadlocks |
| External system smoothing | Bounded queue | Unbounded backlog and stale work |
| Periodic work | Scheduler with explicit ownership | Overlapping runs |
| Retry after failure | Durable job with idempotency | Duplicate side effects |

## Ownership

Every mutable resource should have exactly one clear owner at a time:

- a single task;
- a lock-protected object;
- an actor;
- a database transaction;
- a queue partition;
- an external service with documented consistency.

If ownership is unclear, races are not a possibility. They are a scheduling decision away from reality.

## Cancellation and shutdown

Long-running work must define:

- how it starts;
- who owns it;
- how it receives cancellation;
- how it releases resources;
- whether partial work is committed, rolled back, or resumed;
- how errors are reported.

Fire-and-forget tasks are allowed only when losing the task is acceptable and documented.

## Timeouts

External waits need timeouts:

- network calls;
- database calls;
- queue operations;
- locks where deadlock or starvation is possible;
- hardware interactions;
- child processes.

A timeout should map to a domain or operational error, not vanish into logs like a tiny bureaucratic ghost.

## Backpressure

Backpressure answers what happens when producers are faster than consumers.

Choose one:

- reject new work;
- slow producers;
- drop stale work;
- coalesce work;
- spill to durable storage;
- scale consumers;
- degrade non-critical features.

Do not choose accidental memory growth.

## Locks

Lock rules:

- keep critical sections small;
- avoid external calls while holding locks;
- define lock ordering when multiple locks can be acquired;
- document what invariant the lock protects;
- prefer higher-level ownership models when lock reasoning becomes complex.

## Queues and workers

A worker queue must define:

- message schema;
- idempotency key;
- retry policy;
- dead-letter policy;
- ordering requirements;
- visibility timeout or lease behavior;
- maximum concurrency;
- shutdown behavior;
- observability fields.

## Tests

Concurrency tests should focus on invariants, not sleep-based optimism.

Prefer:

- deterministic scheduling where available;
- stress tests around known race boundaries;
- fake clocks;
- explicit barriers/latches;
- property tests for idempotency;
- database constraint tests for concurrent writes.

Avoid tests that pass because the machine was feeling generous.

## Smells

Treat these as concurrency smells:

- unbounded queues;
- missing timeouts;
- background tasks without ownership;
- retries around non-idempotent side effects;
- locks held during I/O;
- shared dictionaries/maps mutated from many tasks;
- async functions that perform blocking work;
- overlapping scheduled jobs without coordination;
- race fixes that add sleeps.

## Review checklist

Before merging concurrent behavior, verify:

- mutable state ownership is explicit;
- cancellation and shutdown are defined;
- timeouts exist for external waits;
- retry and idempotency behavior is clear;
- queue bounds and backpressure are defined;
- locks protect named invariants;
- tests or constraints cover the important race boundary.
