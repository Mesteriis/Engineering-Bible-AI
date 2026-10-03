# Targeted mutation testing

The repository includes a bounded runner for explicit Python `unittest`
mutations. It checks whether selected tests detect a human-written change to a
selected production file. It does not generate mutants or infer test quality
from coverage.

## Make a plan

Create a snapshot of only the source, test, and text configuration files needed
by the selected test modules. The snapshot format is the captured manifest from
`scripts/worker_snapshot.py`; it records the pinned Git `HEAD`, file hashes, and
the exact file allowlist without storing file contents. A plan has this shape:

```json
{
  "schema_version": 1,
  "base_commit": "40-or-64-character-pinned-git-object-id",
  "snapshot": {
    "state": "captured",
    "sha256": "digest-from-worker-snapshot",
    "files": [
      {"path": "src/access.py", "sha256": "file-digest", "bytes": 100},
      {"path": "tests/test_access.py", "sha256": "file-digest", "bytes": 200}
    ]
  },
  "test_modules": ["tests.test_access"],
  "max_mutants": 2,
  "per_case_timeout_seconds": 20,
  "total_timeout_seconds": 90,
  "mutants": [
    {
      "id": "allow-cross-tenant",
      "path": "src/access.py",
      "before": "role == \"editor\" and same_tenant",
      "after": "role == \"editor\" or same_tenant"
    }
  ]
}
```

The digest values above illustrate the format; use hashes produced by the
snapshot helper. For example, from the repository root:

```python
import json
from pathlib import Path
import sys

sys.path.insert(0, "scripts")
import worker_snapshot

root = Path.cwd()
captured = worker_snapshot.capture_snapshot(
    root,
    ["src/access.py", "tests/test_access.py"],
)
plan = {
    "schema_version": 1,
    **captured,
    "test_modules": ["tests.test_access"],
    "max_mutants": 2,
    "per_case_timeout_seconds": 20,
    "total_timeout_seconds": 90,
    "mutants": [
        {
            "id": "allow-cross-tenant",
            "path": "src/access.py",
            "before": 'role == "editor" and same_tenant',
            "after": 'role == "editor" or same_tenant',
        }
    ],
}
Path("/private/path/plan.json").write_text(json.dumps(plan, indent=2) + "\n")
```

`test_modules` are dotted Python module names. Each selected module's `.py`
file must be present in the snapshot allowlist. Mutations target an allowlisted
production `.py` file, never a selected test file. A replacement must match
exactly once in the captured bytes and produce valid Python syntax. The plan
accepts at most ten mutants and at most 300 seconds for either timeout.

## Run

Choose a new private output directory. Existing output paths, `..` traversal,
and symlink path components are rejected before creating output. The runner
allows a new output directory inside
`.engineering-bible/implementation/cache-mutation/`; an output elsewhere inside
the source root is rejected. Outside the source tree, its parent must already
exist. On supported POSIX systems, run:

```bash
python3 scripts/mutation-check.py /private/path/plan.json \
  --source-root . \
  --artifacts-root .engineering-bible/implementation/cache-mutation/pilot/run-001
```

Use `--validate-only` to check plan shape without running tests. It prints
`PLAN_VALID (execution not run)`; this is not a mutation result.

The runner checks snapshot freshness before execution and after the run, then
copies only allowlisted files into a fresh workspace for the baseline and each
mutant. It invokes the selected test modules with the current Python executable
and the standard library `unittest` loader. The child gets a minimal environment
with an isolated home and temporary directory. It does not install project
dependencies or invoke a shell. A missing dependency, failed import, discovery
error, timeout, or test error cannot count as a killed mutant.

Tests execute with the local user's filesystem and process permissions. The
temporary workspace and child process are not a security sandbox. Run this only
with source and tests you trust. Child stdout and stderr are capped at 256 KiB
each; structured test reports are bounded as well. The result stores readable
UTF-8 text plus base64 for the exact captured bytes. Truncation is explicit and
that run is an `ERROR`, so it cannot pass. The combined evidence file is capped
at 72 MiB; exceeding that bound is a controlled runner failure. The private
`result.json` contains baseline and per-mutant outcomes, test identities,
bounded logs, and a score whose denominator includes only executed `KILLED`
and `SURVIVED` mutants.

## Outcomes and scope

An assertion failure with no test errors and the same test identities as the
passing baseline is `KILLED`. A passing mutant is `SURVIVED`. Invalid syntax is
`INVALID`; import or execution problems are `ERROR`; expired deadlines are
`TIMEOUT`. Invalid, error, and timeout cases never count as kills. An empty,
skipped-only, or expected-failure-only baseline, and a plan without a pinned
Git base commit, produce `SKIP`. A valid run passes only when every selected
mutant is killed.

The runner cancels children in its own process group when a test finishes or
times out. A test that deliberately starts a new session can escape that group.
If such a child keeps an output pipe open, the runner stops waiting after a
bounded drain interval and marks the execution `ERROR`; it does not claim that
the detached process was cancelled.

The CLI exits 0 for `PASS`, 1 for `FAIL` or invalid plans, and 2 for `SKIP`.
Unsupported process-group cancellation also produces `SKIP`. `SKIP` is never a
100% score.

This initial runner supports Python `unittest` only. JavaScript and TypeScript
projects should use a separately scoped StrykerJS setup after deciding whether
to adopt its project dependency and its incremental command for that project;
this repository does not install or invoke StrykerJS.
