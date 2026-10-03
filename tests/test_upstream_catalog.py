from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts import registry
from scripts.upstream_catalog import UpstreamError, load_catalog, select_skills


ROOT = Path(__file__).resolve().parents[1]


def catalog_payload() -> dict:
    return {
        "schema_version": 1,
        "sources": [
            {
                "id": "author",
                "url": "https://github.com/author/skills",
                "revision": "a" * 40,
                "tracking": "main",
                "license": "MIT",
                "license_sha256": "b" * 64,
            }
        ],
        "skills": [
            {
                "id": "author.sample",
                "name": "sample",
                "source": "author",
                "path": "skills/general/sample",
                "tree_sha256": "c" * 64,
                "requires": [],
                "required_tools": [],
                "optional_tools": [],
                "intents": ["sample"],
                "user_invoked": True,
            }
        ],
    }


class UpstreamCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "catalog.json"

    def write(self, payload: dict) -> None:
        self.path.write_text(json.dumps(payload), encoding="utf-8")

    def test_load_and_explicit_selection(self) -> None:
        self.write(catalog_payload())
        catalog = load_catalog(self.path)
        self.assertEqual(select_skills(catalog, ["author.sample"], [], False)[0].name, "sample")
        self.assertEqual(catalog.groups, {})
        self.assertEqual(catalog.sources["author"].layout, "independent")

    def test_source_layout_contract_is_validated(self) -> None:
        payload = catalog_payload()
        payload["sources"][0]["layout"] = "siblings"
        self.write(payload)
        self.assertEqual(load_catalog(self.path).sources["author"].layout, "siblings")
        payload["sources"][0]["layout"] = "unknown"
        self.write(payload)
        with self.assertRaises(UpstreamError):
            load_catalog(self.path)

    def test_declared_author_skill_roots_preserve_provider_paths(self) -> None:
        for root in ("skills", ".agents/skills", ".claude/skills", "plugin/skills"):
            with self.subTest(root=root):
                payload = catalog_payload()
                payload["sources"][0]["skill_roots"] = [root]
                payload["skills"][0]["path"] = root + "/sample"
                self.write(payload)
                catalog = load_catalog(self.path)
                self.assertEqual(catalog.sources["author"].skill_roots, (root,))
                self.assertEqual(catalog.skills["author.sample"].path, root + "/sample")

    def test_skill_roots_are_narrow_safe_and_bound_skill_paths(self) -> None:
        for roots in (
            [],
            "skills",
            [".claude"],
            ["../skills"],
            ["/skills"],
            [".git/skills"],
            [".env/skills"],
            ["skills", "skills"],
            ["skills", "skills/nested/skills"],
        ):
            with self.subTest(roots=roots):
                payload = catalog_payload()
                payload["sources"][0]["skill_roots"] = roots
                self.write(payload)
                with self.assertRaises(UpstreamError):
                    load_catalog(self.path)
        payload = catalog_payload()
        payload["sources"][0]["skill_roots"] = [".claude/skills"]
        for path in ("skills/sample", ".claude/skills-other/sample", ".claude/skills"):
            with self.subTest(path=path):
                payload["skills"][0]["path"] = path
                self.write(payload)
                with self.assertRaises(UpstreamError):
                    load_catalog(self.path)

    def test_reviewed_notice_paths_and_hashes_are_validated(self) -> None:
        payload = catalog_payload()
        payload["sources"][0]["notices"] = [{"path": "NOTICE.md", "sha256": "d" * 64}]
        self.write(payload)
        notices = load_catalog(self.path).sources["author"].notices
        self.assertEqual([(item.path, item.sha256) for item in notices], [("NOTICE.md", "d" * 64)])
        for notices in (
            "NOTICE.md",
            [{"path": "../NOTICE.md", "sha256": "d" * 64}],
            [{"path": ".claude/auth.json", "sha256": "d" * 64}],
            [{"path": "NOTICE.md", "sha256": "wrong"}],
            [{"path": "NOTICE.md", "sha256": "d" * 64, "extra": True}],
            [{"path": "LICENSE", "sha256": "d" * 64}],
            [{"path": "LICENSE/NOTICE.md", "sha256": "d" * 64}],
            [{"path": "NOTICE.md", "sha256": "d" * 64}] * 2,
            [
                {"path": "NOTICE", "sha256": "d" * 64},
                {"path": "NOTICE/third-party.md", "sha256": "d" * 64},
            ],
        ):
            with self.subTest(notices=notices):
                payload["sources"][0]["notices"] = notices
                self.write(payload)
                with self.assertRaises(UpstreamError):
                    load_catalog(self.path)

    def test_immutable_revision_and_digest_required(self) -> None:
        for key, invalid in [
            ("revision", "main"),
            ("revision", "a" * 39),
            ("license_sha256", "no"),
        ]:
            with self.subTest(key=key, invalid=invalid):
                payload = catalog_payload()
                payload["sources"][0][key] = invalid
                self.write(payload)
                with self.assertRaises(UpstreamError):
                    load_catalog(self.path)

    def test_source_url_requires_public_credential_free_github_https(self) -> None:
        for url in [
            "file:///tmp/repo",
            "http://github.com/a/b",
            "https://token@github.com/a/b",
            "https://github.com/a/b?token=secret",
            "https://private.example/a/b",
        ]:
            with self.subTest(url=url):
                payload = catalog_payload()
                payload["sources"][0]["url"] = url
                self.write(payload)
                with self.assertRaises(UpstreamError):
                    load_catalog(self.path)

    def test_unsafe_paths_and_unknown_source_are_rejected(self) -> None:
        for path in [
            "/skills/sample",
            "skills/../sample",
            "skills\\sample",
            "skills",
            "docs/sample",
            "skills//sample",
        ]:
            with self.subTest(path=path):
                payload = catalog_payload()
                payload["skills"][0]["path"] = path
                self.write(payload)
                with self.assertRaises(UpstreamError):
                    load_catalog(self.path)
        payload = catalog_payload()
        payload["skills"][0]["source"] = "unknown"
        self.write(payload)
        with self.assertRaises(UpstreamError):
            load_catalog(self.path)

    def test_duplicate_identity_or_author_name_is_rejected(self) -> None:
        for field in ["id", "name"]:
            payload = catalog_payload()
            duplicate = dict(payload["skills"][0])
            if field == "name":
                duplicate["id"] = "author.other"
            payload["skills"].append(duplicate)
            self.write(payload)
            with self.assertRaises(UpstreamError):
                load_catalog(self.path)

    def test_unknown_fields_duplicate_json_keys_and_invalid_types_are_rejected(self) -> None:
        payload = catalog_payload()
        payload["sources"][0]["token"] = "forbidden"
        self.write(payload)
        with self.assertRaises(UpstreamError):
            load_catalog(self.path)
        self.path.write_text('{"schema_version":1,"schema_version":1,"sources":[],"skills":[]}')
        with self.assertRaises(UpstreamError):
            load_catalog(self.path)
        for field, invalid in [
            ("requires", "sample"),
            ("user_invoked", "true"),
            ("tree_sha256", "c" * 63),
        ]:
            payload = catalog_payload()
            payload["skills"][0][field] = invalid
            self.write(payload)
            with self.assertRaises(UpstreamError):
                load_catalog(self.path)

    def test_license_path_is_safe_and_defaults_to_license(self) -> None:
        self.write(catalog_payload())
        self.assertEqual(load_catalog(self.path).sources["author"].license_path, "LICENSE")
        for invalid in ["../LICENSE", "/LICENSE", "\\LICENSE", "licenses//MIT"]:
            payload = catalog_payload()
            payload["sources"][0]["license_path"] = invalid
            self.write(payload)
            with self.assertRaises(UpstreamError):
                load_catalog(self.path)

    def test_author_names_match_host_and_source_directory(self) -> None:
        for name in ["author.sample", "Sample", "sample_name", "another-name"]:
            payload = catalog_payload()
            payload["skills"][0]["name"] = name
            self.write(payload)
            with self.assertRaises(UpstreamError):
                load_catalog(self.path)

    def test_dependency_order_is_stable_and_complete(self) -> None:
        payload = catalog_payload()
        dependency = dict(
            payload["skills"][0],
            id="author.dep",
            name="dep",
            path="skills/general/dep",
            requires=[],
        )
        payload["skills"][0]["requires"] = ["author.dep"]
        payload["skills"].append(dependency)
        self.write(payload)
        catalog = load_catalog(self.path)
        self.assertEqual(
            [x.id for x in select_skills(catalog, ["author.sample", "author.dep"], [], False)],
            ["author.dep", "author.sample"],
        )

    def test_missing_dependencies_cycles_and_empty_selection_are_rejected(self) -> None:
        for dependency in ["author.missing", "author.sample"]:
            payload = catalog_payload()
            payload["skills"][0]["requires"] = [dependency]
            self.write(payload)
            with self.assertRaises(UpstreamError):
                load_catalog(self.path)
        self.write(catalog_payload())
        catalog = load_catalog(self.path)
        for args in [([], [], False), (["missing"], [], False), ([], ["missing"], False)]:
            with self.assertRaises(UpstreamError):
                select_skills(catalog, *args)

    def test_registry_owns_upstream_membership_and_selection(self) -> None:
        self.write(catalog_payload())
        path = self.root / "registry.yml"
        path.write_text(
            "version: 2\ndefault_groups:\ngroups:\noptional:\nupstream:\n  interviews:\n    - author.sample\n",
            encoding="utf-8",
        )
        catalog = load_catalog(self.path, path)
        self.assertEqual(catalog.groups, {"interviews": ("author.sample",)})
        self.assertEqual(
            [x.id for x in select_skills(catalog, [], ["interviews"], False)], ["author.sample"]
        )
        # Legacy Bible package selection never projects upstream author files.
        self.assertEqual(
            registry.selected_skills(registry.parse_registry(path), groups=[], include_all=True), []
        )

    def test_duplicate_or_incomplete_registry_membership_is_rejected(self) -> None:
        self.write(catalog_payload())
        for members in [
            "  a:\n    - author.sample\n  b:\n    - author.sample\n",
            "  a:\n    - unknown\n",
            "",
        ]:
            path = self.root / "registry.yml"
            path.write_text(
                "version: 2\ndefault_groups:\ngroups:\noptional:\nupstream:\n" + members,
                encoding="utf-8",
            )
            with self.assertRaises(UpstreamError):
                load_catalog(self.path, path)

    def test_version_one_registry_remains_supported(self) -> None:
        path = self.root / "registry.yml"
        path.write_text(
            "version: 1\ndefault_groups:\n  - core\ngroups:\n  core:\n    - local\noptional:\n",
            encoding="utf-8",
        )
        parsed = registry.parse_registry(path)
        self.assertEqual(registry.selected_skills(parsed, groups=[], include_all=False), ["local"])
        self.assertEqual(parsed.get("upstream"), {})

    def test_invalid_registry_versions_and_duplicate_groups_fail(self) -> None:
        for body in [
            "version: 4\n",
            "version: 1\nupstream:\n  a:\n    - author.sample\n",
            "version: 2\ngroups:\n  core:\n  core:\n",
            "version: 2\nversion: 2\n",
        ]:
            path = self.root / "registry.yml"
            path.write_text(body, encoding="utf-8")
            with self.assertRaises(registry.RegistryError):
                registry.parse_registry(path)

    def test_repository_curated_graph(self) -> None:
        catalog = load_catalog(ROOT / "config/upstream-skills.json", ROOT / "skills/registry.yml")
        self.assertEqual(
            set(catalog.skills),
            {identity for group in catalog.groups.values() for identity in group},
        )
        self.assertTrue(
            {"interface.interface-design", "uipro.ui-ux-pro-max", "impeccable.impeccable"}
            <= catalog.skills.keys()
        )
        self.assertEqual(
            [x.name for x in select_skills(catalog, ["pocock.grill-with-docs"], [], False)],
            ["grilling", "domain-modeling", "grill-with-docs"],
        )

    def test_default_owner_groups_require_original_workflows(self) -> None:
        parsed = registry.load_registry(ROOT)
        selected = registry.selected_upstream_skills(parsed, groups=[], include_all=False)
        required = registry.cast_dict(parsed["upstream_required"])
        expected = {
            identity
            for group in registry.default_group_names(parsed)
            for identity in registry.cast_list(required.get(group, []))
        }
        self.assertEqual(set(selected), expected)
        self.assertIn("superpowers.systematic-debugging", selected)
        self.assertIn("superpowers.writing-skills", selected)
        self.assertIn("karpathy.karpathy-guidelines", selected)
        self.assertNotIn("pocock.grill-me", selected)
        self.assertNotIn(
            "karpathy-guidelines",
            registry.selected_skills(parsed, groups=[], include_all=False),
        )

    def test_business_ui_authors_are_required_only_with_ui_owner_group(self) -> None:
        parsed = registry.load_registry(ROOT)
        authors = {"interface.interface-design", "uipro.ui-ux-pro-max", "impeccable.impeccable"}
        requirements = registry.cast_dict(parsed["upstream_required"])
        self.assertEqual(set(registry.cast_list(requirements["ui"])), authors)
        selected = set(registry.selected_upstream_skills(parsed, groups=[], include_all=False))
        self.assertTrue(authors <= selected)
        without_ui = dict(parsed)
        without_ui["default_groups"] = [
            group for group in registry.default_group_names(parsed) if group != "ui"
        ]
        self.assertFalse(
            authors
            & set(registry.selected_upstream_skills(without_ui, groups=[], include_all=False))
        )
        fast_only = dict(parsed, default_groups=[])
        self.assertEqual(
            registry.selected_upstream_skills(
                fast_only, groups=["optional.fast"], include_all=False
            ),
            [],
        )

    def test_property_testing_requires_only_the_core_owner_group(self) -> None:
        parsed = registry.load_registry(ROOT)
        identity = "trailofbits.property-based-testing"
        requirements = registry.cast_dict(parsed["upstream_required"])
        self.assertIn(identity, registry.cast_list(requirements["core"]))
        selected = set(registry.selected_upstream_skills(parsed, groups=[], include_all=False))
        self.assertIn(identity, selected)
        without_core = dict(parsed)
        without_core["default_groups"] = [
            group for group in registry.default_group_names(parsed) if group != "core"
        ]
        self.assertNotIn(
            identity,
            registry.selected_upstream_skills(without_core, groups=[], include_all=False),
        )
        fast_only = dict(parsed, default_groups=[])
        self.assertEqual(
            registry.selected_upstream_skills(
                fast_only, groups=["optional.fast"], include_all=False
            ),
            [],
        )

    def test_continuation_authors_are_opt_in_without_hidden_dependencies(self) -> None:
        catalog = load_catalog(ROOT / "config/upstream-skills.json", ROOT / "skills/registry.yml")
        continuation = {"pocock.handoff", "context.context-compression"}
        self.assertEqual(set(catalog.groups["context-continuation"]), continuation)
        self.assertEqual(
            {skill.id for skill in select_skills(catalog, [], ["context-continuation"], False)},
            continuation,
        )
        self.assertEqual(
            [skill.id for skill in select_skills(catalog, ["pocock.handoff"], [], False)],
            ["pocock.handoff"],
        )
        parsed = registry.load_registry(ROOT)
        self.assertFalse(
            continuation
            & set(registry.selected_upstream_skills(parsed, groups=[], include_all=False))
        )
        self.assertTrue(catalog.skills["pocock.handoff"].user_invoked)
        self.assertFalse(catalog.skills["context.context-compression"].user_invoked)

    def test_quality_authors_keep_reviewed_license_scope_and_existing_pocock_pin(self) -> None:
        catalog = load_catalog(ROOT / "config/upstream-skills.json", ROOT / "skills/registry.yml")
        pbt = catalog.skills["trailofbits.property-based-testing"]
        source = catalog.sources[pbt.source]
        self.assertEqual(source.license, "CC-BY-SA-4.0")
        self.assertEqual(source.skill_roots, ("plugins/property-based-testing/skills",))
        self.assertEqual(pbt.path, source.skill_roots[0] + "/property-based-testing")
        self.assertEqual(source.revision, "82fe8226252622fa807643bdca1710901198553a")
        handoff = catalog.skills["pocock.handoff"]
        previous = catalog.skills["pocock.grill-me"]
        self.assertEqual(handoff.source, previous.source)
        self.assertEqual(
            catalog.sources[handoff.source].revision,
            "d81f3a183412e71a5b1e84ca21bc1a35eea03a60",
        )
        compression = catalog.skills["context.context-compression"]
        self.assertEqual(catalog.sources[compression.source].license, "MIT")
        self.assertEqual(
            catalog.sources[compression.source].revision,
            "58b55a8921758d13453b440704fb1b5b208c0b0e",
        )
        for skill in (pbt, handoff, compression):
            self.assertEqual(skill.requires, ())
            self.assertEqual(skill.required_tools, ())

    def test_profile_requirements_reject_unknown_groups_and_dependencies(self) -> None:
        header = (
            "version: 3\ndefault_groups:\n  - core\ngroups:\n  core:\n    - owner\n"
            "optional:\nupstream:\n  author:\n    - author.sample\nupstream_required:\n"
        )
        path = self.root / "registry.yml"
        for bad in ["  missing:\n    - author.sample\n", "  core:\n    - unknown\n"]:
            path.write_text(header + bad)
            with self.assertRaises(registry.RegistryError):
                registry.parse_registry(path)
        path.write_text(header + "  core:\n    - author.sample\n")
        parsed = registry.parse_registry(path)
        self.assertEqual(
            registry.selected_upstream_skills(parsed, groups=[], include_all=False),
            ["author.sample"],
        )
        with self.assertRaises(registry.RegistryError):
            registry.selected_upstream_skills(parsed, groups=["missing"], include_all=False)


if __name__ == "__main__":
    unittest.main()
