---
name: external-agent-pack-audit
description: "Audits external agent, skill, plugin, hook, or marketplace packs for licenses, installers, secrets, runtime state, and safe adaptation."
---

# External Agent Pack Audit

Use this skill before importing or adapting a third-party agent, skill, command,
hook, plugin, or marketplace pack.

Do not install or execute unknown packs just to inspect them. Read repository
metadata and files first.

## Audit Scope

Check:

- license and attribution requirements;
- install scripts and hooks;
- commands that execute code;
- network access and API keys;
- generated files and caches;
- secret handling;
- compatibility with Codex skill format;
- overlap with existing Engineering Bible skills;
- whether adaptation is safer than direct import.

## Decision Options

Choose one:

- direct install: only when the pack is compatible, trusted, and requested;
- Codex adaptation: rewrite the behavior as a local `SKILL.md`;
- reference only: document the idea without installing;
- reject: unsafe, unclear license, or too much runtime coupling.

## Evidence

Use current sources:

- upstream README;
- license file;
- plugin metadata;
- install scripts;
- relevant source files;
- local validation output if cloned for inspection.

## Output

```markdown
External pack audit:
- Source:
- License:
- Runtime/hooks:
- Secrets/network:
- Overlap:
- Decision:
- Adaptation plan:
- Validation:
```
