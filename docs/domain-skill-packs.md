# Domain Skill Packs — 2026-10-20

The owner selected all five proposed directions and requested router integration.
This expansion adds 135 original skills, bringing the catalog to 247. There are
18 source records for 17 repositories: the existing Trail of Bits property-based
testing source stays managed, and its other leaves have a separate native source
at the same commit. Default profiles require 5 originals; Superpowers comes from the provider plugin. The 217 optional
native skills are explicit additions, not new dependencies for every installation.

## Reviewed Sources

| Source | Immutable revision | Added leaves | License |
| --- | --- | --- | --- |
| [Trail of Bits](https://github.com/trailofbits/skills) | `5c99c03fb8a9ea568432ecbcba5d86e9f4ac2bf0` | 82; existing property-based-testing retained separately | CC-BY-SA-4.0 |
| [HashiCorp](https://github.com/hashicorp/agent-skills) | `f706481af9b8fedb66de909f6243ad29601afa0c` | 20 Terraform/Packer | MPL-2.0 |
| [Sentry Codex distribution](https://github.com/getsentry/plugin-codex) | `420a2f80f58870d2a42489b759ffddba3f0f3841` | 8 | MIT |
| [dbt](https://github.com/dbt-labs/dbt-agent-skills) | `ef5710860f199897a304eabc8cd5c1973beb60ae` | 16, including migrations and DAG extras | Apache-2.0 |
| [Neon](https://github.com/neondatabase/agent-skills) | `d814689cbba1506b7a25a7a6df5346258ba8ccf8` | 9; one canonical copy of each | Apache-2.0 |

Sentry's source repository `getsentry/sentry-for-ai` was inspected at
`bd3d654a456e3898fc467e0ee18f82c111f3a2c5`. Its documentation directs Codex
installations to the generated distribution above. That distribution includes
the hydrated references and Codex invocation policy; frozen `skills-legacy`
entries are excluded. dbt's internal author-audit skill, Trail of Bits' test
fixtures and Neon's duplicate plugin copies are also excluded from discovery.
Trail of Bits plugins without a public SKILL.md are not invented as skill leaves.

The catalog retains original leaf-tree and license hashes. Trail of Bits also
requires 76 adjacent support paths: scripts, role documents, workflows, reference
files and plugin-level guidance. They have separate `support` hashes and stay at
their original paths. Directory hashes include relative filenames, modes and
content; individual files use SHA-256. A changed or missing support payload makes
native reuse a conflict even when the entry-point skill remains unchanged.
Preparation verifies support before publishing the bundle. Existing destinations
are preserved and failed preparation leaves no published provider.

## Installation And Routing

Use a separate host marketplace namespace for this wave so the preceding
marketplace and installed paths remain valid:

```bash
python3 scripts/native_skill_plugins.py --root . \
  --destination /absolute/private/path/to/new-domain-packs \
  --marketplace-name bible-reviewed-domains \
  --source trailofbits-extended --source hashicorp-skills \
  --source sentry-codex --source dbt-skills --source neon-skills
codex plugin marketplace add /absolute/private/path/to/new-domain-packs --json
codex plugin add bible-trailofbits-extended@bible-reviewed-domains --json
codex plugin add bible-hashicorp-skills@bible-reviewed-domains --json
codex plugin add bible-sentry-codex@bible-reviewed-domains --json
codex plugin add bible-dbt-skills@bible-reviewed-domains --json
codex plugin add bible-neon-skills@bible-reviewed-domains --json
```

The wrappers declare explicit skill paths only. Role/workflow documents remain
references; no custom agents, hooks, MCP servers or setup commands are activated.
Use returned `installedPath` values as repeated `--skill-root` arguments to
`be skills plan --all --json`, inspect the plan, then use `ensure` for the same
selection. Pass the roots to `be install` to remember them in the package manifest.
Normal default requirements remain unchanged. Remove an individual native plugin
through its host manager; dependency-record rollback is a separate operation.

[Reviewed Domain Routes](../skills/workflow-router/references/upstream-domains.md)
is the shared selection reference for workflow, review, security and UI QA
routers. It includes both discovery waves. Canonical IDs and exact leaf names
resolve through `be skills route`; route metadata reports invocation restrictions,
dependency integrity and unverified session exposure. Read the author's complete
selected procedure and its required references before execution. An unavailable
dynamic Workflow engine, model, CLI or account remains a reported prerequisite.

The routing regression fixtures cover representative new tasks. Deterministic
tests check that referenced canonical IDs resolve uniquely and optional groups
do not change normal profiles. These checks establish routing contracts; they
do not establish an LLM's natural-language selection accuracy.

The local resolver check covered 12 representative canonical routes across both
waves. Every selected leaf had verified available files. Eleven reported pending
host exposure; Agent Browser additionally retained pending tool/setup metadata.
A preceding browser fixture run is separate evidence and does not silently
clear the lifecycle's setup record.

## Static Scan And Execution Decisions

Cisco Scanner 2.3.0 scanned all 135 added leaves with network denied, dotenv
disabled and no LLM, OSV, VirusTotal or AI Defense. It reported **16 CRITICAL,
17 HIGH, 12 MEDIUM, 14 LOW and 120 INFO** findings. The scan exited 0 because
this inventory run did not set a severity gate. That exit is not a clean verdict.
Raw findings were retained locally; none were suppressed or silently demoted.

Manual inspection of the HIGH/CRITICAL source locations distinguished these
contexts:

- Sentry's shared verification text requires checking real delivery through MCP.
  The generic prompt-injection signature matches that instruction. Its alert
  workflow also uses authentication to make explicit API writes/deletes: real
  task-scoped operations, not permission to run them during installation.
- Security rule examples, masked `AIza****` placeholders, SARIF glob tests and
  test strings containing `eval` or shell commands are analysis/test fixtures.
  The Actions auditor's flagged remote-execution phrase is inside its explicit
  prohibition. Rust review's `find -exec awk 1` reads a finding index.
- Zeroize-audit's flagged output filename is produced by `_poc_filename`, which
  replaces non-alphanumeric/underscore/hyphen finding-ID characters. This source
  inspection does not constitute runtime proof of the complete generator.
- curl-to-shell installers, unverified Collector extraction/execution examples,
  cloud credentials and local setup writes are real effects. Review the exact
  artifact and target at invocation; use the owner's dependency lifecycle rather
  than blindly executing mutable installation examples.
- The devcontainer resource explicitly sets `bypassPermissions`, seeds Claude
  auth state, changes configuration and can invoke `sudo chown`. It is retained
  as original inactive template content. Its unmodified runtime setup is excluded
  from automatic routing/execution; a requested use requires a separately reviewed
  safe configuration. No bypass, credential seeding or ownership change ran.

This was provenance, packaging and bounded static review, not an exhaustive
security certification of every helper. Live Terraform apply, Packer builds,
warehouse access, Neon provisioning, Sentry issue changes, external code review,
mutation campaigns and custom-agent workflows were not enabled by installation.
Sentry and Neon MCP connection files were excluded from the wrappers.

## Evidence Limits

The original `post-patch-validation` Python runner was exercised with network
denied on a disposable Git repository. The synthetic defect omitted quote
escaping in HTML attributes; the patch enabled it. Seven checks covered benign
control, double-quote exploit, single-quote root-cause variant, byte-identical
unaffected behavior, regression, adjacent markup safety and the fixture suite.
The exploit and variant reached their assertions and failed before the patch,
then passed after it. Plan validation and execution both exited 0; assessment
was `complete`, with no findings or gaps, and `human_review_required: true`.
This is runtime proof for that fixture and runner only. No real patch acceptance
or automated approval is inferred from the synthetic passing result.

Host registration, original-file integrity and resolver checks are separate
from current-chat skill exposure. Open a new chat to refresh its skill catalog.
Runtime tests need a concrete target project, authorized tools and any required
accounts. Existing first-wave synthetic browser, PromQL and OTel results remain
documented in the [discovery pilot](skill-discovery-pilot.md); they do not prove
these new cloud workflows. No model-quality improvement or live A/B result is
claimed.
