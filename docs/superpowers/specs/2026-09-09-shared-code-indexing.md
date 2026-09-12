# Shared Code Indexing Design

## Goal

Use Serena as the default symbol-level code navigation layer shared by Codex
and Claude, while retaining Graphify for architecture and dependency graphs
and Repomix for explicit context-pack export.

## Decisions

- Pin `serena-agent` to `1.7.0` in the portable tool catalog.
- Treat Serena as Tier 1 for broad or repeated symbol-oriented exploration,
  but keep `rg` and targeted reads for localized work.
- Treat Graphify as Tier 2 for architecture, dependency, call-graph, and
  repeated large-repository onboarding work.
- Configure Serena as a local stdio MCP server for Codex and Claude without
  installing hooks or committing runtime state.
- Keep generated Serena state and machine-local client configuration outside
  the tracked distribution boundary.
- Remove the stale local `trace-mcp` client entry whose command no longer
  exists; do not install or initialize trace-mcp.

## Verification

- The catalog and policy tests pass.
- `serena --version` reports `1.7.0`.
- Serena can index this repository successfully.
- Both client configurations resolve the installed executable without hooks.
- Repository-wide quick validation passes and the final diff contains no
  machine-local runtime state.
