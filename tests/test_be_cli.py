from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "scripts" / "be.py"


def supported_python() -> str:
    """Return an interpreter satisfying the repository's Python 3.11 minimum."""

    if sys.version_info >= (3, 11):
        return sys.executable
    candidate = shutil.which("python3.11")
    if candidate is None:
        raise RuntimeError("tests require Python 3.11 or newer")
    return candidate


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
            [supported_python(), str(BE), *args],
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
            result = self.run_be(
                "validate",
                "--checkout",
                str(ROOT),
                "--profile",
                "bootstrap",
                tmp=Path(raw),
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[PASS] bash scripts/validate-repo-tree.sh", result.stdout)
        self.assertIn("[PASS] prompt budgets", result.stdout)
        self.assertIn("validation passed", result.stdout)

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

    def test_local_installer_rejects_unsupported_python_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            unsupported_python = tmp / "python-old"
            unsupported_python.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
            unsupported_python.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "CODEX_HOME": str(tmp / "codex"),
                    "AGENTS_HOME": str(tmp / "agents"),
                    "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
                    "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
                    "ENGINEERING_BIBLE_PYTHON": str(unsupported_python),
                }
            )

            result = subprocess.run(
                ["bash", str(ROOT / "scripts" / "install-codex.sh"), "--install"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            mutated = (tmp / "engineering-bible").exists()

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(mutated)

    def test_install_tools_flag_is_deprecated_and_does_not_mutate_core(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", "--dry-run", "--install-tools", tmp=tmp)
            wrapper = tmp / "bin" / "be"

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit selector", result.stderr)
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
                    "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
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

    def test_installed_tree_validation_ignores_runtime_state_outside_managed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", tmp=tmp)
            self.assertEqual(result.returncode, 0, result.stderr)

            (tmp / "codex" / "config.toml").write_text("[local]\n", encoding="utf-8")
            plugin_example = tmp / "codex" / "plugins" / "cache" / "plugin" / ".env.example"
            plugin_example.parent.mkdir(parents=True)
            plugin_example.write_text("EXAMPLE=1\n", encoding="utf-8")
            backup_env = tmp / "codex" / "backups" / "old" / ".env"
            backup_env.parent.mkdir(parents=True)
            backup_env.write_text("LOCAL=1\n", encoding="utf-8")

            validate_result = subprocess.run(
                [
                    "bash",
                    str(
                        tmp
                        / "engineering-bible"
                        / "current"
                        / "scripts"
                        / "validate-installed-tree.sh"
                    ),
                    str(tmp / "engineering-bible" / "current"),
                    str(tmp / "codex"),
                    str(tmp / "agents"),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(validate_result.returncode, 0, validate_result.stderr)
        self.assertIn("installed tree validation passed", validate_result.stdout)

    def test_installed_tree_validation_rejects_secret_like_file_in_managed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", tmp=tmp)
            self.assertEqual(result.returncode, 0, result.stderr)

            managed_env = tmp / "codex" / "skills" / "workflow-router" / ".env"
            managed_env.write_text("LOCAL=1\n", encoding="utf-8")

            validate_result = subprocess.run(
                [
                    "bash",
                    str(
                        tmp
                        / "engineering-bible"
                        / "current"
                        / "scripts"
                        / "validate-installed-tree.sh"
                    ),
                    str(tmp / "engineering-bible" / "current"),
                    str(tmp / "codex"),
                    str(tmp / "agents"),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertNotEqual(validate_result.returncode, 0)
        self.assertIn("runtime or secret-like file", validate_result.stderr)

    def test_installed_validation_checks_manifest_selected_optional_skills(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            install = self.run_be("install", "--group", "wiki", tmp=tmp)
            self.assertEqual(install.returncode, 0, install.stderr)
            optional_skill = tmp / "codex" / "skills" / "code-wiki-ru" / "SKILL.md"
            optional_skill.unlink()

            validate_result = self.run_be("validate", "--installed", tmp=tmp)

        self.assertNotEqual(validate_result.returncode, 0)
        self.assertIn(
            "missing or unsafe managed file: codex_home:skills/code-wiki-ru/SKILL.md",
            validate_result.stderr,
        )

    def test_installed_validation_checks_every_manifest_owned_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            install = self.run_be("install", tmp=tmp)
            self.assertEqual(install.returncode, 0, install.stderr)
            (tmp / "bin" / "be").unlink()

            validate_result = self.run_be("validate", "--installed", tmp=tmp)

        self.assertNotEqual(validate_result.returncode, 0)
        self.assertIn("missing or unsafe managed file: bin_dir:be", validate_result.stderr)

    def test_installed_validation_requires_the_exact_expected_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            install = self.run_be("install", tmp=tmp)
            self.assertEqual(install.returncode, 0, install.stderr)
            manifest_path = tmp / "engineering-bible" / "install-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"] = [
                entry
                for entry in manifest["files"]
                if not (entry["root"] == "be_home" and entry["path"] == "current/scripts/be.py")
            ]
            inventory = json.dumps(
                manifest["files"], sort_keys=True, separators=(",", ":")
            ).encode()
            manifest["package"]["digest"] = "sha256:" + hashlib.sha256(inventory).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            manifest_path.chmod(0o600)
            installed_be = tmp / "engineering-bible" / "current" / "scripts" / "be.py"
            installed_be.write_text("corrupt\n", encoding="utf-8")

            validate_result = self.run_be("validate", "--installed", tmp=tmp)

        self.assertNotEqual(validate_result.returncode, 0)
        self.assertIn("missing expected manifest entries", validate_result.stderr)

    def test_force_backs_up_modified_manifest_owned_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            initial = self.run_be("install", tmp=tmp)
            self.assertEqual(initial.returncode, 0, initial.stderr)
            wrapper = tmp / "bin" / "be"
            original_content = "#!/usr/bin/env bash\nprintf 'old wrapper\\n'\n"
            wrapper.write_text(original_content)
            wrapper.chmod(0o755)

            result = self.run_be("install", "--force", tmp=tmp)
            backup_files = sorted(
                (tmp / "engineering-bible" / "backups").glob("*/files/bin_dir/be")
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(backup_files), 1)
            self.assertEqual(backup_files[0].read_text(), original_content)

    def test_install_preserves_unmanaged_wrapper_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            wrapper = tmp / "bin" / "be"
            wrapper.parent.mkdir(parents=True)
            original_content = "#!/usr/bin/env bash\nprintf 'old wrapper\\n'\n"
            wrapper.write_text(original_content)
            wrapper.chmod(0o755)

            result = self.run_be("install", "--force", tmp=tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("UNMANAGED", result.stdout)
            self.assertIn("--migrate-legacy", result.stderr)
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
            validate_result = self.run_be("validate", "--installed", tmp=tmp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("SKIP", result.stdout)
            self.assertEqual(wrapper.read_text(), original_content)
            self.assertNotEqual(validate_result.returncode, 0)
            self.assertIn("installation is incomplete", validate_result.stderr)

    def test_install_group_wiki_installs_code_wiki_skill(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", "--group", "wiki", tmp=tmp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((tmp / "codex" / "skills" / "code-wiki-ru" / "SKILL.md").is_file())
            self.assertFalse((tmp / "agents" / "skills" / "code-wiki-ru" / "SKILL.md").exists())

    def test_install_copies_engineering_docs_into_agents_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", tmp=tmp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((tmp / "agents" / "engineering" / "README.md").is_file())
            self.assertTrue((tmp / "agents" / "engineering" / "35_evidence_contract.md").is_file())
            self.assertFalse((tmp / "agents" / "skills" / "quality-gates" / "SKILL.md").exists())

    def test_install_preserves_unmanaged_agent_skill_copy(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            stale_skill = tmp / "agents" / "skills" / "go"
            stale_skill.mkdir(parents=True)
            (stale_skill / "SKILL.md").write_text(
                "---\nname: [be] go\ndescription: stale\n---\n",
                encoding="utf-8",
            )

            result = self.run_be("install", tmp=tmp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(stale_skill.is_dir())
            self.assertEqual(
                (stale_skill / "SKILL.md").read_text(encoding="utf-8"),
                "---\nname: [be] go\ndescription: stale\n---\n",
            )

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
            result = self.run_be("self-update", "--dry-run", tmp=tmp)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DEPRECATED: use `be update`", result.stderr)
        self.assertIn("Current version:", result.stdout)
        self.assertIn("Installer args:", result.stdout)

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
            installed_be_home = (
                tmp / "engineering-bible" / "skills" / "external" / "sample-skill-test"
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("installed external skill", result.stdout)
            self.assertTrue(installed.is_dir())
            self.assertFalse(installed_agents.exists())
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
