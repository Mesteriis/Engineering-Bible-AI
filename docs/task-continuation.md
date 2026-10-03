# Continuing long tasks with bounded context

The Bible owns a small state record, not a replacement for an author's handoff
or context-compression workflow. Use the selected complete author skill when
that workflow is needed. The [checkpoint template](../templates/task-resume-checkpoint.md)
records personal decisions, source freshness and raw evidence pointers without
copying plans, specifications, source bundles or session transcripts. The
opt-in `context-continuation` group retains `pocock.handoff` and
`context.context-compression` as separately managed originals. Select either
only when its workflow fits the task; a short follow-up does not need both.

For a same-task continuation, reuse the active primary and supporting skills
and instructions already available. Reload only instructions lost from context
or made relevant by a changed domain, risk, tools or workflow. An ordinary
follow-up does not require a new routing pass, capability inventory or index
rebuild.

## Choosing evidence

Use one discovery route for the question. A local edit or literal starts with
`rg` and bounded reads; definitions and references use current-session
LSP-backed symbolic navigation; architecture and impact use a fresh code
knowledge graph confirmed against current source. Documentation uses scoped
document search. Avoid paying for every index or a full repository pack before
the task needs it. The default steady and minimal profiles share this policy;
the full profile deliberately retains strict initial routing.

## Keeping a checkpoint useful

Save a filled copy under `.engineering-bible/checkpoints/`, which remains
untracked. Keep the goal, accepted decisions and next slice short; link the
canonical plan instead of duplicating it. Record the base commit, relevant file
paths and sha256 hashes, including added and modified files. A matching commit
alone does not establish freshness when the working tree is dirty.

Before reusing a checkpoint, compare current source revision and included file
hashes. If they differ, inspect the changed scope and its effect on the next
slice, then refresh the checkpoint. Reuse unaffected evidence only when its
scope and source snapshot still match. Repeat checks whose inputs changed;
retain earlier outcomes as historical evidence rather than current PASS.

For each check retain its exact command, working directory, exit code, actual
PASS/FAIL/SKIP outcome and raw output pointer. Missing output, an unrun command
or a compressed summary cannot establish PASS. Do not dump all old logs into
the next prompt: open the bounded evidence needed for a failure or decision.

This is an explicit continuation artifact; it does not control host compaction
or promise token savings. Measure the complete task, including repeated reads,
checks and quality, before claiming savings. Keep bytes separate from measured
tokens and provider billing.

## Local state and external workers

Exclude credentials, auth material, machine-local provider configuration,
private conversations and session dumps. A checkpoint is not durable memory
and creating one does not authorize a memory update. It is also not an export
allowlist: an external worker receives only the data authorized for that
destination. Use [context-pack](../skills/context-pack/SKILL.md) when a bounded
export is actually needed, and keep author/provider instructions separate from
the owner checkpoint.
