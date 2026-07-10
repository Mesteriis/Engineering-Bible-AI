# Engineering Bible AI Repository Instructions

## Purpose

This repository packages portable engineering instructions, standards, skills,
templates, validation, and installers. Treat it as a public distribution: local
runtime state and private infrastructure do not belong in tracked files.

## Routing Discipline

Select the narrowest directly relevant skill. Do not invoke `workflow-router`
for a clear single-domain request; reserve it for ambiguous or genuinely mixed
work. Use one primary skill and at most one supporting skill by default.

### Continuation Fast Path

For a same-task follow-up in the same thread, reuse the current skill route and
already-loaded instructions. Do not route again or reread an unchanged
`SKILL.md` unless the domain, risk, required tools, or requested workflow
changed. If compaction removed required instructions, reload only the missing
skill.

## Repository Sources Of Truth

- `skills/registry.yml` owns skill membership, grouping, and order.
- Generated registry blocks in `README.md`, `README.ru.md`, and `MANIFEST.md`
  must be updated with `python3 scripts/registry.py --root . docs --write`; do
  not edit their contents by hand.
- `engineering/README.md` indexes the standards library. Add or remove a
  standard and its index entry together.
- `instructions/global/steady.md` is the default installed global prompt.
- `instructions/global/full.md` preserves exhaustive routing for strict use;
  `instructions/global/minimal.md` is the compact steady-state profile.
- Root `AGENTS.md` contains project-only rules and must not duplicate either
  global prompt.

## Runtime Boundary

Do not commit credentials, auth files, provider endpoints, environment files,
private keys, local agent sessions, caches, generated capability catalogs, or
machine-specific configuration. Runtime tools are discovered dynamically from
the current session; tracked policies must describe capabilities and risk, not
hard-code provider or tool identifiers.

Generated project-local capability files belong under `.engineering-bible/`
and must remain untracked. Do not claim a runtime capability is available until
the current session exposes it.

## Change Rules

- Inspect relevant implementation, tests, docs, and current Git state before
  editing.
- Preserve unrelated dirty-worktree changes; never reset, stash, or overwrite
  them without explicit authorization.
- Prefer the smallest correct change. Keep installer, validation, registry,
  runtime discovery, and documentation responsibilities separate.
- Public CLI changes require compatibility handling, tests, and matching docs.
- Validation output must distinguish `PASS`, `FAIL`, and `SKIP`. A skipped
  release gate is not success.
- Use `apply_patch` for hand-authored edits. Generated-block updates and
  formatting may use their deterministic project commands.
- Never claim a check passed unless the exact command ran successfully.

## Validation

Use the smallest profile that proves the change, then run the broader profile
when shared tooling, installation, or release behavior changes:

```bash
make validate-quick
make validate-bootstrap
make validate
make validate-release
```

Tests are discovered with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Before completion, review the diff for public behavior, runtime-boundary drift,
generated documentation drift, missing regression coverage, and accidental
changes outside scope. Report exact commands, outcomes, assumptions, and
remaining risks.
