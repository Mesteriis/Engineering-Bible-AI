# Worker Evidence

`scripts/worker-evidence.py` is an offline Python helper for the existing
[worker result contract](../skills/subagent-result-merge/SKILL.md). It fingerprints
explicitly allowed files, validates recorded results, and compares matched
historical workloads. It installs no launcher, provider, hook, or runtime.

The launcher must independently record execution facts, original output and exit
codes. Record consistency is not authentication: neither matching metadata nor
existing raw files prove worker execution, provider identity, or a sandbox.
Keep real records and artifacts private and untracked. Runtime activation still
requires the checks in [Worker And Runtime Boundary](worker-runtime-boundary.md).

## Commands

Run from the repository root with Python 3:

```bash
python3 scripts/worker-evidence.py snapshot --root /path/to/source \
  --file src/example.py --file tests/test_example.py
python3 scripts/worker-evidence.py validate /path/to/record.json \
  --source-root /path/to/source --artifacts-root /path/to/private-artifacts
python3 scripts/worker-evidence.py compare /path/to/baseline.json /path/to/candidate.json
```

`snapshot` emits `base_commit` and `snapshot` as JSON on stdout. Only repeated
`--file` selections are read; contents are not exported. Each sorted manifest
entry contains `path`, `sha256`, and `bytes`. The aggregate hash covers the base
commit and manifest, including uncommitted file contents. Capturing twice detects
observed changes; it is not an atomic filesystem snapshot. Outside Git, the base
commit is `unknown`. Paths must stay under the root; symlinks, known private
paths, duplicate aliases, and inputs above the file/count/total limits are rejected.
Limits are 256 files, 8 MiB per file, and 32 MiB total. Hashing requires OS support
for no-follow directory descriptors and fails closed when it is unavailable.
Filename filtering cannot identify every secret; select only authorized files.

`validate` checks one JSON object. `--source-root` recaptures the declared source
files and compares the base commit and manifest; `--artifacts-root` checks that
declared relative artifacts exist as regular files without symlink traversal.
Both roots are required for overall `PASS`. An omitted filesystem check remains
`SKIP`; no referenced command or artifact content is executed.

## Record Details

The common keys remain `task_id`, `goal`, `base_commit`, `snapshot`, `requested`,
`observed`, `status`, `findings`, `checks`, `artifacts`, `open_questions`, and
`usage`. The helper makes these representations executable:

- `snapshot` is the captured object returned by `snapshot`, or exactly
  `{"state":"not_created","sha256":"unknown","files":[]}`. A missing snapshot
  or unknown base revision cannot establish a passing workload.
- `requested` contains the provider/model selected before launch. An observed
  route uses `runtime_metadata` or `provider_response` verification, matches the
  explicitly requested provider/model, and cites a declared artifact in `source`
  (optionally with a `#field` suffix). Without metadata, all four observed fields
  (`provider`, `model`, `source`, `verification`) remain `unknown`.
- Each finding contains nonempty `file_line`, `severity`, `evidence`,
  `limitations`, and `source_reviewer` strings. `file_line` must be `path:line`,
  with a path from the snapshot and a positive line number.
- Checks have unique exact `command` strings. `PASS` requires original integer
  `exit_code: 0`; `FAIL` retains the original integer exit code. Both require a
  declared `raw_artifact`. `SKIP`/`BLOCKED` require `exit_code: null` and a reason.
  A failed check never becomes passing through output processing.
- `artifacts` contains unique canonical relative POSIX paths under the explicit
  artifact root, never host paths or URLs. Declared sources must reference them.
- `usage` is `unknown`, or an object containing `duration_ms`, `tokens`,
  `cost_usd`, `method`, and `source`. Numbers must be finite and nonnegative;
  tokens must be integers. Values may not exceed `2**53 - 1`.
  Use `null` for each unavailable metric, never zero.
  The measurement method is a nonempty string; its source is a declared artifact.
- `status` is `completed`, `failed`, or `blocked`; failed/blocked records need a
  reason or open question. Completion alone does not establish passing checks.

`contract_status` reports record consistency separately from `outcome`.
A consistent record can still have outcome `FAIL`, `SKIP`, or `BLOCKED`.
Unknown observed routing is `BLOCKED`; absent checks or snapshot evidence is
`SKIP`. A known failure takes precedence. Validation additionally reports
`source_status` and `artifact_status`; unchecked filesystem evidence stays `SKIP`.
Exit codes are `0` for `PASS`, `1` for `FAIL`/invalid input, and `2` for
`SKIP`/`BLOCKED`. Preserve these codes when saving output.

## Comparing Recorded Workloads

Each input is a nonempty JSON array with unique task IDs and one requested route
per series. Both arrays must contain the same task IDs, goals, base commits,
complete snapshots, and check commands. The routes may differ between series.
Comparison validates records without checking historical filesystem state.

Results show outcome counts, regressions from baseline `PASS`, and totals/deltas
for each usage metric. Every matched pair must have that metric and the same
measurement method before totals or a delta are reported; missing measurements
are not zero. A zero baseline total or nonfinite computed percentage also
suppresses the delta; `reason` explains unavailable deltas.
A failing candidate remains `FAIL` even when faster. Comparison neither chooses
an automatic winner nor activates a runtime.

## Bounded Run Decisions

`python3 scripts/worker-evidence.py continue /path/to/request.json` evaluates
whether an existing launcher may perform more work. It returns `decision`,
`reasons`, and `next_state`. `continue` exits `0`, `stop` exits `1`, and
`checkpoint` or `blocked` exits `2`. The command never launches a process.

The input uses `schema_version: 1` and three objects:

- `limits`: positive integers `max_steps`, `max_no_progress`,
  `max_consecutive_failures`, `max_tokens`, `max_tool_calls`,
  `max_duration_ms`, and `checkpoint_interval`.
- `state`: `run_id`, `snapshot_sha256`, cumulative `step`, `tokens`,
  `tool_calls`, `duration_ms`, `no_progress_steps`, `consecutive_failures`,
  `last_checkpoint_step`, and `last_progress_sha256`. Initially step,
  streaks, and last checkpoint are zero; resource readings must be known.
- `observation`: the same run/snapshot identity and cumulative resource
  counters, plus `step`, `progress_sha256`, `check_outcome`, and boolean
  `checkpoint_ack`. A work observation advances exactly one step.

Persist each returned `next_state` verbatim in private state before another
dispatch. It binds the original limits through `limits_sha256`, retains pending
checkpoints and `last_observation_sha256`, and prevents terminal runs from
resuming. The last observation digest is required after the initial step;
`last_progress_sha256` retains the last verified progress digest across FAIL/SKIP.
Never reset counters or
increase a budget to bypass a decision. Invalid transitions return `blocked`
with no next state; keep the last valid state for diagnosis.

Only a passed check with a changed evidence digest counts as progress. Hash
verified artifacts/check results, not a worker's claim of progress. Failures and
skips do not erase lack of progress; skips do not erase the failure streak.
Exhausted budgets, repeated failures, and repeated lack of progress stop a run.

For `checkpoint`, first save the actual run artifacts and returned state. Then
replay the accepted observation at the same step with unchanged token/tool
counts and progress digest, setting `checkpoint_ack: true`. Elapsed duration may
increase. Only after `continue` may the launcher dispatch the next step. An
acknowledgment cannot simultaneously record new work.

The evaluator checks caller-supplied evidence at step boundaries. The launcher
must enforce its decision; it does not authenticate the state or stop an ongoing
request. Retain an outer process deadline and process-tree cancellation for
in-flight work. A token budget can stop subsequent work after measured usage
arrives; it is not a provider-side hard token quota. If required measurements
are unavailable, report `blocked` instead of inserting zeros.

`tests/test_worker_control.py` exercises the CLI with actual small subprocesses,
saved/reloaded checkpoint state, and a loop that stops on repeated unchanged
output. It also covers run/source changes, rewritten limits, counter rollback,
missing measurements, exhausted budgets and terminal-state replay.

## Synthetic Example

This temporary fixture demonstrates the file and JSON contracts. Its provider
metadata and measurements are explicitly synthetic; it launches no worker and
does not establish integration or sandbox verification. Run from the repository
root. The example creates a local Git commit only inside its temporary directory.

```bash
example_root="$(mktemp -d)"
mkdir "$example_root/source" "$example_root/artifacts"
printf 'synthetic input\n' > "$example_root/source/input.txt"
git init --quiet "$example_root/source"
git -C "$example_root/source" add input.txt
git -C "$example_root/source" -c user.name='Synthetic Fixture' \
  -c user.email=synthetic@example.invalid -c commit.gpgsign=false \
  -c core.hooksPath=/dev/null commit --quiet -m 'Synthetic fixture'
python3 scripts/worker-evidence.py snapshot --root "$example_root/source" \
  --file input.txt > "$example_root/snapshot.json"
cat > "$example_root/record.json" <<'JSON'
{
  "task_id": "synthetic-example", "goal": "Demonstrate synthetic record validation",
  "requested": {"provider": "synthetic", "model": "fixture"},
  "observed": {"provider": "synthetic", "model": "fixture",
    "verification": "runtime_metadata", "source": "metadata.json"},
  "status": "completed", "findings": [], "open_questions": [],
  "checks": [{"command": "python3 -c 'print(1)'", "exit_code": 0,
    "outcome": "PASS", "raw_artifact": "check.txt"}],
  "artifacts": ["metadata.json", "check.txt"],
  "usage": {"duration_ms": 1000, "tokens": null, "cost_usd": null,
    "method": "synthetic-fixture", "source": "metadata.json"}
}
JSON
python3 - "$example_root" <<'PY'
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
record = json.loads((root / "record.json").read_text())
record.update(json.loads((root / "snapshot.json").read_text()))
check = subprocess.run(["python3", "-c", "print(1)"], capture_output=True)
(root / "artifacts/check.txt").write_bytes(check.stdout + check.stderr)
record["checks"][0].update(exit_code=check.returncode,
    outcome="PASS" if check.returncode == 0 else "FAIL")
(root / "artifacts/metadata.json").write_text(json.dumps({
    "synthetic": True, "provider": "synthetic", "model": "fixture",
    "duration_ms": 1000, "tokens": None, "cost_usd": None}))
(root / "record.json").write_text(json.dumps(record))
(root / "baseline.json").write_text(json.dumps([record]))
(root / "candidate.json").write_text(json.dumps([record]))
PY
python3 scripts/worker-evidence.py validate "$example_root/record.json" \
  --source-root "$example_root/source" --artifacts-root "$example_root/artifacts"
python3 scripts/worker-evidence.py compare \
  "$example_root/baseline.json" "$example_root/candidate.json"
```

Both commands should exit `0`. The identical synthetic duration has a zero
percent delta; unknown tokens/cost have `null` totals and deltas. Omitting either
root from `validate` produces `SKIP` and exit `2`. Temporary files remain under
`$example_root` for inspection; no generated state belongs in the repository.
