# Reviewed Domain Routes

Read only the branch matching the task. These are Bible selection rules;
the selected author's complete workflow and required references remain the
procedure. Canonical IDs resolve with `be skills route ID --json`; exact skill
names also resolve. The catalog owns all leaves and source pins, the registry
owns optional groups. Select one leaf first; add a supporting leaf only for a
distinct evidence need. Reuse the selected provider on follow-ups.

## Provider And Execution Boundary

Prefer an explicitly named compatible session provider. Resolve file integrity,
dependencies, tool availability and current-session exposure before invocation.
`available` reports filesystem readiness, not host exposure or runtime proof.
For missing native packs, use the reviewed native plugin preparation and host
installation in [the discovery guide](../../../docs/skill-discovery-pilot.md).
Read author helpers relative to the resolved skill/plugin path, including
retained sibling support. A missing `Workflow`, agent role, MCP or CLI is a
dependency gap; report it without replacing the required author procedure.

These routes grant no cloud access, source export, model changes, worker
delegation, mutation campaign, production change or external communication.
Apply the task's existing authorization. Author `allowed-tools` metadata is
not a host permission grant. User-invoked leaves require explicit selection;
an ambiguous task must not trigger Tarot, survey interpretation or an external
second opinion. Keep `/multimodel` and `/quorum` opt-in owner policy intact.

## Security And Test Strength — Trail Of Bits

| Concrete task | Canonical leaf |
| --- | --- |
| Existing security patch: reproduce original exploit, variants and regressions locally | `trailofbits.post-patch-validation` |
| Search for the same root cause after a validated finding | `trailofbits.variant-analysis` |
| Configure or interpret a requested mutation campaign | `trailofbits.mutation-testing` |
| Generated-input invariants and round trips | `trailofbits.property-based-testing` |
| AI agents in GitHub Actions: untrusted event data, execution and token boundaries | `trailofbits.agentic-actions-auditor` |
| Check a proposed finding for false positives | `trailofbits.fp-check` |
| Dependency provenance, publishers, install scripts and version-matched advisories | `trailofbits.supply-chain-risk-auditor` |
| Semgrep, CodeQL or SARIF specifically requested | `trailofbits.semgrep`, `trailofbits.codeql`, `trailofbits.sarif-parsing` respectively |
| C/C++ or Rust security audit | `trailofbits.c-review` or `trailofbits.rust-review` |
| Dangerous API/config design or specification compliance | `trailofbits.sharp-edges` or `trailofbits.spec-to-code-compliance` |
| Fuzzing, sanitizers, crypto timing, zeroization, APK or contract audit | Select the exact matching leaf in the `trailofbits-extended` group |

Generic vulnerability fixes and security scans retain their existing native
Codex Security routes. Use Trail of Bits when its named evidence type is the
deliverable. Mutation campaigns require isolated targets and a passing baseline.
The imported devcontainer template sets permission bypass and prepares auth
state: keep it inactive; any requested use needs a separately reviewed safe
configuration. Imported hooks are excluded. Commands in setup examples, mutable
installers and external review launchers are not run merely by selecting a pack.

## Infrastructure — HashiCorp

| Concrete task | Canonical leaf |
| --- | --- |
| Terraform configuration conventions | `hashicorp.terraform-style-guide` |
| Terraform native tests, mocks and assertions | `hashicorp.terraform-test` |
| Refactor existing Terraform into modules | `hashicorp.refactor-module` |
| Policy checks, Stacks or import/search | `hashicorp.terraform-policy`, `hashicorp.terraform-stacks`, `hashicorp.terraform-search-import` respectively |
| Provider resources, data models, tests or framework migration | Matching `hashicorp.provider-*` leaf; `hashicorp.new-terraform-provider` for a new provider |
| Packer image builds or publication | `hashicorp.aws-ami-builder`, `hashicorp.azure-image-builder`, `hashicorp.windows-builder` or `hashicorp.push-to-registry` |

Planning and local validation do not authorize `apply`, image publication,
account changes, real acceptance-test resources or Windows execution-policy
changes. Select the target environment and the corresponding task scope first.

## Observability — Grafana, OpenTelemetry And Sentry

| Concrete task | Canonical leaf |
| --- | --- |
| Prometheus queries or Loki queries | `grafana-skills.promql` or `grafana-skills.loki` |
| Grafana panels/dashboards or k6 execution | `grafana-skills.dashboarding` or `grafana-skills.k6-manage` |
| Instrument an application using OTel | Matching `ollygarden-otel.otel-*` language leaf, such as `ollygarden-otel.otel-python` |
| Collector pipelines, OTTL or conventions | `ollygarden-otel.otel-collector`, `ollygarden-otel.otel-ottl`, `ollygarden-otel.otel-semantic-conventions` respectively |
| Add Sentry instrumentation or inspect a Sentry issue | `sentry.sentry-instrument` or `sentry.sentry-debug-issue` |
| Sentry alerts, releases, stack traces, Cocoa snapshots or OTel exporter | Matching `sentry.sentry-*` leaf |

Choose Grafana Cloud administration only for an explicitly targeted Grafana
Cloud task, via its matching leaf. A Sentry request uses Sentry; a general OTel
request stays vendor-neutral. Sentry/Neon MCP configuration is not activated by
these wrappers. Resolve an existing authorized connection or report setup gaps.
Issue resolution, alerts, release upload, load tests and telemetry export retain
their independent data and mutation boundaries.

## Analytics — dbt

| Concrete task | Canonical leaf |
| --- | --- |
| Build or debug dbt models | `dbt.using-dbt-for-analytics-engineering` |
| Unit-test a dbt model | `dbt.adding-dbt-unit-test` |
| Model/column documentation | `dbt.maintaining-dbt-documentation` |
| Metrics and semantic models | `dbt.building-dbt-semantic-layer` |
| dbt Mesh, state selection, metadata SQL or job failure | Corresponding leaf in the `dbt` group |
| Core-to-v2, platform migration or dbt upgrade | `dbt.migrating-dbt-core-to-v2`, `dbt.migrating-dbt-project-across-platforms`, `dbt.upgrading-dbt` respectively |

Use these for actual dbt projects. Generic SQL and application migrations keep
their existing ecosystem routes. Preserve local/cloud execution profiles and
the author's migration telemetry distinctions; connecting a warehouse, running
jobs or exporting data requires the task's authorization.

## Neon Platform

Route only explicitly Neon-backed work here. Use `neon.neon-postgres` for
Postgres development, `neon.neon-postgres-branches` for database branch workflows,
and `neon.neon-postgres-egress-optimizer` for measured egress reduction. Auth,
Functions, Object Storage, AI Gateway and Realtime use their matching `neon-*`
leaves. An unclear Neon-specific request can enter through `neon.neon`.
Generic PostgreSQL work does not imply Neon provisioning. Branch reset, schema
changes, account creation and provider/model selection keep task boundaries.

## Browser Automation And Agent Evaluation

- Task-selected CLI browser automation -> `vercel-agent-browser.agent-browser`;
  read the workflow served by the matching pinned CLI. Use a named session and
  preserve user-owned profiles. Existing suitable native tools remain preferred
  by the owner's tool-selection policy.
- Author a skill evaluation suite -> `sentry-skillet.skillet-authoring`.
- Start an eval project, discover errors, audit evals, evaluate RAG, write code
  assertions or calibrate a judge -> the matching `evals-course.*` leaf.
- Review a new pack -> `external-agent-pack-audit`; Cisco Scanner and `skil`
  are optional supporting tools, not replacement author workflows.

Skillet uses the reviewed CLI pin instead of the author's mutable `@latest`
example. A live eval needs reviewed sandbox, auth mounts, network and output
destinations. agent-skill-eval schema checks use dotenv disabled; running an
agent or LLM grader is a separate execution. Dry checks and schema validation
do not establish improved model behavior.
