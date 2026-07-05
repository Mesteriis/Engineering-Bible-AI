---
name: [be] review-router
description: "Автороутер ревью и планирования для PR review, local diff review, multi-agent read-only review, architecture mapping, migration planning, subagent result merge и ретроспектив AGENTS.md или skills после повторных ошибок агента."
---

# Review Router

Route review/planning requests without mixing read-only review and editing.

## Workflow

1. Resolve whether the task is review-only, planning-only, or patch-producing.
2. Pick the smallest matching skill.
3. Read the selected skill's `SKILL.md`.
4. For review-only work, do not edit files.
5. For planning work, produce decision-ready slices, risks, and validation gates.

## Routing

- PR, branch, commit, or local diff review with independent dimensions ->
  `multi-agent-pr-review`.
- Codebase orientation, bounded-domain map, or subsystem ownership map ->
  `architecture-map`.
- Framework, schema, API, package, infra, or data migration plan ->
  `migration-planner`.
- Combining multiple subagent reports -> `subagent-result-merge`.
- Post-failure process improvement -> `agent-retrospective`.
- Updating repository or global agent instructions after a repeated pattern ->
  `agents-md-retrospective`.
- Security-sensitive review -> route through `security-router` first.
- UI/frontend review -> route through `ui-router` first.
