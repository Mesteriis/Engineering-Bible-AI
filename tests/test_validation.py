from __future__ import annotations

import importlib.util
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


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
    def test_python_compile_runs_in_process_without_child_interpreters(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "valid.py"
            source.write_text("value: int = 1\n", encoding="utf-8")

            with mock.patch.object(
                validate.subprocess,
                "run",
                side_effect=AssertionError("unexpected child interpreter"),
            ):
                result = validate.validate_python_compile([source])

        self.assertEqual(result.status, validate.Status.PASS)

    def test_python_compile_reports_invalid_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "invalid.py"
            source.write_text("if True print('broken')\n", encoding="utf-8")

            result = validate.validate_python_compile([source])

        self.assertEqual(result.status, validate.Status.FAIL)
        self.assertIn("invalid.py", result.detail)

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

    def test_router_fixtures_keep_default_routes_narrow(self) -> None:
        cases = router_cases.parse_router_cases(ROOT / "tests" / "router-cases.yml")

        for case in cases:
            skills = case.get("skills", [])
            self.assertLessEqual(
                len(skills),
                2,
                f"{case.get('id')}: steady routes should use one primary and at most one support",
            )

    def test_router_fixtures_accept_registered_author_ids_without_local_copies(self) -> None:
        registry = {
            "groups": {"routers": ["workflow-router"]},
            "optional": {},
            "upstream": {"interview": ["pocock.grill-me"]},
        }
        cases = [
            {"id": "interview", "prompt": "Challenge this plan.", "skills": ["pocock.grill-me"]}
        ]
        with (
            mock.patch.object(router_cases, "load_registry", return_value=registry),
            mock.patch.object(router_cases, "parse_router_cases", return_value=cases),
            redirect_stdout(io.StringIO()),
        ):
            status = router_cases.validate_fixtures(ROOT)

        self.assertEqual(status, 0)

    def test_router_fixtures_reject_an_unregistered_author_alias(self) -> None:
        registry = {
            "groups": {"routers": ["workflow-router"]},
            "optional": {},
            "upstream": {"interview": ["pocock.grill-me"]},
        }
        cases = [{"id": "interview", "prompt": "Challenge this plan.", "skills": ["grill-me"]}]
        error = io.StringIO()
        with (
            mock.patch.object(router_cases, "load_registry", return_value=registry),
            mock.patch.object(router_cases, "parse_router_cases", return_value=cases),
            redirect_stderr(error),
        ):
            status = router_cases.validate_fixtures(ROOT)

        self.assertEqual(status, 1)
        self.assertIn("expected skill is not registered: grill-me", error.getvalue())

    def installed_provider_result(self, status: str, *, complete: bool = True) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            manifest = {
                "schema_version": 1,
                "groups": {
                    "requested": [],
                    "include_all": False,
                    "prompt_profile": "steady",
                    "selected_upstream_skills": ["author.example"],
                    "upstream_complete": complete,
                    "upstream_skill_roots": [],
                },
            }
            (home / "install-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            output = io.StringIO()
            with (
                mock.patch("registry.selected_upstream_skills", return_value=["author.example"]),
                mock.patch("upstream_catalog.load_catalog"),
                mock.patch(
                    "upstream_catalog.select_skills",
                    return_value=[SimpleNamespace(id="author.example")],
                ),
                mock.patch("upstream_skills.SkillManager") as manager,
                redirect_stdout(output),
            ):
                manager.return_value.plan.return_value = [
                    {"id": "author.example", "status": status}
                ]
                result = router_cases.validate_installed_providers(
                    ROOT, home / "codex", home / "agents", home
                )
            return result, output.getvalue()

    def test_installed_provider_files_never_claim_session_exposure(self) -> None:
        for status in ("SATISFIED", "REUSE"):
            with self.subTest(status=status):
                result, output = self.installed_provider_result(status)
                self.assertEqual(result, 0)
                self.assertIn(f"PASS: author author.example {status}", output)
                self.assertIn("SKIP: current-session author skill exposure", output)

    def test_missing_changed_and_unrecovered_providers_fail_readiness(self) -> None:
        for status in ("MISSING", "MODIFIED", "CONFLICT", "RECOVERY_REQUIRED", "UPDATE_AVAILABLE"):
            with self.subTest(status=status):
                result, output = self.installed_provider_result(status)
                self.assertEqual(result, 1)
                self.assertIn(f"FAIL: author author.example {status}", output)

    def test_explicit_skipped_author_install_is_not_a_readiness_pass(self) -> None:
        result, output = self.installed_provider_result("MISSING", complete=False)

        self.assertEqual(result, 2)
        self.assertIn("SKIP: author readiness was explicitly skipped", output)
        self.assertNotIn("PASS:", output)

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
