from __future__ import annotations

import base64
import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from typing import cast


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_SPEC = importlib.util.spec_from_file_location(
    "worker_snapshot", ROOT / "scripts" / "worker_snapshot.py"
)
assert SNAPSHOT_SPEC is not None and SNAPSHOT_SPEC.loader is not None
worker_snapshot = importlib.util.module_from_spec(SNAPSHOT_SPEC)
sys.modules[SNAPSHOT_SPEC.name] = worker_snapshot
SNAPSHOT_SPEC.loader.exec_module(worker_snapshot)
MUTATION_SPEC = importlib.util.spec_from_file_location(
    "mutation_check", ROOT / "scripts" / "mutation_check.py"
)
assert MUTATION_SPEC is not None and MUTATION_SPEC.loader is not None
mutation_check = importlib.util.module_from_spec(MUTATION_SPEC)
sys.modules[MUTATION_SPEC.name] = mutation_check
MUTATION_SPEC.loader.exec_module(mutation_check)


class MutationCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "source"
        self.root.mkdir()
        self._write_fixture()
        self._git_commit()

    def _write_fixture(self) -> None:
        (self.root / "src").mkdir(exist_ok=True)
        (self.root / "tests").mkdir(exist_ok=True)
        (self.root / "src" / "__init__.py").write_text("", encoding="utf-8")
        (self.root / "src" / "policy.py").write_text(
            "def can_access(role: str, same_tenant: bool) -> bool:\n"
            '    return role == "editor" and same_tenant\n',
            encoding="utf-8",
        )
        (self.root / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (self.root / "tests" / "test_policy.py").write_text(
            "import unittest\n"
            "from src.policy import can_access\n\n"
            "class PolicyTests(unittest.TestCase):\n"
            "    def test_editor_same_tenant(self):\n"
            "        self.assertTrue(can_access('editor', True))\n\n"
            "    def test_viewer_denied(self):\n"
            "        self.assertFalse(can_access('viewer', True))\n\n"
            "    def test_cross_tenant_denied(self):\n"
            "        self.assertFalse(can_access('editor', False))\n",
            encoding="utf-8",
        )

    def _git_commit(self) -> None:
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "src", "tests"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Mutation Test",
                "-c",
                "user.email=mutation@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
            check=True,
        )

    def _plan(self, mutants: list[dict[str, str]]) -> dict[str, object]:
        files = ["src/__init__.py", "src/policy.py", "tests/__init__.py", "tests/test_policy.py"]
        captured = worker_snapshot.capture_snapshot(self.root, files)
        return {
            "schema_version": 1,
            "base_commit": captured["base_commit"],
            "snapshot": captured["snapshot"],
            "test_modules": ["tests.test_policy"],
            "max_mutants": max(1, len(mutants)),
            "per_case_timeout_seconds": 5,
            "total_timeout_seconds": 30,
            "mutants": mutants,
        }

    def _mutant(self, after: str) -> dict[str, str]:
        return {
            "id": "policy-change",
            "path": "src/policy.py",
            "before": 'role == "editor" and same_tenant',
            "after": after,
        }

    def _artifacts(self, name: str = "artifacts") -> Path:
        return self.root.parent.resolve() / name

    def _run(self, plan: dict[str, object], name: str = "artifacts") -> dict[str, object]:
        return mutation_check.run_plan(plan, self.root, self._artifacts(name))

    def test_real_assertions_kill_a_behavior_change(self) -> None:
        result = self._run(self._plan([self._mutant('role == "editor" or same_tenant')]))
        self.assertEqual(result["decision"], "PASS")
        mutant = cast(list[dict[str, object]], result["mutants"])[0]
        self.assertEqual(mutant["status"], "KILLED")
        self.assertGreater(cast(int, cast(dict[str, object], result["score"])["executed"]), 0)
        self.assertTrue((self._artifacts() / "result.json").is_file())
        self.assertFalse((self._artifacts() / ".workspace-unused").exists())

    def test_weak_tests_leave_a_semantic_mutant_alive(self) -> None:
        result = self._run(self._plan([self._mutant('role == "editor" and (same_tenant)')]))
        self.assertEqual(result["decision"], "FAIL")
        self.assertEqual(cast(list[dict[str, object]], result["mutants"])[0]["status"], "SURVIVED")

    def test_invalid_syntax_is_not_a_kill_and_has_no_score_denominator(self) -> None:
        result = self._run(self._plan([self._mutant("this is not valid python !!!")]))
        self.assertEqual(result["decision"], "SKIP")
        self.assertEqual(cast(list[dict[str, object]], result["mutants"])[0]["status"], "INVALID")
        self.assertEqual(cast(dict[str, object], result["score"])["executed"], 0)

    def test_mutant_import_error_is_an_execution_error_not_a_kill(self) -> None:
        result = self._run(
            self._plan([self._mutant("__import__('module_missing_for_mutation_tests')")])
        )
        self.assertEqual(result["decision"], "FAIL")
        mutant = cast(list[dict[str, object]], result["mutants"])[0]
        self.assertEqual(mutant["status"], "ERROR")
        report = cast(dict[str, object], cast(dict[str, object], mutant["execution"])["report"])
        self.assertTrue(report["errors"])

    def test_baseline_import_error_aborts_before_mutants(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import module_missing_for_mutation_tests\n", encoding="utf-8"
        )
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        result = self._run(plan)
        self.assertEqual(result["decision"], "FAIL")
        self.assertEqual(result["mutants"], [])
        baseline = cast(dict[str, object], result["baseline"])
        report = cast(dict[str, object], baseline["report"])
        self.assertTrue(report["errors"])

    def test_parent_loaded_module_is_missing_when_not_allowlisted(self) -> None:
        # worker_snapshot is imported in this parent test process, but the child
        # must resolve project imports only from the copied selected snapshot.
        (self.root / "tests" / "test_policy.py").write_text(
            "import worker_snapshot\nimport unittest\n"
            "class ImportParentModule(unittest.TestCase):\n"
            "    def test_module(self):\n"
            "        self.assertTrue(worker_snapshot)\n",
            encoding="utf-8",
        )
        result = self._run(self._plan([self._mutant('role == "editor" or same_tenant')]))
        self.assertEqual(result["decision"], "FAIL")
        self.assertEqual(result["mutants"], [])
        baseline = cast(dict[str, object], result["baseline"])
        report = cast(dict[str, object], baseline["report"])
        self.assertTrue(report["errors"])

    def test_zero_tests_is_skipped_without_a_score(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import unittest\nclass Empty(unittest.TestCase):\n    pass\n", encoding="utf-8"
        )
        result = self._run(self._plan([self._mutant('role == "editor" or same_tenant')]))
        self.assertEqual(result["decision"], "SKIP")
        baseline = cast(dict[str, object], result["baseline"])
        report = cast(dict[str, object], baseline["report"])
        self.assertEqual(report["tests_run"], 0)

    def test_expected_failure_only_baseline_is_skipped(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import unittest\n"
            "class Expected(unittest.TestCase):\n"
            "    @unittest.expectedFailure\n"
            "    def test_expected(self):\n"
            "        self.fail('expected')\n",
            encoding="utf-8",
        )
        result = self._run(self._plan([self._mutant('role == "editor" or same_tenant')]))
        self.assertEqual(result["decision"], "SKIP")

    def test_mixed_expected_failure_does_not_mask_a_real_kill(self) -> None:
        test_file = self.root / "tests" / "test_policy.py"
        test_file.write_text(
            test_file.read_text(encoding="utf-8")
            + "\nclass LegacyExpectation(unittest.TestCase):\n"
            + "    @unittest.expectedFailure\n"
            + "    def test_legacy_behavior(self):\n"
            + "        self.fail('expected legacy failure')\n",
            encoding="utf-8",
        )
        result = self._run(self._plan([self._mutant('role == "editor" or same_tenant')]))
        self.assertEqual(result["decision"], "PASS")
        baseline = cast(dict[str, object], result["baseline"])
        report = cast(dict[str, object], baseline["report"])
        self.assertEqual(
            report["expected_failures"],
            ["tests.test_policy.LegacyExpectation.test_legacy_behavior"],
        )
        mutant = cast(list[dict[str, object]], result["mutants"])[0]
        self.assertEqual(mutant["status"], "KILLED")

    def test_unexpected_success_is_not_a_baseline_pass(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import unittest\n"
            "class Unexpected(unittest.TestCase):\n"
            "    @unittest.expectedFailure\n"
            "    def test_unexpected(self):\n"
            "        pass\n",
            encoding="utf-8",
        )
        result = self._run(self._plan([self._mutant('role == "editor" or same_tenant')]))
        self.assertEqual(result["decision"], "FAIL")
        baseline = cast(dict[str, object], result["baseline"])
        report = cast(dict[str, object], baseline["report"])
        self.assertTrue(report["unexpected_successes"])

    def test_truncated_output_is_visible_and_cannot_pass(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import unittest\n"
            "class Noisy(unittest.TestCase):\n"
            "    def test_noisy(self):\n"
            "        print('x' * 300000)\n",
            encoding="utf-8",
        )
        result = self._run(self._plan([self._mutant('role == "editor" or same_tenant')]))
        self.assertEqual(result["decision"], "FAIL")
        baseline = cast(dict[str, object], result["baseline"])
        self.assertTrue(baseline["stdout_truncated"])
        self.assertEqual(len(cast(str, baseline["stdout"]).encode("utf-8")), 256 * 1024)

    def test_raw_output_bytes_survive_readable_decoding(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import sys\n"
            "import unittest\n"
            "class BinaryOutput(unittest.TestCase):\n"
            "    def test_binary(self):\n"
            "        sys.stdout.buffer.write(b'\\xff')\n"
            "        sys.stdout.flush()\n",
            encoding="utf-8",
        )
        result = self._run(self._plan([self._mutant('role == "editor" and (same_tenant)')]))
        baseline = cast(dict[str, object], result["baseline"])
        self.assertEqual(base64.b64decode(cast(str, baseline["stdout_base64"])), b"\xff")
        self.assertIn("\ufffd", cast(str, baseline["stdout"]))

    def test_aggregate_evidence_limit_cannot_leave_a_partial_pass(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        output = self._artifacts()
        with patch.object(mutation_check, "MAX_EVIDENCE_BYTES", 1):
            with self.assertRaisesRegex(
                mutation_check.MutationError, "result evidence exceeded size limit"
            ):
                mutation_check.run_plan(plan, self.root, output)
        self.assertFalse((output / "result.json").exists())

    def test_detached_child_cannot_hold_the_runner_open(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import subprocess\n"
            "import sys\n"
            "import unittest\n"
            "class Detached(unittest.TestCase):\n"
            "    def test_detached(self):\n"
            "        subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(1.5)'], start_new_session=True)\n",
            encoding="utf-8",
        )
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        plan["per_case_timeout_seconds"] = 2
        plan["total_timeout_seconds"] = 5
        started = time.monotonic()
        result = self._run(plan)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 2.5)
        self.assertEqual(result["decision"], "FAIL")
        baseline = cast(dict[str, object], result["baseline"])
        self.assertTrue(baseline["cleanup_error"])

    def test_continuous_output_cannot_starve_the_deadline(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import sys\n"
            "import unittest\n"
            "class NoisyLoop(unittest.TestCase):\n"
            "    def test_noisy_loop(self):\n"
            "        while True:\n"
            "            sys.stdout.buffer.write(b'x' * 65536)\n"
            "            sys.stdout.flush()\n",
            encoding="utf-8",
        )
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        plan["per_case_timeout_seconds"] = 1
        plan["total_timeout_seconds"] = 4
        started = time.monotonic()
        result = self._run(plan)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual(result["decision"], "FAIL")
        baseline = cast(dict[str, object], result["baseline"])
        self.assertTrue(baseline["timed_out"])
        self.assertTrue(baseline["stdout_truncated"])

    def test_expired_deadline_stops_descendant_processes(self) -> None:
        (self.root / "tests" / "test_policy.py").write_text(
            "import os\n"
            "import pathlib\n"
            "import subprocess\n"
            "import sys\n"
            "import time\n"
            "import unittest\n\n"
            "class Hanging(unittest.TestCase):\n"
            "    def test_hang(self):\n"
            "        code = \"import os, pathlib, signal, sys, time; marker=pathlib.Path(os.environ['TMPDIR'])/'child-stopped'; signal.signal(signal.SIGTERM, lambda *_: (marker.write_text('yes'), sys.exit(0))); print('ready', flush=True); time.sleep(60)\"\n"
            "        child = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE, text=True)\n"
            "        assert child.stdout is not None\n"
            "        child.stdout.readline()\n"
            "        print(child.pid, flush=True)\n"
            "        time.sleep(60)\n",
            encoding="utf-8",
        )
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        plan["per_case_timeout_seconds"] = 1
        plan["total_timeout_seconds"] = 5
        output = self._artifacts()
        result = mutation_check.run_plan(plan, self.root, output)
        self.assertEqual(result["decision"], "FAIL")
        baseline = cast(dict[str, object], result["baseline"])
        self.assertTrue(baseline["timed_out"])
        self.assertTrue(baseline["child_cleanup_marker"])

    def test_stale_source_snapshot_fails_before_execution(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        (self.root / "src" / "policy.py").write_text("# changed after capture\n", encoding="utf-8")
        with self.assertRaisesRegex(mutation_check.MutationError, "stale"):
            mutation_check.run_plan(plan, self.root, self._artifacts())
        self.assertFalse(self._artifacts().exists())

    def test_symlinked_snapshot_file_fails_closed(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        source = self.root / "src" / "policy.py"
        saved = source.read_bytes()
        source.unlink()
        outside = self.root.parent / "external.py"
        outside.write_bytes(saved)
        source.symlink_to(outside)
        with self.assertRaises(mutation_check.MutationError):
            mutation_check.run_plan(plan, self.root, self._artifacts())

    def test_artifact_scope_rejects_public_source_subtree(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        output = self.root.resolve() / "public-output"
        with self.assertRaisesRegex(mutation_check.MutationError, "private cache-mutation"):
            mutation_check.run_plan(plan, self.root, output)
        self.assertFalse(output.exists())

    def test_artifact_scope_rejects_parent_traversal_before_creating_output(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        output = (
            self.root
            / ".engineering-bible"
            / "implementation"
            / "cache-mutation"
            / "../../../public-output"
        )
        with self.assertRaisesRegex(mutation_check.MutationError, "parent traversal"):
            mutation_check.run_plan(plan, self.root, output)
        self.assertFalse((self.root / "public-output").exists())

    def test_artifact_scope_rejects_symlink_parent_before_writing(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        outside = self.root.parent / "linked-artifacts"
        outside.mkdir()
        (self.root / ".engineering-bible").symlink_to(outside, target_is_directory=True)
        output = (
            self.root.resolve() / ".engineering-bible" / "implementation" / "cache-mutation" / "run"
        )
        with self.assertRaisesRegex(mutation_check.MutationError, "symlinks"):
            mutation_check.run_plan(plan, self.root, output)
        self.assertFalse((outside / "implementation").exists())

    def test_mutant_cannot_target_an_explicit_test_module_outside_tests_directory(self) -> None:
        (self.root / "checks.py").write_text(
            "import unittest\n"
            "class Checks(unittest.TestCase):\n"
            "    def test_one(self):\n"
            "        self.assertTrue(True)\n",
            encoding="utf-8",
        )
        captured = worker_snapshot.capture_snapshot(
            self.root,
            [
                "checks.py",
                "src/__init__.py",
                "src/policy.py",
                "tests/__init__.py",
                "tests/test_policy.py",
            ],
        )
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        plan["base_commit"] = captured["base_commit"]
        plan["snapshot"] = captured["snapshot"]
        plan["test_modules"] = ["checks"]
        plan["mutants"] = [
            {
                "id": "test-change",
                "path": "checks.py",
                "before": "assertTrue",
                "after": "assertFalse",
            }
        ]
        with self.assertRaisesRegex(mutation_check.MutationError, "production"):
            mutation_check.validate_plan(plan)

    def test_artifact_scope_accepts_private_ignored_cache_subtree(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        output = (
            self.root.resolve()
            / ".engineering-bible"
            / "implementation"
            / "cache-mutation"
            / "run-a"
        )
        result = mutation_check.run_plan(plan, self.root, output)
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(output.stat().st_mode & 0o777, 0o700)
        self.assertEqual((output / "result.json").stat().st_mode & 0o777, 0o600)

    def test_cli_exit_codes_pass_fail_and_skip(self) -> None:
        good_plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        bad_plan = self._plan([self._mutant('role == "editor" and (same_tenant)')])
        codes = [
            self._cli(good_plan, "cli-pass"),
            self._cli(bad_plan, "cli-fail"),
        ]
        self.assertEqual(codes, [0, 1])
        unknown_root = Path(self.temporary.name) / "unversioned"
        unknown_root.mkdir()
        for path in (
            "src/__init__.py",
            "src/policy.py",
            "tests/__init__.py",
            "tests/test_policy.py",
        ):
            source_path = self.root / path
            destination = unknown_root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source_path.read_bytes())
        unknown_plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        unknown_plan["base_commit"] = "unknown"
        snap = cast(dict[str, object], unknown_plan["snapshot"])
        unknown_plan["snapshot"] = {
            **snap,
            "sha256": worker_snapshot.snapshot_digest(
                "unknown", cast(list[dict[str, object]], snap["files"])
            ),
        }
        codes.append(self._cli(unknown_plan, "cli-skip", unknown_root))
        self.assertEqual(codes, [0, 1, 2])

    def test_malformed_unicode_is_a_controlled_validation_failure(self) -> None:
        plan = self._plan([self._mutant('role == "editor" or same_tenant')])
        mutants = cast(list[dict[str, object]], plan["mutants"])
        mutants[0]["before"] = "\ud800"
        with self.assertRaisesRegex(mutation_check.MutationError, "valid UTF-8"):
            mutation_check.validate_plan(plan)
        cli = self._cli_result(plan, "cli-malformed-unicode")
        self.assertEqual(cli.returncode, 1)
        self.assertIn(b"ERROR:", cli.stderr)
        self.assertNotIn(b"Traceback", cli.stderr)

    def _cli(self, plan: dict[str, object], name: str, source: Path | None = None) -> int:
        return self._cli_result(plan, name, source).returncode

    def _cli_result(
        self, plan: dict[str, object], name: str, source: Path | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        plan_path = self.root.parent / f"{name}.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        artifact_path = self.root.parent.resolve() / name
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "mutation-check.py"),
                str(plan_path),
                "--source-root",
                str(source or self.root),
                "--artifacts-root",
                str(artifact_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
        return result


if __name__ == "__main__":
    unittest.main()
