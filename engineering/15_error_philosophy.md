# Error Philosophy

Errors are part of the contract.

## Principles

- Fail explicitly.
- Preserve cause and context.
- Use specific error types where the project has that pattern.
- Do not swallow errors.
- Do not double-log and re-raise unless there is a clear operational reason.
- Do not expose internal details in public API responses.
- Map infrastructure errors to appropriate application/domain errors at boundaries.
- Make retryable and non-retryable failures distinguishable where relevant.
- Include enough context to debug without leaking secrets.

## Error boundary examples

- Transport layer maps errors to protocol-specific responses.
- Application layer coordinates error handling and retries.
- Domain layer raises domain-meaningful failures.
- Infrastructure layer preserves low-level context but does not leak it upward unnecessarily.

## Anti-patterns

```python
try:
    ...
except Exception:
    pass
```

```text
log error -> re-raise -> log same error again five layers up
```

```text
return None for every failure and force callers to guess
```

## Reporting rule

When changing error behavior, document changed failure modes and validation.
