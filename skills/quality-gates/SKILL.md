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

## Author Verification Provider

For workflow completion, invoke `superpowers:verification-before-completion`
(author skill `superpowers.verification-before-completion`, provided by the
agent's own `superpowers` plugin) and read the complete exposed author skill and
its required references. Its procedure remains upstream. The evidence, release
and library-drift rules below are Bible's separate owner policy. Bible never
installs a copy of Superpowers; report a missing plugin. Do not replace the
author procedure with this policy checklist.

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

## Quality Floor

Never weaken a gate silently to make a check pass. Fix the cause, not the check.
Without explicit owner approval, do not:

- add lint suppressions, `@ts-ignore`, `expect-error`, `noqa`, `nolint` or
  equivalents;
- skip, `only`, disable or delete tests, or remove or loosen assertions;
- replace real behavior with stubs or fake placeholders;
- lower coverage thresholds, size or complexity limits, or other metrics;
- disable rules, hooks or CI steps.

Treat every metric as a ratchet: it may only improve or hold, never regress.

A real exception must be explicit and scoped to the smallest unit, carry a
reason and an expiry (date, version or linked follow-up), and be reported to the
user in the final output. An exception that is not reported is a silent weakening.

## Optional Test-Strength Check

For explicitly selected critical logic or a suspected weak test, use
[Targeted Mutation Testing](../../docs/targeted-mutation-testing.md). Select a
small verified source/test allowlist and human-reviewed replacements. The
Python helper executes baseline and mutant tests in separate temporary copies;
those copies are not a sandbox for untrusted test code. Require a passing
baseline and retain raw outputs and original exits. Assertion failures can kill
a mutant; syntax, import and execution errors or timeouts cannot. A surviving
mutant needs a concrete test-strength assessment, not a claimed passing gate.
Do not run campaigns on every edit, install a framework implicitly, or mutate
the working source. Select project-native Stryker separately for TypeScript.

## Output

When this skill materially affects the work, report:

- evidence used;
- lifecycle gates completed;
- validation commands and results;
- review or regression reasoning;
- remaining risks.
