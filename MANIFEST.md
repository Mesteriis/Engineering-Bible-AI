# Manifest

## Portable Artifacts

- `AGENTS.md`
- `instructions/global/steady.md`
- `instructions/global/full.md`
- `instructions/global/minimal.md`
- `instructions/global/fast.md`
- `engineering/`
- `skills/`
- `skills/registry.yml`
- `reference/` legacy/deprecated compatibility references.
- `templates/`
- `scripts/`
- `tests/`
- `examples/`
- `schemas/`
- `config/tools.json`
- `config/upstream-skills.json` reviewed portable dependency provenance only.
- `docs/`
- `.github/`
- `Makefile`
- `VERSION`
- `.python-version`
- `pyproject.toml`
- `.secret-sanity-allowlist`

## OSS Files

- `LICENSE`
- `CHANGELOG.md`
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- `GOVERNANCE.md`
- `SECURITY.md`
- `SUPPORT.md`
- `THIRD_PARTY_NOTICES.md`
- `docs/oss-release-checklist.md`
- `.github/CODEOWNERS`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/dependabot.yml`
- `.github/ISSUE_TEMPLATE/`
- `.github/workflows/validate.yml`
- `.github/workflows/release.yml`

## Command Entry Points

- `Makefile`
- `scripts/install.sh`
- `scripts/install-codex.sh`
- `scripts/install-tools.sh`
- `scripts/install_codex.py`
- `scripts/installer_core.py`
- `scripts/be.py`
- installed wrapper: `be`
- `scripts/registry.py`
- `scripts/audit-quality-gates.py`
- `scripts/validate-repo-tree.sh`
- `scripts/validate-installed-tree.sh`
- `scripts/validate-skill-tree.sh`
- `scripts/validate-router-cases.py`
- `scripts/validate-skill-frontmatter.py`
- `scripts/check-file-size.py`
- `scripts/secret-sanity.sh`
- `scripts/validate-markdown-style.py`
- `scripts/validate.py`
- `scripts/mcp_catalog.py`
- `scripts/mcp_catalog_cli.py`
- `scripts/mcp_catalog_storage.py`
- `scripts/tool_catalog.py`
- `scripts/upstream_catalog.py`
- `scripts/upstream_sources.py`
- `scripts/upstream_skills.py`
- `scripts/upstream_cli.py`
- `scripts/build-release.py`
- `scripts/validate-actions-pins.py`
- `scripts/validate-release-contract.py`

Validation profiles: `quick`, `bootstrap`, `full`, and `release`.
The release snapshot is derived exclusively from `git ls-files`.

Worker evidence uses `scripts/worker-evidence.py` with `scripts/worker_snapshot.py`,
`scripts/worker_results.py`, and `scripts/worker_control.py`; its snapshot,
comparison, and bounded continuation commands are documented in
[docs/worker-evidence.md](docs/worker-evidence.md). Optional retrieval uses
`scripts/memory-retrieval.py` and `scripts/memory_retrieval.py`, documented in
[docs/memory-retrieval.md](docs/memory-retrieval.md). These are portable offline
helpers. Actual run records, source snapshots, and raw artifacts stay untracked.
The [Ruflo adoption decision](docs/ruflo-adoption.md) records the scoped evaluation.

Optional stable-context preparation and usage inspection use
`scripts/context-cache.py` with `scripts/context_cache.py`, documented in
[docs/context-cache.md](docs/context-cache.md). Selected Python test-strength
checks use `scripts/mutation-check.py` with `scripts/mutation_check.py` and the
isolated `scripts/mutation_unittest.py` reporter, described in
[docs/targeted-mutation-testing.md](docs/targeted-mutation-testing.md).
Context requests, provider responses, temporary mutation workspaces and raw
results remain private and untracked. These tools do not install a model runtime.

Prompt profiles: `steady` (new-install default), `full`, `minimal`, and `fast`.
All profiles except `fast` retain the complete selected skill catalog. Existing
installation manifests preserve their recorded profile during update.

Author skill dependencies use the separate `be skills` lifecycle described in
[docs/upstream-skills.md](docs/upstream-skills.md). Downloaded author trees,
dependency ownership locks, provenance records and rollback backups remain local
and untracked. Existing Bible package installation and `be update` remain separate.

## Skill Groups

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

## Explicitly Not Included

- Local Codex config.
- Auth files.
- Credentials.
- Local MCP secrets.
- Runtime app state.
- Generated Codex cache.
