# Worker And Runtime Boundary

This repository packages portable Codex instructions and skills. It does not
package a local worker runtime.

## Included

- Engineering standards.
- Codex-compatible skills.
- Router and wrapper skills.
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

- `engineering/`
- selected `skills/`
- `templates/`
- `scripts/`
- `tests/`
- example root instructions

The installer must not write or synthesize secrets, model provider config, MCP
server credentials, or auth files.

## Existing Codex Worker

If a machine already has a working Codex worker, keep its runtime configuration
in place and install this repository as a skill/standards layer only.
