from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from scripts import registry
from scripts.upstream_catalog import load_catalog
from scripts.upstream_skills import SkillManager


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "business_ui_installer", ROOT / "scripts" / "installer_core.py"
)
assert SPEC is not None and SPEC.loader is not None
installer_core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer_core
SPEC.loader.exec_module(installer_core)


class BusinessUIIntegrationTests(unittest.TestCase):
    def test_profile_and_brief_are_in_the_actual_installer_projection(self) -> None:
        parsed = registry.load_registry(ROOT)
        skills = registry.selected_skills(parsed, groups=[], include_all=False)
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            options = installer_core.InstallerOptions(
                repo_root=ROOT,
                codex_home=home / "codex",
                agents_home=home / "agents",
                be_home=home / "bible",
                bin_dir=home / "bin",
                dry_run=True,
                backup_only=False,
                no_overwrite=False,
                force=False,
                diff=False,
                groups=[],
                all_groups=False,
                install_tools=False,
                migrate_legacy=False,
                prompt_profile="steady",
                backup_dir=home / "backup",
            )
            files = {
                (item.root, item.path): item
                for item in installer_core.build_desired_files(options, skills)
            }
            profile = files[("codex_home", "skills/ui-business-apps/SKILL.md")]
            brief = files[("be_home", "current/templates/business-ui-brief.md")]
            self.assertEqual(
                profile.content, (ROOT / "skills/ui-business-apps/SKILL.md").read_bytes()
            )
            self.assertEqual(brief.content, (ROOT / "templates/business-ui-brief.md").read_bytes())
            for name in ("interface-design", "ui-ux-pro-max", "impeccable"):
                self.assertFalse(
                    any(
                        root == "codex_home" and path.startswith(f"skills/{name}/")
                        for root, path in files
                    )
                )
            self.assertFalse((home / "codex").exists())

    def test_business_intents_resolve_author_paths_without_setup_or_mutation(self) -> None:
        catalog = load_catalog(ROOT / "config/upstream-skills.json")
        expected = {
            "crm-workspace-design": "interface.interface-design",
            "business-ui-pattern-research": "uipro.ui-ux-pro-max",
            "business-ui-critique": "impeccable.impeccable",
            "ui-hardening": "impeccable.impeccable",
        }
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            manager = SkillManager(catalog, home / "bible", home / "skills")
            for intent, identity in expected.items():
                with self.subTest(intent=intent):
                    route = manager.route(intent)
                    self.assertEqual(route["skill_id"], identity)
                    self.assertEqual(
                        route["path"], str(home / "skills" / catalog.skills[identity].name)
                    )
                    self.assertEqual(route["status"], "unavailable")
                    self.assertEqual(route["exposure"], "unverified")
            self.assertFalse((home / "bible").exists())
            self.assertFalse((home / "skills").exists())


if __name__ == "__main__":
    unittest.main()
