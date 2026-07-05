---
name: [be] karpathy-guidelines
description: "Анти-синдром отличника для coding agents: не гадать, не переусложнять, не плодить dead code, спорить с сомнительными предположениями и сначала думать."
---

# Karpathy Guidelines

Use this skill when the main risk is agent overconfidence, assumption drift,
overengineering, dead code, or silent confusion.

This is a Codex-native adaptation of compact coding-agent discipline rules. It
composes with `quality-gates`, `engineering-standards`, and language skills.

## Rules

### Think Before Coding

- Restate the intended behavior.
- Inspect relevant files before editing.
- Identify the smallest change that can work.
- Name one assumption that could be false.

### Ask Instead Of Guessing

Ask or verify when:

- the target behavior has multiple interpretations;
- the repository convention is unclear;
- a command, API, schema, or package manager is unconfirmed;
- a change could affect data, security, billing, or production behavior.

### Keep It Boring

- Prefer direct code over speculative abstractions.
- Do not create a framework for one use case.
- Do not add dependencies for trivial behavior.
- Do not write code that only demonstrates cleverness.

### Clean As You Go

- Remove dead code introduced by the change.
- Do not leave fake TODO implementation.
- Keep names specific to the domain.
- Keep final diffs reviewable.

## Self-Check

Before finalizing, answer briefly:

```markdown
Self-check:
- What assumption did I verify?
- What did I deliberately keep simple?
- What dead or speculative code did I avoid?
```

## Output

When this skill materially affects work, report:

- challenged assumption;
- chosen simple path;
- validation;
- any remaining uncertainty.
