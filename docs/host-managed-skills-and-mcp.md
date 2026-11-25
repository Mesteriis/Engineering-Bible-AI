# Hosts That Manage Skills and MCP

Some agent hosts run several providers (Codex, Claude Code, Pi, ACP agents)
and distribute skills and MCP servers to all of them from one place. BB is an
example. On such a host, Bible keeps its scope narrow: it supplies rules,
standards and its own skills; the host supplies everything it already manages.
This avoids two sources of truth and the drift between per-provider copies.

## Division of ownership

| Concern | Owner on a managing host | What Bible does |
| --- | --- | --- |
| Global instructions | Bible (`steady`, `full`, `minimal`) | Installs them; the host injects or imports them |
| Bible's own skills | Bible | Installs them into its skill root |
| Superpowers | The provider's own `superpowers` plugin | Records the reviewed revision; never copies it |
| Other author skills required by a profile | Bible's missing-only lifecycle | Installs them unless the host already exposes a compatible copy |
| Optional domain packs | Installed on demand, per host | Prepares native providers only when asked |
| MCP servers | The host | Nothing; it writes no provider MCP configuration |
| Provider skill directories (`~/.claude/skills` and similar) | The host or the user | Nothing; it creates no links |

## Superpowers

The catalog marks `obra-superpowers` as `installation: provider` with
`provider_namespace: superpowers`. As a result:

- normal profiles no longer require Superpowers copies; `be install` and
  `be update` never place them in the skill root;
- `be skills plan`, `ensure` and `route` report Superpowers skills as
  `PROVIDER` / `provider` with the invocation name, for example
  `superpowers:test-driven-development`;
- an older Bible copy left in the skill root is ignored, not treated as a
  second source; remove it to avoid duplicate names;
- Bible's compatibility skills (`debugging`, `testing-tdd`, `code-review`,
  `tdd-guard`, `quality-gates`, `agent-squad`, `specialist-dispatch`) invoke the
  plugin skill by name and report a missing plugin instead of installing a copy.

A provider without the plugin has no Superpowers. Install the plugin through
that provider; Bible does not fill the gap.

## Skills distribution

Install Bible once. Let the host expose the installed skill root to its
providers by its own mechanism (a user skill directory, a plugin, or a
provider-agnostic skill registry). Do not also link Bible skills into each
provider's private skill directory: a skill reachable through two paths shows
up twice or in two versions. Keep host-specific adaptations of third-party
skills (for example a `product-design` entry skill rewritten for the host's
preview, browser and sharing tools) in the host's own skill store, outside
this public repository, when their licence does not allow redistribution.

UI routers name `product-design` as one entry skill with internal workflows
(`audit`, `ideate`, `image-to-code`, `url-to-code`, `design-qa`, `research`,
`share`). Use it only when the session exposes it.

## MCP servers

Bible does not register MCP servers in `~/.claude.json`, `~/.codex/config.toml`,
`~/.pi` or any other provider file. On a managing host, keep every server in
the host's own mechanism, for example a bridge that starts one process per
server for all threads and lets agents search tools on demand. Keep
credentials in files or a secret store outside any repository and reference
them from the launcher, never from a tracked configuration.

Legacy stdio servers that do not answer an unknown method sent before
`initialize` can hang a client that probes with a newer protocol request
first. Wrap them with a small shim that answers that probe with "method not
found" and passes everything else through unchanged.

## Validation

`skills/workflow-router/scripts/validate-routing.sh --all-agents` also checks
the Claude, OpenCode and Gemini roots that exist. On a managing host, list the
providers it manages:

```bash
ENGINEERING_BIBLE_HOST_MANAGED=claude,opencode \
  skills/workflow-router/scripts/validate-routing.sh --all-agents
```

They are reported as `SKIP`, not checked and not counted as `PASS`.
