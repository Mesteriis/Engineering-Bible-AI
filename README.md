# Engineering Bible AI

[![Validate](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml/badge.svg)](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Portable engineering standards, routing skills, and repository documentation
tools for AI coding agents. The package contains reproducible standards,
skills, templates, tests, and installers only; it does not contain local runtime
state or secrets.

## Contents

- `AGENTS.md` - instructions for contributing to this repository.
- `instructions/global/` - installable full and minimal global prompt profiles.
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

<!-- BEGIN GENERATED SKILL REGISTRY -->
### Default groups

- **core:** `workflow-router`, `mcp-tool-router`, `engineering-standards`, `core-engineering`, `code-quality`, `architecture-principles`, `testing-tdd`, `tdd-guard`, `debugging`, `code-review`, `security`, `performance`, `refactoring`, `documentation`, `quality-gates`, `karpathy-guidelines`, `context-pack`, `session-memory`.
- **ecosystems:** `python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`, `esp32`.
- **routers:** `review-router`, `security-router`, `ui-router`, `ui-research`, `ui-build`, `ui-figma`, `ui-qa`.
- **review:** `architecture-map`, `architecture-normalizer`, `migration-planner`, `multi-agent-pr-review`, `agent-squad`, `specialist-dispatch`, `subagent-result-merge`, `external-agent-pack-audit`, `agent-retrospective`, `agents-md-retrospective`.
- **security:** `security-diff-review`, `fix-security-finding`, `threat-model`, `dependency-advisory-audit`, `secrets-and-config-review`, `authz-boundary-review`, `deserialization-parser-review`, `supply-chain-review`.
- **ui:** `ui-concept-first`, `design-system-extractor`, `figma-to-code`, `code-to-figma`, `playwright-visual-qa`, `responsive-breakpoint-check`, `accessibility-ui-review`.

### Optional groups

- **fast:** `fast`.
- **wiki:** `code-wiki-ru`.
<!-- END GENERATED SKILL REGISTRY -->

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

Inspect and explicitly select optional companion CLI tools:

```bash
be tools list
be tools plan --group foundation
be tools install --group foundation --allow-unpinned
be tools list --capability dependency-docs --json
be tools configure --tool agent-browser --step browser-runtime --allow-network
be tools doctor --tool agent-browser
```

The versioned catalog reports `OK`, `MISMATCH`, `UNPINNED`, `MISSING`, and
`UNSUPPORTED` when a catalog entry is not available on the current platform.
No install starts without `--group`, `--tool`, or `--all`. Core Bible install
does not install companion tools; configure one setup step at a time with
explicit side-effect permissions. The command never enables hooks, provider
configuration, credentials, or local runtime services implicitly.

The audited optional catalog includes pinned workflow state, browser evidence,
dependency source, and dependency documentation capabilities. Browser runtime
setup is explicit and headless; project task state uses stealth mode; external
documentation authentication is never part of the Bible install.

Install every registry group:

```bash
make install-all
```

Stable install from a GitHub release:

```bash
RELEASE=v0.1.0
curl -fSLo engineering-bible-install.sh \
  "https://github.com/Mesteriis/Engineering-Bible-AI/releases/download/${RELEASE}/install.sh"
bash engineering-bible-install.sh --dry-run --diff
```

Then replace `--dry-run --diff` with `--install` when the planned changes look
correct.

Mutable branches are development-only and require both an explicit ref and
`--allow-unstable`:

```bash
bash engineering-bible-install.sh --ref main --allow-unstable --dry-run
```

The complete portable snapshot is installed under
`$ENGINEERING_BIBLE_HOME/current`. Active instructions and skills are projected
into `CODEX_HOME`/`AGENTS_HOME`; the ownership manifest records every managed
file hash and mode. Unmanaged files are never overwritten or removed, including
with `--force`. Use `--migrate-legacy` only for an intentional takeover of an
identical legacy installation. Installation is journaled, backed up, and rolled
back on failure.

After installation, the package installs a small `be` manager command into
`~/.local/bin/be` by default. If `~/.local/bin` is not on your shell `PATH`,
run the command through `~/.local/bin/be` or add that directory to `PATH`.

Initial `be` commands:

```bash
be version
be doctor
be doctor --json
be validate --checkout .
be validate --checkout . --profile quick
be validate --checkout . --profile release
be validate --installed
be install --dry-run --diff
be install --dry-run --prompt-profile minimal
be install --dry-run --prompt-profile fast
be install --dry-run --migrate-legacy
be update
be update --ref main --allow-unstable --dry-run
RUNTIME_METADATA=/path/to/runtime-metadata.json
be mcp refresh --repo . --json < "$RUNTIME_METADATA"
be mcp status --repo . --json
printf '%s\n' 'review this repository' | be mcp candidates --repo . --task-stdin --json
TOOL_ID=opaque-tool-id
be mcp show "$TOOL_ID" --json
be tools list
TOOL_ID=tool-id
be tools plan --tool "$TOOL_ID"
SKILL_SOURCE=https://github.com/OWNER/REPOSITORY
SKILL_PATH=path/to/skill
be add skill "$SKILL_SOURCE" --path "$SKILL_PATH"
be acceptance validate .engineering-bible/evidence/acceptance.json --json
be audit
```

`be self-update` remains a one-release deprecated alias for `be update`.
Runtime capability names are discovered from the current host session and are
written only to local Git-excluded state under `.engineering-bible/mcp/`.
`refresh` does not query or invoke capabilities: a host adapter must serialize
the current in-memory registry to stdin using the normalized schema illustrated
by `examples/runtime-capabilities.synthetic.json`. Do not build that input from
repository configuration or a remembered provider list.
`--repo` must point to a Git working tree: refresh fails before writing catalog
files if the local exclude cannot be secured.

CLI command variants from Make:

```bash
make be-update
make be-self-update
make be-audit
make be-add-skill SOURCE="$SKILL_SOURCE" NAME=optional-name REF=optional-ref SKILL_PATH="$SKILL_PATH"
```

```bash
make audit
make quality-audit-tests
make shell-lint
make markdown-lint
```

## Validate

```bash
make validate-quick
make validate-bootstrap
make validate
make validate-release
```

The unified runner reports every check as `PASS`, `FAIL`, or `SKIP`. The
release profile treats every `SKIP` as a failure and verifies its required
snapshot against `git ls-files`.

Validation entry points:

- `scripts/validate.py --profile quick|bootstrap|full|release`
- `scripts/validate-repo-tree.sh .`
- `be validate --installed`
- `scripts/validate-installed-tree.sh "$ENGINEERING_BIBLE_HOME/current" ~/.codex ~/.agents`
- `scripts/validate-skill-tree.sh` as a compatibility wrapper.
- `scripts/validate-router-cases.py --fixtures`
- `ENGINEERING_BIBLE_ROUTER_EVALUATOR=/absolute/path/to/evaluator scripts/validate-router-cases.py --runtime`
- `scripts/validate-markdown-style.py .`
- `skills/workflow-router/scripts/validate-routing.sh --codex-only`

Tests are always discovered with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

`skills/registry.yml` owns the generated registry blocks in both READMEs and
the manifest. Update them with `make registry-docs`; validation fails on drift.
The opt-in runtime evaluator receives JSON `{schema_version, cases}` on stdin
and must return `{schema_version, results: [{id, skills}]}` on stdout. If no
evaluator is configured, runtime evaluation exits with `SKIP` rather than
claiming success.

GitHub Actions runs repository-local validation on pushes and pull requests.

## OSS Project

- License: MIT, see `LICENSE`.
- Contributions: see `CONTRIBUTING.md`.
- Security reports: see `SECURITY.md`.
- Support: use GitHub Issues and see `SUPPORT.md`.
- Release checklist: `docs/oss-release-checklist.md`.
- Third-party notices: `THIRD_PARTY_NOTICES.md`.

## Notes

- Installed global instructions stay technology-neutral and capability-based.
- The default prompt profile is `full`; `minimal` is an opt-in compact profile.
  `fast` activates only the fast skill and skips routing, MCP discovery,
  evidence overhead, and external tool setup.
- Language-specific rules live in ecosystem skills.
- Broad engineering principles live in `engineering/`; use
  `engineering/README.md` to select only the relevant reference documents.
- `workflow-router` remains the entry point for non-trivial engineering tasks.
- `engineering-standards` is read only when standards, boundaries, smells,
  naming, refactoring, complexity, or task/TODO structure matter.
