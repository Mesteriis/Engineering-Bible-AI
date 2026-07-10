from __future__ import annotations

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
SPEC = importlib.util.spec_from_file_location("be_validate", ROOT / "scripts" / "validate.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load scripts/validate.py")
validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate)

ROUTER_SPEC = importlib.util.spec_from_file_location(
    "router_cases_for_test", ROOT / "scripts" / "validate-router-cases.py"
)
if ROUTER_SPEC is None or ROUTER_SPEC.loader is None:
    raise RuntimeError("cannot load scripts/validate-router-cases.py")
router_cases = importlib.util.module_from_spec(ROUTER_SPEC)
ROUTER_SPEC.loader.exec_module(router_cases)


class ValidationTests(unittest.TestCase):
    def test_make_help_is_the_default_target(self) -> None:
        result = subprocess.run(
            ["make", "-s"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Targets:", result.stdout)
        self.assertIn("make validate-release", result.stdout)

    def test_router_fixture_mode_is_canonical(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate-router-cases.py"),
                "--fixtures",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fixture validation passed", result.stdout)

    def test_unavailable_runtime_router_evaluation_is_not_success(self) -> None:
        env = os.environ.copy()
        env.pop("ENGINEERING_BIBLE_ROUTER_EVALUATOR", None)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate-router-cases.py"),
                "--runtime",
            ],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SKIP:", result.stdout)

    def test_configured_runtime_router_evaluator_runs_cases(self) -> None:
        cases = router_cases.parse_router_cases(ROOT / "tests" / "router-cases.yml")
        results = [
            {
                "id": case["id"],
                "skills": case.get("skills", []),
            }
            for case in cases
        ]
        with tempfile.TemporaryDirectory() as raw:
            evaluator = Path(raw) / "runtime-evaluator"
            response = json.dumps({"schema_version": 1, "results": results})
            evaluator.write_text(
                f"#!{sys.executable}\n"
                "import json\n"
                "import sys\n"
                "json.load(sys.stdin)\n"
                f"print({response!r})\n",
                encoding="utf-8",
            )
            evaluator.chmod(0o755)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate-router-cases.py"),
                    "--runtime",
                    "--runtime-evaluator",
                    str(evaluator),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("runtime router evaluation passed", result.stdout)

    def test_shell_syntax_checks_every_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            valid = root / "valid.sh"
            invalid = root / "invalid.sh"
            valid.write_text("#!/usr/bin/env bash\nprintf 'ok\\n'\n", encoding="utf-8")
            invalid.write_text("#!/usr/bin/env bash\nif true; then\n", encoding="utf-8")

            result = validate.validate_shell_syntax([valid, invalid])

        self.assertEqual(result.status, validate.Status.FAIL)
        self.assertIn("invalid.sh", result.detail)

    def test_prompt_budgets_pass_for_repository_profiles(self) -> None:
        result = validate.validate_prompt_budgets(ROOT)

        self.assertEqual(result.status, validate.Status.PASS, result.detail)

    def test_release_snapshot_rejects_required_untracked_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            tracked = root / "tracked.txt"
            untracked = root / "required.txt"
            tracked.write_text("tracked\n", encoding="utf-8")
            untracked.write_text("required\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)

            result = validate.validate_release_membership(root, ["tracked.txt", "required.txt"])

        self.assertEqual(result.status, validate.Status.FAIL)
        self.assertIn("required.txt", result.detail)

    def test_release_snapshot_accepts_required_tracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            required = root / "required.txt"
            required.write_text("required\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "required.txt"], check=True)

            result = validate.validate_release_membership(root, ["required.txt"])

        self.assertEqual(result.status, validate.Status.PASS, result.detail)


if __name__ == "__main__":
    unittest.main()
