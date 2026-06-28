# Security Policy

## Supported Versions

The `main` branch is the supported development line until release tags are
introduced.

## Reporting Security Issues

Do not open public issues for vulnerabilities, leaked credentials, or bypasses
of the runtime boundary.

Prefer GitHub private vulnerability reporting when available for this
repository. If that is unavailable, contact the maintainer through the GitHub
repository owner profile and include only enough information to establish
impact. Do not include secrets in the first message.

## Runtime Boundary

This repository must not contain:

- local Codex `config.toml`;
- auth files;
- `.env` files;
- Moon Bridge, DeepSeek, OpenAI, Home Assistant, GitHub, or MCP credentials;
- private SSH material;
- Codex session, cache, rollout, or worktree state.

The validation script `scripts/secret-sanity.sh` is a guardrail, not a complete
secret scanner. Review changes manually before publishing.
