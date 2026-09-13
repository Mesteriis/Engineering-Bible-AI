---
name: agent-squad
description: "Plans parallel agents or worktrees with isolated ownership, validation lanes, and merge rules. Use only for safely separable work."
---

# Agent Squad

Use this skill when parallel agent work can reduce risk or time without
creating file conflicts.

This skill is inspired by multi-agent terminal orchestrators. It is not a TUI
installer. It defines the planning, isolation, review, and merge contract for
Codex-compatible parallel work.

## When To Use

Use for:

- large refactors with separable modules;
- implementation plus tests plus review lanes;
- independent security, performance, UI, and docs reviews;
- migration slices that can be validated independently;
- comparing alternative approaches before selecting one.

Avoid for:

- tiny changes;
- tasks where all lanes must edit the same file;
- unclear goals;
- work that needs secrets or production access in multiple contexts.

## Lane Design

Each lane needs:

- goal;
- allowed files or directories;
- forbidden files or directories;
- validation command;
- expected artifact;
- merge owner.

Common lanes:

- implementation;
- tests/TDD;
- security review;
- architecture review;
- docs/update notes;
- regression validation.

## Isolation Rules

- Prefer separate git worktrees or read-only subagents for parallel work.
- Do not let two write lanes own the same files.
- Keep secret-bearing files out of all lanes unless explicitly scoped.
- Merge through one owner after reviewing diffs.
- If lanes conflict, stop and re-plan before editing more.

For multi-step runs, the optional offline `scripts/worker-evidence.py continue`
command evaluates fixed resource budgets, repeated failures, unchanged progress,
and checkpoint acknowledgments. The launcher must persist the returned state,
stop on `stop` or `blocked`, and save a checkpoint before acknowledging it. Supply
actual cumulative counters and evidence hashes; a rewritten summary is not
progress. This decision helper does not enforce an in-flight timeout or cancel
processes. See `docs/worker-evidence.md` for the transition contract.

## Merge Contract

Before finalizing:

1. Collect lane results.
2. Deduplicate findings.
3. Verify changed files against allowed scopes.
4. Run integration validation from the main worktree.
5. Summarize what was accepted, rejected, or deferred.

## Output

Report:

- lanes created;
- isolation method;
- per-lane result;
- merge decision;
- final validation.
