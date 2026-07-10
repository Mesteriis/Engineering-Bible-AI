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
- Strict test-first gate explicitly requested -> `tdd-guard`; practical behavior
  testing -> `testing-tdd`.
- Assumption checking or explicit anti-overengineering discipline ->
  `karpathy-guidelines`.
- Completion evidence, release gates, or drift audit -> `quality-gates`.
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

- Repository handoff or Repomix-style bundle -> `context-pack`.
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

- Parallel implementation lanes or worktrees -> `agent-squad`.
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
