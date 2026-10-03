# Worker And Runtime Boundary

This repository packages portable Codex instructions and skills. It does not
package a local worker runtime.

## Included

- Engineering standards.
- Codex-compatible skills.
- Router and wrapper skills.
- A provider-neutral contract for context-efficient graph and symbolic code
  navigation when the current agent host exposes those capabilities.
- `code-wiki-ru` scripts and references.
- Install and validation helpers.
- Documentation and templates.

## Excluded

- `~/.codex/config.toml`
- `~/.codex/auth.json`
- Codex sessions, rollouts, cache, worktrees, and app state.
- `.env` files and credential stores.
- Moon Bridge configuration.
- DeepSeek, OmniRoute, OpenAI, Home Assistant, GitHub, or MCP credentials.
- Private SSH config and private keys.
- Local app bundles and LaunchAgents.
- Local worker launchers, role-to-model mappings, provider endpoints, MCP
  configuration, weights, indexes, capability snapshots and machine reports.

## Why

Worker/runtime configuration is machine-specific and often contains credentials
or permission surfaces. It must be reviewed locally and should not be published
as a reusable engineering package.

## Safe Install Rule

The installer may copy:

- `engineering/` into `CODEX_HOME` and `AGENTS_HOME`
- selected `skills/` into `CODEX_HOME`
- `templates/`
- `scripts/`
- `tests/`
- example root instructions

Managed skills are not mirrored into `AGENTS_HOME` by default. Keeping one
visible skill root prevents duplicate entries in Codex UI while preserving
`AGENTS_HOME/engineering` references for skill-relative documentation links.

The installer must not write or synthesize secrets, model provider config, MCP
server credentials, or auth files.

## Compatible Agent Hosts

The global prompt profiles may be reused by Codex-compatible agent hosts. The
host remains responsible for exposing and authorizing its local code knowledge
graph and LSP-backed symbolic navigation services. The portable package names
capability roles, not provider identifiers, launch commands, endpoints, or
credentials.

Agents should reuse fresh indexes and active project state, use graph evidence
for cross-file structure and impact, use symbolic navigation for the smallest
necessary definitions and references, and fall back to targeted text search for
literals, configuration, non-code files, or unavailable services. Local host
configuration must remain untracked and be validated on that machine.

Select targeted text search for a local edit, symbolic navigation for
definitions/references, a fresh graph for architecture/impact, local document
search for documentation/ADRs, version-matched documentation for external
libraries, and bounded packs for handoff. Index presence does not establish
freshness: compare source revision and relevant file hashes, including local
changes. Refresh stale scope or use current source with the limitation stated.

## External Worker Activation

Keep a capability matrix with distinct states: installed, configured, exposed
to the current host session, and functionally verified. A configuration written
for a future session remains inactive until tested. Preserve existing parent
model/provider, auth mechanism, unrelated configuration and user changes.
Do not extract subscription tokens for third-party APIs or duplicate a working
router. Native custom-model support must be verified against the installed
host; otherwise use an explicit verified external CLI route.

Portable roles and the result contract live in `specialist-dispatch`,
`agent-squad`, `context-pack`, and `subagent-result-merge`. Effective permissions,
model IDs, endpoints, provider secrets, launch commands and artifacts belong to
private machine state. Local helper inference starts on demand, binds only to
loopback when served, and has an explicit stop command. Text response and tool
calling are separate capabilities; do not claim the latter without a test.

Before activation, a synthetic parent-to-worker test must prove the parent's
dispatch and returned result. Record requested provider/model separately from
runtime/provider metadata, its source and verification level, or `unknown`.
A worker's self-description and a manual CLI run are insufficient. Provider
metadata is not independent verification of internal execution.

Verify enforced write denial, reads outside the allowlist, arbitrary execution
denial, minimal environment, absence of a fake secret canary, timeout, process
tree cancellation, retry limits, and no hidden fallback. Inspect actual flags,
including nested launchers: approval-bypass or sandbox-bypass modes are
forbidden. A worktree or textual read-only role is not a security sandbox, and
read access does not itself authorize export. If the effective boundary cannot
be verified, leave that route inactive and mark it BLOCKED.

Capture command stdout/stderr and the original exit code before output
compression. Store safe raw artifacts privately and link them from results;
filters and summaries cannot convert FAIL or SKIP to PASS. Verify automatic
wrappers with an intentionally failing fixture. State independent checks that
passed even when another component remains BLOCKED.

The portable [worker evidence helper](worker-evidence.md) can fingerprint an
explicit source allowlist, validate launcher-supplied records against source and
artifact roots, and compare matched historical workloads. Its consistency checks
do not authenticate metadata, prove execution, or enforce a sandbox. The launcher
still records execution facts independently; an artifact's existence is not proof
of its contents. Comparison never activates a route or selects a winner.

## Cache And Mutation Helpers

The opt-in [context cache helper](context-cache.md) prepares stable text and
reads provider-reported token counters. It performs no dispatch, authentication,
remote cache creation or automatic context export. A private verified adapter
owns actual API caching and captured usage; unknown savings remain unknown.

The opt-in [mutation helper](targeted-mutation-testing.md) runs selected local
Python tests in temporary source copies with a minimal environment and bounded
process execution. Test code still executes on the local host: a temporary
directory is not a sandbox. It does not execute author helpers, alter working
source, install a framework or turn runner errors into killed mutants.

## Existing Codex Worker

Cross-provider voting uses the portable [quorum contract](worker-quorum.md)
and [integration guide](cross-provider-review.md). The evaluator binds target,
policy and retained evidence; it launches no provider and establishes no
authentication or sandbox. Keep missing or unverified routes blocked. Required
failures and confirmed critical evidence cannot be replaced by majority approval.

Default: keep the current selected model; multimodel and quorum are off.
`/multimodel` enables the budget-proposal/stronger-review workflow;
`/quorum` separately enables fixed voting. They are task-scoped commands, not
implicit consequences of parallel agents, quality requirements or task risk.
Neither command grants source export or makes an unverified route available.

If a machine already has a working Codex worker, keep its runtime configuration
in place and install this repository as a skill/standards layer only.
