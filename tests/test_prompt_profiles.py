from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


install_codex = load_script("install_codex_profiles_under_test", "install_codex.py")
installer_core = load_script("installer_core_profiles_under_test", "installer_core.py")
be = load_script("be_profiles_under_test", "be.py")


class PromptProfileTests(unittest.TestCase):
    def make_options(self, root: Path, profile: str) -> object:
        return installer_core.InstallerOptions(
            repo_root=ROOT,
            codex_home=root / "codex",
            agents_home=root / "agents",
            be_home=root / "engineering-bible",
            bin_dir=root / "bin",
            dry_run=True,
            backup_only=False,
            no_overwrite=False,
            force=False,
            diff=False,
            groups=[],
            all_groups=False,
            install_tools=False,
            migrate_legacy=False,
            prompt_profile=profile,
            backup_dir=root / "backups",
        )

    def test_local_installer_defaults_to_steady(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            env = {
                "CODEX_HOME": str(root / "codex"),
                "AGENTS_HOME": str(root / "agents"),
                "ENGINEERING_BIBLE_HOME": str(root / "engineering-bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(root / "bin"),
            }
            with mock.patch.dict(os.environ, env, clear=False):
                args = install_codex.parse_args([])
                options = install_codex.build_options(args)

        self.assertIsNone(args.prompt_profile)
        self.assertEqual(options.prompt_profile, "steady")

    def test_be_install_defers_default_for_manifest_aware_resolution(self) -> None:
        args = be.build_parser().parse_args(["install"])

        self.assertIsNone(args.prompt_profile)

    def test_steady_profile_uses_full_default_skill_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            options = self.make_options(Path(raw), "steady")

            skills = install_codex.selected_skill_names(options)

        self.assertIn("workflow-router", skills)
        self.assertIn("python", skills)
        self.assertIn("security-diff-review", skills)
        self.assertIn("ui-router", skills)
        self.assertNotIn("fast", skills)
        self.assertNotIn("code-wiki-ru", skills)

    def test_prompt_source_resolves_steady_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            options = self.make_options(Path(raw), "steady")

            source = installer_core.prompt_source(options)

        self.assertEqual(source, ROOT / "instructions" / "global" / "steady.md")

    def test_manifest_selection_accepts_steady_and_preserves_full(self) -> None:
        steady = {
            "groups": {
                "requested": [],
                "include_all": False,
                "prompt_profile": "steady",
            }
        }
        full = {
            "groups": {
                "requested": [],
                "include_all": False,
                "prompt_profile": "full",
            }
        }

        self.assertEqual(be.manifest_install_selection(steady)[2], "steady")
        self.assertEqual(be.manifest_install_selection(full)[2], "full")

    def test_manifest_round_trip_records_steady_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            options = self.make_options(root, "steady")
            registry = {"default_groups": [], "groups": {}, "optional": {}}

            manifest = installer_core.build_manifest(
                options,
                desired_files=[],
                actions=[],
                registry=registry,
                skills=[],
                previous=None,
            )
            serialized = json.loads(json.dumps(manifest))

        self.assertEqual(serialized["groups"]["prompt_profile"], "steady")


if __name__ == "__main__":
    unittest.main()
