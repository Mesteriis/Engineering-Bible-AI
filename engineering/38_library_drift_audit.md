# Library Drift Audit

Engineering Bible is useful only if instructions, skills, scripts, manifests,
installer behavior, and validation agree.

## Drift Classes

Audit should catch:

- a document exists but is not indexed;
- a skill exists but is not installed or validated;
- a command exists but is missing from `MANIFEST.md`;
- an installer copies files but validation does not require them;
- routing references a missing skill;
- docs describe behavior not implemented by scripts;
- runtime or secret-like files enter the portable tree.

## Audit Behavior

Audit commands must:

- read repository files directly;
- report all detected drift issues in one run;
- exit `0` when clean;
- exit `1` when drift exists;
- print actionable messages.

## Required Output Shape

Passing audit:

```text
quality audit passed
- engineering index: ok
- skill references: ok
- validation tree: ok
- manifest: ok
- installer: ok
- golden cases: ok
- runtime boundary: ok
```

Failing audit:

```text
quality audit failed
missing engineering index entry: engineering/35_evidence_contract.md
missing validation required file: skills/quality-gates/SKILL.md
```

## Runtime Boundary

The portable tree must not contain:

- `.env` files;
- auth files;
- `config.toml`;
- private keys;
- certificates;
- provider credentials;
- local worker state.
