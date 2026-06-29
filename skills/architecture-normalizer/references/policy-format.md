# Policy Format

Architecture analysis must load policy before generating remediation plans. Do not hardcode language limits or allowed dependencies outside policy.

## Policy File

Store repository policies in `.architecture/policy.yaml` or `.architecture/policies/<language>.yaml`.

```yaml
version: 1
kind: architecture-policy
language: python
policy_version: python-v1
status: proposed
limits:
  max_file_lines: 500
  max_public_types_per_file: 1
  max_class_lines: 200
  max_function_lines: 60
public_api:
  explicit_export_file: __init__.py
  wildcard_exports: forbid
  compatibility_exports: required_for_public_moves
naming:
  forbidden_module_names:
    - utils
    - helpers
    - common
    - misc
    - manager
    - processor
    - engine
    - handler
    - base
    - shared
    - core
layout:
  hierarchy: domain-first
  one_directory_responsibility: true
layers:
  order:
    - ui
    - application
    - domain
    - infrastructure
  reverse_dependencies: forbid
dependencies:
  bidirectional_imports: forbid
  cyclic_imports: forbid
  external_imports_through_public_exports: prefer
validation:
  commands: []
```

`status` controls execution:

- `proposed`: usable for analysis, not executable.
- `approved`: executable when referenced actions are also approved.
- `rejected`: not usable.

## Language Public API Defaults

Use these defaults only to create a proposed policy when the repository has no policy.

| Language | Public API surface | Formatter or validator candidates |
| --- | --- | --- |
| Python | `__init__.py` explicit imports | `ruff`, `black`, `pytest`, `pyright`, `mypy` |
| TypeScript | `index.ts`, package `exports` | `tsc`, `eslint`, package test script |
| JavaScript | `index.js`, package `exports` | `eslint`, package test script |
| Rust | `pub use`, `mod.rs` or `lib.rs` | `cargo fmt`, `cargo clippy`, `cargo test` |
| Go | exported symbols and package docs | `gofmt`, `go vet`, `go test ./...` |
| C++ | public headers and exported targets | project build/test commands |
| C | public headers and exported symbols | project build/test commands |

Candidates are not validation claims. Confirm commands from repository files before putting them in `validation-plan.yaml`.

## Default Thresholds

When no repository policy exists, proposed policies may start with these conservative limits:

```yaml
limits:
  max_file_lines: 500
  max_public_types_per_file: 1
  max_class_lines: 200
  max_function_lines: 60
  max_package_files: 40
```

Adjust proposed thresholds only with explicit rationale in `analysis.md`.

## Exception Format

Exceptions must be explicit and reviewable:

```yaml
exceptions:
  - id: EXC-0001
    rule: max_public_types_per_file
    path: src/protocols.ts
    reason: Public protocol cluster intentionally versioned together.
    expires: null
```

Execution must not silently rely on undocumented exceptions.
