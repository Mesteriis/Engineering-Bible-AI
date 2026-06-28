# Code Review Checklist

A review should prioritize real risk over cosmetic noise.

## Severity

### Critical

Breaks correctness, security, data integrity, physical safety, or production behavior.

### Major

Likely bug, architectural violation, missing validation, serious maintainability issue, or risky operational behavior.

### Minor

Small style, naming, readability, or cleanup issue.

### Suggestion

Optional improvement.

## Checklist

Review for:

- correctness;
- edge cases;
- failure modes;
- data integrity;
- security;
- authorization;
- architecture boundaries;
- responsibility and cohesion;
- coupling;
- naming;
- tests;
- validation quality;
- error handling;
- observability;
- performance where relevant;
- compatibility/public contracts;
- documentation where relevant.

## Review output

Use this shape:

```markdown
## Critical
- ...

## Major
- ...

## Minor
- ...

## Suggestions
- ...

## Positive notes
- ...

## Validation gaps
- ...
```

If the code is correct, say so.

Do not invent problems.
