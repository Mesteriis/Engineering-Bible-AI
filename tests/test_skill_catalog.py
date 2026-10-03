from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

from scripts import registry


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
        registered = set(registry.all_registered_skills(registry.load_registry(ROOT)))
        self.assertEqual({path.parent.name for path in self.skills()}, registered)

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
        }
        missing: list[str] = []
        for name in sorted(generic):
            description = metadata_module.parse_frontmatter(ROOT / "skills" / name / "SKILL.md")[
                "description"
            ].lower()
            if not any(marker in description for marker in ("do not", "not for", "only when")):
                missing.append(name)

        self.assertEqual(missing, [])

    def test_absorbed_workflows_are_thin_author_routes(self) -> None:
        providers = {
            "debugging": "superpowers.systematic-debugging",
            "testing-tdd": "superpowers.test-driven-development",
            "code-review": "superpowers.requesting-code-review",
        }
        upstream = registry.cast_dict(registry.load_registry(ROOT)["upstream"])
        registered = {skill for group in upstream.values() for skill in registry.cast_list(group)}
        for name, provider in providers.items():
            with self.subTest(alias=name):
                text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(text.split())
                self.assertLess(len(text.encode("utf-8")), 1800)
                self.assertIn(provider, registered)
                self.assertIn(f"Provider: `{provider}`", normalized)
                self.assertIn("complete `SKILL.md`", normalized)
                self.assertIn("no replacement", normalized)
                self.assertIn("author tree unchanged", normalized)
                self.assertNotIn("## Workflow", text)

    def test_owner_gates_and_worker_policy_load_original_workflows(self) -> None:
        for name, provider in (
            ("quality-gates", "superpowers.verification-before-completion"),
            ("tdd-guard", "superpowers.test-driven-development"),
            ("agent-squad", "superpowers.dispatching-parallel-agents"),
            ("specialist-dispatch", "superpowers.subagent-driven-development"),
        ):
            with self.subTest(policy=name):
                text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(provider, text)
                self.assertIn("complete", text)
                self.assertIn("policy", text)

    def test_native_ui_routes_require_complete_current_author_providers(self) -> None:
        for name in ("ui-router", "ui-build", "ui-research", "ui-figma", "ui-qa"):
            with self.subTest(router=name):
                text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(text.split()).lower()
                self.assertIn("complete", normalized)
                self.assertIn("current", normalized)
                self.assertIn("native", normalized)
                self.assertIn("exposure", normalized)
        build = (ROOT / "skills/ui-build/SKILL.md").read_text(encoding="utf-8")
        research = (ROOT / "skills/ui-research/SKILL.md").read_text(encoding="utf-8")
        qa = (ROOT / "skills/ui-qa/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("build-web-apps:frontend-app-builder", build)
        self.assertIn("product-design:audit", research)
        self.assertNotIn("design-taste-frontend", build)
        self.assertNotIn("lazyweb-deep-design-research", research)
        self.assertNotIn("principal-review", qa)

    def test_core_engineering_routes_shared_context_tools_by_role(self) -> None:
        text = (ROOT / "skills" / "core-engineering" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("### Context Tooling Tiers", text)
        self.assertIn("| Local edit or literal | `rg`", text)
        self.assertIn("| Definitions and references | Serena", text)
        self.assertIn("| Architecture and impact | Graphify", text)
        self.assertIn("| Documentation and ADRs | QMD", text)
        self.assertIn("Repomix is an export, not a live code index", text)


if __name__ == "__main__":
    unittest.main()
