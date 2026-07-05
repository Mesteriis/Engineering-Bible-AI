---
name: [be] session-memory
description: "Создаёт безопасную долговременную память между сессиями: фиксирует только проверенные факты, решения, предпочтения и открытые вопросы без фонового слежения и секретов."
---

# Session Memory

Use this skill when continuity between sessions matters: project conventions,
decisions, repeated user preferences, unresolved risks, or next-step state.

This is a conservative Codex adaptation of persistent-memory tools. It does not
install a background watcher, does not sync to external memory services, and
does not write secrets.

## Memory Contract

Only persist:

- verified project facts;
- explicit user preferences;
- architectural decisions;
- commands that passed or failed;
- unresolved questions;
- next steps with dates or commit references when useful.

Do not persist:

- credentials, tokens, private keys, `.env` values;
- personal data unrelated to the work;
- guesses presented as facts;
- transient thoughts that will confuse future sessions;
- large raw logs when a summary is enough.

## Where To Store

Prefer existing project docs:

- `docs/`
- `AGENTS.md` when the rule should affect future agents;
- a user-approved memory file if the repository already has one.

If there is no existing convention, output a proposed memory delta instead of
writing a new file automatically.

## Workflow

1. Read existing durable instructions or memory files.
2. Identify what changed in the current session.
3. Separate facts, decisions, preferences, and open questions.
4. Remove secrets and unverified claims.
5. Write only if the user asked for persistence or the repository already has
   an established memory/update rule.

## Memory Delta Format

```markdown
Memory delta:
- Fact:
- Decision:
- Preference:
- Open question:
- Validation:
```

## Output

Report:

- memory read;
- memory written or proposed;
- redactions made;
- facts that remain unconfirmed.
