from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.native_skill_plugins import prepare
from scripts.upstream_catalog import Catalog, NoticeSpec, SkillSpec, SourceSpec, UpstreamError
from scripts.upstream_sources import fingerprint_tree


class NativeSkillPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        leaf = self.source / "skills/group/sample"
        leaf.mkdir(parents=True)
        (leaf / "SKILL.md").write_text("---\nname: sample\ndescription: Synthetic\n---\n")
        (self.source / "LICENSE").write_text("Synthetic license\n")
        (self.source / "AGENTS.md").write_text("Root instructions must stay out\n")
        (self.source / "hooks").mkdir()
        (self.source / "hooks/hooks.json").write_text("{}")
        source = SourceSpec(
            "author",
            "https://github.com/example/skills",
            "a" * 40,
            "main",
            "MIT",
            hashlib.sha256((self.source / "LICENSE").read_bytes()).hexdigest(),
            installation="native",
        )
        skill = SkillSpec(
            "author.sample",
            "sample",
            "author",
            "skills/group/sample",
            fingerprint_tree(leaf),
            (),
            (),
            (),
            ("sample",),
            False,
        )
        self.catalog = Catalog({"author": source}, {skill.id: skill}, {})
        self.destination = self.root / "marketplace"
        self.stage = patch(
            "scripts.native_skill_plugins.stage_source",
            side_effect=lambda source, destination: Path(shutil.copytree(self.source, destination)),
        )
        self.stage_mock = self.stage.start()
        self.addCleanup(self.stage.stop)

    def test_preserves_paths_and_attribution_without_root_instructions_or_hooks(self) -> None:
        result = prepare(self.catalog, self.destination)
        provider = self.destination / "providers/author"
        self.assertEqual(result["plugins"], ["bible-author"])
        self.assertTrue((provider / "skills/group/sample/SKILL.md").is_file())
        self.assertEqual(
            (provider / "LICENSE").read_bytes(), (self.source / "LICENSE").read_bytes()
        )
        self.assertFalse((provider / "AGENTS.md").exists())
        self.assertFalse((provider / "hooks").exists())
        manifest = json.loads((provider / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(set(manifest), {"name", "version", "description", "skills"})
        self.assertEqual(manifest["skills"], ["./skills/group/sample"])
        self.assertFalse((self.destination / "staging").exists())

    def test_digest_failure_leaves_no_published_bundle(self) -> None:
        skill = replace(self.catalog.skills["author.sample"], tree_sha256="b" * 64)
        catalog = replace(self.catalog, skills={skill.id: skill})
        with self.assertRaisesRegex(UpstreamError, "digest mismatch"):
            prepare(catalog, self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob(".native-plugins-*")), [])

    def test_multiple_roots_keep_reviewed_support_without_activating_it(self) -> None:
        extra = self.source / "plugins/extra/skills/other"
        extra.mkdir(parents=True)
        (extra / "SKILL.md").write_text("---\nname: other\ndescription: Synthetic\n---\n")
        support = self.source / "plugins/extra/agents"
        support.mkdir()
        (support / "review.md").write_text("Author role reference\n")
        original = self.catalog.sources["author"]
        source = replace(
            original,
            skill_roots=("skills", "plugins/extra/skills"),
            support=(NoticeSpec("plugins/extra/agents", fingerprint_tree(support)),),
        )
        other = replace(
            self.catalog.skills["author.sample"],
            id="author.other",
            name="other",
            path="plugins/extra/skills/other",
            tree_sha256=fingerprint_tree(extra),
        )
        catalog = replace(
            self.catalog,
            sources={"author": source},
            skills={**self.catalog.skills, other.id: other},
        )
        prepare(catalog, self.destination)
        provider = self.destination / "providers/author"
        self.assertTrue((provider / "plugins/extra/agents/review.md").is_file())
        manifest = json.loads((provider / ".codex-plugin/plugin.json").read_text())
        self.assertNotIn("agents", manifest)
        self.assertEqual(len(manifest["skills"]), 2)

    def test_support_digest_failure_leaves_no_bundle(self) -> None:
        support = self.source / "references"
        support.mkdir()
        (support / "guide.md").write_text("changed\n")
        source = replace(
            self.catalog.sources["author"], support=(NoticeSpec("references", "b" * 64),)
        )
        catalog = replace(self.catalog, sources={"author": source})
        with self.assertRaisesRegex(UpstreamError, "support digest mismatch"):
            prepare(catalog, self.destination)
        self.assertFalse(self.destination.exists())

    def test_existing_destination_is_preserved_without_staging(self) -> None:
        self.destination.mkdir()
        sentinel = self.destination / "sentinel"
        sentinel.write_text("keep")
        with self.assertRaises(UpstreamError):
            prepare(self.catalog, self.destination)
        self.stage_mock.assert_not_called()
        self.assertEqual(sentinel.read_text(), "keep")

    def test_explicit_marketplace_namespace_and_source_selection(self) -> None:
        prepare(
            self.catalog,
            self.destination,
            source_ids=("author",),
            marketplace_name="reviewed-wave-two",
        )
        manifest = json.loads((self.destination / ".agents/plugins/marketplace.json").read_text())
        self.assertEqual(manifest["name"], "reviewed-wave-two")
        self.assertEqual(len(manifest["plugins"]), 1)

    def test_unknown_or_managed_source_is_refused_before_staging(self) -> None:
        for ids in [("unknown",), ("author",)]:
            catalog = replace(
                self.catalog,
                sources={"author": replace(self.catalog.sources["author"], installation="managed")},
            )
            with self.subTest(ids=ids), self.assertRaises(UpstreamError):
                prepare(catalog, self.destination, source_ids=ids)
        self.stage_mock.assert_not_called()
