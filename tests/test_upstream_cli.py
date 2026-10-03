from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import upstream_cli


ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "scripts" / "be.py"


class UpstreamCliTests(unittest.TestCase):
    def fixture(
        self, tmp: Path, *, required_tools: list[str] | None = None
    ) -> tuple[Path, Path, Path]:
        from scripts.upstream_sources import fingerprint_tree

        tree = tmp / "providers" / "sample-interview"
        tree.mkdir(parents=True)
        (tree / "SKILL.md").write_text(
            "---\nname: sample-interview\ndescription: Example author interview.\n---\n"
            "\nRead references/questions.md before interviewing.\n",
            encoding="utf-8",
        )
        (tree / "references").mkdir()
        (tree / "references" / "questions.md").write_text("# Author questions\n", encoding="utf-8")
        payload = {
            "schema_version": 1,
            "sources": [
                {
                    "id": "sample",
                    "url": "https://github.com/example/skills",
                    "revision": "a" * 40,
                    "tracking": "main",
                    "license": "MIT",
                    "license_sha256": "b" * 64,
                }
            ],
            "skills": [
                {
                    "id": "sample.interview",
                    "name": "sample-interview",
                    "source": "sample",
                    "path": "skills/productivity/sample-interview",
                    "tree_sha256": fingerprint_tree(tree),
                    "requires": [],
                    "required_tools": required_tools or [],
                    "optional_tools": [],
                    "intents": ["interview"],
                    "user_invoked": True,
                }
            ],
        }
        catalog = tmp / "catalog.json"
        catalog.write_text(json.dumps(payload), encoding="utf-8")
        registry = tmp / "registry.yml"
        registry.write_text(
            "version: 2\ndefault_groups:\ngroups:\noptional:\nupstream:\n"
            "  interviews:\n    - sample.interview\n",
            encoding="utf-8",
        )
        return catalog, registry, tree

    def run_be(self, tmp: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CODEX_HOME": str(tmp / "codex"),
                "AGENTS_HOME": str(tmp / "agents"),
                "ENGINEERING_BIBLE_HOME": str(tmp / "bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
                "PATH": "/usr/bin:/bin",
            }
        )
        return subprocess.run(
            [sys.executable, str(BE), *args],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_ensure_and_plan_require_explicit_selection_before_reading_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            for command in ("plan", "ensure", "update"):
                result = self.run_be(tmp, "skills", command, "--catalog", str(tmp / "missing.json"))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("explicit selection", result.stderr)
            self.assertFalse((tmp / "bible").exists())
            self.assertFalse((tmp / "codex").exists())

    def test_help_describes_independent_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be(Path(raw), "skills", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("list", "plan", "status", "ensure", "check", "update", "rollback", "route"):
            self.assertIn(command, result.stdout)

    def test_existing_package_update_and_add_help_remain_available(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            update = self.run_be(tmp, "update", "--help")
            add = self.run_be(tmp, "add", "skill", "--help")
        self.assertEqual(update.returncode, 0, update.stderr)
        self.assertIn("--allow-unstable", update.stdout)
        self.assertEqual(add.returncode, 0, add.stderr)
        self.assertIn("--ref", add.stdout)

    def test_default_list_is_read_only_and_provenance_is_json(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be(tmp, "skills", "list", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            skills = json.loads(result.stdout)
            self.assertTrue(skills)
            for skill in skills:
                self.assertIn("id", skill)
                self.assertIn("source", skill)
                self.assertEqual(skill["exposure"], "unverified")
            self.assertFalse((tmp / "bible").exists())
            self.assertFalse((tmp / "codex").exists())

    def test_explicit_provider_reuse_and_route_do_not_download_or_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            catalog, registry, tree = self.fixture(tmp)
            options = [
                "--catalog",
                str(catalog),
                "--registry",
                str(registry),
                "--skill-root",
                str(tree.parent),
                "--json",
            ]
            before = {
                str(path.relative_to(tree)): path.read_bytes()
                for path in tree.rglob("*")
                if path.is_file()
            }
            plan = self.run_be(tmp, "skills", "plan", "--group", "interviews", *options)
            self.assertEqual(plan.returncode, 0, plan.stderr)
            self.assertEqual(json.loads(plan.stdout)["skills"][0]["status"], "REUSE")
            ensure = self.run_be(tmp, "skills", "ensure", "--skill", "sample.interview", *options)
            self.assertEqual(ensure.returncode, 0, ensure.stderr)
            self.assertEqual(json.loads(ensure.stdout)["status"], "ok")
            route = self.run_be(tmp, "skills", "route", "interview", *options)
            self.assertEqual(route.returncode, 0, route.stderr)
            self.assertEqual(json.loads(route.stdout)["status"], "pending-exposure")
            self.assertEqual(json.loads(route.stdout)["filesystem_status"], "available")
            after = {
                str(path.relative_to(tree)): path.read_bytes()
                for path in tree.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertFalse((tmp / "codex" / "skills" / "sample-interview").exists())

    def test_dry_run_missing_dependency_does_not_mutate_homes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            catalog, registry, _ = self.fixture(tmp)
            result = self.run_be(
                tmp,
                "skills",
                "ensure",
                "--skill",
                "sample.interview",
                "--dry-run",
                "--catalog",
                str(catalog),
                "--registry",
                str(registry),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "dry-run")
            self.assertEqual(payload["skills"][0]["status"], "MISSING")
            self.assertFalse((tmp / "bible").exists())
            self.assertFalse((tmp / "codex").exists())

    def test_conflict_preserves_existing_provider_and_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            catalog, registry, tree = self.fixture(tmp)
            marker = tree / "personal.md"
            marker.write_text("Keep my changes.\n", encoding="utf-8")
            result = self.run_be(
                tmp,
                "skills",
                "ensure",
                "--skill",
                "sample.interview",
                "--catalog",
                str(catalog),
                "--registry",
                str(registry),
                "--skill-root",
                str(tree.parent),
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("CONFLICT", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "Keep my changes.\n")

    def test_unknown_tool_stops_before_skill_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            catalog, registry, tree = self.fixture(tmp, required_tools=["missing-tool-id"])
            result = self.run_be(
                tmp,
                "skills",
                "ensure",
                "--skill",
                "sample.interview",
                "--catalog",
                str(catalog),
                "--registry",
                str(registry),
                "--skill-root",
                str(tree.parent),
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("unknown tool", result.stderr)
            self.assertFalse((tmp / "bible").exists())

    def test_route_missing_required_tool_is_unavailable_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            catalog, registry, tree = self.fixture(tmp, required_tools=["ty"])
            result = self.run_be(
                tmp,
                "skills",
                "route",
                "interview",
                "--catalog",
                str(catalog),
                "--registry",
                str(registry),
                "--skill-root",
                str(tree.parent),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["filesystem_status"], "available")
            self.assertEqual(payload["status"], "unavailable")
            self.assertEqual(payload["pending_tools_or_setup"], ["ty"])
            self.assertFalse((tmp / "bible").exists())

    def test_tracking_check_error_returns_failure_and_preserves_json_report(self) -> None:
        from scripts import tool_catalog, upstream_catalog, upstream_skills

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            catalog, registry, _ = self.fixture(tmp)
            args = argparse.Namespace(
                skills_command="check",
                catalog=str(catalog),
                registry=str(registry),
                skill_root=[],
                skill=["sample.interview"],
                group=[],
                all=False,
                json=True,
            )
            paths = SimpleNamespace(repo_root=ROOT, be_home=tmp / "bible", codex_home=tmp / "codex")
            report = [
                {
                    "id": "sample.interview",
                    "tracking_status": "ERROR",
                    "reason": "network unavailable",
                }
            ]
            output = io.StringIO()
            modules = {
                "tool_catalog": tool_catalog,
                "upstream_catalog": upstream_catalog,
                "upstream_skills": upstream_skills,
            }
            with (
                patch.dict(sys.modules, modules),
                patch.object(upstream_skills.SkillManager, "check", return_value=report),
                redirect_stdout(output),
            ):
                code = upstream_cli.command_skills(args, paths)
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.getvalue()), report)
            self.assertFalse((tmp / "bible").exists())


class UpstreamToolAdapterTests(unittest.TestCase):
    def test_human_tracking_output_shows_changes_and_failures(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            upstream_cli._emit(
                [
                    {
                        "status": "SATISFIED",
                        "id": "author.sample",
                        "name": "sample",
                        "tracking_status": "CHANGED",
                        "reviewed_revision": "a" * 40,
                        "tracking_revision": "b" * 40,
                    },
                    {
                        "status": "SATISFIED",
                        "id": "other.sample",
                        "name": "other",
                        "tracking_status": "ERROR",
                        "reason": "network unavailable",
                    },
                ],
                False,
            )
        text = output.getvalue()
        self.assertIn("CHANGED", text)
        self.assertIn("b" * 40, text)
        self.assertIn("ERROR", text)
        self.assertIn("network unavailable", text)

    def test_installer_failure_preserves_raw_output_and_exit_code(self) -> None:
        process = subprocess.CompletedProcess([], 7, "TOOL-INSTALL example\n", "installer failed\n")
        plan = {"required": [{"id": "example", "status": "MISSING"}]}
        with patch.object(upstream_cli.subprocess, "run", return_value=process) as run:
            result = upstream_cli._install_required_tools(SimpleNamespace(repo_root=ROOT), plan)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["exit_code"], 7)
        self.assertEqual(result["stdout"], process.stdout)
        self.assertEqual(result["stderr"], process.stderr)
        self.assertEqual(run.call_args.args[0][-2:], ["--tool", "example"])

    def test_spawn_failure_is_a_partial_result_after_skill_installation(self) -> None:
        plan = {"required": [{"id": "example", "status": "MISSING"}]}
        with patch.object(
            upstream_cli.subprocess, "run", side_effect=OSError("cannot start installer")
        ):
            result = upstream_cli._install_required_tools(SimpleNamespace(repo_root=ROOT), plan)
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["exit_code"])
        self.assertIn("cannot start installer", result["stderr"])

    def test_existing_required_tools_are_not_reinstalled(self) -> None:
        plan = {"required": [{"id": "example", "status": "OK"}]}
        with patch.object(upstream_cli.subprocess, "run") as run:
            result = upstream_cli._install_required_tools(SimpleNamespace(repo_root=ROOT), plan)
        run.assert_not_called()
        self.assertEqual(result["status"], "unchanged")


if __name__ == "__main__":
    unittest.main()
