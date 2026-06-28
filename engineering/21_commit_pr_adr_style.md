# Commit, PR, and ADR Style

Engineering communication should preserve intent and evidence.

## Commit message shape

Prefer:

```text
<area>: <what changed>

Why:
- ...

What:
- ...

Validation:
- ...

Risks:
- ...
```

Use repository conventions when they exist.

## PR description shape

```markdown
## Why

## What Changed

## Validation

## Risks

## Rollback

## Notes for Reviewers
```

## ADR shape

```markdown
# ADR: <decision>

## Status

Proposed | Accepted | Superseded

## Context

## Decision

## Consequences

## Alternatives Considered

## Validation

## Review Date
```

## Rule

Do not write process documents that obscure the engineering decision.
