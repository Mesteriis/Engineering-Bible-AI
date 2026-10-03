# Engineering Bible AI

[![Validate](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml/badge.svg)](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Portable engineering standards, routing skills, and repository documentation
tools for AI coding agents. The package contains reproducible standards,
skills, templates, tests, and installers only; it does not contain local runtime
state or secrets.

## Contents

- `AGENTS.md` - instructions for contributing to this repository.
- `instructions/global/` - installable steady, full, minimal, and fast global
  prompt profiles.
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

- **core:** `workflow-router`, `mcp-tool-router`, `engineering-standards`, `core-engineering`, `code-quality`, `architecture-principles`, `testing-tdd`, `tdd-guard`, `debugging`, `code-review`, `security`, `performance`, `refactoring`, `documentation`, `quality-gates`, `context-pack`, `session-memory`.
- **ecosystems:** `python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`, `esp32`.
- **routers:** `review-router`, `security-router`, `ui-router`, `ui-research`, `ui-build`, `ui-figma`, `ui-qa`.
- **review:** `architecture-map`, `architecture-normalizer`, `migration-planner`, `multi-agent-pr-review`, `agent-squad`, `specialist-dispatch`, `subagent-result-merge`, `external-agent-pack-audit`, `agent-retrospective`, `agents-md-retrospective`.
- **security:** `security-diff-review`, `fix-security-finding`, `threat-model`, `dependency-advisory-audit`, `secrets-and-config-review`, `authz-boundary-review`, `deserialization-parser-review`, `supply-chain-review`.
- **ui:** `ui-business-apps`, `ui-concept-first`, `design-system-extractor`, `figma-to-code`, `code-to-figma`, `playwright-visual-qa`, `mobile-qa`, `responsive-breakpoint-check`, `accessibility-ui-review`.

### Optional groups

- **fast:** `fast`.
- **wiki:** `wiki-query`, `code-wiki-ru`.

### Opt-in upstream groups

- **pocock-interview:** `pocock.grill-me`, `pocock.grilling`, `pocock.grill-with-docs`, `pocock.domain-modeling`.
- **pocock-writing:** `pocock.writing-for-agents`, `pocock.pr`.
- **pocock-retro:** `pocock.retro`.
- **pocock-questionnaire:** `pocock.to-questionnaire`.
- **superpowers:** `superpowers.brainstorming`, `superpowers.diagnosing-superpowers`, `superpowers.dispatching-parallel-agents`, `superpowers.executing-plans`, `superpowers.finishing-a-development-branch`, `superpowers.receiving-code-review`, `superpowers.requesting-code-review`, `superpowers.subagent-driven-development`, `superpowers.systematic-debugging`, `superpowers.test-driven-development`, `superpowers.using-git-worktrees`, `superpowers.using-superpowers`, `superpowers.verification-before-completion`, `superpowers.writing-plans`, `superpowers.writing-skills`.
- **karpathy:** `karpathy.karpathy-guidelines`.
- **business-ui:** `interface.interface-design`, `uipro.ui-ux-pro-max`, `impeccable.impeccable`.
- **property-testing:** `trailofbits.property-based-testing`.
- **context-continuation:** `pocock.handoff`, `context.context-compression`.

### Author dependencies of owner groups

- **core:** `superpowers.systematic-debugging`, `superpowers.test-driven-development`, `superpowers.requesting-code-review`, `superpowers.receiving-code-review`, `superpowers.verification-before-completion`, `karpathy.karpathy-guidelines`, `trailofbits.property-based-testing`.
- **review:** `superpowers.brainstorming`, `superpowers.diagnosing-superpowers`, `superpowers.dispatching-parallel-agents`, `superpowers.executing-plans`, `superpowers.finishing-a-development-branch`, `superpowers.receiving-code-review`, `superpowers.requesting-code-review`, `superpowers.subagent-driven-development`, `superpowers.systematic-debugging`, `superpowers.test-driven-development`, `superpowers.using-git-worktrees`, `superpowers.using-superpowers`, `superpowers.verification-before-completion`, `superpowers.writing-plans`, `superpowers.writing-skills`.
- **ui:** `interface.interface-design`, `uipro.ui-ux-pro-max`, `impeccable.impeccable`.
<!-- END GENERATED SKILL REGISTRY -->

## Author-Maintained Skill Dependencies

Bible owns policy, standards and routers; reviewed author skill trees retain
their origin and update independently. The catalog contains 30 original trees:
all 15 Superpowers 6.4.2 skills, the original Karpathy-inspired guidelines, and
nine Matt Pocock skills, three business UI specialists, property-based testing
and context compression. Normal profiles install their 20 required originals;
Pocock groups remain explicit selections. Local debugging, TDD and review names
are thin adapters; the Karpathy rewrite is removed. See the
[complete 62-skill migration ledger](docs/absorbed-skills-migration.md).

The [business UI profile](docs/business-ui-profile.md) focuses on dashboards,
CRM and working applications. It selects original Interface Design, UI UX Pro
Max and Impeccable 4.5.0, alongside native component and data-visualization tools.
`implement-spec` and unverified additional sources remain deferred.

[Testing and context authors](docs/quality-context-authors.md) add original
property-based testing and optional handoff/compression. The
[continuation policy](docs/task-continuation.md) preserves concise state and
fresh evidence. [Cross-provider review](docs/cross-provider-review.md) and the
[offline quorum evaluator](docs/worker-quorum.md) bind decisions to a fixed
target and verified records; they do not install a model runtime.

Both modes are off by default. Use `/multimodel <task>` for budget code proposals
and stronger review, `/quorum <task>` for fixed review voting, or both commands
for both modes. Ordinary tasks keep the selected model. These task-text commands
are documented in [Explicit Activation](docs/cross-provider-review.md#explicit-activation).

[Context cache preparation](docs/context-cache.md) preserves stable author and
source text, checks freshness and reads provider-reported cache usage.
[Targeted mutation checks](docs/targeted-mutation-testing.md) run selected Python
test-strength probes in isolated copies. Both are opt-in; they do not activate
cloud accounts, guarantee billed savings or install a mutation framework.

```bash
be skills list --json
be install --dry-run
be skills plan --group pocock-interview --json
be skills ensure --group pocock-interview
be skills route grill-me --json
be skills check --group pocock-interview --json
be skills update --group pocock-interview --dry-run --json
```

`ensure` installs missing reviewed dependencies and reuses identical existing
trees. `update` applies the catalog's reviewed revision; an author tracking tip
is only reported by `check`. `be update` updates Bible and fills missing profile
dependencies; author version changes remain separate. `--skip-upstream` prepares
portable files only and reports incomplete author readiness as `SKIP`.
The selected Codex skill root is inspected recursively, including `external/`;
extra native provider roots can be inspected through repeated `--skill-root`.
Files on disk do not prove current-session exposure. See the
[lifecycle and recovery guide](docs/upstream-skills.md),
[architecture](docs/superpowers/specs/2026-10-03-upstream-managed-skills-design.md),
and [addition queue](docs/upstream-skills-backlog.md).

## Runtime Boundary

This repo intentionally does not include local worker/runtime configuration:

- no `~/.codex/config.toml`;
- no auth files;
- no `.env` files;
- no model provider credentials;
- no MCP server secrets;
- no Codex session/cache/worktree state.

The portable package includes engineering instructions, skills, standards,
documentation, and CLI helpers. Your existing Codex worker, MCP, notify,
Computer Use, and model provider setup remain local.

Installed profiles select a discovery route for the question: targeted text
search for literals, LSP navigation for symbols, a fresh code graph for
architecture, and scoped document search for docs and ADRs. They do not require
every tool on every task. Runtime services remain local and their availability
must be verified in the current host.

Focused workflows include `wiki-query` for read-only answers from an existing
wiki (optional `wiki` group), `mobile-qa` for native Android/iOS checks using a
selected device and expected-state assertions, and optional Archify rendering
after `architecture-map` verifies source facts. These skills do not install
Mobile MCP, another wiki manager, a renderer, or an agent framework. External
runtime pilots retain the common worker contract and must demonstrate their
actual scope before activation.

See `docs/worker-runtime-boundary.md`.

The offline [worker evidence helper](docs/worker-evidence.md) fingerprints an
explicit file allowlist, validates the common worker result contract, and
compares matched historical workloads. It preserves failed/skipped checks and
unknown measurements; it installs no runtime and does not authenticate execution.
It also evaluates bounded run decisions from measured counters, progress hashes,
and checkpoint state. The optional [memory retrieval helper](docs/memory-retrieval.md)
plans query variants and combines ranked results from an existing search service
while retaining source hashes and the original results. See the
[Ruflo adoption decision and pilot results](docs/ruflo-adoption.md).

## Prompt Profiles

- `steady` is the default for new installs. It keeps the complete default skill
  catalog, selects a narrow leaf workflow directly, and reuses the active route,
  loaded skill instructions, and runtime metadata on same-task follow-ups.
- `full` keeps exhaustive first-turn routing and capability discovery, but also
  reuses them while the task, risk, and required tools remain unchanged.
- `minimal` keeps the steady-state behavior with a smaller global prompt.
- `fast` is a deliberately limited mode that installs only the `fast` skill.

Updating or reinstalling through `be`, `make install`, or the local installer
preserves the profile recorded in the existing manifest. Migrate explicitly
after reviewing the plan:

```bash
be update --dry-run --prompt-profile steady
be update --prompt-profile steady
```

Switching between `steady`, `full`, and `minimal` changes routing policy while
preserving the selected specialist catalog. Switching from `fast` to `steady`
also restores the default specialist skills.

## Install

Primary install path:

```bash
git clone https://github.com/Mesteriis/Engineering-Bible-AI.git
cd Engineering-Bible-AI
make validate
make dry-run
make install
```

Install optional wiki skills:

```bash
make install-wiki
```

This preserves the existing prompt profile. If it is `fast`, first switch to
`steady` using the commands above; `fast` activates only its own skill even when
additional groups are requested. The same rule applies to `make install-all`.

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
explicit side-effect permissions. Bible does not synthesize hooks, provider
configuration, credentials, or local runtime services. Upstream package install
scripts can still modify user settings: inspect those scripts and back up only
affected settings before installation, then compare them after the smoke test.
Do not treat a package's automatic plugin activation as a verified integration.

The audited optional catalog includes pinned workflow state, browser evidence,
dependency source, and dependency documentation capabilities. Browser runtime
setup is explicit and headless; project task state uses stealth mode; external
documentation authentication is never part of the Bible install.

The pinned `opencode`, `qmd`, and `semgrep` CLIs are separate opt-in selections:

```bash
be tools plan --tool opencode --tool qmd --tool semgrep
be tools install --tool opencode --tool qmd --tool semgrep
be tools doctor --tool opencode --tool qmd --tool semgrep
```

`doctor` proves CLI startup, not a working provider or MCP integration. Check
the executable path as well: a private installation may be available to the host
without appearing in its package manager's global inventory. Do not install a
duplicate solely because the catalog reports `MISSING`. Worker configuration,
keys, MCP, scanner rules, document collections, model weights, and functional
evidence stay outside the public package. Delegation evidence follows
`skills/subagent-result-merge/SKILL.md`.

Claude Code uses its own format. Its personal `CLAUDE.md` can import the installed
`instructions/global/steady.md`, and personal skill directories can link to the
installed skills. Verify support in the installed host version and preserve
existing custom files. Keep one discoverable Bible skill root per host; never
copy Codex TOML into Claude settings. The main installer still owns only its
Codex-compatible files, not Claude authorization or runtime configuration.

Install every registry group:

```bash
make install-all
```

Stable install from a GitHub release:

```bash
RELEASE=v0.4.1
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
into `CODEX_HOME`/`AGENTS_HOME`. Managed `engineering/`, `docs/` and `templates/`
copies also live in `CODEX_HOME` so relative links from active owner skills
resolve. Claude adapters should bind helper and reference paths to the resolved
canonical skill directory. The ownership manifest records every managed
file hash and mode. Unmanaged files are never overwritten or removed, including
with `--force`. Use `--migrate-legacy` only for an intentional takeover of an
identical legacy installation. Installation is journaled, backed up, and rolled
back on failure.
Upgrades prune retired empty directories only inside the portable package
snapshot; rollback restores their prior modes. Active custom skill directories
remain outside this cleanup.

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
be install --dry-run --prompt-profile full
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
- The default prompt profile is `steady`; `full` keeps strict first-turn
  routing, `minimal` is compact steady-state mode, and `fast` activates only the
  fast skill.
- Language-specific rules live in ecosystem skills.
- Broad engineering principles live in `engineering/`; use
  `engineering/README.md` to select only the relevant reference documents.
- In `steady` and `minimal`, clear tasks select the narrowest leaf skill;
  `workflow-router` handles ambiguous or mixed-domain work. `full` routes the
  first non-trivial turn through `workflow-router` unless a narrower skill was
  explicitly requested.
- `engineering-standards` is read only when standards, boundaries, smells,
  naming, refactoring, complexity, or task/TODO structure matter.
