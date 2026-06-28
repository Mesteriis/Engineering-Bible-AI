# API Philosophy

An API is a contract. Treat it as a product boundary, not as a convenient way to expose whatever the database happened to look like during a late-night sprint. Humanity tried that. The logs are not flattering.

## Scope

This document applies to:

- public HTTP APIs;
- internal service APIs;
- RPC interfaces;
- SDK surfaces;
- events and webhooks;
- streaming interfaces;
- CLI contracts when other systems automate them.

## Core principles

- Define the caller, purpose, invariants, failure modes, and compatibility expectations before exposing the API.
- Keep transport models separate from persistence models unless the project is intentionally tiny and the coupling is acceptable.
- Prefer additive changes over breaking changes.
- Make retries safe with idempotency when callers can reasonably retry.
- Make pagination, filtering, ordering, and consistency explicit.
- Return errors that callers can act on.
- Do not expose internal enum names, database column names, stack traces, framework errors, or infrastructure details as contract.
- Authentication answers who the caller is. Authorization answers what this caller may do. Do not blend them into wishful middleware soup.

## Protocol selection

Use the smallest protocol that fits the interaction:

| Need | Prefer | Avoid |
|---|---|---|
| Resource lifecycle with stable nouns | REST-like HTTP | RPC names pretending to be resources |
| Command with strong intent | RPC or command endpoint | Forcing noun-shaped REST when the action is the concept |
| Fact that already happened | Event | Synchronous callback chains |
| External asynchronous notification | Webhook | Polling by default |
| Long-running ordered output | Stream | Large fake paginated blobs |
| Human/manual automation | CLI | Hidden config mutation |

## Compatibility rules

Backward-compatible changes usually include:

- adding optional request fields;
- adding response fields that clients must ignore if unknown;
- adding new event types with clear versioning;
- adding new enum values only if clients are documented to tolerate unknown values.

Breaking changes include:

- removing or renaming fields;
- changing field meaning;
- changing default behavior;
- changing validation rules in a way that rejects previously valid requests;
- changing ordering, pagination, idempotency, or consistency guarantees;
- changing error codes that clients branch on.

Breaking changes require an explicit migration path.

## Request design

A request should make the operation unambiguous:

- identify the target resource or command;
- carry caller intent, not internal implementation detail;
- validate at the boundary;
- reject impossible combinations early;
- separate identity, filters, payload, and options;
- avoid boolean parameters that create hidden modes.

Prefer named modes or separate endpoints when behavior changes materially.

## Response design

A response should answer the caller's next useful question:

- what happened;
- what resource or operation was affected;
- what state is now observable;
- what the caller may do next;
- what failed and whether retry can help.

Do not return accidental data just because it is cheap to serialize.

## Error contract

Every API error should define:

- stable machine-readable code;
- human-readable message safe for logs and UI;
- HTTP/RPC status or protocol-level equivalent;
- retryability;
- field-level validation details when relevant;
- correlation or request identifier when available;
- safe remediation hint when useful.

Do not leak secrets, SQL, stack traces, filesystem paths, or provider internals.

## Idempotency

Use idempotency when:

- clients may retry after timeouts;
- the operation creates money, orders, payments, messages, tickets, hardware actions, or irreversible side effects;
- network failure can leave the caller uncertain whether the operation succeeded.

An idempotent operation must define:

- idempotency key scope;
- replay window;
- request equivalence rules;
- stored response behavior;
- conflict behavior when the same key is reused with different payload.

## Pagination and listing

List endpoints must define:

- ordering;
- cursor or offset behavior;
- maximum and default page size;
- consistency expectation under concurrent writes;
- filter semantics;
- whether total count is exact, approximate, omitted, or expensive.

Unbounded list endpoints are production incidents wearing a nice hat.

## Versioning

Prefer versioning at the contract boundary, not inside random fields.

Version when:

- old and new behavior must coexist;
- migration takes more than one coordinated deploy;
- clients outside the repository need time to adapt;
- events are persisted or replayed.

Do not version for every additive change.

## API review checklist

Before merging an API change, verify:

- caller and use case are named;
- authn/authz behavior is explicit;
- request and response are stable contracts;
- validation is defined;
- error codes are actionable;
- idempotency is considered;
- pagination and ordering are defined for lists;
- compatibility impact is known;
- tests cover success, validation failure, authorization failure, and at least one operational failure mode.
