# Observability Contract

Production code should be diagnosable.

## Questions every meaningful runtime path should answer

- What can fail here?
- How will the operator know?
- What context is needed to debug it?
- What must not be logged?
- Is there a correlation/request/task/device ID?
- Are retries visible?
- Are timeouts visible?
- Are partial failures visible?
- Can this failure be distinguished from similar failures?

## Prefer

- structured logs where the project supports them;
- meaningful error messages;
- correlation/request IDs;
- metrics when the project already has metrics;
- tracing/spans when the project already has tracing;
- clear state transitions for long-running jobs or hardware control.

## Avoid

- logging secrets;
- noisy logs for normal behavior;
- duplicate logs for the same failure;
- vague messages like `failed`, `error`, or `something went wrong`;
- print debugging committed as observability;
- logging entire payloads without considering sensitive data.

## Smart home / embedded note

For hardware-facing behavior, observability should make boot state, fail-safe state, reconnect behavior, relay state, sensor availability, and command outcomes clear where practical.
