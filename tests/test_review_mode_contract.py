from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReviewModePolicyTests(unittest.TestCase):
    """Check packaged instructions, not live model execution or identity."""

    def text(self, relative: str) -> str:
        return " ".join((ROOT / relative).read_text(encoding="utf-8").split())

    def test_every_prompt_defaults_to_current_model_with_separate_task_modes(self) -> None:
        for profile in ("steady", "full", "minimal", "fast"):
            with self.subTest(profile=profile):
                text = self.text(f"instructions/global/{profile}.md")
                self.assertIn(
                    "Default: keep the current selected model; multimodel and quorum are off.",
                    text,
                )
                self.assertIn("`/multimodel`", text)
                self.assertIn("`/quorum`", text)
                self.assertIn("continuations", text)
                self.assertIn("completion", text)
                self.assertIn("replacement", text)
                self.assertIn("Same-model", text)
                self.assertRegex(text, r"Quot(?:ed|es)")
                self.assertNotIn("For delegated code, select verified budget models", text)
                if profile == "minimal":
                    self.assertIn("no voting", text)
                    self.assertIn("no budget author", text)
                    self.assertIn("permissions unchanged", text)
                else:
                    self.assertIn("it does not enable voting", text)
                    self.assertIn("it does not enable budget implementation", text)
                    self.assertIn("Use both commands for both modes", text)
                    self.assertIn("generic quality, risk or review requests", text)
                    self.assertIn("do not grant source export", text)

    def test_routes_and_merge_rules_do_not_enable_implicit_voting(self) -> None:
        for relative in (
            "skills/agent-squad/SKILL.md",
            "skills/specialist-dispatch/SKILL.md",
            "skills/multi-agent-pr-review/SKILL.md",
        ):
            with self.subTest(path=relative):
                text = self.text(relative)
                self.assertIn("Default: keep the current selected model", text)
                self.assertIn("`/multimodel`", text)
                self.assertIn("`/quorum`", text)
                self.assertIn("Same-model", text)
        review = self.text("skills/multi-agent-pr-review/SKILL.md")
        merge = self.text("skills/subagent-result-merge/SKILL.md")
        self.assertIn("Without `/quorum`, merge findings without votes", review)
        self.assertIn("Without `/quorum`, merge findings without votes", merge)
        self.assertIn("Only when `/quorum` is active", merge)
        self.assertIn("author's model unchanged", self.text("tests/router-cases.yml"))

    def test_canonical_contract_keeps_commands_independent_and_permissions_bounded(self) -> None:
        text = self.text("docs/cross-provider-review.md")
        for phrase in (
            "## Explicit Activation",
            "`/multimodel <task>`",
            "`/quorum <task>`",
            "`/multimodel /quorum <task>`",
            "`/multimodel` never implies `/quorum`",
            "`/quorum` never implies the budget-author workflow",
            "Same-model parallel agents",
            "better quality, security review",
            "an instruction about the commands are not activation",
            "a new task starts with both modes off",
            "does not create a new task",
            "do not persist a global enable flag",
            "not registered native app slash-menu entries",
            "offline `worker-evidence.py quorum`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn("Live voting is off by default", self.text("docs/worker-quorum.md"))

    def test_checkpoint_and_public_examples_preserve_explicit_task_selection(self) -> None:
        checkpoint = self.text("templates/task-resume-checkpoint.md")
        self.assertIn("Active `/multimodel` / `/quorum` commands (default off)", checkpoint)
        self.assertIn("task scope and direct user authorization", checkpoint)
        for relative in ("README.md", "README.ru.md", "templates/agent-implementation-prompt.md"):
            with self.subTest(path=relative):
                text = self.text(relative)
                self.assertIn("`/multimodel", text)
                self.assertIn("`/quorum", text)


if __name__ == "__main__":
    unittest.main()
