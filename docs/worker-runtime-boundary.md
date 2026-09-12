# Worker And Runtime Boundary

This repository packages portable Codex instructions and skills. It does not
package a local worker runtime.

## Included

- Engineering standards.
- Codex-compatible skills.
- Router and wrapper skills.
- A provider-neutral contract for context-efficient graph and symbolic code
  navigation when the current agent host exposes those capabilities.
- `code-wiki-ru` scripts and references.
- Install and validation helpers.
- Documentation and templates.

## Excluded

- `~/.codex/config.toml`
- `~/.codex/auth.json`
- Codex sessions, rollouts, cache, worktrees, and app state.
- `.env` files and credential stores.
- Moon Bridge configuration.
- DeepSeek, OmniRoute, OpenAI, Home Assistant, GitHub, or MCP credentials.
- Private SSH config and private keys.
- Local app bundles and LaunchAgents.

## Why

Worker/runtime configuration is machine-specific and often contains credentials
or permission surfaces. It must be reviewed locally and should not be published
as a reusable engineering package.

## Safe Install Rule

The installer may copy:

- `engineering/` into `CODEX_HOME` and `AGENTS_HOME`
- selected `skills/` into `CODEX_HOME`
- `templates/`
- `scripts/`
- `tests/`
- example root instructions

Managed skills are not mirrored into `AGENTS_HOME` by default. Keeping one
visible skill root prevents duplicate entries in Codex UI while preserving
`AGENTS_HOME/engineering` references for skill-relative documentation links.

The installer must not write or synthesize secrets, model provider config, MCP
server credentials, or auth files.

## Compatible Agent Hosts

The global prompt profiles may be reused by Codex-compatible agent hosts. The
host remains responsible for exposing and authorizing its local code knowledge
graph and LSP-backed symbolic navigation services. The portable package names
capability roles, not provider identifiers, launch commands, endpoints, or
credentials.

Agents should reuse fresh indexes and active project state, use graph evidence
for cross-file structure and impact, use symbolic navigation for the smallest
necessary definitions and references, and fall back to targeted text search for
literals, configuration, non-code files, or unavailable services. Local host
configuration must remain untracked and be validated on that machine.

## Existing Codex Worker

If a machine already has a working Codex worker, keep its runtime configuration
in place and install this repository as a skill/standards layer only.
