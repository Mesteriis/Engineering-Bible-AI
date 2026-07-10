from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SteadyProfileContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_steady_profile_has_continuation_fast_path(self) -> None:
        text = self.read("instructions/global/steady.md")

        self.assertIn("Continuation Fast Path", text)
        self.assertIn("Do not route the request again", text)
        self.assertIn("Do not reread an unchanged `SKILL.md`", text)
        self.assertIn("Reuse current-session capability metadata", text)

    def test_steady_profile_uses_direct_leaf_selection(self) -> None:
        text = self.read("instructions/global/steady.md")

        self.assertIn("select the narrowest leaf skill directly", text)
        self.assertIn("one primary skill and at most one supporting skill", text)
        self.assertNotIn("Mandatory Routing", text)
        self.assertNotIn("For every non-trivial engineering request", text)

    def test_minimal_profile_uses_steady_routing_not_mandatory_routing(self) -> None:
        text = self.read("instructions/global/minimal.md")

        self.assertIn("Continuation Fast Path", text)
        self.assertNotIn("Mandatory Routing", text)
        self.assertNotIn("invoke `workflow-router`", text)

    def test_full_profile_keeps_strict_initial_routing_but_reuses_it(self) -> None:
        text = self.read("instructions/global/full.md")

        self.assertIn("Initial Task Routing", text)
        self.assertIn("Invoke `workflow-router` first", text)
        self.assertIn("Continuation Fast Path", text)
        self.assertIn("Do not invoke `workflow-router` again", text)
        self.assertIn("Reuse current-session capability metadata", text)
        self.assertNotIn("For every non-trivial engineering request", text)

    def test_repository_agents_uses_direct_routing(self) -> None:
        text = self.read("AGENTS.md")

        self.assertIn("Continuation Fast Path", text)
        self.assertNotIn("Mandatory Routing", text)
        self.assertNotIn("For every non-trivial engineering request", text)

    def test_workflow_router_keeps_common_path_small(self) -> None:
        skill = self.read("skills/workflow-router/SKILL.md")
        routes = self.read("skills/workflow-router/references/routes.md")

        self.assertLess(len(skill), 3500)
        self.assertIn("same-task follow-up", skill)
        self.assertIn("Do not reread", skill)
        self.assertIn("security-router", routes)
        self.assertIn("ui-router", routes)
        self.assertIn("mcp-tool-router", routes)
        self.assertIn("session-memory", routes)
        self.assertIn("quality-gates", routes)
        self.assertIn("quick-fix", routes)
        self.assertIn(".serena/", routes)
        self.assertIn("context-mode upgrade", routes)
        self.assertIn("discussion-mode: active", routes)
        self.assertIn("final confirmation", routes)

    def test_mcp_router_reuses_session_metadata(self) -> None:
        skill = self.read("skills/mcp-tool-router/SKILL.md")
        adapter = self.read("skills/mcp-tool-router/references/host-adapter.md")

        self.assertLess(len(skill), 3000)
        self.assertIn("Do not refresh", skill)
        self.assertIn("ordinary local repository work", skill)
        self.assertIn("at most eight", skill)
        self.assertIn("first three", skill)
        self.assertIn("Host Adapter Contract", adapter)
        self.assertIn("be mcp refresh", adapter)

    def test_installed_routing_healthcheck_accepts_every_supported_profile(self) -> None:
        script = self.read("skills/workflow-router/scripts/validate-routing.sh")

        self.assertIn("## Skill Selection", script)
        self.assertIn("## Initial Task Routing", script)
        self.assertIn("## Routing Discipline", script)


if __name__ == "__main__":
    unittest.main()
