# OpenCode DeepSeek

Use OpenCode only after deterministic scripts generate a bounded context pack.

## Verified Local Capability

Codex or Claude may dispatch a `tests-docs` worker through the locally verified
external CLI capability. Resolve its provider/model from machine-local role
mapping and the current supported model catalog. Keep the parent model and
authorization unchanged. This reference does not install or activate a worker.

Before dispatch, verify the installed launcher's interface, effective flags,
tools, permissions, and runtime metadata. Supply only a checked, allowlisted
pack through stdin or a supported file in a sanitized working directory, never
the full repository as cwd or pack text in argv. Deny source edits, arbitrary
shell, reads outside that directory, dependency installation and delegation.
Use no approval or sandbox bypass flags and no hidden model fallback.

Require a synthetic parent-to-worker smoke test with route metadata, read/write
canaries, timeout and cancellation evidence. An installed binary or standalone
OpenCode call does not verify delegation. If that capability is unavailable or
restrictions are unverified, mark external drafting BLOCKED and continue with
deterministic local wiki generation. Use the existing `subagent-result-merge`
contract for findings, actual exit codes and raw artifact pointers.

## Rules

- Do not pass secret-bearing file contents to OpenCode.
- Do not ask DeepSeek to apply patches.
- Treat DeepSeek output as a draft that must be staged under `_meta/drafts/`.
- Only the main agent may stage the returned draft and apply validated changes.
- Validate staged wiki pages before apply.
- Preserve Russian prose and exact source identifiers.
