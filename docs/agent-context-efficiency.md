# Context efficiency

Use this workflow for long command output, broad code discovery, and experiments
that measure agent time or token usage. Use the project's current checkout,
including relevant uncommitted changes, as the source for code decisions.

| Need | First choice |
| --- | --- |
| Find a file or literal | Scope `rg` to the relevant tree and read the matching lines |
| Find a definition or its callers | Use an exposed language server and read the relevant symbols |
| Find a syntactic pattern | Use ast-grep with an explicit language and path |
| Understand an unfamiliar subsystem | Read its entry point and a small set of relevant files. Use a fresh project-scoped index when it saves repeated discovery |
| Compare runs or inspect structured results | Project the needed fields with a deterministic filter such as `jq` |
| Inspect noisy human-readable output | Use the host's evidence-capturing wrapper with a supported RTK filter |
| Return to different parts of a long log | Index only the explicit saved artifact in a private task scope and retrieve short excerpts |
| Hand off a bounded snapshot | Use an explicit Repomix allowlist or a short map with a fixed token budget. Follow the existing data boundary |

Keep full command evidence outside tracked files. Preserve exit status and
retain enough context to reproduce failures. Reopen the raw result when a
filter drops a needed field, hides a failure, or returns an ambiguous result.
Keep archived outputs on the approved host. Use existing host bindings for
local tools and avoid loading unrelated tool packages.

For recurring tasks, keep repo instructions focused on invariants, commands,
and source pointers. Reuse verified decisions and stop repeating identical
failures. Use provider-native deferred tool loading where verified, or test
scoped tool profiles when the host exposes them. Keep the selected model and
follow the existing rules for delegation and data export.

## Measure a change before making it the default

Use paired tasks at the same revision, with the same model, reasoning, and
acceptance checks. Include at least one real failure or missing-result case.
Compare elapsed time, time to first relevant evidence, successful outcomes,
and retries. Record uncached input, cache reads and writes where available,
and output tokens. Keep byte counts, token counts, and billing estimates in
separate columns. Include index preparation, extra model calls, and failed
attempts in any end-to-end comparison.

For an optional plugin, test one mechanism in one project first. Prefer a
proposal-only mode for changes to available tools. Check the tool's data flow,
how it is attached to the host, and how to restore the prior configuration.
Use the same acceptance criteria for the baseline and the candidate.

In bb, use the provider-agnostic user instructions as a small entry point to
the installed Bible and expose its selected skills through the user skill
root. Keep project instructions scoped to the project. Use the provider's
available context and usage evidence. Report missing usage independently
from the outcome of a task.

## Project MCP in bb

Keep the project tool list in `.bb/mcp.json` if the host has MCP Hub.
Add only servers used by the project. Run `bb mcp-hub plan --path <project>`
before applying and check ownership, collisions, and unresolved variables.
Keep secret values out of the authored list and leave foreign files intact.
MCP Hub can materialize project configuration for Claude Code and OpenCode.
For Codex, use the trusted project's `.codex/config.toml`; do not put a
project-only server in the user config. Pi reads `.pi/mcp.json` for trusted
projects. Verify the chosen bb provider with a successful read-only MCP call
and run the same check from a workspace without that server.

Treat this as project-scoped exposure of the servers managed by the pilot.
Other native client tools can still come from user configuration. ACP adapters
can have different tool exposure even when they share a provider name.

Cursor ACP reads the project's Cursor MCP file and requires approval of the
specific server. Check that server with `cursor-agent mcp list` from the project.
For Codex ACP, bb can pass the adapter's `CODEX_CONFIG` using a project
machine-environment override. Keep the override limited to the approved
server definition and verify that it is absent in other projects.
bb's ACP session request carries its own dynamic-tools bridge. Where a
provider needs an ACP-supplied server, use a local adapter that can append only
reviewed definitions for explicit project roots. Keep the original route
available and preserve existing ACP entries and permissions.

## TokenEconomizer proposal pilot

Use a reviewed upstream revision, a private state directory, and the selected
project's provider hooks. Set `toolprune=propose`, `microskills=off`,
`loopguard=off` and `history_import=off` in the pilot. Review and trust only
the intended hooks through the provider's own controls. Keep observation
inside that project. Inspect `status` and `toolprune show` after sessions
have closed or folded. Require separate approval before applying a proposal
to provider settings.

Check a successful live fold, the resulting proposal state, and the absence
of automatic deny rules. An empty proposal during early observations is
expected until the configured evidence requirements are met. Use an upstream
regression fixture to check that forming a proposal leaves settings intact.
Record any reduced thresholds used for a trial, restore normal thresholds
after measuring, and keep trial output distinct from recommendations based on
normal work. A global tool catalog and a short task sample can produce
proposals for capabilities that are essential on other task types. Review
their relevance against the project scope and keep required fallback tools.
