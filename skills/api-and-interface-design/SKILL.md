---
name: api-and-interface-design
description: "Use when designing or changing an API, RPC, CLI, endpoint, schema, public function signature or plugin contract: «спроектируй API/интерфейс», «добавь эндпоинт», «поменяй контракт», breaking changes, versioning, pagination, retries, error format. Not for internal module seams (architecture-principles)."
---

# Skill: api-and-interface-design

Design interfaces that are stable, documented and hard to misuse. Applies to
HTTP/RPC APIs, CLIs, schemas, public library functions and plugin contracts.

## Hyrum's law

With enough users, every observable behaviour becomes depended on, whatever the
contract says: error text, ordering, timing, undocumented quirks.

- Be deliberate about what is exposed; do not leak implementation details.
- Treat every observable behaviour of a published interface as a commitment.
- Plan deprecation at design time; tests alone do not catch undocumented use.
- Prefer one live version of a thing: extend rather than fork.

## Contract first

Write the contract (types, schema, signatures, documented errors) before the
implementation, and commit it with the code. For each operation state inputs,
outputs, server-generated fields, error cases and whether it is safe to retry.
Keep input shapes separate from output shapes. Model variants as explicit tagged
unions, not flags and nullable fields.

## Error model

Pick one error strategy and use it everywhere.

- One structured shape: machine-readable `code`, human `message`, optional
  `details`. Clients branch on `code`, never on message text.
- Map causes consistently: invalid input, unauthenticated, forbidden, not found,
  conflict, unprocessable, internal. Never expose internals in server errors.
- Do not mix throwing, returning null and returning an error object for the same
  kind of failure.

## Validate at the edge

- Validate where external input enters: request handlers, CLI arguments, config
  and environment loading, parsing of third-party responses.
- Treat third-party responses as untrusted data: check shape and content before
  use.
- Inside the trusted core rely on types; do not scatter re-validation through
  internal functions or over data read from your own store.

## Backwards compatibility

- Prefer additive change: new optional fields, new operations, new enum values
  that old clients can ignore or default.
- Do not remove or rename fields, change types, tighten validation or change
  defaults in place; that is a breaking change.
- Breaking change: introduce a new version or name, run both with a documented
  deprecation window, and say who is affected. Do not keep many versions alive.
- Check consumers (search the repo, clients, docs) before declaring a change safe.

## Idempotency and retries

- Mark each state-changing operation as idempotent or document it unsafe to
  retry. Deletes and PUT-style replaces should be idempotent.
- Derive an idempotency key from the intent (stable across retries, different
  across intents), supplied by the client or initiating event; never a fresh
  random value or timestamp per attempt.
- Claim the key atomically (unique constraint), not check-then-act. Reusing a key
  with a different payload must fail loudly. Decide what an in-flight duplicate
  gets: reject (conflict), wait with a bound, or return pending plus a status
  location.
- A timeout means outcome unknown, not failure. Record intent before the call.
- Keep keys longer than the longest retry or replay path.

## Pagination and limits

- Paginate every list operation from the start; prefer cursors for changing data.
- Enforce and document a maximum page size, a default, and a stable sort order.
- Bound request size, filter complexity and rate; state the limits in the
  contract and the error returned when exceeded.
- Support partial update (patch semantics) where full replacement forces clients
  to send data they do not own.

## Naming

- One convention per surface; follow what the repository already uses.
- Resources as nouns; operations as verbs only where the style is RPC or CLI.
- Booleans read as questions (`is_`, `has_`, `can_`); units and time zones are
  part of the name or the type; identifiers are distinct types where the
  language allows.
- Same concept, same word, everywhere.

## Red flags

- Same operation returning different shapes by condition.
- Inconsistent error formats; verbs in resource paths.
- List operations without pagination or limits.
- Breaking changes to existing fields without a version or deprecation path.
- Idempotency key read then written in separate steps.
- Third-party data used without validation.

## Verification

- [ ] Every operation has typed input and output and documented errors.
- [ ] One error format; validation only at the edge.
- [ ] Lists paginated with documented limits.
- [ ] New fields additive; breaking changes versioned and announced.
- [ ] State-changing operations idempotent or documented unsafe to retry.
- [ ] Contract committed with the implementation; consumers checked.
