from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-skill-frontmatter.py"
SPEC = importlib.util.spec_from_file_location("skill_frontmatter_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
skill_frontmatter = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = skill_frontmatter
SPEC.loader.exec_module(skill_frontmatter)


class SkillFrontmatterTests(unittest.TestCase):
    def make_skill(self, root: Path, directory: str, *, name: str, description: str) -> Path:
        skill_dir = root / directory
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f'---\nname: {name}\ndescription: "{description}"\n---\n\n# Skill\n',
            encoding="utf-8",
        )
        return skill_dir

    def test_rejects_branded_name_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill_dir = self.make_skill(
                Path(raw),
                "sample-skill",
                name="[be] sample-skill",
                description="Use for a sample task.",
            )

            errors = skill_frontmatter.validate_skill(skill_dir)

        self.assertTrue(any("invalid skill name" in error for error in errors), errors)

    def test_rejects_uppercase_name_even_when_directory_matches(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill_dir = self.make_skill(
                Path(raw),
                "SampleSkill",
                name="SampleSkill",
                description="Use for a sample task.",
            )

            errors = skill_frontmatter.validate_skill(skill_dir)

        self.assertTrue(any("invalid skill name" in error for error in errors), errors)

    def test_rejects_consecutive_hyphens(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill_dir = self.make_skill(
                Path(raw),
                "sample--skill",
                name="sample--skill",
                description="Use for a sample task.",
            )

            errors = skill_frontmatter.validate_skill(skill_dir)

        self.assertTrue(any("invalid skill name" in error for error in errors), errors)

    def test_requires_exact_directory_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill_dir = self.make_skill(
                Path(raw),
                "sample-skill",
                name="other-skill",
                description="Use for a sample task.",
            )

            errors = skill_frontmatter.validate_skill(skill_dir)

        self.assertTrue(any("does not match directory" in error for error in errors), errors)

    def test_accepts_description_at_1024_character_limit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill_dir = self.make_skill(
                Path(raw),
                "sample-skill",
                name="sample-skill",
                description="x" * 1024,
            )

            errors = skill_frontmatter.validate_skill(skill_dir)

        self.assertEqual(errors, [])

    def test_rejects_description_over_1024_characters(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill_dir = self.make_skill(
                Path(raw),
                "sample-skill",
                name="sample-skill",
                description="x" * 1025,
            )

            errors = skill_frontmatter.validate_skill(skill_dir)

        self.assertTrue(any("1024" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
