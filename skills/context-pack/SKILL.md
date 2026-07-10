---
name: context-pack
description: "Builds a compact secret-safe repository pack for AI handoff, review, or large analysis; prefers Repomix when available."
---

# Context Pack

Use this skill when the agent needs to package repository context for another
agent, a long review, an architecture handoff, or an external LLM session.

The preferred external tool is Repomix when it is already available or the user
explicitly asks for it. Use `repomix --compress` for architecture handoffs,
large reviews, and external LLM sessions when compressed structure is more
useful than full implementation detail. Otherwise, use repository-native
commands such as `rg`, `git ls-files`, targeted file reads, and structured
summaries.

## When To Use

Use for:

- large repository handoff;
- architecture or migration planning;
- multi-agent review setup;
- bug reports that require a bounded source bundle;
- sharing code context outside the current session.

Avoid for:

- tiny tasks where direct file reads are clearer;
- repositories containing unreviewed secrets;
- user requests to dump private source into an external service without review.
- small implementation/debugging tasks where `rg`, symbol lookup, and targeted
  file reads produce better evidence than a repository pack.

## Context Selection

Include:

- relevant source files;
- tests touching the behavior;
- public configuration and dependency manifests;
- route, schema, API, migration, or build files needed to understand the task;
- a short file tree and rationale.

Exclude:

- `.env`, auth, tokens, private keys, credentials;
- generated caches, build artifacts, lockfiles unless dependency resolution is
  part of the task;
- vendored or third-party code unless directly relevant;
- unrelated large files.

## Repomix Workflow

If `repomix` is available and appropriate:

```bash
repomix --compress --style markdown --output <target-file>
repomix --style markdown --output <target-file>
```

Prefer `--compress` for architecture or handoff context. Use the uncompressed
form when exact implementation details matter. Use include/exclude flags or
stdin file lists when the full repo would be too large.

Repomix has no project initialization step. Before writing a pack, check whether
the requested output already exists and whether source files changed since it
was generated. Reuse an existing pack only when its scope and freshness match
the current request.

Prefer a user-requested path or a clearly generated local path for packs. Do not
leave a repo-local pack silently: report the path, scope, and whether it should
remain untracked.

If `repomix` is unavailable, produce a manual context pack:

```markdown
# Context Pack
## Goal
## Repository Facts
## Relevant Files
## Key Snippets
## Validation Commands
## Open Questions
```

## Safety

- Run or reuse secret scanning before exporting a pack outside the local
  machine.
- Run or reuse runtime-boundary checks before exporting a pack outside the local
  machine.
- Prefer summaries over full files when the recipient only needs architecture.
- Label generated context as stale once source files change.

## Output

Report:

- pack target path or summary;
- included/excluded scope;
- secret/runtime boundary check;
- token or size concerns when known;
- remaining context gaps.
