from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts import registry


ROOT = Path(__file__).resolve().parents[1]


class RegistryDocumentationTests(unittest.TestCase):
    def test_repository_generated_blocks_are_current(self) -> None:
        self.assertEqual(registry.validate_generated_docs(ROOT), [])

    def test_generated_block_drift_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "skills").mkdir()
            (root / "skills" / "registry.yml").write_text(
                "version: 1\n"
                "default_groups:\n"
                "  - core\n"
                "groups:\n"
                "  core:\n"
                "    - sample\n"
                "optional:\n",
                encoding="utf-8",
            )
            for name in registry.GENERATED_DOCS:
                (root / name).write_text(
                    f"{registry.GENERATED_BEGIN}\nwrong\n{registry.GENERATED_END}\n",
                    encoding="utf-8",
                )

            issues = registry.validate_generated_docs(root)

        self.assertEqual(len(issues), len(registry.GENERATED_DOCS))
        self.assertTrue(all("generated skill registry block is stale" in issue for issue in issues))

    def test_update_generated_docs_preserves_surrounding_text(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "skills").mkdir()
            (root / "skills" / "registry.yml").write_text(
                "version: 1\n"
                "default_groups:\n"
                "  - core\n"
                "groups:\n"
                "  core:\n"
                "    - sample\n"
                "optional:\n",
                encoding="utf-8",
            )
            for name in registry.GENERATED_DOCS:
                (root / name).write_text(
                    f"before\n{registry.GENERATED_BEGIN}\nstale\n{registry.GENERATED_END}\nafter\n",
                    encoding="utf-8",
                )

            registry.update_generated_docs(root)

            for name in registry.GENERATED_DOCS:
                text = (root / name).read_text(encoding="utf-8")
                self.assertTrue(text.startswith("before\n"))
                self.assertTrue(text.endswith("after\n"))
                self.assertIn("`sample`", text)

    def test_generated_block_preserves_default_group_order(self) -> None:
        rendered = registry.render_generated_block(
            {
                "version": 1,
                "default_groups": ["second", "first"],
                "groups": {"first": ["alpha"], "second": ["beta"]},
                "optional": {},
            },
            default_heading="Defaults",
            optional_heading="Optional",
        )

        self.assertLess(rendered.index("**second:**"), rendered.index("**first:**"))


if __name__ == "__main__":
    unittest.main()
