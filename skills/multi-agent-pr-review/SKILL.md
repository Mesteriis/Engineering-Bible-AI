---
name: [be] multi-agent-pr-review
description: "Read-only multi-agent review for a PR, branch, commit, or local Git diff. Use when independent review dimensions such as security, bugs, tests, maintainability, performance, and UI regressions can be analyzed in parallel, then merged into one severity-ranked report."
---

# Multi-Agent PR Review

Review a Git-backed change set with bounded read-only reviewers.

## Workflow

1. Resolve the exact base and head, or state that the current working tree is
   the target.
2. Read repository instructions and relevant changed files.
3. If subagent tools are available, dispatch independent read-only reviewers:
   security, runtime bugs, tests/flakiness, maintainability/architecture,
   performance, and UI/UX only when frontend files changed.
4. If subagents are unavailable, run the same categories sequentially.
5. Merge results with `subagent-result-merge`.

## Reviewer Contract

Each reviewer returns:

- finding
- severity
- evidence with file/line
- confidence
- suggested minimal fix
- validation gaps

## Rules

- Do not edit files.
- Do not report style-only issues unless they hide a real risk.
- Mark unverified concerns as uncertainty.
- Use `security-router` for deep security workflow when security findings are
  material.
