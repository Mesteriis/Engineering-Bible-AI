---
name: [be] agent-retrospective
description: "Анализирует запуск агента после повторных сбоев, шумного роутинга, пропущенной валидации, плохих правок или неудачного выбора skill; выдаёт конкретные улучшения для AGENTS.md, описаний skills, роутинга, quality gates или runbook-ов."
---

# Agent Retrospective

Turn repeated agent failure into a small process fix.

## Workflow

1. Identify the failure pattern from actual evidence.
2. Separate one-off mistakes from durable routing or instruction problems.
3. Propose the smallest instruction, skill, or validation update.
4. If editing instructions, use `agents-md-retrospective`.
5. Record validation or explain why only a documentation change was possible.

## Output

- failure pattern
- root cause category
- proposed fix
- files to edit
- validation plan
- residual risk

## Rule

Do not add broad personality prompts. Improve routing, evidence requirements,
or validation gates instead.
