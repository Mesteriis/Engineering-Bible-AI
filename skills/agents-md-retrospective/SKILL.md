---
name: [be] agents-md-retrospective
description: "Обновляет AGENTS.md или глобальные инструкции агента после повторных подтверждённых ошибок; подходит для устойчивых правил репозитория, роутинга, команд валидации, safety-ограничений и уточнений workflow."
---

# AGENTS.md Retrospective

Make instruction updates only when the pattern is durable.

## Workflow

1. Read the relevant local and global instruction files.
2. Identify the exact repeated failure or missing rule.
3. Add the smallest durable instruction that would have prevented it.
4. Avoid duplicating existing rules.
5. Validate by grepping the final instruction and checking for conflicts.

## Rules

- Do not add secrets or environment-specific sensitive values.
- Do not turn AGENTS.md into a skill body.
- Prefer routing rules and validation commands over broad role prose.
- Respect scoped directory instructions.

## Output

- changed instruction file
- rule added or changed
- why it belongs there
- validation command
