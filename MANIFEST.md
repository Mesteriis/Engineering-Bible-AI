# Manifest

## Portable Artifacts

- `AGENTS.md`
- `instructions/global/full.md`
- `instructions/global/minimal.md`
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
- `scripts/build-release.py`
- `scripts/validate-actions-pins.py`
- `scripts/validate-release-contract.py`

Validation profiles: `quick`, `bootstrap`, `full`, and `release`.
The release snapshot is derived exclusively from `git ls-files`.

## Skill Groups

<!-- BEGIN GENERATED SKILL REGISTRY -->
### Default groups

- **core:** `workflow-router`, `mcp-tool-router`, `engineering-standards`, `core-engineering`, `code-quality`, `architecture-principles`, `testing-tdd`, `tdd-guard`, `debugging`, `code-review`, `security`, `performance`, `refactoring`, `documentation`, `quality-gates`, `karpathy-guidelines`, `context-pack`, `session-memory`.
- **ecosystems:** `python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`, `esp32`.
- **routers:** `review-router`, `security-router`, `ui-router`, `ui-research`, `ui-build`, `ui-figma`, `ui-qa`.
- **review:** `architecture-map`, `architecture-normalizer`, `migration-planner`, `multi-agent-pr-review`, `agent-squad`, `specialist-dispatch`, `subagent-result-merge`, `external-agent-pack-audit`, `agent-retrospective`, `agents-md-retrospective`.
- **security:** `security-diff-review`, `fix-security-finding`, `threat-model`, `dependency-advisory-audit`, `secrets-and-config-review`, `authz-boundary-review`, `deserialization-parser-review`, `supply-chain-review`.
- **ui:** `ui-concept-first`, `design-system-extractor`, `figma-to-code`, `code-to-figma`, `playwright-visual-qa`, `responsive-breakpoint-check`, `accessibility-ui-review`.

### Optional groups

- **wiki:** `code-wiki-ru`.
<!-- END GENERATED SKILL REGISTRY -->

## Explicitly Not Included

- Local Codex config.
- Auth files.
- Credentials.
- Local MCP secrets.
- Runtime app state.
- Generated Codex cache.
