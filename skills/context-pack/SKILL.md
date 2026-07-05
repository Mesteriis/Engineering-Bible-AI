---
name: [be] context-pack
description: "Собирает компактный AI-friendly контекст репозитория для handoff, ревью или большого анализа; предпочитает repomix при наличии и не допускает secrets/runtime state."
---

# Context Pack

Use this skill when the agent needs to package repository context for another
agent, a long review, an architecture handoff, or an external LLM session.

The preferred external tool is Repomix when it is already available or the user
explicitly asks for it. Otherwise, use repository-native commands such as `rg`,
`git ls-files`, targeted file reads, and structured summaries.

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
repomix --style markdown --output <target-file>
```

Use include/exclude flags or stdin file lists when the full repo would be too
large.

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
- Prefer summaries over full files when the recipient only needs architecture.
- Label generated context as stale once source files change.

## Output

Report:

- pack target path or summary;
- included/excluded scope;
- secret/runtime boundary check;
- token or size concerns when known;
- remaining context gaps.
