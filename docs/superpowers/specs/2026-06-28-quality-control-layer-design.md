# Engineering Bible Quality Control Layer Design

## Context

Engineering Bible AI already contains portable root instructions, routing
skills, engineering standards, installer support, the `be` CLI foundation, and
repository validation. The next quality step is not another broad prose layer.
The missing capability is a lightweight control layer that makes agent work
more evidence-bound, lifecycle-aware, reviewable, and resistant to library
drift.

The user selected two quality priorities:

- improve the quality of agent answers;
- improve control and verification.

The layer must address four failure modes:

- hallucinated or unverified claims;
- task execution without scope, inspection, planning, or validation gates;
- weak review of finished changes;
- drift between skills, docs, manifests, installer behavior, and validation.

## Goals

- Add a reusable quality-gates skill that acts as a guardrail for non-trivial
  engineering work.
- Add neutral engineering reference documents for evidence, lifecycle, review,
  regression, and library drift.
- Add executable audit coverage that checks the parts of the quality contract
  that can be verified from repository files.
- Integrate audit into both `be` and `make validate`.
- Preserve the existing worker/runtime boundary and avoid local runtime config
  changes.
- Keep the first implementation slice small enough to review and validate.

## Non-Goals

- No full LLM eval runner in the first slice.
- No automatic execution of agents against golden cases.
- No `be audit --json` in the first slice.
- No release automation or GitHub publishing workflow changes.
- No policy engine with severity levels.
- No replacement of existing routing, security, review, UI, or ecosystem
  skills.

## Proposed Approach

Use a thin Quality Control Layer rather than a strict compliance framework.

The layer defines quality contracts in docs and enforces structural invariants
with scripts. It keeps the existing development flow fast for small tasks while
making important claims, task progress, validation, and drift checks explicit.

This approach intentionally combines:

- a light guardrail skill for agent behavior;
- neutral engineering docs for reference quality;
- a repository audit command for enforceable drift checks;
- focused regression/golden cases for failure modes.

## Components

### `quality-gates` skill

Create `skills/quality-gates/SKILL.md`.

Responsibilities:

- define when quality gates apply;
- route agents to the relevant quality references;
- require evidence-backed claims for important assertions;
- require explicit task lifecycle gates for non-trivial work;
- require review and regression thinking before completion;
- keep the contract lightweight for small changes.

The skill must not duplicate detailed language-specific, security, UI, or review
skills. It should compose with them.

### Engineering reference docs

Add these documents under `engineering/`:

- `35_evidence_contract.md`
- `36_task_lifecycle_gates.md`
- `37_review_regression_gates.md`
- `38_library_drift_audit.md`

Expected responsibilities:

- `35_evidence_contract.md`: what counts as evidence, how to report
  unconfirmed facts, and when file/command/source references are required.
- `36_task_lifecycle_gates.md`: scope, inspection, planning, implementation,
  validation, reporting, and risk gates.
- `37_review_regression_gates.md`: diff-risk review, regression classes, test
  expectations, documentation impact, runtime impact, and unresolved risk
  reporting.
- `38_library_drift_audit.md`: invariants for skills, docs, manifests,
  installer contents, validation scripts, runtime boundary, and audit output.

Update `engineering/README.md` and `skills/engineering-standards/SKILL.md` so
the new documents are discoverable without loading the entire standards
library.

### Audit engine

Add `scripts/audit-quality-gates.py`.

The audit engine reads repository files and reports all detected issues in one
run. It exits `0` when all checks pass and `1` when any issue is found.

Initial checks:

- `engineering/README.md` lists every `engineering/*.md` document.
- `skills/engineering-standards/SKILL.md` references quality-gate engineering
  docs where relevant.
- `skills/quality-gates/SKILL.md` exists and has valid frontmatter.
- `scripts/validate-skill-tree.sh` requires the new skill and new engineering
  docs.
- `MANIFEST.md` includes new command entry points when command entry points are
  added.
- The portable tree does not contain forbidden runtime/secrets files.
- Golden quality-gate cases exist in the expected location.

The checker should produce actionable messages, for example:

```text
quality audit failed
missing engineering index entry: engineering/35_evidence_contract.md
missing validation required file: skills/quality-gates/SKILL.md
```

When passing, it should produce concise human-readable output:

```text
quality audit passed
- engineering index: ok
- skill references: ok
- validation tree: ok
- runtime boundary: ok
```

### CLI integration

Extend `scripts/be.py` with:

```bash
be audit
```

Behavior:

- delegates to `scripts/audit-quality-gates.py`;
- exits with the audit engine exit code;
- prints the audit engine output directly;
- does not require local runtime configuration.

`be audit --json` is explicitly deferred.

### Make integration

Add:

```make
make audit
```

Then include `audit` in `make validate`.

The CI workflow already runs `make validate`, so no workflow structural change
is expected.

### Golden cases

Add a static corpus under:

```text
tests/quality-gates/
```

Initial cases:

- hallucinated test result;
- skipped inspection;
- skipped validation;
- weak review;
- stale routing reference;
- missing manifest entry.

The first implementation slice should treat these as corpus fixtures for the
audit/checking layer, not as a full LLM evaluation runner.

## Data Flow

### Agent behavior flow

1. `workflow-router` remains the entry point for non-trivial engineering work.
2. For non-trivial engineering tasks, routing can include `quality-gates` as a
   general control layer.
3. `quality-gates` points to the smallest relevant quality docs.
4. Domain-specific skills still handle actual work: `python`, `security`,
   `review-router`, `documentation`, UI skills, and other existing skills.

### Audit flow

1. User or CI runs `make validate`, `make audit`, or `be audit`.
2. The command invokes `scripts/audit-quality-gates.py`.
3. The audit engine reads repository files.
4. It accumulates all drift issues.
5. It prints human-readable output and exits `0` or `1`.

## Error Handling

- Audit failures must be actionable and specific.
- Missing unreadable files are failures.
- Broken skill frontmatter is a failure.
- Missing docs, manifest entries, or validation-tree references are failures.
- Runtime/secrets-like files in the portable tree are failures.
- The checker should report all discovered issues in one run instead of failing
  on the first issue.
- No silent skips are allowed. If a check is intentionally out of scope, it must
  not be implemented as a skipped check.

## Testing Strategy

Add tests for:

- audit happy path on the current repository;
- missing engineering index entry;
- missing `quality-gates` skill reference;
- missing validation-tree required file;
- manifest drift;
- forbidden runtime/secrets-like file detection;
- `be audit` exits `0` on the current repository.

`make validate` must remain the final integration check.

## Documentation Updates

Update:

- `README.md` and `README.ru.md` with `be audit` and `make audit`;
- `MANIFEST.md` with new script and skill;
- `CONTRIBUTING.md` and `docs/oss-release-checklist.md` if expanded validation
  commands change;
- `engineering/README.md` and `skills/engineering-standards/SKILL.md` for new
  engineering docs;
- `scripts/validate-skill-tree.sh` so the new quality layer is part of the
  portable tree contract.

## First Implementation Slice

The first slice includes:

- `skills/quality-gates/SKILL.md`;
- `engineering/35_evidence_contract.md`;
- `engineering/36_task_lifecycle_gates.md`;
- `engineering/37_review_regression_gates.md`;
- `engineering/38_library_drift_audit.md`;
- `scripts/audit-quality-gates.py`;
- `be audit`;
- `make audit`;
- static golden cases in `tests/quality-gates/`;
- tests for audit behavior and `be audit`;
- docs, manifest, and validation updates.

## Risks

- Too much process could slow down small tasks. Mitigation: make the lifecycle
  gates proportional to task complexity.
- The audit script could become a second manifest system. Mitigation: keep
  checks focused on invariants that catch real drift.
- The skill could duplicate existing review/security/router skills. Mitigation:
  make `quality-gates` a coordination layer that points to existing skills.
- Golden cases could be mistaken for an LLM eval runner. Mitigation: document
  them as static corpus fixtures for now.

## Definition of Done

- The quality-gates skill exists and is routed/discoverable.
- The four engineering docs exist and are indexed.
- `be audit` and `make audit` run successfully on the current repo.
- `make validate` includes audit and passes.
- Audit tests cover happy path and drift/failure cases.
- Docs and manifest reflect the new commands, skill, and script.
- No local runtime config, secrets, or worker state are added.
