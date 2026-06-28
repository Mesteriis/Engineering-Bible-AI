# Data Philosophy

Data outlives code. This is inconvenient, so naturally software teams keep pretending migrations are a side quest.

## Core principles

- Every important fact needs a source of truth.
- Ownership of data must be explicit.
- Schema changes are product changes when external behavior depends on them.
- Derived data must be labeled as derived.
- Caches are copies, not truth.
- Deletion, retention, and privacy requirements are design inputs.
- Consistency choices must be intentional.
- Data migrations need validation and rollback thinking.

## Source of truth

For each domain fact, identify:

- owning system;
- write path;
- read paths;
- consistency model;
- retention rule;
- audit requirement;
- recovery strategy.

If two systems can independently edit the same fact, you have a conflict policy whether you admit it or not.

## Data ownership

Data ownership answers:

- who may write it;
- who may read it;
- who defines its meaning;
- who migrates it;
- who deletes it;
- who handles incidents involving it.

Shared tables and shared schemas are allowed only when ownership and invariants are explicit.

## Schema changes

Schema changes must consider:

- forward compatibility;
- backward compatibility;
- deploy order;
- backfill strategy;
- validation before and after migration;
- rollback or roll-forward plan;
- effect on queries, indexes, caches, exports, and downstream consumers.

Prefer expand-and-contract migrations for production systems:

1. Add new nullable/compatible shape.
2. Write both old and new if needed.
3. Backfill.
4. Read new shape.
5. Stop writing old shape.
6. Remove old shape after verification.

Skipping steps is allowed only when blast radius is understood. This is not a vibes-based activity, despite industry tradition.

## Caches

A cache must define:

- source of truth;
- key structure;
- value schema;
- TTL or invalidation rule;
- consistency expectation;
- stampede protection if needed;
- behavior when cache is unavailable;
- observability.

Do not put irreplaceable data only in cache.

## Projections and read models

Use projections when read needs differ from write needs.

A projection must define:

- source events or tables;
- rebuild process;
- lag expectation;
- idempotency;
- failure handling;
- whether clients can tolerate stale data.

A projection is not the source of truth unless explicitly promoted to one.

## Event sourcing

Event sourcing is appropriate when:

- audit history is central;
- state reconstruction matters;
- domain events are meaningful and stable;
- temporal queries matter;
- the team accepts event versioning and operational complexity.

Do not use event sourcing merely because append-only sounds elegant. Many disasters also append successfully.

## Retention and deletion

Data design must define:

- retention period;
- legal or business hold behavior;
- deletion semantics;
- anonymization or pseudonymization when applicable;
- backup behavior;
- derived data cleanup;
- audit log treatment.

Delete means little if every projection, cache, export, and backup quietly keeps the ghost.

## Consistency

Name the consistency model:

- strong consistency;
- read-your-writes;
- eventual consistency;
- monotonic reads;
- best-effort freshness;
- explicitly stale snapshot.

Then design UI, API, retries, and support workflows around that truth.

## Review checklist

Before merging a data change, verify:

- source of truth is named;
- owner is clear;
- migration path is safe;
- derived data is labeled;
- cache invalidation or TTL is defined;
- consistency model is explicit;
- retention and deletion are considered;
- tests or scripts validate migration and rollback assumptions where practical.
