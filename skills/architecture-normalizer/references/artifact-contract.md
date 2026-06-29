# Artifact Contract

Use these schemas for `.architecture/` artifacts. Keep files deterministic: stable keys, sorted paths, stable IDs, and no current-time values unless the timestamp is derived from repository state.

## Common Rules

- Use YAML for plans and reports unless a specific format is required.
- Store all artifacts under `.architecture/`.
- Use `status: proposed`, `approved`, `rejected`, `done`, or `blocked`.
- Use `approved` only after explicit human approval or user-edited artifacts.
- Every executable action must include `id`, `status`, `rationale`, `evidence`, and rollback notes.
- Every path must be repository-relative with POSIX separators.
- No wildcard exports.

## manifest.yaml

```yaml
version: 1
kind: architecture-manifest
repository_hash:
  algorithm: architecture-normalizer-repo-fingerprint-v1
  value: sha256:<hex>
  file_count: 0
generated_at: null
languages:
  - python
policies:
  - path: .architecture/policies/python.yaml
    status: proposed
    policy_version: python-v1
artifacts:
  - path: .architecture/move-plan.yaml
    kind: move-plan
    sha256: sha256:<hex>
```

Execution must refuse to run if the current repository hash differs from `repository_hash.value`.

## analysis.md

Human-readable summary of:

- detected languages and tooling
- current architecture shape
- major cohesion/coupling findings
- public API preservation strategy
- recommended execution slices
- unresolved questions and blockers

Do not hide decisions in prose only. Every executable decision must also appear in a plan artifact.

## entropy.json

```json
{
  "version": 1,
  "scores": {
    "architecture": {"score": 0, "why": []},
    "entropy": {"score": 0, "why": []},
    "coupling": {"score": 0, "why": []},
    "cohesion": {"score": 0, "why": []},
    "layer_integrity": {"score": 0, "why": []},
    "public_api_stability": {"score": 0, "why": []},
    "naming_quality": {"score": 0, "why": []},
    "dependency_health": {"score": 0, "why": []},
    "package_complexity": {"score": 0, "why": []}
  }
}
```

Scores use a 0 to 100 scale. Every score must explain why.

## Graph Artifacts

`dependency-graph.graphml` represents module/file/package dependencies. `package-layout.graphml` represents the proposed package hierarchy. Include deterministic node IDs derived from normalized paths or package names.

If GraphML tooling is unavailable, write minimal valid GraphML with known nodes and edges, then record the limitation in `risk-report.yaml`.

## move-plan.yaml

```yaml
version: 1
kind: move-plan
actions:
  - id: MOVE-0001
    status: proposed
    source: old/path.py
    destination: new/path.py
    rationale: One responsibility per file.
    public_api: preserve
    compatibility_actions:
      - COMPAT-0001
    evidence:
      - type: symbol
        path: old/path.py
        detail: Exported public type Foo.
    rollback: Move file back and restore imports from imports-plan.
```

## split-plan.yaml

```yaml
version: 1
kind: split-plan
actions:
  - id: SPLIT-0001
    status: proposed
    source: package/large_file.py
    outputs:
      - path: package/domain/model.py
        symbols:
          - Model
    rationale: Separate domain model from transport concerns.
    evidence: []
    rollback: Restore original file from git and revert generated outputs.
```

## rename-plan.yaml

```yaml
version: 1
kind: rename-plan
actions:
  - id: RENAME-0001
    status: proposed
    old_name: helpers
    new_name: parsing
    scope: package/helpers.py
    rationale: Replace forbidden generic module name with semantic responsibility.
    evidence: []
    rollback: Restore previous name and imports.
```

## imports-plan.yaml

```yaml
version: 1
kind: imports-plan
actions:
  - id: IMPORT-0001
    status: proposed
    path: consumer/file.py
    old_import: from old.path import Foo
    new_import: from new.path import Foo
    depends_on:
      - MOVE-0001
    evidence: []
    rollback: Restore old import.
```

## exports-plan.yaml

```yaml
version: 1
kind: exports-plan
actions:
  - id: EXPORT-0001
    status: proposed
    path: package/__init__.py
    export: Foo
    source: package/domain/model.py
    rationale: Maintain explicit package public API.
    evidence: []
    rollback: Remove export.
```

## compatibility-plan.yaml

```yaml
version: 1
kind: compatibility-plan
actions:
  - id: COMPAT-0001
    status: proposed
    old_public_path: old.path.Foo
    new_public_path: new.path.Foo
    strategy: explicit re-export
    removal_policy: keep until separately approved
    evidence: []
    rollback: Remove compatibility layer after reverting dependent moves.
```

## risk-report.yaml

```yaml
version: 1
kind: risk-report
risks:
  - id: RISK-0001
    severity: medium
    area: public-api
    description: Public import path has external consumers not visible in repository.
    mitigation: Generate compatibility re-export.
    related_actions:
      - COMPAT-0001
```

## validation-plan.yaml

```yaml
version: 1
kind: validation-plan
commands:
  - id: VAL-0001
    status: proposed
    command: pytest
    reason: Python test suite.
    required: true
public_api_checks:
  - import old.path.Foo
architecture_checks:
  - no cyclic imports in proposed dependency graph
```

## validation-results.yaml

Create after execution:

```yaml
version: 1
kind: validation-results
commands:
  - id: VAL-0001
    command: pytest
    exit_code: 0
    result: passed
```
