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
    def run_be(
        self,
        *args: str,
        tmp: Path,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CODEX_HOME": str(tmp / "codex"),
                "AGENTS_HOME": str(tmp / "agents"),
                "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
            }
        )
        if extra_env:
            env.update(extra_env)
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
        self.assertIn("repository", check_names)
        self.assertIn("runtime-boundary", check_names)

    def test_validate_checkout_runs_repository_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("validate", "--checkout", str(ROOT), tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repo tree validation passed", result.stdout)
        self.assertIn("skill frontmatter validation passed", result.stdout)
        self.assertIn("router cases static validation passed", result.stdout)

    def test_audit_runs_quality_gate_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("audit", tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("quality audit passed", result.stdout)

    def test_audit_json_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("audit", "--json", tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tool"], "quality-audit")
        self.assertEqual(payload["status"], "ok")

    def test_install_dry_run_delegates_to_installer_without_writing_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", "--dry-run", tmp=tmp)
            wrapper = tmp / "bin" / "be"

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Mode: --dry-run", result.stdout)
        self.assertIn("ADD", result.stdout)
        self.assertIn("bin/be", result.stdout)
        self.assertFalse(wrapper.exists())

    def test_install_writes_wrapper_with_literal_target_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="be install $path ") as raw:
            tmp = Path(raw)
            result = self.run_be("install", tmp=tmp)
            wrapper = tmp / "bin" / "be"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(wrapper.is_file())
            self.assertTrue(os.access(wrapper, os.X_OK))
            self.assertFalse((tmp / "codex" / "skills" / "code-wiki-ru" / "SKILL.md").exists())

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

    def test_installed_wrapper_can_run_install_from_installed_tree(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", tmp=tmp)
            wrapper = tmp / "bin" / "be"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(wrapper.is_file())

            env = os.environ.copy()
            env.update(
                {
                    "CODEX_HOME": str(tmp / "codex"),
                    "AGENTS_HOME": str(tmp / "agents"),
                    "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
                }
            )
            installed_result = subprocess.run(
                [str(wrapper), "install"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(installed_result.returncode, 0, installed_result.stderr)
        self.assertNotIn("are identical", installed_result.stderr)

    def test_install_backs_up_existing_bin_wrapper_before_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            wrapper = tmp / "bin" / "be"
            wrapper.parent.mkdir(parents=True)
            original_content = "#!/usr/bin/env bash\nprintf 'old wrapper\\n'\n"
            wrapper.write_text(original_content)
            wrapper.chmod(0o755)

            result = self.run_be("install", "--force", tmp=tmp)
            backup_files = sorted(
                (tmp / "codex" / "backups").glob("engineering-bible-ai-*/bin/be")
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(backup_files), 1)
            self.assertEqual(backup_files[0].read_text(), original_content)

    def test_install_conflicts_on_existing_modified_wrapper_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            wrapper = tmp / "bin" / "be"
            wrapper.parent.mkdir(parents=True)
            original_content = "#!/usr/bin/env bash\nprintf 'old wrapper\\n'\n"
            wrapper.write_text(original_content)
            wrapper.chmod(0o755)

            result = self.run_be("install", tmp=tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CONFLICT", result.stdout)
            self.assertIn("--force", result.stderr)
            self.assertEqual(wrapper.read_text(), original_content)

    def test_install_no_overwrite_preserves_existing_modified_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            wrapper = tmp / "bin" / "be"
            wrapper.parent.mkdir(parents=True)
            original_content = "#!/usr/bin/env bash\nprintf 'old wrapper\\n'\n"
            wrapper.write_text(original_content)
            wrapper.chmod(0o755)

            result = self.run_be("install", "--no-overwrite", tmp=tmp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("SKIP", result.stdout)
            self.assertEqual(wrapper.read_text(), original_content)

    def test_install_group_wiki_installs_code_wiki_skill(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", "--group", "wiki", tmp=tmp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((tmp / "codex" / "skills" / "code-wiki-ru" / "SKILL.md").is_file())
            self.assertTrue((tmp / "agents" / "skills" / "code-wiki-ru" / "SKILL.md").is_file())

    def test_update_runs_bootstrap_install_script(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("update", "--dry-run", tmp=tmp)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Installer args:", result.stdout)
        self.assertIn("--dry-run", result.stdout)

    def test_self_update_runs_bootstrap_script(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            bootstrap = tmp / "bootstrap.sh"
            bootstrap.write_text(
                "#!/usr/bin/env bash\n"
                'if [ "$1" = "--dry-run" ]; then\n'
                '  echo "[self-update-dry-run] Mode: $1"\n'
                "else\n"
                '  echo "[self-update] Mode: $1"\n'
                "fi\n",
                encoding="utf-8",
            )
            bootstrap.chmod(0o755)
            result = self.run_be(
                "self-update",
                "--dry-run",
                tmp=tmp,
                extra_env={"ENGINEERING_BIBLE_BOOTSTRAP_URL": f"file://{bootstrap}"},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[self-update-dry-run] Mode: --dry-run", result.stdout)

    def test_add_skill_from_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            source = tmp / "source-skill"
            skill = source / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: sample skill\n---\n",
                encoding="utf-8",
            )
            (skill / "README.md").write_text("sample\n", encoding="utf-8")

            result = self.run_be(
                "add",
                "skill",
                str(skill),
                "--name",
                "sample-skill-test",
                tmp=tmp,
            )

            installed = tmp / "codex" / "skills" / "external" / "sample-skill-test"
            installed_agents = tmp / "agents" / "skills" / "external" / "sample-skill-test"
            installed_be_home = tmp / "engineering-bible" / "skills" / "external" / "sample-skill-test"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("installed external skill", result.stdout)
            self.assertTrue(installed.is_dir())
            self.assertTrue(installed_agents.is_dir())
            self.assertTrue(installed_be_home.is_dir())
            self.assertTrue((installed / "SKILL.md").is_file())

    def test_add_skill_dry_run_does_not_write_destination(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            source = tmp / "source-skill"
            skill = source / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: sample skill\n---\n",
                encoding="utf-8",
            )

            result = self.run_be(
                "add",
                "skill",
                str(skill),
                "--name",
                "sample-skill-dry",
                "--dry-run",
                tmp=tmp,
            )

            installed = tmp / "codex" / "skills" / "external" / "sample-skill-dry"

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--dry-run", result.stdout)
        self.assertFalse(installed.exists())


if __name__ == "__main__":
    unittest.main()
