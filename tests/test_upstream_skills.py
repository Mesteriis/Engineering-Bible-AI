from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import cast
import unittest
from unittest.mock import patch

from scripts.upstream_catalog import (
    Catalog,
    NoticeSpec,
    SkillSpec,
    SourceSpec,
    UpstreamError,
    fingerprint_tree,
)
from scripts.upstream_skills import SkillManager


class UpstreamLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "source"
        self.tree = self.repo / "skills" / "sample"
        self.tree.mkdir(parents=True)
        (self.repo / "LICENSE").write_text("Synthetic MIT license\n")
        (self.tree / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Synthetic interview\n---\nRead reference.md\n"
        )
        (self.tree / "reference.md").write_text("Original author reference\n")
        (self.tree / "helper.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.tree / "helper.sh").chmod(0o755)
        self.source = SourceSpec(
            id="author",
            url="https://github.com/example/skills",
            revision="a" * 40,
            tracking="main",
            license="MIT",
            license_sha256=hashlib.sha256((self.repo / "LICENSE").read_bytes()).hexdigest(),
        )
        self.skill = SkillSpec(
            id="author.sample",
            name="sample",
            source="author",
            path="skills/sample",
            tree_sha256=fingerprint_tree(self.tree),
            requires=(),
            required_tools=(),
            optional_tools=(),
            intents=("interview",),
            user_invoked=True,
        )
        self.catalog = Catalog(
            sources={"author": self.source}, skills={self.skill.id: self.skill}, groups={}
        )
        self.home = self.root / "bible"
        self.active = self.root / "codex" / "skills"
        self.manager = SkillManager(self.catalog, self.home, self.active)

        def stage(source: SourceSpec, destination: Path) -> Path:
            shutil.copytree(self.repo, destination)
            return destination

        self.stage = patch("scripts.upstream_skills.stage_source", side_effect=stage)
        self.stage_mock = self.stage.start()
        self.addCleanup(self.stage.stop)

    def install(self) -> dict[str, object]:
        return self.manager.ensure([self.skill])

    def test_plan_and_dry_run_do_not_write_or_download(self) -> None:
        self.assertEqual(self.manager.plan([self.skill])[0]["status"], "MISSING")
        self.manager.ensure([self.skill], dry_run=True)
        self.assertFalse(self.home.exists())
        self.assertFalse(self.active.exists())
        self.stage_mock.assert_not_called()

    def test_install_preserves_author_tree_mode_and_provenance(self) -> None:
        result = self.install()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(fingerprint_tree(self.active / "sample"), self.skill.tree_sha256)
        state = json.loads((self.home / "dependencies" / "state.json").read_text())
        record = state["skills"][self.skill.id]
        self.assertEqual(record["revision"], self.source.revision)
        self.assertEqual(record["source"], self.source.url)
        self.assertEqual(record["owner"], "bible")
        self.assertEqual(self.manager.plan([self.skill])[0]["status"], "SATISFIED")
        self.assertEqual(result["exposure"], "unverified")

    def notice_manager(self) -> tuple[SkillManager, Path]:
        notice = self.repo / "legal" / "NOTICE.md"
        notice.parent.mkdir()
        notice.write_text("Original author attribution\n")
        source = replace(
            self.source,
            notices=(
                NoticeSpec("legal/NOTICE.md", hashlib.sha256(notice.read_bytes()).hexdigest()),
            ),
        )
        catalog = replace(self.catalog, sources={source.id: source})
        return SkillManager(catalog, self.home, self.active), notice

    def test_original_notices_are_retained_separately_with_provenance(self) -> None:
        manager, notice = self.notice_manager()
        manager.ensure([self.skill])
        root = manager.store / "licenses" / self.source.id / self.source.revision
        self.assertEqual((root / "legal/NOTICE.md").read_bytes(), notice.read_bytes())
        self.assertEqual((root / "LICENSE").read_bytes(), (self.repo / "LICENSE").read_bytes())
        self.assertEqual(fingerprint_tree(self.active / "sample"), self.skill.tree_sha256)
        state = json.loads(manager.state_path.read_text())
        self.assertEqual(state["skills"][self.skill.id]["notices"][0]["path"], "legal/NOTICE.md")

    def test_added_notice_is_retained_without_replacing_unchanged_skill(self) -> None:
        self.install()
        manager, notice = self.notice_manager()
        entry = self.active / "sample/SKILL.md"
        before = entry.stat().st_ino
        self.stage_mock.reset_mock()
        self.assertEqual(manager.plan([self.skill])[0]["status"], "ATTRIBUTION_REQUIRED")
        self.assertEqual(manager.route("interview")["status"], "unavailable")
        result = manager.ensure([self.skill])
        self.stage_mock.assert_called_once()
        root = manager.store / "licenses" / self.source.id / self.source.revision
        self.assertEqual((root / "legal/NOTICE.md").read_bytes(), notice.read_bytes())
        self.assertEqual(entry.stat().st_ino, before)
        rows = result["skills"]
        assert isinstance(rows, list)
        rows = cast(list[dict[str, object]], rows)
        self.assertEqual(rows[0]["status"], "SATISFIED")
        self.assertEqual(manager.route("interview")["status"], "available")
        self.stage_mock.reset_mock()
        self.assertIsNone(manager.ensure([self.skill])["backup"])
        self.stage_mock.assert_not_called()

    def test_missing_retained_license_or_notice_is_repaired_without_tree_changes(self) -> None:
        manager, _ = self.notice_manager()
        manager.ensure([self.skill])
        root = manager.store / "licenses" / self.source.id / self.source.revision
        entry = self.active / "sample/SKILL.md"
        before = entry.stat().st_ino
        for relative in ("LICENSE", "legal/NOTICE.md"):
            with self.subTest(relative=relative):
                retained = root / relative
                content = retained.read_bytes()
                retained.unlink()
                self.stage_mock.reset_mock()
                self.assertEqual(manager.plan([self.skill])[0]["status"], "ATTRIBUTION_REQUIRED")
                manager.ensure([self.skill])
                self.stage_mock.assert_called_once()
                self.assertEqual(retained.read_bytes(), content)
                self.assertEqual(entry.stat().st_ino, before)

    def test_changed_retained_attribution_blocks_unchanged_install(self) -> None:
        manager, _ = self.notice_manager()
        manager.ensure([self.skill])
        root = manager.store / "licenses" / self.source.id / self.source.revision
        before = manager.state_path.read_bytes()
        for relative in ("LICENSE", "legal/NOTICE.md"):
            with self.subTest(relative=relative):
                retained = root / relative
                content = retained.read_bytes()
                retained.write_text("User annotation\n")
                self.stage_mock.reset_mock()
                self.assertEqual(manager.plan([self.skill])[0]["status"], "MODIFIED")
                with self.assertRaises(UpstreamError):
                    manager.ensure([self.skill])
                self.stage_mock.assert_not_called()
                self.assertEqual(manager.state_path.read_bytes(), before)
                self.assertEqual(retained.read_text(), "User annotation\n")
                retained.write_bytes(content)

    def test_external_notice_provider_is_reused_without_managed_attribution(self) -> None:
        manager, _ = self.notice_manager()
        self.active.mkdir(parents=True)
        shutil.copytree(self.tree, self.active / "sample")
        manager.ensure([self.skill])
        self.stage_mock.reset_mock()
        self.assertEqual(manager.plan([self.skill])[0]["status"], "SATISFIED")
        self.assertIsNone(manager.ensure([self.skill])["backup"])
        self.stage_mock.assert_not_called()
        self.assertFalse((manager.store / "licenses").exists())

    def test_declared_codex_source_leaf_installs_unchanged(self) -> None:
        author_tree = self.repo / ".agents/skills/sample"
        author_tree.parent.mkdir(parents=True)
        shutil.move(self.tree, author_tree)
        source = replace(self.source, skill_roots=(".agents/skills",))
        skill = replace(self.skill, path=".agents/skills/sample")
        catalog = replace(self.catalog, sources={source.id: source}, skills={skill.id: skill})
        manager = SkillManager(catalog, self.home, self.active)
        manager.ensure([skill])
        self.assertEqual(fingerprint_tree(self.active / "sample"), fingerprint_tree(author_tree))
        self.assertEqual(stat.S_IMODE((self.active / "sample/helper.sh").stat().st_mode), 0o755)
        self.assertFalse((self.active / ".agents").exists())
        state = json.loads(manager.state_path.read_text())
        self.assertEqual(state["skills"][skill.id]["skill_roots"], [".agents/skills"])

    def test_notice_file_and_parent_symlinks_are_rejected_before_activation(self) -> None:
        for parent_link in (False, True):
            with self.subTest(parent_link=parent_link):
                manager, notice = self.notice_manager()
                root = manager.store / "licenses" / self.source.id / self.source.revision
                root.mkdir(parents=True)
                outside = self.root / "outside-notice"
                outside.mkdir()
                (outside / "NOTICE.md").write_text("Personal file\n")
                if parent_link:
                    (root / "legal").symlink_to(outside, target_is_directory=True)
                else:
                    (root / "legal").mkdir()
                    (root / "legal/NOTICE.md").symlink_to(outside / "NOTICE.md")
                with self.assertRaises(UpstreamError):
                    manager.ensure([self.skill])
                self.assertFalse((self.active / "sample").exists())
                self.assertFalse(manager.state_path.exists())
                self.assertEqual((outside / "NOTICE.md").read_text(), "Personal file\n")
                shutil.rmtree(manager.store)
                shutil.rmtree(outside)
                shutil.rmtree(notice.parent)

    def test_wrong_notice_hash_is_rejected_before_active_skill_mutation(self) -> None:
        manager, notice = self.notice_manager()
        notice.write_text("Unexpected changed attribution\n")
        with self.assertRaises(UpstreamError):
            manager.ensure([self.skill])
        self.assertFalse((self.active / "sample").exists())
        self.assertFalse(manager.state_path.exists())

    def test_modified_retained_attribution_is_not_overwritten(self) -> None:
        manager, _ = self.notice_manager()
        root = manager.store / "licenses" / self.source.id / self.source.revision
        (root / "legal").mkdir(parents=True)
        retained = root / "legal/NOTICE.md"
        retained.write_text("User annotation\n")
        with self.assertRaises(UpstreamError):
            manager.ensure([self.skill])
        self.assertFalse((self.active / "sample").exists())
        self.assertEqual(retained.read_text(), "User annotation\n")

    def test_second_ensure_is_unchanged_and_does_not_download(self) -> None:
        self.install()
        before = (self.home / "dependencies" / "state.json").read_bytes()
        self.stage_mock.reset_mock()
        result = self.install()
        self.assertIsNone(result["backup"])
        self.stage_mock.assert_not_called()
        self.assertEqual((self.home / "dependencies" / "state.json").read_bytes(), before)

    def test_identical_unowned_tree_is_reused_and_never_owned(self) -> None:
        self.active.mkdir(parents=True)
        shutil.copytree(self.tree, self.active / "sample")
        self.assertEqual(self.manager.plan([self.skill])[0]["status"], "REUSE")
        self.install()
        self.stage_mock.assert_not_called()
        state = json.loads((self.home / "dependencies" / "state.json").read_text())
        self.assertEqual(state["skills"][self.skill.id]["owner"], "external")

    def test_compatible_provider_in_extra_root_is_reused_without_duplicate(self) -> None:
        native = self.root / "native"
        native.mkdir()
        shutil.copytree(self.tree, native / "sample")
        manager = SkillManager(self.catalog, self.home, self.active, existing_roots=(native,))
        manager.ensure([self.skill])
        self.assertFalse((self.active / "sample").exists())
        self.assertEqual(manager.route("interview")["path"], str(native / "sample"))

    def test_relocated_original_does_not_inherit_stale_bible_ownership(self) -> None:
        self.install()
        shutil.rmtree(self.active / "sample")
        native_root = self.root / "native"
        native_root.mkdir()
        native = native_root / "sample"
        shutil.copytree(self.tree, native)
        manager = SkillManager(self.catalog, self.home, self.active, (native_root,))
        row = manager.plan([self.skill])[0]
        self.assertEqual(row["status"], "REUSE")
        self.assertEqual(row["owner"], "external")
        manager.ensure([self.skill])
        state = json.loads(manager.state_path.read_text())
        self.assertEqual(state["skills"][self.skill.id]["owner"], "external")
        self.assertFalse((self.active / "sample").exists())
        self.assertEqual(fingerprint_tree(native), self.skill.tree_sha256)

    def test_native_source_with_missing_siblings_refuses_split_installation(self) -> None:
        native_root = self.root / "native"
        native_root.mkdir()
        native = native_root / "sample"
        shutil.copytree(self.tree, native)
        dependency = replace(
            self.skill,
            id="author.dependency",
            name="dependency",
            path="skills/dependency",
            intents=("dependency",),
        )
        entry = replace(self.skill, requires=(dependency.id,))
        source = replace(self.source, layout="siblings")
        catalog = replace(
            self.catalog,
            sources={source.id: source},
            skills={entry.id: entry, dependency.id: dependency},
        )
        manager = SkillManager(catalog, self.home, self.active, (native_root,))
        with self.assertRaises(UpstreamError):
            manager.ensure([dependency, entry])
        self.assertFalse((self.active / "dependency").exists())
        self.assertFalse(manager.state_path.exists())
        self.assertEqual(manager.route("interview")["status"], "unavailable")
        self.stage_mock.assert_not_called()

    def test_unowned_different_tree_is_conflict_and_preserved(self) -> None:
        self.active.mkdir(parents=True)
        shutil.copytree(self.tree, self.active / "sample")
        (self.active / "sample" / "reference.md").write_text("User-owned changes\n")
        with self.assertRaises(UpstreamError):
            self.install()
        self.assertEqual(
            (self.active / "sample" / "reference.md").read_text(), "User-owned changes\n"
        )
        self.stage_mock.assert_not_called()

    def test_verified_package_owned_rewrite_can_migrate_to_original(self) -> None:
        self.active.mkdir(parents=True)
        target = self.active / "sample"
        shutil.copytree(self.tree, target)
        (target / "reference.md").write_text("Rewritten Bible procedure\n")
        legacy = {"sample": fingerprint_tree(target)}
        self.assertEqual(self.manager.plan([self.skill])[0]["status"], "CONFLICT")
        self.assertEqual(
            self.manager.plan([self.skill], legacy_owned=legacy)[0]["status"], "MIGRATE_OWNED"
        )
        self.manager.ensure([self.skill], legacy_owned=legacy)
        self.assertEqual(fingerprint_tree(target), self.skill.tree_sha256)
        self.assertEqual(self.manager.plan([self.skill])[0]["owner"], "bible")
        self.manager.rollback()
        self.assertEqual(fingerprint_tree(target), legacy["sample"])

    def test_legacy_handoff_digest_cannot_adopt_user_edits(self) -> None:
        self.active.mkdir(parents=True)
        target = self.active / "sample"
        shutil.copytree(self.tree, target)
        legacy = {"sample": fingerprint_tree(target)}
        (target / "reference.md").write_text("Unowned user edit\n")
        with self.assertRaises(UpstreamError):
            self.manager.ensure([self.skill], legacy_owned=legacy)
        self.assertEqual((target / "reference.md").read_text(), "Unowned user edit\n")
        self.stage_mock.assert_not_called()

    def test_verified_rewrite_retires_when_native_original_exists(self) -> None:
        self.active.mkdir(parents=True)
        rewritten = self.active / "sample"
        shutil.copytree(self.tree, rewritten)
        (rewritten / "reference.md").write_text("Condensed Bible procedure\n")
        legacy_digest = fingerprint_tree(rewritten)
        native_root = self.root / "native"
        native_root.mkdir()
        native = native_root / "sample"
        shutil.copytree(self.tree, native)
        manager = SkillManager(self.catalog, self.home, self.active, (native_root,))
        self.assertEqual(manager.plan([self.skill])[0]["status"], "CONFLICT")
        result = manager.ensure([self.skill], legacy_owned={"sample": legacy_digest})
        result_skills = result["skills"]
        assert isinstance(result_skills, list)
        result_skills = cast(list[dict[str, object]], result_skills)
        self.assertEqual(result_skills[0]["owner"], "external")
        self.assertFalse(rewritten.exists())
        self.stage_mock.assert_not_called()
        self.assertEqual(fingerprint_tree(native), self.skill.tree_sha256)
        manager.rollback()
        self.assertEqual(fingerprint_tree(rewritten), legacy_digest)
        self.assertEqual(fingerprint_tree(native), self.skill.tree_sha256)

    def test_modified_managed_tree_and_extra_file_are_conflicts(self) -> None:
        self.install()
        (self.active / "sample" / "extra.md").write_text("Local addition\n")
        self.assertEqual(self.manager.plan([self.skill])[0]["status"], "MODIFIED")
        with self.assertRaises(UpstreamError):
            self.manager.ensure([self.skill], upgrade=True)

    def test_bad_staged_digest_does_not_activate_or_write_state(self) -> None:
        (self.tree / "reference.md").write_text("Changed upstream bytes\n")
        with self.assertRaises(UpstreamError):
            self.install()
        self.assertFalse((self.active / "sample").exists())
        self.assertFalse((self.home / "dependencies" / "state.json").exists())

    def test_matching_digest_with_invalid_skill_name_does_not_activate(self) -> None:
        (self.tree / "SKILL.md").write_text(
            "---\nname: different\ndescription: Synthetic skill\n---\n"
        )
        skill = replace(self.skill, tree_sha256=fingerprint_tree(self.tree))
        catalog = replace(self.catalog, skills={skill.id: skill})
        manager = SkillManager(catalog, self.home, self.active)
        with self.assertRaises(UpstreamError):
            manager.ensure([skill])
        self.assertFalse((self.active / "sample").exists())

    def test_symlink_destination_is_not_followed(self) -> None:
        self.active.mkdir(parents=True)
        (self.active / "sample").symlink_to(self.tree, target_is_directory=True)
        with self.assertRaises(UpstreamError):
            self.install()
        self.assertTrue((self.active / "sample").is_symlink())

    def test_duplicate_provider_roots_are_conflict(self) -> None:
        self.active.mkdir(parents=True)
        shutil.copytree(self.tree, self.active / "sample")
        native = self.root / "native"
        native.mkdir()
        shutil.copytree(self.tree, native / "sample")
        manager = SkillManager(self.catalog, self.home, self.active, existing_roots=(native,))
        with self.assertRaises(UpstreamError):
            manager.ensure([self.skill])

    def updated(self) -> tuple[SkillManager, SkillSpec]:
        (self.tree / "reference.md").write_text("New author reference\n")
        skill = replace(self.skill, tree_sha256=fingerprint_tree(self.tree))
        source = replace(self.source, revision="b" * 40)
        catalog = replace(self.catalog, sources={source.id: source}, skills={skill.id: skill})
        return SkillManager(catalog, self.home, self.active), skill

    def test_update_requires_explicit_operation_and_rollback_restores_previous(self) -> None:
        self.install()
        manager, skill = self.updated()
        self.assertEqual(manager.plan([skill])[0]["status"], "UPDATE_AVAILABLE")
        with self.assertRaises(UpstreamError):
            manager.ensure([skill])
        result = manager.ensure([skill], upgrade=True)
        self.assertTrue(result["backup"])
        self.assertEqual(fingerprint_tree(self.active / "sample"), skill.tree_sha256)
        manager.rollback()
        self.assertEqual(fingerprint_tree(self.active / "sample"), self.skill.tree_sha256)

    def test_compensation_cannot_rollback_another_transaction(self) -> None:
        initial = self.install()
        manager, skill = self.updated()
        updated = manager.ensure([skill], upgrade=True)
        with self.assertRaises(UpstreamError):
            manager.rollback(expected_backup=str(initial["backup"]))
        self.assertEqual(fingerprint_tree(self.active / "sample"), skill.tree_sha256)
        state = json.loads(manager.state_path.read_text())
        self.assertEqual(state["last_backup"], updated["backup"])
        self.assertFalse(manager.journal_path.exists())

    def test_rollback_refuses_local_edits(self) -> None:
        self.install()
        manager, skill = self.updated()
        manager.ensure([skill], upgrade=True)
        (self.active / "sample" / "reference.md").write_text("User changes\n")
        with self.assertRaises(UpstreamError):
            manager.rollback()
        self.assertFalse(manager.journal_path.exists())
        self.assertEqual(manager.plan([skill])[0]["status"], "MODIFIED")

    def test_legacy_nested_external_provider_is_reused(self) -> None:
        legacy = self.active / "external" / "sample"
        legacy.parent.mkdir(parents=True)
        shutil.copytree(self.tree, legacy)
        self.assertEqual(self.manager.plan([self.skill])[0]["status"], "REUSE")
        self.install()
        self.assertFalse((self.active / "sample").exists())
        self.stage_mock.assert_not_called()

    def test_symlinked_license_file_cannot_overwrite_user_file(self) -> None:
        outside = self.root / "user-file"
        outside.write_text("User data\n")
        license_root = self.manager.store / "licenses" / self.source.id / self.source.revision
        license_root.mkdir(parents=True)
        (license_root / "LICENSE").symlink_to(outside)
        with self.assertRaises(UpstreamError):
            self.install()
        self.assertEqual(outside.read_text(), "User data\n")

    def test_failed_state_commit_rolls_back_active_tree(self) -> None:
        self.install()
        manager, skill = self.updated()
        before = (self.home / "dependencies" / "state.json").read_bytes()
        with patch.object(manager, "_write_state", side_effect=OSError("Injected disk failure")):
            with self.assertRaises((OSError, UpstreamError)):
                manager.ensure([skill], upgrade=True)
        self.assertEqual(fingerprint_tree(self.active / "sample"), self.skill.tree_sha256)
        self.assertEqual((self.home / "dependencies" / "state.json").read_bytes(), before)

    def test_edit_during_backup_is_preserved_before_activation(self) -> None:
        self.install()
        manager, skill = self.updated()
        backup = manager._backup

        def edit_after_backup(names, after):
            result = backup(names, after)
            (self.active / "sample" / "reference.md").write_text("Concurrent user edit\n")
            return result

        with patch.object(manager, "_backup", side_effect=edit_after_backup):
            with self.assertRaises(UpstreamError):
                manager.ensure([skill], upgrade=True)
        self.assertEqual(
            (self.active / "sample" / "reference.md").read_text(), "Concurrent user edit\n"
        )
        self.assertFalse(manager.journal_path.exists())

    def test_edit_during_active_displacement_is_preserved(self) -> None:
        self.install()
        manager, skill = self.updated()
        rename = os.rename

        def edit_displaced(source, destination):
            rename(source, destination)
            if Path(source) == self.active / "sample":
                (Path(destination) / "reference.md").write_text("Concurrent user edit\n")

        with patch("scripts.upstream_skills.os.rename", side_effect=edit_displaced):
            with self.assertRaises(UpstreamError):
                manager.ensure([skill], upgrade=True)
        self.assertEqual(
            (self.active / "sample" / "reference.md").read_text(), "Concurrent user edit\n"
        )

    def test_interrupted_commit_recovers_on_next_mutation(self) -> None:
        self.install()
        manager, skill = self.updated()
        with patch.object(manager, "_write_state", side_effect=SystemExit("Power loss")):
            with self.assertRaises(SystemExit):
                manager.ensure([skill], upgrade=True)
        self.assertTrue((self.home / "dependencies" / "transaction.json").is_file())
        self.manager.ensure([self.skill])
        self.assertEqual(fingerprint_tree(self.active / "sample"), self.skill.tree_sha256)

    def test_explicit_recovery_is_noop_without_journal(self) -> None:
        self.assertFalse(self.manager.recover())
        self.assertFalse(self.home.exists())

    def test_explicit_recovery_restores_interrupted_handoff(self) -> None:
        self.active.mkdir(parents=True)
        target = self.active / "sample"
        shutil.copytree(self.tree, target)
        (target / "reference.md").write_text("Bible rendition\n")
        old_digest = fingerprint_tree(target)
        with patch.object(self.manager, "_write_state", side_effect=SystemExit("Interrupt")):
            with self.assertRaises(SystemExit):
                self.manager.ensure([self.skill], legacy_owned={"sample": old_digest})
        self.assertTrue(self.manager.recover())
        self.assertEqual(fingerprint_tree(target), old_digest)
        self.assertFalse(self.manager.journal_path.exists())

    def test_route_does_not_claim_current_session_exposure(self) -> None:
        self.assertEqual(self.manager.route("interview")["status"], "unavailable")
        self.install()
        route = self.manager.route("interview")
        self.assertEqual(route["status"], "available")
        self.assertEqual(route["skill_name"], "sample")
        self.assertEqual(route["exposure"], "unverified")

    def test_route_checks_transitive_skill_dependencies(self) -> None:
        entry = replace(
            self.skill,
            id="author.entry",
            name="entry",
            requires=(self.skill.id,),
            intents=("entry-interview",),
        )
        catalog = replace(self.catalog, skills={self.skill.id: self.skill, entry.id: entry})
        root = self.active / "entry"
        root.mkdir(parents=True)
        shutil.copytree(self.tree, root, dirs_exist_ok=True)
        entry = replace(entry, tree_sha256=fingerprint_tree(root))
        catalog = replace(catalog, skills={self.skill.id: self.skill, entry.id: entry})
        manager = SkillManager(catalog, self.home, self.active)
        self.assertEqual(manager.route("entry-interview")["status"], "unavailable")

    def test_symlinked_license_store_cannot_write_outside_home(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        self.manager.store.mkdir(parents=True)
        (self.manager.store / "licenses").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(UpstreamError):
            self.install()
        self.assertEqual(list(outside.iterdir()), [])

    def test_rollback_preserves_external_reused_provider(self) -> None:
        self.active.mkdir(parents=True)
        shutil.copytree(self.tree, self.active / "sample")
        self.install()
        self.manager.rollback()
        self.assertEqual(fingerprint_tree(self.active / "sample"), self.skill.tree_sha256)

    def test_changed_backup_metadata_cannot_remove_an_unowned_skill(self) -> None:
        installed = self.install()
        personal = self.active / "personal"
        shutil.copytree(self.tree, personal)
        backup_file = self.manager.store / "backups" / str(installed["backup"]) / "backup.json"
        metadata = json.loads(backup_file.read_text())
        metadata["targets"]["personal"] = {
            "existed": False,
            "before_digest": None,
            "after_digest": fingerprint_tree(personal),
        }
        backup_file.write_text(json.dumps(metadata))
        with self.assertRaises(UpstreamError):
            self.manager.rollback()
        self.assertTrue(personal.is_dir())
        self.assertFalse(self.manager.journal_path.exists())

    def test_interrupted_install_is_not_reported_as_available(self) -> None:
        with patch.object(self.manager, "_write_state", side_effect=SystemExit("Power loss")):
            with self.assertRaises(SystemExit):
                self.install()
        self.assertEqual(self.manager.route("interview")["status"], "unavailable")

    def test_read_only_check_distinguishes_tracking_tip_from_reviewed_pin(self) -> None:
        self.install()
        with patch("scripts.upstream_skills.tracking_revision", return_value="c" * 40):
            before = (self.home / "dependencies" / "state.json").read_bytes()
            result = self.manager.check([self.skill])
        self.assertEqual(result[0]["tracking_revision"], "c" * 40)
        self.assertEqual(result[0]["reviewed_revision"], "a" * 40)
        self.assertEqual(result[0]["tracking_status"], "CHANGED")
        self.assertEqual((self.home / "dependencies" / "state.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
