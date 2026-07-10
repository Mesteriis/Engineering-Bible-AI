---
name: quality-gates
description: "Use only at validation, integration, completion, release, or drift-review boundaries. Do not load for every implementation step."
---

# Skill: quality-gates

## Purpose

Use this skill as a lightweight control layer for non-trivial engineering work.
It keeps agent output evidence-bound, task execution lifecycle-aware, reviewable,
and resistant to Engineering Bible drift.

This skill does not replace language, security, UI, documentation, or review
skills. It composes with them.

## Required References

Read only the references needed for the task:

- `../../engineering/35_evidence_contract.md` for claims, facts, validation, and uncertainty.
- `../../engineering/36_task_lifecycle_gates.md` for task scope, inspection, planning, validation, and reporting.
- `../../engineering/37_review_regression_gates.md` for diff-risk review and regression coverage.
- `../../engineering/38_library_drift_audit.md` for repository integrity and portable-tree drift.

## When To Use

Use this skill when a request is non-trivial and involves any of:

- code changes;
- repository structure changes;
- installer or CLI behavior;
- docs that define behavior or process;
- validation, CI, test, or review workflows;
- multi-step debugging or refactoring;
- claims about current code, runtime state, test results, or external behavior.

For trivial read-only answers, apply the evidence contract without loading every
reference document.

## Operating Rules

- Important factual claims need evidence: file path, command output, test result, or explicit uncertainty.
- Do not claim validation passed unless the exact command was run.
- Inspect relevant files before changing them.
- Keep task gates proportional to task risk.
- Review behavior changes before completion.
- Add or update regression coverage when a defect class is fixed.
- Treat library drift as a repository bug, not as documentation polish.

## Output

When this skill materially affects the work, report:

- evidence used;
- lifecycle gates completed;
- validation commands and results;
- review or regression reasoning;
- remaining risks.
