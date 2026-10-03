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

Author workflow providers are `superpowers.dispatching-parallel-agents` for
independent tasks and `superpowers.subagent-driven-development` for an approved
implementation plan. Resolve the selected provider with `be skills route ID
--json`, then read its complete exposed instructions and required references.
These author procedures remain upstream; the lane, export and worker boundaries
below are separate owner policy. Reuse compatible native providers, install a
missing reviewed dependency through the selected profile, and report unavailable
delegation or pending exposure. The author workflow does not grant workers
additional permissions.

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

A worktree is not a security sandbox. Read-only permission does not authorize
exporting source. External workers receive only an approved context pack or
sanitized snapshot; enforce denial of source writes, arbitrary shell, and
reads outside the allowed scope. Text-only prohibitions do not prove isolation.
Disable dangerous tools and do not activate a route whose restrictions cannot
be verified. Native trusted implementation lanes may own edits; external
worker roles return artifacts for the main agent to review and apply.

## Explicit Review Modes

Default: keep the current selected model; multimodel and quorum are off.
Same-model parallel lanes do not enable either mode. Only a direct user command
for this task activates `/multimodel` or `/quorum`; quoted examples, task risk,
quality requirements and a request for more agents are not activation.
Use [the task-scoped command contract](../../docs/cross-provider-review.md#explicit-activation).

`/multimodel` selects budget code proposals and stronger review without votes.
`/quorum` selects fixed review voting without budget implementation. Use both
commands for both modes; neither grants export or additional tool permissions.

## External Execution Limits

When `/multimodel` is active, the owner's cost policy assigns code proposals to
budget models and independent review to stronger models. Keep concrete mappings private and
record actual routing and usage. A tool-free external proposer returns a patch
artifact for the parent to inspect and apply; it does not write the active
source tree. All patch authors and the integrator belong in quorum `author_ids`.
Do not silently upgrade a budget implementation route. Failed acceptance checks
return concrete feedback for a bounded new candidate; changed targets invalidate
previous votes. A repair round is distinct from a transient transport retry.

Starting policy, configurable by the user rather than a product capability:
at most two external workers concurrently, one local inference process, a
timeout of five minutes per task, and at most one retry for a transient error.
Do not retry permission, authentication, or invalid-request failures.
No recursive delegation, hidden model fallback, or transfer of the parent's
approvals to a worker. Never enable approval or sandbox bypass flags.

Prefer an existing verified launcher. If a local adapter is necessary, keep it
outside tracked files; use argument arrays, stdin or supported input files,
never `shell=True` or `eval` for task content. Enforce timeout, cancel the
process tree, validate result metadata, and preserve raw artifacts. Test these
boundaries with temporary synthetic fixtures before activating the route.

For multi-step runs, the optional offline `scripts/worker-evidence.py continue`
command evaluates fixed resource budgets, repeated failures, unchanged progress,
and checkpoint acknowledgments. The launcher must persist the returned state,
stop on `stop` or `blocked`, and save a checkpoint before acknowledging it. Supply
actual cumulative counters and evidence hashes; a rewritten summary is not
progress. This decision helper does not enforce an in-flight timeout or cancel
processes. See `docs/worker-evidence.md` for the transition contract.

## Merge Contract

Only when `/quorum` is active, select the fixed roster, common target and decision
mode before dispatch using [Worker Quorum](../../docs/worker-quorum.md).
Keep initial drafts independent. Verified route metadata and required evidence
determine vote eligibility; a role name or model self-description does not.
Use the existing worker records with the offline quorum evaluator. Confirmation
of a critical counterexample or required failure takes precedence over votes.
No quorum output grants deployment, merge or external communication authority.
Record parent and worker usage separately before claiming a quality or cost gain.

Before finalizing:

1. Collect lane results using the existing `subagent-result-merge` contract.
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
