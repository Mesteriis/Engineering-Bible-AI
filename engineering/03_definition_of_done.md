# Definition of Done

A task is done only when all applicable conditions are true.

## Required

- The requested behavior is implemented.
- The change fits the existing architecture.
- The code style matches the project.
- Public contracts are preserved unless explicitly changed.
- Relevant tests are added or updated when appropriate.
- Validation is run or explicitly reported as not run with a reason.
- Assumptions are documented.
- Risks are documented.
- No fake placeholders remain.
- No TODO is used as implementation.
- No unrelated files are modified.
- No secrets are hardcoded or logged.
- The result is understandable to a senior engineer.

## Final report shape

```markdown
Changed files:
- ...

Summary:
- ...

Validation:
- Ran: ...
- Result: ...

Assumptions:
- ...

Risks:
- ...
```

If validation cannot be run:

```markdown
Validation:
- Not run.
- Reason: ...
```

If no known risks remain:

```markdown
Risks:
- No known remaining risks from the available context.
```
