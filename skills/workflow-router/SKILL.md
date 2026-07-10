---
name: [be] workflow-router
description: "Основная autorouting entrypoint для нетривиальных инженерных prompts: PR/diff review, security review, UI/frontend, Figma/code workflows, migrations, architecture exploration, dependency/advisory checks и запросы с несколькими skills; выбирает минимальный downstream skill set."
---

# Workflow Router

Use this as the first stop for non-trivial engineering work unless the user
explicitly invokes a narrower skill.

## Workflow

1. Classify the request.
2. Choose the smallest matching downstream skill set.
3. Read every selected downstream `SKILL.md` before acting.
4. State active skills and any next skill that still needs to be read.
5. Prefer built-in plugin skills over duplicating their procedures.

## Routing

- Product UI, frontend visual design, Figma, image-to-code, or visual QA ->
  `ui-router`.
- Security scan, security review, threat model, finding fix, authz, secrets,
  dependency advisory, parser, or supply-chain work -> `security-router`.
- PR review, branch review, code review, parallel review, architecture mapping,
  migration planning, or post-run retrospective -> `review-router`.
- General implementation, bug fixing, debugging, refactoring, documentation,
  performance work, or language/ecosystem-specific engineering -> select the
  smallest applicable engineering skills:
  `quality-gates`, `karpathy-guidelines`, `engineering-standards`,
  `core-engineering`, `debugging`, `testing-tdd`, `tdd-guard`,
  `code-quality`, `architecture-principles`, `refactoring`, `documentation`,
  `performance`, and the relevant ecosystem skill (`python`, `typescript`,
  `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`, or `esp32`).
- Evidence, validation claims, task lifecycle, completion review, regression
  gates, or repository drift concerns -> `quality-gates`.
- Runtime capability selection, MCP/tool discovery, or a non-trivial task where
  currently exposed host tools may improve evidence -> `mcp-tool-router`.
  Refresh from current-session metadata and rank by capability and risk; never
  route from remembered server or tool identifiers.
- Task profiles: classify work as `quick-fix`, `feature`, `migration`,
  `frontend-live`, `deep-review`, or `research` before selecting skills. A
  profile describes evidence and mutation policy, not a fixed provider list.
- Behavior changes that should be test-first, bug regressions, or requests that
  mention TDD/test blocking/guardrails -> `tdd-guard`.
- Large context handoff, repository packing, AI-friendly code bundles,
  Repomix-style output, or sharing context with another model -> `context-pack`.
- Project-local context tooling state, Serena `.serena/`, Graphify
  `graphify-out/`, Repomix pack reuse, or questions about whether to initialize
  context indexes -> `core-engineering`; add `architecture-map` for graph or
  dependency questions and `context-pack` for handoff packs.
- Context Mode hooks, `context-mode upgrade`, Codex hook/config changes, or
  automatic log/context capture -> `core-engineering`; add
  `external-agent-pack-audit` before installing or changing third-party hooks.
- Durable cross-session facts, preferences, memory deltas, handoff notes, or
  "remember this" requests -> `session-memory`.
- Parallel implementation lanes, multiple agents/worktrees, Claude Squad-style
  orchestration, or independent implementation/test/review streams ->
  `agent-squad`.
- Specialist agent/team selection, role dispatch, or requests for a team of
  architecture/security/frontend/data/docs reviewers -> `specialist-dispatch`.
- External agent/skill/plugin packs, marketplaces, Claude Code packs, hooks, or
  "install/adapt this repo" requests -> `external-agent-pack-audit` before
  copying or executing anything.
- Agent overconfidence, unclear assumptions, overengineering risk, dead code,
  or "Karpathy rules" style discipline -> `karpathy-guidelines`.
- Broad standards work, responsibility boundary analysis, complexity budgets,
  engineering smells, naming rules, refactoring catalogs, or long TODO/task-plan
  structure -> `engineering-standards`.
- GitHub PR/comments/CI workflows -> use the relevant `github:*` skill after
  this router if available.
- OpenAI API, ChatGPT app, Agents SDK, or platform-key work ->
  `openai-docs` or the matching `openai-developers:*` skill.
- Cloudflare Workers, agents, Durable Objects, or Wrangler work ->
  matching `cloudflare:*` skill.
- Documents, PDFs, spreadsheets, slides, Gmail, calendar, Drive, Canva, or
  Hugging Face work -> matching plugin skill.

### Adversarial Discussion Mode (Opponent / Оппонирование)

When the request is decision-oriented (comparisons, trade-offs, approach choices,
risk analysis, naming of alternatives, policy/architecture options) and does
**not** contain an explicit implementation order (`сделай`, `выполни`,
`implement`, `давай сделать`, etc.), this router should prefer:

- `quality-gates`
- `karpathy-guidelines`
- `engineering-standards`
- `core-engineering`
- `documentation` (for option framing and assumptions logs)

In this mode, the agent must use debate-by-default behavior: challenge
assumptions, give 1-3 viable alternatives with trade-offs, and ask for
final confirmation before changing files.

If uncertainty is high, force a short self-check before answering:

- "Какая гипотеза может быть ложной?"
- "Что изменится, если принять противоположное предположение?"

## Priority

Auto-routing is the default. Direct invocation still wins: if the user names
`$security-diff-review`, `$ui-concept-first`, `$architecture-map`, or any other
skill, use that skill directly and only add routers when the prompt spans
multiple modes.

## Output

Before substantive work, briefly say:

- active skill(s)
- why they were selected
- any next skill to read if the request is mixed
- if adversarial mode is active: list `discussion-mode: active` and the alternatives you'll compare.

## Healthcheck

When asked to verify, repair, or remove routing risk, run:

```bash
bash ~/.codex/skills/workflow-router/scripts/validate-routing.sh
```

The script checks managed Codex skill files, absence of duplicate managed skills
in `~/.agents/skills`, reference docs in `~/.agents/engineering`, global
instruction blocks, template placeholders, and Codex prompt-input visibility for
key routing skills.
