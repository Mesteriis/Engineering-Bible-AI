---
name: [be] core-engineering
description: "Default production engineering workflow for implementation, maintenance, and validation."
---

# Skill: core-engineering

## Purpose

Apply the default engineering workflow for production-grade implementation work.

## Core Rules

- Verify before acting.
- Prefer the smallest correct change.
- Preserve public contracts unless explicitly asked to change them.
- Match existing project style.
- Do not introduce unrelated refactors.
- Do not invent files, APIs, schemas, commands, or test results.
- Do not use placeholders as implementation.
- Do not leave dead code.
- Do not hide uncertainty.

## Workflow

### 1. Understand

Identify:

- requested behavior;
- expected output;
- constraints;
- ambiguous points;
- relevant domain boundaries.

If ambiguity blocks correctness, ask one precise question.

If ambiguity is manageable, proceed with an explicit assumption.

### 2. Inspect

Before writing code, inspect:

- relevant files;
- nearby related code;
- project config;
- tests;
- existing patterns;
- validation commands.

### 3. Plan

Create a concise plan:

- target files;
- intended changes;
- expected behavior;
- validation method;
- risks/assumptions.

For small tasks, one short paragraph is enough. The plan is a tool, not a paperwork shrine.

### 4. Implement

Implement in small focused slices.

Rules:

- one concern per change;
- explicit control flow;
- explicit error handling;
- no hidden global state;
- no unrelated formatting churn;
- no new dependencies unless justified.

### 5. Validate

Run the best available targeted validation.

If validation fails, report the failure honestly and fix root causes when in scope.

If validation cannot be run, explain exactly why.

### 6. Report

Report:

- changed files;
- summary;
- validation command and result;
- assumptions;
- remaining risks.

## Assumptions Format

```markdown
Assumption: <clear assumption>
Reason: <why this assumption is reasonable>
Risk: <what breaks if it is wrong>
```

## Definition of Done

The task is done when:

- behavior is implemented;
- architecture is respected;
- tests/validation are handled;
- assumptions and risks are explicit;
- no fake placeholders remain;
- output is understandable to a senior engineer.
