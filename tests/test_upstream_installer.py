from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scripts import installer_core  # noqa: E402
from scripts.upstream_catalog import fingerprint_tree  # noqa: E402


class UpstreamInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "package"
        self.author = self.root / "author"
        self.author_tree = self.author / "skills" / "sample"
        self.author_tree.mkdir(parents=True)
        (self.author / "LICENSE").write_text("Synthetic MIT license\n")
        (self.author_tree / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Original author behavior\n---\nOriginal.\n"
        )
        (self.author_tree / "reference.md").write_text("Original reference.\n")
        (self.author_tree / "helper.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.author_tree / "helper.sh").chmod(0o755)
        (self.repo / "config").mkdir(parents=True)
        (self.repo / "skills" / "router").mkdir(parents=True)
        (self.repo / "instructions" / "global").mkdir(parents=True)
        (self.repo / "VERSION").write_text("1.0.0\n")
        (self.repo / "instructions/global/steady.md").write_text("Use original author skills.\n")
        (self.repo / "skills/router/SKILL.md").write_text(
            "---\nname: router\ndescription: Personal routing policy\n---\nRoute to sample.\n"
        )
        self.write_registry()
        catalog = {
            "schema_version": 1,
            "sources": [
                {
                    "id": "author",
                    "url": "https://github.com/example/skills",
                    "revision": "a" * 40,
                    "tracking": "main",
                    "license": "MIT",
                    "license_sha256": hashlib.sha256(
                        (self.author / "LICENSE").read_bytes()
                    ).hexdigest(),
                }
            ],
            "skills": [
                {
                    "id": "author.sample",
                    "name": "sample",
                    "source": "author",
                    "path": "skills/sample",
                    "tree_sha256": fingerprint_tree(self.author_tree),
                    "requires": [],
                    "required_tools": [],
                    "optional_tools": [],
                    "intents": ["sample"],
                    "user_invoked": False,
                }
            ],
        }
        (self.repo / "config/upstream-skills.json").write_text(json.dumps(catalog))
        self.options = installer_core.InstallerOptions(
            repo_root=self.repo,
            codex_home=self.root / "codex",
            agents_home=self.root / "agents",
            be_home=self.root / "bible",
            bin_dir=self.root / "bin",
            dry_run=False,
            backup_only=False,
            no_overwrite=False,
            force=False,
            diff=False,
            groups=[],
            all_groups=False,
            install_tools=False,
            migrate_legacy=False,
            prompt_profile="steady",
            backup_dir=self.root / "bible/backups/initial",
        )

        def stage(source: object, destination: Path) -> Path:
            shutil.copytree(self.author, destination)
            return destination

        self.staging = patch("upstream_skills.stage_source", side_effect=stage)
        self.stage = self.staging.start()
        self.addCleanup(self.staging.stop)

    @property
    def active(self) -> Path:
        return self.options.codex_home / "skills/sample"

    def write_registry(self, legacy: bool = False) -> None:
        (self.repo / "skills/registry.yml").write_text(
            "version: 3\ndefault_groups:\n  - core\ngroups:\n  core:\n    - router\n"
            + ("    - sample\n" if legacy else "")
            + "optional:\nupstream:\n  author:\n    - author.sample\n"
            "upstream_required:\n  core:\n    - author.sample\n"
        )

    def install(self, **overrides: object) -> None:
        options = replace(
            self.options,
            backup_dir=self.options.be_home / "backups" / uuid.uuid4().hex,
            **overrides,
        )
        local = ["router", "sample"] if (self.repo / "skills/sample").exists() else ["router"]
        with redirect_stdout(io.StringIO()):
            installer_core.run_install(options, local)

    def legacy_install(self) -> tuple[bytes, str]:
        leaf = self.repo / "skills/sample"
        leaf.mkdir()
        (leaf / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Former absorbed behavior\n---\nRewritten.\n"
        )
        (leaf / "OLD.md").write_text("Former Bible reference.\n")
        self.write_registry(legacy=True)
        self.install(skip_upstream=True)
        manifest = self.options.manifest_path.read_bytes()
        digest = fingerprint_tree(self.active)
        shutil.rmtree(leaf)
        self.write_registry()
        return manifest, digest

    def test_default_install_keeps_originals_out_of_package_ownership(self) -> None:
        self.install()
        manifest = json.loads(self.options.manifest_path.read_text())
        self.assertTrue(manifest["groups"]["upstream_complete"])
        self.assertEqual(manifest["groups"]["selected_upstream_skills"], ["author.sample"])
        self.assertFalse(
            any(
                item["root"] == "codex_home" and item["path"].startswith("skills/sample/")
                for item in manifest["files"]
            )
        )
        self.assertEqual(fingerprint_tree(self.active), fingerprint_tree(self.author_tree))
        self.stage.reset_mock()
        self.install()
        self.stage.assert_not_called()

    def test_dry_run_has_no_download_or_written_state(self) -> None:
        self.install(dry_run=True)
        self.stage.assert_not_called()
        self.assertFalse(self.options.be_home.exists())

    def test_unmodified_owned_package_files_upgrade_without_force(self) -> None:
        self.install()
        router = self.repo / "skills/router/SKILL.md"
        router.write_text(router.read_text() + "Updated personal route.\n")
        self.install()
        self.assertEqual(
            (self.options.codex_home / "skills/router/SKILL.md").read_bytes(), router.read_bytes()
        )

    def test_package_upgrade_preserves_local_changes_without_force(self) -> None:
        self.install()
        target = self.options.codex_home / "skills/router/SKILL.md"
        target.write_text("User edit.\n")
        source = self.repo / "skills/router/SKILL.md"
        source.write_text(source.read_text() + "Updated route.\n")
        with self.assertRaises(installer_core.InstallError):
            self.install()
        self.assertEqual(target.read_text(), "User edit.\n")

    def test_native_original_is_reused_without_duplicate(self) -> None:
        native = self.root / "native"
        native.mkdir()
        shutil.copytree(self.author_tree, native / "sample")
        self.install(skill_roots=(native,))
        self.stage.assert_not_called()
        self.assertFalse(self.active.exists())
        state = json.loads((self.options.be_home / "dependencies/state.json").read_text())
        self.assertEqual(state["skills"]["author.sample"]["owner"], "external")

    def test_legacy_leaf_handoff_releases_prior_package_ownership(self) -> None:
        self.legacy_install()
        self.install()
        self.assertEqual(fingerprint_tree(self.active), fingerprint_tree(self.author_tree))
        manifest = json.loads(self.options.manifest_path.read_text())
        self.assertFalse(
            any(
                item["root"] == "codex_home" and item["path"].startswith("skills/sample/")
                for item in manifest["files"]
            )
        )

    def test_legacy_leaf_is_retired_when_native_original_is_available(self) -> None:
        self.legacy_install()
        native = self.root / "native"
        native.mkdir()
        shutil.copytree(self.author_tree, native / "sample")
        before = fingerprint_tree(native / "sample")
        self.install(skill_roots=(native,))
        self.stage.assert_not_called()
        self.assertFalse(self.active.exists())
        self.assertEqual(fingerprint_tree(native / "sample"), before)
        self.install()
        self.assertFalse(self.active.exists())
        self.assertEqual(fingerprint_tree(native / "sample"), before)

    def test_native_reuse_handoff_rolls_back_on_package_failure(self) -> None:
        manifest, before = self.legacy_install()
        native = self.root / "native"
        native.mkdir()
        shutil.copytree(self.author_tree, native / "sample")
        native_before = fingerprint_tree(native / "sample")
        with patch.dict("os.environ", {"ENGINEERING_BIBLE_TEST_FAIL_AFTER": "1"}):
            with self.assertRaises(installer_core.InstallError):
                self.install(skill_roots=(native,))
        self.assertEqual(fingerprint_tree(self.active), before)
        self.assertEqual(fingerprint_tree(native / "sample"), native_before)
        self.assertEqual(self.options.manifest_path.read_bytes(), manifest)

    def test_interrupted_native_reuse_resumes_from_stale_package_inventory(self) -> None:
        self.legacy_install()
        native = self.root / "native"
        native.mkdir()
        shutil.copytree(self.author_tree, native / "sample")
        native_before = fingerprint_tree(native / "sample")
        with patch(
            "scripts.installer_core.apply_transaction", side_effect=SystemExit("interrupted")
        ):
            with self.assertRaises(SystemExit):
                self.install(skill_roots=(native,))
        self.assertFalse(self.active.exists())
        self.install(skip_upstream=True, force=True)
        self.assertEqual(fingerprint_tree(native / "sample"), native_before)
        self.assertFalse(self.active.exists())
        self.stage.assert_not_called()

    def test_force_cannot_handoff_modified_or_extra_legacy_files(self) -> None:
        for modification in ("content", "mode", "extra"):
            with self.subTest(modification=modification):
                _, before = self.legacy_install()
                if modification == "content":
                    (self.active / "OLD.md").write_text("User edit.\n")
                elif modification == "mode":
                    (self.active / "OLD.md").chmod(0o600)
                else:
                    (self.active / "LOCAL.md").write_text("User file.\n")
                observed = fingerprint_tree(self.active)
                self.assertNotEqual(observed, before)
                with self.assertRaises(installer_core.InstallError):
                    self.install(force=True)
                self.assertEqual(fingerprint_tree(self.active), observed)
                shutil.rmtree(self.options.be_home)
                shutil.rmtree(self.options.codex_home)
                shutil.rmtree(self.options.agents_home)
                shutil.rmtree(self.options.bin_dir)

    def test_package_failure_rolls_back_author_handoff(self) -> None:
        manifest, before = self.legacy_install()
        with patch.dict("os.environ", {"ENGINEERING_BIBLE_TEST_FAIL_AFTER": "1"}):
            with self.assertRaises(installer_core.InstallError):
                self.install()
        self.assertEqual(fingerprint_tree(self.active), before)
        self.assertEqual(self.options.manifest_path.read_bytes(), manifest)
        self.assertFalse((self.options.be_home / "dependencies/state.json").exists())

    def test_no_overwrite_refuses_legacy_handoff(self) -> None:
        manifest, before = self.legacy_install()
        with self.assertRaisesRegex(installer_core.InstallError, "without --no-overwrite"):
            self.install(no_overwrite=True)
        self.stage.assert_not_called()
        self.assertEqual(fingerprint_tree(self.active), before)
        self.assertEqual(self.options.manifest_path.read_bytes(), manifest)

    def test_interrupted_package_commit_resumes_without_retiring_original(self) -> None:
        self.legacy_install()
        with patch(
            "scripts.installer_core.apply_transaction", side_effect=SystemExit("interrupted")
        ):
            with self.assertRaises(SystemExit):
                self.install()
        self.assertEqual(fingerprint_tree(self.active), fingerprint_tree(self.author_tree))
        self.stage.reset_mock()
        self.install()
        self.stage.assert_not_called()
        self.assertEqual(fingerprint_tree(self.active), fingerprint_tree(self.author_tree))

    def test_interrupted_dependency_handoff_recovers_before_package_ownership_preflight(
        self,
    ) -> None:
        self.legacy_install()
        with patch(
            "upstream_skills.SkillManager._write_state", side_effect=SystemExit("interrupted")
        ):
            with self.assertRaises(SystemExit):
                self.install()
        journal = self.options.be_home / "dependencies/transaction.json"
        self.assertTrue(journal.exists())
        self.install()
        self.assertFalse(journal.exists())
        self.assertEqual(fingerprint_tree(self.active), fingerprint_tree(self.author_tree))

    def test_read_only_modes_refuse_pending_legacy_recovery_without_writes(self) -> None:
        self.legacy_install()
        with patch(
            "upstream_skills.SkillManager._write_state", side_effect=SystemExit("interrupted")
        ):
            with self.assertRaises(SystemExit):
                self.install()
        journal = self.options.be_home / "dependencies/transaction.json"
        before = journal.read_bytes()
        active_before = fingerprint_tree(self.active)
        self.stage.reset_mock()
        for flags in ({"dry_run": True}, {"skip_upstream": True}, {"backup_only": True}):
            with self.subTest(flags=flags):
                with self.assertRaisesRegex(installer_core.InstallError, "recovery"):
                    self.install(**flags)
                self.assertEqual(journal.read_bytes(), before)
                self.assertEqual(fingerprint_tree(self.active), active_before)
        self.stage.assert_not_called()

    def test_portable_only_reinstall_preserves_modified_managed_original(self) -> None:
        self.legacy_install()
        with patch(
            "scripts.installer_core.apply_transaction", side_effect=SystemExit("interrupted")
        ):
            with self.assertRaises(SystemExit):
                self.install()
        (self.active / "reference.md").write_text("User edit.\n")
        before = fingerprint_tree(self.active)
        self.install(skip_upstream=True, force=True)
        self.assertEqual(fingerprint_tree(self.active), before)

    def test_package_conflict_does_not_install_author_dependencies(self) -> None:
        self.options.bin_dir.mkdir()
        (self.options.bin_dir / "be").write_text("User wrapper.\n")
        with self.assertRaises(installer_core.InstallError):
            self.install(force=True)
        self.stage.assert_not_called()
        self.assertFalse(self.active.exists())

    def test_unmanaged_different_provider_is_preserved(self) -> None:
        self.active.mkdir(parents=True)
        (self.active / "SKILL.md").write_text("User source.\n")
        with self.assertRaises(RuntimeError):
            self.install(force=True)
        self.assertEqual((self.active / "SKILL.md").read_text(), "User source.\n")


if __name__ == "__main__":
    unittest.main()
