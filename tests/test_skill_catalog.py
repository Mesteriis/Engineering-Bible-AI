from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-skill-frontmatter.py"
SPEC = importlib.util.spec_from_file_location("skill_catalog_metadata", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
metadata_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = metadata_module
SPEC.loader.exec_module(metadata_module)


class SkillCatalogTests(unittest.TestCase):
    def skills(self) -> list[Path]:
        return sorted((ROOT / "skills").glob("*/SKILL.md"))

    def test_catalog_keeps_all_registered_skill_directories(self) -> None:
        self.assertEqual(len(self.skills()), 60)

    def test_all_skill_names_are_exact_and_spec_compliant(self) -> None:
        errors: list[str] = []
        for skill_file in self.skills():
            errors.extend(metadata_module.validate_skill(skill_file.parent))

        self.assertEqual(errors, [])

    def test_description_catalog_stays_within_steady_state_budget(self) -> None:
        descriptions = [
            metadata_module.parse_frontmatter(skill_file)["description"]
            for skill_file in self.skills()
        ]

        self.assertLessEqual(sum(map(len, descriptions)), 7200)
        self.assertLessEqual(max(map(len, descriptions)), 240)

    def test_generic_skills_define_negative_trigger_boundaries(self) -> None:
        generic = {
            "workflow-router",
            "mcp-tool-router",
            "core-engineering",
            "engineering-standards",
            "architecture-principles",
            "code-quality",
            "quality-gates",
            "tdd-guard",
            "karpathy-guidelines",
        }
        missing: list[str] = []
        for name in sorted(generic):
            description = metadata_module.parse_frontmatter(ROOT / "skills" / name / "SKILL.md")[
                "description"
            ].lower()
            if not any(marker in description for marker in ("do not", "not for", "only when")):
                missing.append(name)

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
