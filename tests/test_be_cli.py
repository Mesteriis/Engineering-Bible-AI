from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "scripts" / "be.py"


class BeCliTests(unittest.TestCase):
    def run_be(self, *args: str, tmp: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CODEX_HOME": str(tmp / "codex"),
                "AGENTS_HOME": str(tmp / "agents"),
                "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
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

    def test_version_prints_tool_name(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("version", tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Engineering Bible AI", result.stdout)
        self.assertIn("be", result.stdout)

    def test_doctor_json_reports_required_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("doctor", "--json", tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tool"], "be")
        self.assertIn(payload["status"], {"ok", "warn"})
        check_names = {check["name"] for check in payload["checks"]}
        self.assertIn("python3", check_names)
        self.assertIn("rsync", check_names)
        self.assertIn("repository", check_names)
        self.assertIn("runtime-boundary", check_names)

    def test_validate_checkout_runs_repository_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("validate", "--checkout", str(ROOT), tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("skill tree validation passed", result.stdout)
        self.assertIn("skill frontmatter validation passed", result.stdout)

    def test_install_dry_run_delegates_to_installer_without_writing_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", "--dry-run", tmp=tmp)
            wrapper = tmp / "bin" / "be"

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Mode: --dry-run", result.stdout)
        self.assertIn("[dry-run] write be wrapper", result.stdout)
        self.assertFalse(wrapper.exists())

    def test_install_writes_wrapper_with_literal_target_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="be install $path ") as raw:
            tmp = Path(raw)
            result = self.run_be("install", tmp=tmp)
            wrapper = tmp / "bin" / "be"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(wrapper.is_file())
            self.assertTrue(os.access(wrapper, os.X_OK))

            wrapper_result = subprocess.run(
                [str(wrapper), "version"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(wrapper_result.returncode, 0, wrapper_result.stderr)
            self.assertIn("Engineering Bible AI be", wrapper_result.stdout)


if __name__ == "__main__":
    unittest.main()
