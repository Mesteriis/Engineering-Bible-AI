---
name: specialist-dispatch
description: "Selects scoped architecture, backend, frontend, security, data, DevOps, QA, docs, performance, or product roles."
---

# Specialist Dispatch

Use this skill when a task benefits from a specialist lens but does not require
installing a large external agent marketplace.

This skill turns broad agent catalogs into a small Codex-native dispatch layer.
It can be used with subagents when available, or as a checklist for the main
agent when no subagent tool exists.

## Specialist Profiles

Choose the smallest set:

- architect: boundaries, dependency direction, module shape, migration seams;
- backend: APIs, domain logic, persistence, concurrency, errors;
- frontend: UI behavior, state, accessibility, visual quality;
- security: auth, authz, secrets, parser risk, supply chain;
- data: schemas, migrations, analytics, integrity, retention;
- DevOps: CI, deploy, runtime config, observability;
- QA: test plan, regression coverage, edge cases;
- docs: user-facing and operator-facing documentation;
- performance: evidence-led bottleneck analysis;
- product: user workflow, scope, acceptance criteria.

## Dispatch Rules

- Do not spawn a specialist without a concrete question.
- Give each specialist bounded files and expected output.
- Prefer read-only specialist review unless implementation ownership is clear.
- Use `agent-squad` when multiple specialists will work in parallel.
- Use `subagent-result-merge` to consolidate outputs.

## Specialist Prompt Shape

```markdown
Specialist:
Question:
Scope:
Allowed files:
Forbidden files:
Evidence required:
Expected output:
Validation:
```

## Output

Report:

- selected specialists;
- why each was needed;
- scope boundaries;
- result or next routing skill.
