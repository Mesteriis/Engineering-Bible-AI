import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "workflow-router" / "scripts" / "validate-routing.sh"
FALLBACK_SKILLS = (
    "workflow-router",
    "engineering-standards",
    "review-router",
    "security-router",
    "ui-router",
    "ui-research",
    "ui-build",
    "ui-figma",
    "ui-qa",
)


class HostManagedRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        codex = self.home / ".codex"
        for skill in FALLBACK_SKILLS:
            (codex / "skills" / skill).mkdir(parents=True)
            (codex / "skills" / skill / "SKILL.md").write_text(f"---\nname: {skill}\n---\n")
        (codex / "AGENTS.md").write_text("## Skill Selection\nUse workflow-router.\n")
        (self.home / ".agents" / "engineering").mkdir(parents=True)
        (self.home / ".agents" / "engineering" / "README.md").write_text("index\n")
        # A host that manages Claude's skills leaves this root without Bible skills.
        (self.home / ".claude" / "skills").mkdir(parents=True)

    def run_script(self, **extra: str) -> subprocess.CompletedProcess[str]:
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.home),
            "ENGINEERING_BIBLE_HOME": str(self.home / "no-package"),
            **extra,
        }
        return subprocess.run(
            ["bash", str(SCRIPT), "--all-agents"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_unmanaged_provider_root_without_bible_skills_fails(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing", result.stderr)
        self.assertIn(".claude/skills", result.stderr)

    def test_host_managed_provider_is_reported_as_skip(self) -> None:
        result = self.run_script(ENGINEERING_BIBLE_HOST_MANAGED="claude")
        self.assertIn("SKIP: claude skills and instructions are managed by the host", result.stderr)
        # Later checks need an installed package; the Claude root must not be the failure.
        self.assertNotIn(".claude", result.stderr.replace("SKIP: claude", ""))

    def test_unknown_host_managed_provider_is_rejected(self) -> None:
        result = self.run_script(ENGINEERING_BIBLE_HOST_MANAGED="claude,unknown")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown host-managed provider: unknown", result.stderr)


if __name__ == "__main__":
    unittest.main()
