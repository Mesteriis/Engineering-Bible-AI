---
name: workflow-router
description: "Primary autorouting entrypoint for non-trivial engineering prompts. Use first for PR/diff review, security review, UI/frontend work, Figma/code workflows, migrations, architecture exploration, dependency/advisory checks, or requests that mention multiple skills. Chooses the smallest downstream skill set while keeping each selected skill directly runnable."
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
  `quality-gates`, `engineering-standards`, `core-engineering`, `debugging`, `testing-tdd`, `code-quality`,
  `architecture-principles`, `refactoring`, `documentation`, `performance`,
  and the relevant ecosystem skill (`python`, `typescript`, `rust`, `go`,
  `c-cpp`, `homeassistant`, `esphome`, or `esp32`).
- Evidence, validation claims, task lifecycle, completion review, regression
  gates, or repository drift concerns -> `quality-gates`.
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
bash ~/.agents/skills/workflow-router/scripts/validate-routing.sh
```

The script checks mirrored skill files, managed global instruction blocks,
Codex skill frontmatter validation, missing template placeholder text, and
Codex prompt-input visibility for key routing skills.
