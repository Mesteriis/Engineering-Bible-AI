from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SPEC = importlib.util.spec_from_file_location("worker_results", ROOT / "scripts/worker_results.py")
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
compare_runs = module.compare_runs
inspect_record = module.inspect_record


def record(task_id: str = "case-1") -> dict:
    files = [{"path": "example.txt", "sha256": "a" * 64, "bytes": 10}]
    digest = hashlib.sha256(
        json.dumps(
            {"base_commit": "b" * 40, "files": files},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    return {
        "task_id": task_id,
        "goal": "Check the synthetic fixture",
        "base_commit": "b" * 40,
        "snapshot": {"state": "captured", "sha256": digest, "files": files},
        "requested": {"provider": "synthetic", "model": "model-a"},
        "observed": {
            "provider": "synthetic",
            "model": "model-a",
            "source": "route.json#/metadata",
            "verification": "runtime_metadata",
        },
        "status": "completed",
        "findings": [],
        "checks": [
            {
                "command": "fixture-check",
                "exit_code": 0,
                "raw_artifact": "check.log",
                "outcome": "PASS",
            }
        ],
        "artifacts": ["check.log", "route.json", "usage.json"],
        "open_questions": [],
        "usage": {
            "duration_ms": 100,
            "tokens": 50,
            "cost_usd": 0.01,
            "method": "synthetic-v1",
            "source": "usage.json",
        },
    }


class WorkerResultsTests(unittest.TestCase):
    def test_completed_is_not_a_pass_when_check_failed(self) -> None:
        payload = record()
        payload["checks"][0].update(exit_code=7, outcome="FAIL")
        result = inspect_record(payload)
        self.assertEqual(result["contract_status"], "PASS")
        self.assertEqual(result["outcome"], "FAIL")
        self.assertEqual(payload["checks"][0]["exit_code"], 7)

    def test_failure_cannot_be_relabelled_pass(self) -> None:
        for exit_code in (1, -15, True, None):
            with self.subTest(exit_code=exit_code):
                payload = record()
                payload["checks"][0]["exit_code"] = exit_code
                self.assertEqual(inspect_record(payload)["contract_status"], "FAIL")

    def test_skipped_checks_remain_skipped(self) -> None:
        payload = record()
        payload["checks"][0].update(
            exit_code=None, outcome="SKIP", reason="Unavailable fixture", raw_artifact=None
        )
        result = inspect_record(payload)
        self.assertEqual(result["contract_status"], "PASS")
        self.assertEqual(result["outcome"], "SKIP")

    def test_unknown_route_and_missing_checks_do_not_pass(self) -> None:
        payload = record()
        payload["observed"] = dict.fromkeys(
            ("provider", "model", "source", "verification"), "unknown"
        )
        result = inspect_record(payload)
        self.assertEqual(result["contract_status"], "PASS")
        self.assertEqual(result["outcome"], "BLOCKED")
        payload = record()
        payload["checks"] = []
        self.assertEqual(inspect_record(payload)["outcome"], "SKIP")

    def test_blocked_documentation_example_remains_valid(self) -> None:
        import re

        text = (ROOT / "skills/subagent-result-merge/SKILL.md").read_text()
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        assert match is not None
        result = inspect_record(json.loads(match.group(1)))
        self.assertEqual(result["contract_status"], "PASS", result)
        self.assertEqual(result["outcome"], "BLOCKED")

    def test_no_hidden_route_fallback(self) -> None:
        payload = record()
        payload["observed"]["model"] = "other-model"
        self.assertEqual(inspect_record(payload)["contract_status"], "FAIL")

    def test_findings_must_reference_a_file_in_the_snapshot(self) -> None:
        for location, expected in (
            ("example.txt:1", "PASS"),
            ("../../outside.txt:1", "FAIL"),
            ("absent.txt:1", "FAIL"),
            ("example.txt:0", "FAIL"),
            ("example.txt:not-a-line", "FAIL"),
        ):
            with self.subTest(location=location):
                payload = record()
                payload["findings"] = [
                    {
                        "file_line": location,
                        "severity": "P2",
                        "evidence": "Synthetic finding",
                        "limitations": "Synthetic test only",
                        "source_reviewer": "fixture",
                    }
                ]
                self.assertEqual(inspect_record(payload)["contract_status"], expected)

    def test_derived_metric_overflow_stays_serializable(self) -> None:
        baseline, candidate = record(), record()
        baseline["usage"]["cost_usd"] = 1e-308
        candidate["usage"]["cost_usd"] = 9e15
        result = compare_runs([baseline], [candidate])
        self.assertIsNone(result["metrics"]["cost_usd"]["delta_percent"])
        self.assertIn("reason", result["metrics"]["cost_usd"])
        json.dumps(result, allow_nan=False)

    def test_tampered_snapshot_and_unsafe_artifacts_are_rejected(self) -> None:
        payload = record()
        payload["snapshot"]["files"][0]["bytes"] += 1
        self.assertEqual(inspect_record(payload)["contract_status"], "FAIL")
        for path in ("../private.txt", "/tmp/private.txt", "C:\\private.txt", "logs/../secret", ""):
            with self.subTest(path=path):
                payload = record()
                payload["checks"][0]["raw_artifact"] = path
                self.assertEqual(inspect_record(payload)["contract_status"], "FAIL")

    def test_invalid_types_and_nonfinite_usage_never_crash(self) -> None:
        for key in record():
            with self.subTest(key=key):
                payload = record()
                payload[key] = (
                    [] if key not in ("checks", "findings", "artifacts", "open_questions") else None
                )
                self.assertEqual(inspect_record(payload)["contract_status"], "FAIL")
        for value in (True, -1, float("nan"), float("inf"), 10**1000):
            payload = record()
            payload["usage"]["tokens"] = value
            self.assertEqual(inspect_record(payload)["contract_status"], "FAIL")

    def test_compare_preserves_failures_and_reports_paired_metrics(self) -> None:
        baseline = record()
        candidate = deepcopy(baseline)
        candidate["requested"]["model"] = candidate["observed"]["model"] = "model-b"
        candidate["usage"]["duration_ms"] = 80
        candidate["checks"][0].update(exit_code=3, outcome="FAIL")
        result = compare_runs([baseline], [candidate])
        self.assertEqual(result["outcome"], "FAIL")
        self.assertEqual(result["regressions"], ["case-1"])
        self.assertEqual(result["metrics"]["duration_ms"]["delta_percent"], -20.0)
        self.assertEqual(result["candidate"]["FAIL"], 1)

    def test_compare_requires_identical_workloads(self) -> None:
        baseline = record()
        for mutate in (
            lambda r: r.update(task_id="other"),
            lambda r: r.update(goal="Different task"),
            lambda r: r["checks"][0].update(command="different-check"),
        ):
            candidate = record()
            mutate(candidate)
            self.assertEqual(compare_runs([baseline], [candidate])["contract_status"], "FAIL")
        self.assertEqual(compare_runs([baseline, baseline], [baseline])["contract_status"], "FAIL")
        self.assertEqual(compare_runs([], [baseline])["contract_status"], "FAIL")

    def test_compare_unknown_metrics_are_not_zero_or_improvements(self) -> None:
        baseline, candidate = record(), record()
        candidate["usage"]["tokens"] = None
        result = compare_runs([baseline], [candidate])
        self.assertIsNone(result["metrics"]["tokens"]["delta_percent"])
        self.assertEqual(result["metrics"]["tokens"]["paired_cases"], 0)
        candidate["usage"]["method"] = "different-measurement"
        result = compare_runs([baseline], [candidate])
        self.assertIsNone(result["metrics"]["duration_ms"]["delta_percent"])

    def test_compare_rejects_mixed_routes_within_series(self) -> None:
        one, two = record(), record("case-2")
        two["requested"]["model"] = two["observed"]["model"] = "model-b"
        self.assertEqual(compare_runs([one, two], [one, two])["contract_status"], "FAIL")

    def test_unverified_baseline_does_not_become_a_verified_comparison(self) -> None:
        baseline, candidate = record(), record()
        baseline["observed"] = dict.fromkeys(
            ("provider", "model", "source", "verification"), "unknown"
        )
        self.assertEqual(compare_runs([baseline], [candidate])["outcome"], "BLOCKED")

    def test_cli_reports_actual_outcome_and_bad_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "record.json"
            payload = record()
            payload["checks"][0].update(exit_code=9, outcome="FAIL")
            path.write_text(json.dumps(payload))
            command = [
                sys.executable,
                str(ROOT / "scripts/worker-evidence.py"),
                "validate",
                str(path),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["outcome"], "FAIL")
            path.write_text('{"status": "completed", "status": "failed"}')
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate", result.stderr)


class WorkerEvidenceCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.source)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.source),
                "-c",
                "user.name=Synthetic Test",
                "-c",
                "user.email=synthetic@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--allow-empty",
                "--quiet",
                "-m",
                "synthetic input",
            ],
            check=True,
        )
        (self.source / "example.txt").write_text("synthetic source")
        captured = self.run_cli("snapshot", "--root", str(self.source), "--file", "example.txt")
        self.assertEqual(captured.returncode, 0, captured.stderr)
        self.payload = record()
        self.payload.update(json.loads(captured.stdout))
        for name in self.payload["artifacts"]:
            (self.artifacts / name).write_text("synthetic evidence only")
        self.record_path = self.root / "record.json"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/worker-evidence.py"), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def validate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        self.record_path.write_text(json.dumps(self.payload))
        return self.run_cli("validate", str(self.record_path), *extra)

    def roots(self) -> tuple[str, ...]:
        return ("--source-root", str(self.source), "--artifacts-root", str(self.artifacts))

    def test_freshness_and_artifact_checks_are_required_for_pass(self) -> None:
        unverified = self.validate()
        self.assertEqual(unverified.returncode, 2, unverified.stderr)
        verified = self.validate(*self.roots())
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["proof_scope"], "record_consistency_only")
        (self.source / "example.txt").write_text("changed uncommitted input")
        changed = self.validate(*self.roots())
        self.assertEqual(changed.returncode, 1)
        self.assertEqual(json.loads(changed.stdout)["source_status"], "FAIL")

    def test_real_failing_subprocess_cannot_become_pass(self) -> None:
        raw = subprocess.run(
            [sys.executable, "-c", "import sys; print('synthetic failure'); sys.exit(7)"],
            capture_output=True,
            text=True,
            check=False,
        )
        log = self.artifacts / "check.log"
        log.write_text(raw.stdout + raw.stderr)
        self.payload["checks"][0].update(exit_code=raw.returncode, outcome="FAIL")
        failed = self.validate(*self.roots())
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout)["contract_status"], "PASS")
        self.assertEqual(json.loads(failed.stdout)["checks"]["FAIL"], 1)
        self.assertEqual(log.read_text(), raw.stdout + raw.stderr)

    def test_missing_artifact_and_symlink_are_failures(self) -> None:
        path = self.artifacts / "check.log"
        path.unlink()
        self.assertEqual(self.validate(*self.roots()).returncode, 1)
        path.symlink_to(self.artifacts / "route.json")
        self.assertEqual(self.validate(*self.roots()).returncode, 1)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO unavailable")
    def test_fifo_json_input_is_rejected_without_hanging(self) -> None:
        path = self.root / "input.pipe"
        os.mkfifo(path)
        self.assertEqual(self.run_cli("validate", str(path)).returncode, 1)

    def test_compare_cli_returns_failure_for_faster_failed_candidate(self) -> None:
        baseline = self.root / "baseline.json"
        candidate = self.root / "candidate.json"
        baseline.write_text(json.dumps([self.payload]))
        self.payload["checks"][0].update(exit_code=5, outcome="FAIL")
        self.payload["usage"]["duration_ms"] = 1
        candidate.write_text(json.dumps([self.payload]))
        result = self.run_cli("compare", str(baseline), str(candidate))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["regressions"], ["case-1"])


if __name__ == "__main__":
    unittest.main()
