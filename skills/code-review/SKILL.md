---
name: code-review
description: "Reviews code, diffs, or PRs for correctness, regressions, security, architecture, maintainability, and test gaps."
---

# Skill: code-review

## Purpose

Review code like a senior engineer: prioritize correctness, safety, architecture, maintainability, and testability over cosmetic noise.

## Review Rules

- Do not invent problems.
- Do not nitpick style unless it affects readability or violates project conventions.
- If code is correct, say so.
- Verify claims against the provided diff or repository context.
- Distinguish confirmed issues from assumptions.
- Focus on behavior, contracts, boundaries, error handling, security, and tests.

## Severity Levels

### Critical

Breaks correctness, security, data integrity, safety, or production behavior.

Examples:

- authorization bypass;
- data corruption;
- unsafe hardware behavior;
- leaking secrets;
- invalid transaction behavior;
- confirmed crash in normal usage.

### Major

Likely bug, architectural violation, missing validation, broken edge case, serious maintainability issue.

Examples:

- missing error handling for expected failure;
- broken retry/cancellation behavior;
- layer leakage that will spread;
- missing regression test for bug fix;
- public API behavior changed without notice.

### Minor

Style, naming, readability, small cleanup.

### Suggestion

Optional improvement.

## Review Output Format

```markdown
## Findings

### Critical
- ...

### Major
- ...

### Minor
- ...

### Suggestions
- ...

## What looks good
- ...

## Validation gaps
- ...
```

Omit empty sections when appropriate.

## Review Checklist

Check:

- correctness of behavior;
- edge cases;
- error handling;
- security and data exposure;
- transaction/data integrity;
- concurrency/cancellation;
- public contracts;
- architecture boundaries;
- single responsibility;
- file/module size and cohesion;
- tests and validation;
- observability where needed;
- performance only when relevant.

## No Cosmetic Flooding

Do not bury important findings under twenty naming comments. Human attention is already a scarce resource, mostly wasted on meetings.
## Extended References


For deeper work, read:

- `../../engineering/20_review_checklist.md`
