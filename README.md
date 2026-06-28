# Engineering Bible AI

[![Validate](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml/badge.svg)](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Portable engineering standards, routing skills, and repository documentation
tools for AI coding agents.

This repository is the shareable version of the local Codex setup built on
`mb-avm`. It contains the reusable artifacts, not local runtime state.

## Contents

- `AGENTS.md` - portable root Codex instructions.
- `engineering/` - language-neutral engineering standards library.
- `skills/` - Codex-compatible skills for routing, engineering standards,
  implementation, review, security, UI routing, and code wiki generation.
- `templates/` - report, ADR, PR, commit, and implementation prompt templates.
- `scripts/` - validation and installation helpers.
- `tests/` - router behavior cases.
- `reference/` - compact legacy reference docs.
- `examples/` - repo-level `AGENTS.md` example.
- `.github/` - issue templates, pull request template, CODEOWNERS, Dependabot,
  and validation workflow.

## Included Skill Groups

- Routing: `workflow-router`, `review-router`, `security-router`, `ui-router`,
  `ui-research`, `ui-build`, `ui-figma`, and `ui-qa`.
- Engineering Bible: `engineering-standards`, `core-engineering`,
  `code-quality`, `architecture-principles`, `testing-tdd`, `debugging`,
  `code-review`, `security`, `performance`, `refactoring`, and `documentation`.
- Ecosystems: `python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`,
  `esphome`, and `esp32`.
- Review/security/UI wrappers: architecture, migration, diff/security,
  supply-chain, authz, parser, Figma, visual QA, responsive QA, and accessibility
  wrappers used by the router.
- Wiki tooling: `code-wiki-ru` for Russian Obsidian-compatible code wiki
  generation and drift checks.

## Runtime Boundary

This repo intentionally does not include local worker/runtime configuration:

- no `~/.codex/config.toml`;
- no auth files;
- no `.env` files;
- no Moon Bridge or DeepSeek credentials;
- no MCP server secrets;
- no Codex session/cache/worktree state.

The portable package installs skills and standards only. Your existing Codex
worker, MCP, notify, Computer Use, and model provider setup remain local.

See `docs/worker-runtime-boundary.md`.

## Install

One-command install from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh | bash -s
```

Remote dry-run:

```bash
curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh | bash -s -- --dry-run
```

Dry-run:

```bash
make dry-run
```

Install into default `~/.codex` and `~/.agents/skills`:

```bash
make install
```

The installer backs up replaced files under `~/.codex/backups/`.
It does not overwrite `~/.codex/config.toml`.

## Validate

```bash
make validate
```

GitHub Actions runs the same repository-local validation on pushes and pull
requests.

## OSS Project

- License: MIT, see `LICENSE`.
- Contributions: see `CONTRIBUTING.md`.
- Security reports: see `SECURITY.md`.
- Support: use GitHub Issues and see `SUPPORT.md`.
- Release checklist: `docs/oss-release-checklist.md`.
- Third-party notices: `THIRD_PARTY_NOTICES.md`.

## Notes

- Root instructions stay technology-neutral.
- Language-specific rules live in ecosystem skills.
- Broad engineering principles live in `engineering/`.
- `workflow-router` remains the entry point for non-trivial engineering tasks.
- `engineering-standards` is read only when standards, boundaries, smells,
  naming, refactoring, complexity, or task/TODO structure matter.
