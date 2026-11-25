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
- **trailofbits-extended:** `trailofbits.agentic-actions-auditor`, `trailofbits.audit-context-building`, `trailofbits.algorand-vulnerability-scanner`, `trailofbits.audit-prep-assistant`, `trailofbits.cairo-vulnerability-scanner`, `trailofbits.code-maturity-assessor`, `trailofbits.cosmos-vulnerability-scanner`, `trailofbits.guidelines-advisor`, `trailofbits.secure-workflow-guide`, `trailofbits.solana-vulnerability-scanner`, `trailofbits.substrate-vulnerability-scanner`, `trailofbits.token-integration-analyzer`, `trailofbits.ton-vulnerability-scanner`, `trailofbits.burpsuite-project-parser`, `trailofbits.c-review`, `trailofbits.chrome-mcp-troubleshooting`, `trailofbits.code-improver`, `trailofbits.pr-improver`, `trailofbits.skill-improver`, `trailofbits.constant-time-analysis`, `trailofbits.interpreting-culture-index`, `trailofbits.devcontainer-setup`, `trailofbits.differential-review`, `trailofbits.dimensional-analysis`, `trailofbits.dwarf-expert`, `trailofbits.entry-point-analyzer`, `trailofbits.firebase-apk-scanner`, `trailofbits.fp-check`, `trailofbits.gh-cli`, `trailofbits.github-triage`, `trailofbits.goal-prompt`, `trailofbits.let-fate-decide`, `trailofbits.modern-cpp`, `trailofbits.modern-python`, `trailofbits.mutation-testing`, `trailofbits.open-sourcing`, `trailofbits.post-patch-validation`, `trailofbits.review-walkthrough`, `trailofbits.rust-review`, `trailofbits.second-opinion`, `trailofbits.semgrep-rule-creator`, `trailofbits.semgrep-rule-variant-creator`, `trailofbits.sharp-edges`, `trailofbits.spec-to-code-compliance`, `trailofbits.codeql`, `trailofbits.sarif-parsing`, `trailofbits.semgrep`, `trailofbits.supply-chain-risk-auditor`, `trailofbits.address-sanitizer`, `trailofbits.aflpp`, `trailofbits.atheris`, `trailofbits.cargo-fuzz`, `trailofbits.constant-time-testing`, `trailofbits.coverage-analysis`, `trailofbits.fuzzing-dictionary`, `trailofbits.fuzzing-obstacles`, `trailofbits.harness-writing`, `trailofbits.libafl`, `trailofbits.libfuzzer`, `trailofbits.ossfuzz`, `trailofbits.ruzzy`, `trailofbits.testing-handbook-generator`, `trailofbits.wycheproof`, `trailofbits.audit-augmentation`, `trailofbits.crypto-protocol-diagram`, `trailofbits.diagramming-code`, `trailofbits.genotoxic`, `trailofbits.graph-evolution`, `trailofbits.mermaid-to-proverif`, `trailofbits.slicing-code-context`, `trailofbits.trailmark`, `trailofbits.trailmark-finding-triage`, `trailofbits.trailmark-review-gate`, `trailofbits.trailmark-structural`, `trailofbits.trailmark-summary`, `trailofbits.trailmark-variant-neighborhood`, `trailofbits.vector-forge`, `trailofbits.variant-analysis`, `trailofbits.vulnerability-triage-brocards`, `trailofbits.writing-lean-proofs`, `trailofbits.yara-rule-authoring`, `trailofbits.zeroize-audit`.
- **hashicorp:** `hashicorp.aws-ami-builder`, `hashicorp.azure-image-builder`, `hashicorp.push-to-registry`, `hashicorp.windows-builder`, `hashicorp.azure-verified-modules`, `hashicorp.new-terraform-provider`, `hashicorp.provider-actions`, `hashicorp.provider-configuration`, `hashicorp.provider-docs`, `hashicorp.provider-ephemeral-resources`, `hashicorp.provider-framework-migration`, `hashicorp.provider-resources`, `hashicorp.provider-test-patterns`, `hashicorp.refactor-module`, `hashicorp.run-acceptance-tests`, `hashicorp.terraform-policy`, `hashicorp.terraform-search-import`, `hashicorp.terraform-stacks`, `hashicorp.terraform-style-guide`, `hashicorp.terraform-test`.
- **sentry:** `sentry.sentry-create-alert`, `sentry.sentry-debug-issue`, `sentry.sentry-fix-stack-traces`, `sentry.sentry-get-started`, `sentry.sentry-instrument`, `sentry.sentry-otel-exporter-setup`, `sentry.sentry-setup-releases`, `sentry.sentry-snapshots-cocoa`.
- **dbt:** `dbt.adding-dbt-unit-test`, `dbt.answering-natural-language-questions-with-dbt`, `dbt.building-dbt-semantic-layer`, `dbt.configuring-dbt-mcp-server`, `dbt.fetching-dbt-docs`, `dbt.maintaining-dbt-documentation`, `dbt.querying-the-dbt-information-schema`, `dbt.running-dbt-commands`, `dbt.troubleshooting-dbt-job-errors`, `dbt.using-dbt-for-analytics-engineering`, `dbt.using-dbt-state`, `dbt.working-with-dbt-mesh`, `dbt.creating-mermaid-dbt-dag`, `dbt.migrating-dbt-core-to-v2`, `dbt.migrating-dbt-project-across-platforms`, `dbt.upgrading-dbt`.
- **neon:** `neon.neon`, `neon.neon-ai-gateway`, `neon.neon-auth`, `neon.neon-functions`, `neon.neon-object-storage`, `neon.neon-postgres`, `neon.neon-postgres-branches`, `neon.neon-postgres-egress-optimizer`, `neon.neon-realtime`.
- **property-testing:** `trailofbits.property-based-testing`.
- **context-continuation:** `pocock.handoff`, `context.context-compression`.
- **sentry-authoring:** `sentry-skillet.skillet-authoring`.
- **evals:** `evals-course.build-review-interface`, `evals-course.error-discovery`, `evals-course.eval-audit`, `evals-course.evals-start`, `evals-course.evaluate-rag`, `evals-course.generate-synthetic-data`, `evals-course.validate-evaluator`, `evals-course.write-code-eval`, `evals-course.write-judge-prompt`.
- **grafana:** `grafana-skills.admission-control`, `grafana-skills.app-sdk-concepts`, `grafana-skills.cue-kind-definition`, `grafana-skills.reconciler-logic`, `grafana-skills.adaptive-metrics`, `grafana-skills.admin`, `grafana-skills.app-observability`, `grafana-skills.assistant-mcp`, `grafana-skills.cloud-integrations`, `grafana-skills.cost-management`, `grafana-skills.database-observability`, `grafana-skills.dpm-finder`, `grafana-skills.fleet-management`, `grafana-skills.frontend-session-rca`, `grafana-skills.infrastructure`, `grafana-skills.loki-label-analyzer`, `grafana-skills.ml-ai`, `grafana-skills.oncall-irm`, `grafana-skills.private-connectivity`, `grafana-skills.prometheus-cardinality-troubleshooter`, `grafana-skills.prometheus-label-strategy`, `grafana-skills.send-data`, `grafana-skills.synthetic-monitoring-checks`, `grafana-skills.testing`, `grafana-skills.alerting-irm`, `grafana-skills.alloy`, `grafana-skills.beyla`, `grafana-skills.dashboarding`, `grafana-skills.grafana-oss`, `grafana-skills.opentelemetry`, `grafana-skills.promql`, `grafana-skills.skill-authoring`, `grafana-skills.datasources-provisioning`, `grafana-skills.k6`, `grafana-skills.k6-browser-test`, `grafana-skills.k6-cloud-investigate-test`, `grafana-skills.k6-docs`, `grafana-skills.k6-manage`, `grafana-skills.k6-perf-test-website`, `grafana-skills.k6-test-maintenance`, `grafana-skills.k6-trend-analysis`, `grafana-skills.loki`, `grafana-skills.mimir`, `grafana-skills.profilecli-insights`, `grafana-skills.prometheus`, `grafana-skills.pyroscope`, `grafana-skills.tempo`, `grafana-skills.audit-and-reduce-dependencies`, `grafana-skills.check-npm`, `grafana-skills.grafana-scenes`, `grafana-skills.plugin-bundle-size`, `grafana-skills.react-19-plugin-migration`.
- **opentelemetry:** `ollygarden-otel.otel-browser`, `ollygarden-otel.otel-collector`, `ollygarden-otel.otel-collector-builder`, `ollygarden-otel.otel-declarative-config`, `ollygarden-otel.otel-dotnet`, `ollygarden-otel.otel-go`, `ollygarden-otel.otel-java`, `ollygarden-otel.otel-js`, `ollygarden-otel.otel-ottl`, `ollygarden-otel.otel-profiles`, `ollygarden-otel.otel-python`, `ollygarden-otel.otel-ruby`, `ollygarden-otel.otel-sdk-versions`, `ollygarden-otel.otel-semantic-conventions`, `ollygarden-otel.otel-span-events-to-logs-migration`, `ollygarden-otel.otel-telemetry-emissions`, `ollygarden-otel.otel-telemetrygen`, `ollygarden-otel.otel-upgrade`, `ollygarden-otel.otel-weaver`.
- **browser-cli:** `vercel-agent-browser.agent-browser`.

### Author dependencies of owner groups

- **core:** `karpathy.karpathy-guidelines`, `trailofbits.property-based-testing`.
- **ui:** `interface.interface-design`, `uipro.ui-ux-pro-max`, `impeccable.impeccable`.
<!-- END GENERATED SKILL REGISTRY -->

## Explicitly Not Included

- Local Codex config.
- Auth files.
- Credentials.
- Local MCP secrets.
- Runtime app state.
- Generated Codex cache.
