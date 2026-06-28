# Documentation Style

Documentation must be accurate, minimal, and useful.

## Standard structure

For technical documentation, prefer sections like:

```markdown
# Title

## Purpose
## Responsibilities
## Public API
## Dependencies
## Lifecycle
## Failure Modes
## Configuration
## Validation
## Examples
## Operational Notes
```

Use only the sections that apply.

## Rules

- Document real behavior only.
- Do not document future behavior as if it exists.
- Keep examples runnable or clearly marked as illustrative.
- Include validation commands where useful.
- Explain non-obvious constraints.
- Avoid marketing prose.
- Update docs when public behavior, configuration, deployment, or usage changes.

## Comments vs documentation

Comments explain local why.

Documentation explains broader usage, boundaries, lifecycle, operations, and contracts.
