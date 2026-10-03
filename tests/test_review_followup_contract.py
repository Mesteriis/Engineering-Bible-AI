from __future__ import annotations

from pathlib import Path
import unittest

from scripts import registry


ROOT = Path(__file__).resolve().parents[1]


class ReviewFollowupContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_narrow_skills_are_registered_in_correct_groups(self) -> None:
        groups = registry.group_map(registry.load_registry(ROOT), include_optional=True)
        self.assertIn("mobile-qa", groups["ui"])
        self.assertIn("wiki-query", groups["optional.wiki"])

    def test_wiki_query_is_compact_read_only_and_evidence_based(self) -> None:
        text = self.read("skills/wiki-query/SKILL.md")
        self.assertLessEqual(len(text.encode("utf-8")), 3500)
        for phrase in ("read-only", "source", "stale", "QMD", "code-wiki-ru", "output"):
            self.assertIn(phrase, text)
        self.assertIn("Do not rebuild indexes", text)
        self.assertNotIn("build_repo_index.py", text)
        self.assertNotIn("plan_wiki_update.py", text)

    def test_wiki_builder_and_reference_both_preserve_worker_boundary(self) -> None:
        for path in (
            "skills/code-wiki-ru/SKILL.md",
            "skills/code-wiki-ru/references/opencode-deepseek.md",
        ):
            with self.subTest(path=path):
                text = self.read(path)
                self.assertNotIn('--dir "$REPO_ROOT"', text)
                self.assertNotIn('"$(cat', text)
                self.assertNotIn("deepseek/deepseek-", text)
                self.assertIn("stdin", text)
                self.assertIn("subagent-result-merge", text)

    def test_mobile_qa_separates_device_scope_actions_and_assertions(self) -> None:
        text = self.read("skills/mobile-qa/SKILL.md")
        for phrase in (
            "device",
            "expected state",
            "accessibility",
            "screenshot",
            "physical",
            "secrets",
            "batch",
            "telemetry",
            "SKIP",
            "host",
        ):
            self.assertIn(phrase, text)
        router = self.read("skills/ui-qa/SKILL.md")
        self.assertIn("Native Android/iOS", router)
        self.assertIn("mobile-qa", router)

    def test_renderer_is_optional_and_does_not_establish_source_truth(self) -> None:
        text = self.read("skills/architecture-map/SKILL.md")
        self.assertIn("Archify", text)
        self.assertIn("optional", text)
        self.assertIn("does not prove", text)
        self.assertIn("source", text)

    def test_external_audit_checks_takeover_transport_and_tool_composition(self) -> None:
        text = self.read("skills/external-agent-pack-audit/SKILL.md")
        for phrase in ("AGENTS.md", "CLAUDE.md", "host-key", "fallback", "telemetry", "batch"):
            self.assertIn(phrase, text)

    def test_compact_data_experiment_preserves_canonical_json_and_types(self) -> None:
        text = " ".join(self.read("skills/context-pack/SKILL.md").split())
        for phrase in (
            "canonical JSON",
            "round-trip",
            "format instructions",
            "nested",
            "tokenizer",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
