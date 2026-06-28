# State Machine Philosophy

Any workflow with statuses is already a state machine. The only question is whether the state machine is explicit, or whether it is hiding in scattered `if` statements like a raccoon in the walls.

## Use explicit state machines when

Use an explicit state model when:

- an object has named lifecycle states;
- valid transitions are limited;
- side effects depend on transitions;
- retries or concurrency can repeat operations;
- invalid transitions are meaningful errors;
- auditability matters;
- behavior differs by state.

## State design

A state should represent a meaningful condition, not a UI label or database convenience.

Good states:

- `draft`;
- `submitted`;
- `approved`;
- `rejected`;
- `cancelled`;
- `expired`.

Suspicious states:

- `pending2`;
- `processed_flag_true`;
- `new_new`;
- `failed_but_retrying_maybe`.

If the name sounds like a confession, redesign it.

## Transition design

Every transition should define:

- source state;
- target state;
- command or event causing the transition;
- guard conditions;
- side effects;
- idempotency behavior;
- emitted events;
- audit requirements.

Example:

| From | Action | To | Guard | Side effect |
|---|---|---|---|---|
| `draft` | `submit` | `submitted` | required fields valid | emit `Submitted` |
| `submitted` | `approve` | `approved` | actor can approve | emit `Approved` |
| `submitted` | `reject` | `rejected` | reason provided | emit `Rejected` |
| `approved` | `cancel` | `cancelled` | cancellation window open | emit `Cancelled` |

## Invalid transitions

Invalid transitions must not be silently ignored unless idempotency explicitly requires it.

Return or raise a domain error that names:

- current state;
- attempted transition;
- reason it is invalid;
- whether retry can help.

## Side effects

Separate transition validation from external side effects.

Prefer this order:

1. Load current state.
2. Validate transition.
3. Persist state change transactionally where possible.
4. Emit event or enqueue side effect.
5. Execute external side effect through an idempotent worker when needed.

Do not send email, charge money, call hardware, or publish irreversible messages before the transition is durable unless the system explicitly accepts that failure mode.

## Idempotency

A repeated command should be classified as:

- same command already applied: return prior result or no-op safely;
- conflicting command already applied: reject with conflict;
- stale command: reject with current state;
- retryable operational failure: allow retry using the same idempotency key.

## Concurrency

State transitions need concurrency control when two actors can change the same object.

Use one of:

- optimistic locking with version checks;
- pessimistic locking for short critical sections;
- single-threaded actor or queue per aggregate/resource;
- database constraints that protect invariants;
- compare-and-swap semantics.

Do not rely on hope. Hope is not a transaction isolation level.

## Smells

Treat these as state machine smells:

- multiple booleans encode lifecycle;
- repeated conditionals over the same status;
- impossible states can be represented;
- transitions are spread across controllers, jobs, UI, and database triggers;
- status changes without named transition methods;
- side effects happen before state is durable;
- tests cover states but not transitions;
- failed transitions are logged but not rejected.

## Review checklist

Before merging workflow logic, verify:

- states are named domain concepts;
- allowed transitions are explicit;
- invalid transitions fail predictably;
- side effects are ordered safely;
- idempotency is defined;
- concurrency is handled;
- tests cover valid transitions, invalid transitions, retries, and at least one concurrent or stale update case when relevant.
