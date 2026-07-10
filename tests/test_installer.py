from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_codex.py"
INSTALLER_CORE_PATH = ROOT / "scripts" / "installer_core.py"
sys.path.insert(0, str(INSTALLER_CORE_PATH.parent))
INSTALLER_CORE_SPEC = importlib.util.spec_from_file_location(
    "installer_core_under_test", INSTALLER_CORE_PATH
)
assert INSTALLER_CORE_SPEC is not None and INSTALLER_CORE_SPEC.loader is not None
installer_core = importlib.util.module_from_spec(INSTALLER_CORE_SPEC)
sys.modules[INSTALLER_CORE_SPEC.name] = installer_core
INSTALLER_CORE_SPEC.loader.exec_module(installer_core)


class InstallerTests(unittest.TestCase):
    def run_installer(
        self,
        tmp: Path,
        *args: str,
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
            [sys.executable, str(INSTALLER), *args],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def install(self, tmp: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = self.run_installer(tmp, "--install", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def installer_options(self, tmp: Path) -> installer_core.InstallerOptions:
        be_home = tmp / "engineering-bible"
        return installer_core.InstallerOptions(
            repo_root=ROOT,
            codex_home=tmp / "codex",
            agents_home=tmp / "agents",
            be_home=be_home,
            bin_dir=tmp / "bin",
            dry_run=False,
            backup_only=False,
            no_overwrite=False,
            force=False,
            diff=False,
            groups=[],
            all_groups=False,
            install_tools=False,
            migrate_legacy=False,
            prompt_profile="full",
            backup_dir=be_home / "backups" / "pre-backup-failure",
        )

    def test_lock_symlink_is_rejected_without_mutating_victim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            be_home = tmp / "engineering-bible"
            be_home.mkdir()
            victim = tmp / "victim"
            victim.write_bytes(b"unmanaged victim\n")
            victim.chmod(0o640)
            lock_path = be_home / ".install.lock"
            lock_path.symlink_to(victim)

            result = self.run_installer(tmp, "--install")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(victim.read_bytes(), b"unmanaged victim\n")
            self.assertEqual(victim.stat().st_mode & 0o777, 0o640)
            self.assertTrue(lock_path.is_symlink())

    def test_unmanaged_lock_content_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            be_home = tmp / "engineering-bible"
            be_home.mkdir()
            lock_path = be_home / ".install.lock"
            lock_path.write_bytes(b"unmanaged lock content\n")
            lock_path.chmod(0o640)

            result = self.run_installer(tmp, "--install")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(lock_path.read_bytes(), b"unmanaged lock content\n")
            self.assertEqual(lock_path.stat().st_mode & 0o777, 0o640)

    def test_hardlinked_lock_is_rejected_without_mutating_victim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            be_home = tmp / "engineering-bible"
            be_home.mkdir()
            victim = tmp / "victim"
            victim.write_bytes(b"pid=123\n")
            victim.chmod(0o640)
            lock_path = be_home / ".install.lock"
            os.link(victim, lock_path)

            result = self.run_installer(tmp, "--install")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(victim.read_bytes(), b"pid=123\n")
            self.assertEqual(victim.stat().st_mode & 0o777, 0o640)
            self.assertEqual(victim.stat().st_nlink, 2)

    def test_managed_lock_mode_is_repaired_to_private(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self.install(tmp)
            lock_path = tmp / "engineering-bible" / ".install.lock"
            lock_path.chmod(0o644)

            self.install(tmp)

            self.assertEqual(lock_path.stat().st_mode & 0o777, 0o600)

    def test_pre_backup_failure_preserves_untouched_manifest_bytes_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            options = self.installer_options(tmp)
            options.be_home.mkdir(parents=True)
            original = b'{"existing": "manifest"}\n'
            options.manifest_path.write_bytes(original)
            options.manifest_path.chmod(0o640)

            with mock.patch.object(
                installer_core,
                "prepare_backup",
                side_effect=OSError("injected pre-backup failure"),
            ):
                with self.assertRaises(installer_core.InstallError):
                    installer_core.apply_transaction([], {"replacement": True}, options)

            self.assertEqual(options.manifest_path.read_bytes(), original)
            self.assertEqual(options.manifest_path.stat().st_mode & 0o777, 0o640)

    def test_install_creates_namespaced_snapshot_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="be installer $path ") as raw:
            tmp = Path(raw)
            self.install(tmp)

            be_home = tmp / "engineering-bible"
            current = be_home / "current"
            manifest_path = be_home / "install-manifest.json"
            wrapper = tmp / "bin" / "be"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertTrue((current / "scripts" / "be.py").is_file())
            self.assertTrue((current / "skills" / "registry.yml").is_file())
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["package"]["version"], (ROOT / "VERSION").read_text().strip())
            self.assertRegex(manifest["package"]["digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(manifest["roots"]["be_home"], str(be_home.resolve()))
            self.assertIn("selected_skills", manifest["groups"])
            self.assertTrue(manifest["files"])
            self.assertTrue(
                all({"root", "path", "sha256", "mode"} <= set(entry) for entry in manifest["files"])
            )
            self.assertIn(str(current / "scripts" / "be.py"), wrapper.read_text(encoding="utf-8"))
            self.assertIn("Python 3.11+ is required", wrapper.read_text(encoding="utf-8"))
            self.assertEqual(wrapper.stat().st_mode & 0o777, 0o755)

            wrapper_entry = next(
                entry
                for entry in manifest["files"]
                if entry["root"] == "bin_dir" and entry["path"] == "be"
            )
            self.assertEqual(wrapper_entry["mode"], "0755")
            self.assertEqual(
                wrapper_entry["sha256"],
                hashlib.sha256(wrapper.read_bytes()).hexdigest(),
            )

    def test_force_never_overwrites_unmanaged_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            wrapper = tmp / "bin" / "be"
            wrapper.parent.mkdir(parents=True)
            wrapper.write_text("unmanaged\n", encoding="utf-8")
            wrapper.chmod(0o755)

            result = self.run_installer(tmp, "--install", "--force")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("UNMANAGED", result.stdout)
            self.assertIn("--migrate-legacy", result.stderr)
            self.assertEqual(wrapper.read_text(encoding="utf-8"), "unmanaged\n")
            self.assertFalse((tmp / "engineering-bible" / "install-manifest.json").exists())

    def test_migrate_legacy_adopts_only_identical_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self.install(tmp)
            manifest_path = tmp / "engineering-bible" / "install-manifest.json"
            before = manifest_path.read_bytes()
            manifest_path.unlink()

            rejected = self.run_installer(tmp, "--install", "--force")
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("UNMANAGED", rejected.stdout)

            adopted = self.run_installer(tmp, "--install", "--migrate-legacy")
            self.assertEqual(adopted.returncode, 0, adopted.stderr)
            self.assertIn("ADOPT", adopted.stdout)
            self.assertEqual(manifest_path.read_bytes(), before)

            manifest_path.unlink()
            wrapper = tmp / "bin" / "be"
            wrapper.write_text("modified legacy wrapper\n", encoding="utf-8")
            modified = self.run_installer(tmp, "--install", "--migrate-legacy", "--force")
            self.assertNotEqual(modified.returncode, 0)
            self.assertIn("UNMANAGED", modified.stdout)
            self.assertEqual(wrapper.read_text(encoding="utf-8"), "modified legacy wrapper\n")

    def test_reinstall_repairs_managed_executable_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self.install(tmp)
            wrapper = tmp / "bin" / "be"
            wrapper.chmod(0o644)

            result = self.install(tmp)

            self.assertIn("MODE", result.stdout)
            self.assertEqual(wrapper.stat().st_mode & 0o777, 0o755)

    def test_installed_snapshot_reinstall_preserves_original_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self.install(tmp)
            manifest_path = tmp / "engineering-bible" / "install-manifest.json"
            before = json.loads(manifest_path.read_text(encoding="utf-8"))
            installed = tmp / "engineering-bible" / "current" / "scripts" / "install_codex.py"
            env = os.environ.copy()
            env.update(
                {
                    "CODEX_HOME": str(tmp / "codex"),
                    "AGENTS_HOME": str(tmp / "agents"),
                    "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
                    "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
                }
            )

            result = subprocess.run(
                [sys.executable, str(installed), "--install"],
                cwd=tmp,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            after = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(after["package"]["source"], before["package"]["source"])

    def test_transaction_rolls_back_files_and_manifest_after_injected_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self.install(tmp)
            wrapper = tmp / "bin" / "be"
            manifest_path = tmp / "engineering-bible" / "install-manifest.json"
            old_wrapper = b"locally modified managed wrapper\n"
            wrapper.write_bytes(old_wrapper)
            old_manifest = manifest_path.read_bytes()

            failed = self.run_installer(
                tmp,
                "--install",
                "--force",
                extra_env={"ENGINEERING_BIBLE_TEST_FAIL_AFTER": "1"},
            )

            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("rolled back", failed.stderr)
            self.assertEqual(wrapper.read_bytes(), old_wrapper)
            self.assertEqual(manifest_path.read_bytes(), old_manifest)

    def test_unmanaged_files_inside_managed_directories_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self.install(tmp)
            local_file = tmp / "codex" / "skills" / "workflow-router" / "LOCAL.md"
            local_file.write_text("user-owned\n", encoding="utf-8")

            self.install(tmp, "--force")

            self.assertEqual(local_file.read_text(encoding="utf-8"), "user-owned\n")

    def test_switching_groups_removes_only_manifest_owned_active_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self.install(tmp, "--group", "wiki")
            active_skill = tmp / "codex" / "skills" / "code-wiki-ru" / "SKILL.md"
            snapshot_skill = (
                tmp / "engineering-bible" / "current" / "skills" / "code-wiki-ru" / "SKILL.md"
            )
            unmanaged = active_skill.parent / "LOCAL.md"
            unmanaged.write_text("keep\n", encoding="utf-8")

            result = self.install(tmp)

            self.assertIn("REMOVE", result.stdout)
            self.assertFalse(active_skill.exists())
            self.assertEqual(unmanaged.read_text(encoding="utf-8"), "keep\n")
            self.assertTrue(snapshot_skill.is_file())


if __name__ == "__main__":
    unittest.main()
