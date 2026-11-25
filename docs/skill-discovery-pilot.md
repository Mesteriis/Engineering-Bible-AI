# Skill Discovery Pilot — 2026-10-20

This report records the first discovery wave. The later
[domain expansion](domain-skill-packs.md) adds 135 skills and router integration;
the current catalog contains 247 originals.

The owner selected all eight researched projects for installation and bounded
demonstrations. Five sources contribute 82 optional original skills to the
catalog, bringing it to 112. The default profiles require 5 originals; Superpowers comes from the provider plugin.
Internal author test skills, malicious scanner fixtures, repository setup and
root instructions are not active skills. Explicit plugin entry paths expose
only the 82 selected leaves while retaining their complete referenced trees.

## Selection And Provenance

| Project | Reviewed selection | License | Bible surface |
| --- | --- | --- | --- |
| [Sentry Skillet](https://github.com/getsentry/skillet) | `6938fd269958440a5b160ee3370ebed3e5fb1d4a`, CLI 1.8.0 | MIT | `sentry-authoring`: one skill; `skillet` companion CLI |
| [Cisco Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner) | CLI 2.3.0; source inspected at `8554b119bd118583f1a235e4e7aad8f2005ef904` | Apache-2.0 | `skill-scanner` companion CLI |
| [AI Evals Course](https://github.com/ai-evals-course/evals-skills) | `80d5f7b0127c7572ed9e9339937adbfd7240ffeb` | Apache-2.0 | `evals`: nine original skills |
| [Grafana](https://github.com/grafana/skills) | `cc33318b60a7fbc2c69a25122164baf00e805f79` | Apache-2.0 | `grafana`: 52 original skills |
| [OllyGarden OpenTelemetry](https://github.com/ollygarden/opentelemetry-agent-skills) | `06b42b61399c8bb3ed54d14ca0daa8c0c4cbaaa9` | Apache-2.0 | `opentelemetry`: 19 original skills |
| [Agent Browser](https://github.com/vercel-labs/agent-browser) | `5ee8691339a5a002e4d7454eec95250253bc7419`, CLI 0.39.1 | Apache-2.0 | `browser-cli`: discovery skill; workflows served by the matching CLI |
| [agent-skill-eval](https://github.com/tardigrde/agent-skill-eval) | CLI 0.7.0; source inspected at `59de161f657b82bfaf8f6abe83dfff38552deb21` | MIT | `agent-skill-eval` companion CLI |
| [skil](https://github.com/domehahn/skil) | Go module `9016d9a21c5e1a2b5fb9c11b97100d444f7d7071` | Apache-2.0 | Separate native Go tool; not an npm/uv/Brew catalog entry |

Skill commits, license hashes and complete leaf digests are in
`config/upstream-skills.json`. npm versions and registry integrity are in
`config/tools.json`. Published CLI artifacts and inspected source commits are
distinct evidence: no reproducible-build equivalence is claimed. The pilot
verified npm tarball integrity and installed exact npm/PyPI versions. npm
installation used `--ignore-scripts`; Agent Browser's native executable was
already inside its integrity-verified tarball. No upstream `prepare`, `init`,
plugin hooks or root setup was run.

## Native Provider Installation

Grafana contains links between nested groups. Flattening its leaves breaks
them; retaining a file with a matching hash alone is insufficient. These five
sources therefore use `installation: native`. Bible records and verifies their
provenance; the host plugin manager owns installation and activation.

Prepare a new destination outside the checkout:

```bash
python3 scripts/native_skill_plugins.py --root . --destination /absolute/private/path/to/new-marketplace
codex plugin marketplace add /absolute/private/path/to/new-marketplace --json
codex plugin add bible-sentry-skillet@bible-reviewed-additions --json
codex plugin add bible-evals-course@bible-reviewed-additions --json
codex plugin add bible-grafana-skills@bible-reviewed-additions --json
codex plugin add bible-ollygarden-otel@bible-reviewed-additions --json
codex plugin add bible-vercel-agent-browser@bible-reviewed-additions --json
```

Preparation downloads only immutable catalog pins, checks archive boundaries,
licenses and every selected leaf digest, and copies declared skill roots and
attribution into separate host wrappers. Original bytes and directory paths
stay intact. The wrappers declare skill entry paths only: no hooks, MCP servers,
agents, credentials or root instructions. The command refuses an existing
destination and does not register or activate a plugin. Changed native packs
require a new prepared destination and explicit host update; `be skills update`
does not modify external providers.

Use each `installedPath` returned by `codex plugin add` as an explicit
`--skill-root`. Repeat that flag for all selected providers:

```bash
be skills plan --group grafana --skill-root /path/from/plugin-add --json
be skills ensure --group grafana --skill-root /path/from/plugin-add --json
be install --skill-root /path/from/plugin-add
```

The package manifest remembers explicitly supplied native roots. Native reuse
records external ownership; same-name edited or differently laid-out providers
remain conflicts. Do not resolve them with force or by editing author files.
Valid indented and folded frontmatter descriptions are supported without
rewriting the three Grafana originals that use them.

## Invocation Policy

Use existing session-exposed native tools when they meet the task. Agent
Browser's broad preference for its CLI does not override the owner's tool
selection or authorization. Its installed discovery skill points to
`agent-browser skills get core` and specialized workflows; read the selected
workflow before invocation. Keep browser tasks in named sessions and preserve
user-owned tabs, profiles and credentials. Browser, cloud and Electron access
remain task-scoped.

Skillet's original authoring instructions request `@latest`. For Bible-managed
use, bind invocation to the reviewed CLI pin, currently `skillet` 1.8.0, and
review updates through the catalog. This is an explicit owner-policy override;
the original skill is unchanged. Skillet performs an npm version check and
cache write on ordinary commands. Offline pilot commands denied network and
writes to the user's home. Its direct eval harness bypasses the agent sandbox;
its Docker defaults also mount existing agent auth directories read-write and
enable network. For isolated evals, explicitly set `mount_auth: []`, a reviewed
image, and the intended network policy. Never treat those defaults as isolation
from private history or configuration.

agent-skill-eval loads `.env` at CLI import. Use `PYTHON_DOTENV_DISABLED=1` and a
clean working directory/environment for fixture checks. Its Codex harness uses
workspace-write; other harnesses have different permission behavior. Separate
LLM grading can transmit outputs to a configured provider. Do not enable it for
private traces by implication.

Cisco Scanner's core and behavioral analysis can run locally. LLM judging,
OSV, VirusTotal and AI Defense have distinct network/export effects. The pilot
enabled none of them and denied network. ONNX Runtime attempted to persist a
telemetry identifier; the filesystem sandbox refused it. No exemption was added.
`skil` ran with `--static-only --airgap` under the same network denial. Its
semantic analysis, MCP service, policy enforcement and attestations were not
activated. Its source-pinned Go installation has separate maintenance and
rollback from the package-manager tool catalog.

## Demonstration Results

| Project | Real bounded check | Result and limit |
| --- | --- | --- |
| Skillet | Validate the upstream commit-conventions example and run its two cases with `eval --dry --json` | Schema valid; both cases are non-vacuous. No model trials or efficacy comparison ran. |
| Cisco Scanner | Scan the 82 selected leaves; scan separate safe and adversarial text controls with a HIGH gate | Safe control exits 0; adversarial control exits 1 as expected. Candidate scan: 1 HIGH, 15 MEDIUM, 2 LOW, 35 INFO. |
| AI Evals Course | Apply `write-code-eval` to the observed wrong-executable preflight failure class | Four local tests cover matching checks, wrong executable/arguments/environment/exit, missing evidence, malformed targets and boolean exits. Structured traces are synthetic. |
| Grafana | Apply `promql` to a temporary Prometheus 3.15.0 and synthetic request counters | Expected error ratio 0.2, observed 0.2; malformed aggregate-before-rate expression rejected. The temporary container and fixture server were removed. |
| OllyGarden OTel | Apply `otel-python` with SDK 1.45.1, in-memory spans and metrics, network denied | Two related spans, propagation round trip and counter sum 5 verified; no network exporter. |
| Agent Browser | Fresh named session; open a loopback fixture, fill the input, click its button, wait for the result and capture a screenshot | Actual DOM result verified; session and fixture server closed. No personal browser profile or account used. |
| agent-skill-eval | Validate its upstream validate-config suite with dotenv disabled and network denied | Suite validation succeeds; no live agent or LLM judge was run. |
| skil | Static, airgapped scan of the same safe/adversarial controls | Safe control exits 0; adversarial control exits 1 as expected. No model/runtime enforcement proof. |

The Cisco HIGH finding in `k6-manage/SKILL.md:290` is an explicit
`subprocess.run(["gcx", ...], timeout=60)` example for paginated API queries.
The reviewed fragment uses a fixed executable and an argv list, not shell
evaluation or downloaded code. It remains a task-authorized external API
operation, not an automatic startup action. Its raw finding is retained; the
pilot did not suppress or relabel the scanner result as a security guarantee.

These checks prove the listed operations only. They do not establish correct
execution of all 82 workflows, real-cloud access, private trace safety under
different flags, or improved model behavior. Host registration and filesystem
integrity also do not prove that the current chat has refreshed its skill list.

## Recovery

Native plugins can be removed individually with `codex plugin remove` using
their IDs shown above. Preserve any needed source bundle and evidence first.
Dependency rollback and native plugin removal are separate operations; inspect
current provider paths before rolling back records. CLI installations have
their own package-manager state. Agent Browser's preceding catalog pin was
0.37.1; restoring skill files does not restore that executable. No user service,
agent account, credential configuration or private history was migrated.
