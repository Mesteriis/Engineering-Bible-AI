# `be` CLI Design

## Purpose

Add a small console utility for managing Engineering Bible AI after install.
The first release optimizes for the owner's local workstation workflow while
using state formats that can later support reproducible multi-machine sync.

The CLI must improve day-to-day DX without taking ownership of local Codex
runtime configuration, credentials, MCP setup, or model provider state.

## Goals

- Install a `be` command with the Engineering Bible package.
- Support update, self-update, validation, doctor, profiles, lockfiles,
  backups, rollback, export/import, and external skill management.
- Keep all mutating operations previewable with `--dry-run`.
- Keep removal and rollback gated by explicit confirmation.
- Preserve the existing runtime boundary: no auth files, no `.env`, no
  `config.toml`, no MCP credentials, and no worker runtime state.
- Use only Python standard library and existing shell scripts for v1.

## Non-Goals

- No package-manager dependency such as pipx, uv, npm, or Homebrew in v1.
- No automatic Codex plugin installation.
- No edits to `~/.codex/config.toml`.
- No secret storage, secret generation, or credential migration.
- No commits, pushes, or changes to user repositories.
- No physical deletion of skill files without `--delete-files --yes`.

## Recommended Approach

Use a Python standard-library CLI with a thin shell wrapper.

The installed command should be:

```text
~/.local/bin/be
```

The wrapper should call:

```bash
python3 ~/.codex/scripts/be.py "$@"
```

This keeps installation compatible with `curl | bash`, avoids packaging
dependencies, and gives the CLI enough structure for JSON state, profiles,
lockfiles, archive downloads, validation, and rollback manifests.

## Architecture

`be` is a manager above the existing installer. It should call
`scripts/install-codex.sh` instead of replacing it.

The implementation can start as one Python file, `scripts/be.py`, while keeping
clear internal boundaries:

- Command routing: `argparse` command tree.
- Paths: resolve `CODEX_HOME`, `AGENTS_HOME`, `BE_HOME`, and `BIN_DIR`.
- State store: atomic read/write JSON.
- Source fetch: download and extract GitHub archives.
- Validation: tree, frontmatter, secret-like path, and runtime-boundary checks.
- Installer adapter: invoke `scripts/install-codex.sh`.
- Skill registry: import, inspect, enable, disable, and remove external skills.
- Profile manager: create, select, and edit profile JSON.
- Backup/rollback: write manifests and restore files from known backups.

## State Layout

Default state root:

```text
~/.codex/engineering-bible/
  state.json
  lock.json
  profiles/
    default.json
    minimal.json
    full.json
  skills/
    registry.json
    external/
      <skill-name>/
  backups/
    20260628-150000/
      manifest.json
      files/
```

`state.json` records machine-local installed state:

```json
{
  "version": 1,
  "source": {
    "repo": "Mesteriis/Engineering-Bible-AI",
    "ref": "main",
    "commit": "8eae819"
  },
  "paths": {
    "codex_home": "~/.codex",
    "agents_home": "~/.agents",
    "bin_dir": "~/.local/bin"
  },
  "active_profile": "default",
  "last_install": "2026-06-28T15:00:00+02:00"
}
```

`lock.json` records reproducible content:

```json
{
  "version": 1,
  "core": {
    "repo": "Mesteriis/Engineering-Bible-AI",
    "ref": "main",
    "commit": "8eae819"
  },
  "skills": [
    {
      "name": "code-wiki-ru",
      "source": "core",
      "sha256": "sha256:core-code-wiki-ru-content-hash"
    },
    {
      "name": "some-external-skill",
      "source": "https://github.com/org/repo",
      "ref": "main",
      "commit": "abcdef1234567890",
      "sha256": "sha256:external-skill-content-hash"
    }
  ]
}
```

Profiles are named sets of enabled skills. Example:

```json
{
  "version": 1,
  "name": "default",
  "skills": [
    "workflow-router",
    "engineering-standards",
    "python",
    "typescript",
    "code-wiki-ru"
  ]
}
```

## Command Surface

Core commands:

- `be version`
- `be doctor [--json]`
- `be validate [--installed|--checkout PATH]`
- `be install [--profile default] [--dry-run]`
- `be update [--dry-run]`
- `be self-update [--dry-run]`

Skill commands:

- `be list skills [--all|--enabled|--external]`
- `be add skill <git-url|path> [--ref main] [--name NAME] [--path PATH] [--profile default] [--dry-run]`
- `be remove skill <name> [--profile default] [--delete-files] [--yes]`
- `be inspect skill <name>`
- `be enable skill <name> [--profile default]`
- `be disable skill <name> [--profile default]`

Profile commands:

- `be profile list`
- `be profile show <name>`
- `be profile create <name> [--from default]`
- `be profile use <name>`
- `be profile add-skill <profile> <skill>`
- `be profile remove-skill <profile> <skill>`
- `be profile diff <left> <right>`

Reproducibility commands:

- `be lock`
- `be lock verify`
- `be export --output engineering-bible-lock.json`
- `be import engineering-bible-lock.json [--dry-run]`

Recovery commands:

- `be backup list`
- `be backup show <id>`
- `be rollback <id> [--dry-run] [--yes]`

DX commands:

- `be explain <command>`
- `be open docs`
- `be completion zsh`

`be completion zsh` is a later enhancement, not required for v1.

## External Skill Flow

`be add skill <source>` should:

1. Resolve source as either local path or GitHub archive.
2. Copy the candidate into a temporary staging directory.
3. Reject secret-like files and runtime config:
   `.env`, `.env.*`, `auth.json`, `config.toml`, private keys, certificates,
   token files, and credential files.
4. Locate the target `SKILL.md`.
5. If multiple `SKILL.md` files exist, require `--path`.
6. Validate frontmatter name and description.
7. Copy into `~/.codex/engineering-bible/skills/external/<name>`.
8. Register source/ref/commit/hash in `skills/registry.json`.
9. Enable it in the selected profile unless `--dry-run` was used.
10. Copy to active skill roots only after validation passes.

External skills must never execute code during import.

## Safety Rules

- Every mutating command supports `--dry-run`.
- Remove and rollback require `--yes` for physical file changes.
- `be add skill` validates before installing.
- `be remove skill` disables by default; physical deletion requires
  `--delete-files --yes`.
- `be self-update` refuses dirty local checkouts unless `--force` is passed.
- `be update` shows current commit and target commit before changing files.
- `be rollback` prints exact files before restore.
- JSON writes are atomic: write temp file, fsync when practical, then rename.
- Runtime boundary validation is shared by `be doctor`, `be validate`, and
  `be add skill`.

## Error Handling

Default errors should be concise and actionable:

- what failed;
- which path or command was involved;
- how to retry or inspect;
- whether any changes were applied.

Stack traces should be hidden by default and shown only with `--debug`.

Exit codes:

- `0`: success.
- `1`: validation or command failure.
- `2`: usage error.
- `3`: unsafe runtime-boundary violation.
- `4`: dependency missing.

## Validation Strategy

Repository validation:

```bash
make validate
python3 scripts/be.py doctor --json
python3 scripts/be.py validate --checkout .
```

CLI smoke tests:

```bash
python3 scripts/be.py version
python3 scripts/be.py doctor --json --home <tmp>
python3 scripts/be.py install --dry-run --home <tmp>
python3 scripts/be.py profile create test --home <tmp>
python3 scripts/be.py add skill tests/fixtures/skills/minimal-skill --dry-run --home <tmp>
```

Fixtures:

```text
tests/fixtures/skills/minimal-skill/SKILL.md
tests/fixtures/skills/bad-secret/.env
tests/fixtures/skills/bad-frontmatter/SKILL.md
```

CI should keep using `make validate` and add the CLI smoke tests once
`scripts/be.py` exists.

## Phased Roadmap

Phase 1: CLI foundation

- `scripts/be.py`
- `be version`
- `be doctor`
- `be validate`
- `be install --dry-run`
- installer writes `~/.local/bin/be`
- `make be-smoke`

Phase 2: update and self-update

- `be update`
- `be self-update`
- source ref/commit tracking in `state.json`
- backup manifest per install/update

Phase 3: profiles and lockfile

- `be profile list/show/create/use`
- `be lock`
- `be export`
- `be import --dry-run`

Phase 4: external skills

- `be add skill <git-url|path>`
- `be inspect skill`
- `be enable/disable/remove skill`
- external registry and validation

Phase 5: quality DX

- `be doctor --json`
- structured error hints
- `be explain <command>`
- `be backup list/show`
- `be rollback`
- `be profile diff`
- `be lock verify`
- `be open docs`

## Open Implementation Decisions

- Whether `~/.local/bin` is the only default `BIN_DIR`, or whether installer
  should fall back to `~/.codex/bin` when `~/.local/bin` is absent.
- Whether `be update` should update from branch `main` by default or require a
  pinned commit after the first install.
- Whether external skill sources should support arbitrary Git providers in v1
  or only GitHub archive URLs plus local paths.

The implementation plan should resolve these before coding.
