# Manifest

## Portable Artifacts

- `AGENTS.md`
- `engineering/`
- `skills/`
- `skills/registry.yml`
- `reference/` legacy/deprecated compatibility references.
- `templates/`
- `scripts/`
- `tests/`
- `examples/`
- `docs/`
- `.github/`
- `Makefile`
- `VERSION`
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

## Command Entry Points

- `Makefile`
- `scripts/install.sh`
- `scripts/install-codex.sh`
- `scripts/install_codex.py`
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

## Default Skill Groups

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
`architecture-map`, `architecture-normalizer`, `migration-planner`,
`multi-agent-pr-review`, `subagent-result-merge`, `agent-retrospective`,
`agents-md-retrospective`.

Security:
`security-diff-review`, `fix-security-finding`, `threat-model`,
`dependency-advisory-audit`, `secrets-and-config-review`,
`authz-boundary-review`, `deserialization-parser-review`,
`supply-chain-review`.

UI:
`ui-concept-first`, `design-system-extractor`, `figma-to-code`,
`code-to-figma`, `playwright-visual-qa`, `responsive-breakpoint-check`,
`accessibility-ui-review`.

## Optional Skill Groups

Wiki:
`code-wiki-ru`.

## Explicitly Not Included

- Local Codex config.
- Auth files.
- Credentials.
- Local MCP secrets.
- Runtime app state.
- Generated Codex cache.
