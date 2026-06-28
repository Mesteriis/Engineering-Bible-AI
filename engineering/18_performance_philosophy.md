# Performance Philosophy

Performance work must be evidence-driven.

## Principles

- Measure before optimizing.
- Optimize bottlenecks, not guesses.
- Preserve correctness.
- Avoid unnecessary I/O.
- Avoid repeated work.
- Avoid N+1 queries.
- Batch where it preserves correctness.
- Reduce allocations and copies when they are material.
- Prefer locality and simple data structures.
- Add caching only when invalidation, consistency, and memory behavior are understood.

## Performance report

When optimizing, report:

- suspected or measured bottleneck;
- change made;
- measurement or validation;
- correctness risks;
- rollback/safety considerations where relevant.

## Anti-patterns

- caching without invalidation policy;
- async code that blocks the event loop;
- parallelism without lifecycle control;
- micro-optimizing cold paths;
- trading correctness for speed without explicit approval.
