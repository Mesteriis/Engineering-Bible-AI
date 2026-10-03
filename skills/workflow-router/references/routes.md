# Exhaustive Workflow Routes

Read this file only when the compact routes in `../SKILL.md` cannot resolve an
ambiguous or mixed request.

## Product UI

- Any broad product UI request spanning research, concept, implementation, Figma,
  or rendered QA -> `ui-router`.
- Visual direction before implementation -> `ui-concept-first`.
- Evidence, critique, comparisons, or design research -> `ui-research`.
- Figma selection or component to code -> `figma-to-code`.
- Implemented UI back to Figma or Code Connect -> `code-to-figma`.
- Rendered browser or screenshot validation -> `ui-qa`, then the narrowest QA
  leaf such as `playwright-visual-qa`, `responsive-breakpoint-check`, or
  `accessibility-ui-review`.

## Security

- Mixed security work -> `security-router`.
- PR, commit, branch, or patch security review -> `security-diff-review`.
- Fix one finding -> `fix-security-finding`.
- Threat model -> `threat-model`.
- Dependency advisory or CVE -> `dependency-advisory-audit`.
- Secrets/config, authorization, parser/deserialization, or supply-chain work ->
  the matching leaf review skill.

## Review And Architecture

- Mixed review/planning request -> `review-router`.
- Read-only PR or local diff review across independent dimensions ->
  `multi-agent-pr-review`.
- Repository or subsystem map -> `architecture-map`.
- Deterministic large-tree decomposition -> `architecture-normalizer`.
- Framework, schema, API, package, infrastructure, or data migration ->
  `migration-planner`.
- Merge independent agent reports -> `subagent-result-merge`.
- Repeated agent failure retrospective -> `agent-retrospective`.
- Durable AGENTS.md rule update after repeated evidence ->
  `agents-md-retrospective`.

## General Engineering

- General implementation when no narrower task skill fits -> `core-engineering`.
- Standards, responsibility boundaries, complexity, smells, naming, or task-plan
  conventions -> `engineering-standards`.
- Architecture boundary or dependency-direction work ->
  `architecture-principles`.
- Maintainability cleanup or explicit code-quality review -> `code-quality`.
- Strict test-first gate explicitly requested -> `tdd-guard` with the original
  `superpowers.test-driven-development`; behavior testing uses that author
  provider directly.
- Useful invariants, roundtrips or generated-input testing -> original
  `trailofbits.property-based-testing`; preserve target dependency policy.
- Assumption checking or explicit anti-overengineering discipline ->
  `karpathy.karpathy-guidelines`.
- Completion evidence, release gates, or drift audit -> `quality-gates`.
- Explicit targeted mutation or weak-test assessment -> `quality-gates` with
  `docs/targeted-mutation-testing.md`; execute only the selected isolated pilot.
- Documentation change -> `documentation`.
- Python, TypeScript/JavaScript, Rust, Go, C/C++, Home Assistant, ESPHome, or
  ESP32 work -> matching ecosystem skill.

## Task Profiles

When profile classification changes mutation or evidence policy, classify the
task as one of:

- `quick-fix`: local, reversible, and narrowly scoped;
- `feature`: cross-module behavior or persistent state;
- `migration`: schema, protocol, auth, infrastructure, or compatibility change;
- `frontend-live`: user-visible behavior requiring a built app and browser
  evidence;
- `deep-review`: read-only adversarial review;
- `research`: version-specific external documentation or dependency source.

A profile controls workflow and evidence. It never implies a provider or fixed
runtime-tool inventory.

## Context And Memory

- Explicit fresh-agent handoff -> original `pocock.handoff`; long-task
  compression -> original `context.context-compression`. Both are opt-in;
  checkpoint facts and source freshness remain owner policy in
  `docs/task-continuation.md`.

- Repository handoff or Repomix-style bundle -> `context-pack`.
- Repeated authorized worker context or cache-hit evidence -> `context-pack`
  with `docs/context-cache.md`; a prepared prefix does not activate a provider.
- Project-local context tooling state, Serena `.serena/`, Graphify
  `graphify-out/`, Repomix-pack reuse, or whether to initialize indexes ->
  `core-engineering`; add `architecture-map` for graph/dependency questions or
  `context-pack` for a handoff bundle.
- Context Mode hooks, `context-mode upgrade`, Codex hook/config changes, or
  automatic log/context capture -> `core-engineering`; add
  `external-agent-pack-audit` before installing or modifying third-party hooks.
- Verified durable facts, preferences, decisions, or handoff notes ->
  `session-memory`.
- Russian Obsidian-compatible code wiki -> `code-wiki-ru`.

## Agents And External Packs

- `/multimodel` -> `agent-squad` budget-proposal/stronger-review policy;
  `/quorum` -> `multi-agent-pr-review` fixed voting and `docs/worker-quorum.md`
  evidence. Use both commands for both modes. They are off for ordinary tasks;
  same-model parallel lanes do not activate them. Apply `agent-squad` export limits.
  A provider-neutral record does not establish a working model launcher.

- Parallel independent tasks -> `superpowers.dispatching-parallel-agents` with
  `agent-squad` owner policy; implementation from an approved plan ->
  `superpowers.subagent-driven-development` with that policy.
- Isolated Git worktree setup -> `superpowers.using-git-worktrees`.
- Specialist role/team selection -> `specialist-dispatch`.
- External skill, plugin, hook, marketplace, or agent pack import ->
  `external-agent-pack-audit`; add `supply-chain-review` when executable or
  dependency provenance is involved.

## Runtime Capabilities

Use `mcp-tool-router` only when the user asks to inspect/select current-session
capabilities or an external capability is materially required. Do not use it for
ordinary local repository work. Reuse current-session metadata until there is
evidence that it changed.

## Adversarial Discussion

For decision-oriented comparisons without an implementation order, challenge
material assumptions, present one to three viable alternatives with trade-offs,
and separate verified facts from judgment. Use only the narrow skills required
for the decision; do not automatically load the old generic bundle of
`quality-gates`, `engineering-standards`, `core-engineering`, and
`documentation`.

When this mode materially affects the response, report
`discussion-mode: active`. Ask for final confirmation before changing files if
the user requested comparison or recommendation but did not authorize an
implementation. Under high uncertainty, explicitly test both questions:

- Which material hypothesis could be false?
- What changes if the opposite assumption is accepted?

## External Product Skills

When the runtime exposes a product-specific built-in skill, prefer that skill to
copying its procedure into Engineering Bible. Examples include GitHub, OpenAI,
Cloudflare, documents, PDFs, spreadsheets, slides, Gmail, calendar, Drive,
Canva, and Hugging Face workflows. Availability must come from the current
session, not memory.

## Reviewed Upstream Workflows

The opt-in upstream groups and their skill IDs are owned by `skills/registry.yml`;
`config/upstream-skills.json` records immutable sources and workflow intents.
Use `be skills list --json` to inspect them only when provider selection needs
that information. Do not copy a third-party workflow into a Bible route.

- Explicit assumption interview -> catalog intent `grill-me`.
- Interview with glossary and ADRs -> catalog intent `grill-with-docs`.
- Author guidance for writing agent instructions -> `writing-for-agents`.
- Author PR workflow -> `pr`; respect the user's authorization for publication.
- Author retrospective -> `retro`; `agent-retrospective` remains a separately
  named owner workflow.
- Questions for an external requirements expert -> `to-questionnaire`.

Resolve the selected intent or canonical ID with `be skills route INTENT --json`.
The command reports filesystem availability, required tools/setup, and
unverified session exposure. Use the real host invocation after exposure is
established. An absent provider is a dependency of the selected installation
profile; use its missing-only install and report pending reload or unavailable
host tools. Keep author procedures and owner policy separate. Updates require
reviewed catalog pins, not a mutable tracking tip. These routes never imply
background monitoring.

## Original Superpowers Providers

Use complete author skills from `obra/superpowers`. The registry owns membership
and profile dependencies; the catalog owns reviewed revisions and tree digests.
Native compatible plugins retain their ownership. Every selection below uses
the provider-resolution contract above and the actual current host invocation.

| Intent | Canonical author provider | Separate Bible policy |
| --- | --- | --- |
| Clarify a design before building | `superpowers.brainstorming` | User scope and personal decision rules |
| Write an implementation plan | `superpowers.writing-plans` | Repository validation commands |
| Execute an approved plan | `superpowers.executing-plans` | Existing authorization and checkpoints |
| Implement through planned subagents | `superpowers.subagent-driven-development` | `agent-squad`, worker permissions |
| Dispatch independent investigations | `superpowers.dispatching-parallel-agents` | `agent-squad`, worker permissions |
| Investigate a failure | `superpowers.systematic-debugging` | Global evidence rules, ecosystem skill |
| Test behavior before implementation | `superpowers.test-driven-development` | Explicit `tdd-guard` policy when requested |
| Request an engineering review | `superpowers.requesting-code-review` | Repository review scope and findings policy |
| Process review feedback | `superpowers.receiving-code-review` | Current source evidence and user scope |
| Verify before a completion claim | `superpowers.verification-before-completion` | `quality-gates`, release and drift rules |
| Create an isolated checkout | `superpowers.using-git-worktrees` | Existing worktree reuse and export limits |
| Finish a development branch | `superpowers.finishing-a-development-branch` | User authorization for publication and merge |
| Create or update an author skill | `superpowers.writing-skills` | `external-agent-pack-audit` when importing |
| Enter the author pack explicitly | `superpowers.using-superpowers` | Current user instructions and host invocation |
| Diagnose pack behavior | `superpowers.diagnosing-superpowers` | Verified runtime evidence |

`debugging`, `testing-tdd` and `code-review` are thin compatibility route names.
They must load their author provider; none stores a shortened author workflow.
The original `karpathy-guidelines` is the separately pinned
`karpathy.karpathy-guidelines` provider. Owner standards, security policy,
context/export controls and result contracts remain Bible content.
