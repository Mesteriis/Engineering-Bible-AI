# Engineering Bible AI

[![Validate](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml/badge.svg)](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Portable engineering standards, routing skills, and repository documentation
tools for AI coding agents. The package contains reproducible standards,
skills, templates, tests, and installers only; it does not contain local runtime
state or secrets.

## Contents

- `AGENTS.md` - portable root Codex instructions.
- `engineering/` - language-neutral engineering standards library with
  `engineering/README.md` as the selection index.
- `skills/` - Codex-compatible skills.
- `skills/registry.yml` - the single source of truth for skill groups.
- `templates/` - report, ADR, PR, commit, and implementation prompt templates.
- `scripts/` - validation, installation, and `be` CLI helpers.
- `tests/` - executable router behavior cases.
- `reference/` - legacy/deprecated compact references kept for compatibility.
- `examples/` - repo-level `AGENTS.md` example.
- `.github/` - issue templates, pull request template, CODEOWNERS, Dependabot,
  and validation workflow.

## Skill Registry

Default install uses the non-optional registry groups from `skills/registry.yml`.
The optional wiki group is not installed by default.

Core:
`workflow-router`, `engineering-standards`, `core-engineering`, `code-quality`,
`architecture-principles`, `testing-tdd`, `debugging`, `code-review`,
`security`, `performance`, `refactoring`, `documentation`, `quality-gates`.

Ecosystems:
`python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`,
`esp32`.

Routers:
`review-router`, `security-router`, `ui-router`, `ui-research`, `ui-build`,
`ui-figma`, `ui-qa`.

Review:
`architecture-map`, `migration-planner`, `multi-agent-pr-review`,
`subagent-result-merge`, `agent-retrospective`, `agents-md-retrospective`.

Security:
`security-diff-review`, `fix-security-finding`, `threat-model`,
`dependency-advisory-audit`, `secrets-and-config-review`,
`authz-boundary-review`, `deserialization-parser-review`,
`supply-chain-review`.

UI:
`ui-concept-first`, `design-system-extractor`, `figma-to-code`,
`code-to-figma`, `playwright-visual-qa`, `responsive-breakpoint-check`,
`accessibility-ui-review`.

Optional wiki:
`code-wiki-ru`.

## Runtime Boundary

This repo intentionally does not include local worker/runtime configuration:

- no `~/.codex/config.toml`;
- no auth files;
- no `.env` files;
- no model provider credentials;
- no MCP server secrets;
- no Codex session/cache/worktree state.

The portable package installs skills and standards only. Your existing Codex
worker, MCP, notify, Computer Use, and model provider setup remain local.

See `docs/worker-runtime-boundary.md`.

## Install

Primary install path:

```bash
git clone https://github.com/Mesteriis/Engineering-Bible-AI.git
cd Engineering-Bible-AI
make validate
make dry-run
make install
```

Install optional wiki tooling:

```bash
make install-wiki
```

Install every registry group:

```bash
make install-all
```

Advanced quick install from GitHub:

```bash
ENGINEERING_BIBLE_REF=v0.1.0 \
  curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/v0.1.0/scripts/install.sh \
  | bash -s -- --dry-run --diff
```

Then replace `--dry-run --diff` with `--install` when the planned changes look
correct. Override `ENGINEERING_BIBLE_REF` for a specific tag, branch, or commit.

The installer writes only managed portable files under `CODEX_HOME`,
`AGENTS_HOME`, and the `be` wrapper path. It reports `ADD`, `UPDATE`,
`UNCHANGED`, `SKIP`, and `CONFLICT`. Changed existing managed targets are not
overwritten unless `--force` is passed. `--no-overwrite` copies only missing
targets.

After installation, the package installs a small `be` manager command into
`~/.local/bin/be` by default. If `~/.local/bin` is not on your shell `PATH`,
run the command through `~/.local/bin/be` or add that directory to `PATH`.

Initial `be` commands:

```bash
be version
be doctor
be doctor --json
be validate --checkout .
be install --dry-run --diff
be update
be self-update
be add skill https://github.com/<owner>/<repo>/<path>
be audit
```

CLI command variants from Make:

```bash
make be-update
make be-self-update
make be-audit
make be-add-skill SOURCE=https://github.com/<owner>/<repo>/<path> [NAME=<name>] [REF=<ref>] [SKILL_PATH=<subdir>]
```

```bash
make audit
make quality-audit-tests
```

## Validate

```bash
make validate
```

Important validation entry points:

- `scripts/validate-repo-tree.sh .`
- `scripts/validate-installed-tree.sh ~/.codex ~/.agents`
- `scripts/validate-skill-tree.sh` as a compatibility wrapper.
- `scripts/validate-router-cases.py --static`
- `skills/workflow-router/scripts/validate-routing.sh --codex-only`

GitHub Actions runs repository-local validation on pushes and pull requests.

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
- Broad engineering principles live in `engineering/`; use
  `engineering/README.md` to select only the relevant reference documents.
- `workflow-router` remains the entry point for non-trivial engineering tasks.
- `engineering-standards` is read only when standards, boundaries, smells,
  naming, refactoring, complexity, or task/TODO structure matter.
