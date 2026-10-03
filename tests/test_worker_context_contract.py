from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import re
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "worker_context_installer", ROOT / "scripts" / "installer_core.py"
)
assert SPEC is not None and SPEC.loader is not None
installer_core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer_core
SPEC.loader.exec_module(installer_core)


class WorkerContextContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_local_search_does_not_require_graph_bootstrap(self) -> None:
        steady = self.read("instructions/global/steady.md")
        minimal = self.read("instructions/global/minimal.md")
        core = self.read("skills/core-engineering/SKILL.md")
        for text in (steady, minimal, core):
            with self.subTest(profile=text.splitlines()[0]):
                self.assertIn("Local edit or literal", text)
                self.assertIn("Definitions and references", text)
                self.assertIn("Architecture and impact", text)
                self.assertIn("Documentation and ADRs", text)
                self.assertIn("External library documentation", text)
                self.assertIn("Dependency source", text)
                self.assertIn("Worker handoff", text)
                self.assertNotIn("graph first for structure", text)
                self.assertIn("Do not run every search tool", text)
        for tool in ("Serena", "Graphify", "QMD", "Context7", "opensrc", "Repomix"):
            self.assertIn(tool, core)

    def test_steady_and_minimal_use_the_same_question_specific_discovery_routes(self) -> None:
        expected = {
            "Local edit or literal": "`rg` and targeted text search, then bounded reads",
            "Definitions and references": "Session-exposed LSP-backed symbolic navigation",
            "Architecture and impact": "Fresh code knowledge graph; confirm against source",
            "Documentation and ADRs": "Scoped local document search",
            "External library documentation": "Version-matched documentation retrieval",
            "Dependency source": "Scoped dependency-source retrieval",
            "Worker handoff": "Explicitly allowed context pack; export only required files",
        }
        for profile in ("steady", "minimal"):
            text = self.read(f"instructions/global/{profile}.md")
            section = text.split("## Context-Efficient Code Discovery\n", 1)[1]
            section = section.split("\n## ", 1)[0]
            routes = dict(re.findall(r"^\| ([^|]+?) \| ([^|]+?) \|$", section, re.MULTILINE))
            routes.pop("Need", None)
            routes.pop("---", None)
            with self.subTest(profile=profile):
                self.assertEqual(routes, expected)

    def test_checkpoint_packaging_preserves_public_template_and_excludes_private_state(
        self,
    ) -> None:
        public_files = (
            "templates/task-resume-checkpoint.md",
            "docs/task-continuation.md",
            "templates/agent-implementation-prompt.md",
            "instructions/global/minimal.md",
            "skills/registry.yml",
        )
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            package = home / "source"
            for relative in public_files:
                target = package / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            private_checkpoint = package / ".engineering-bible/checkpoints/task.md"
            private_checkpoint.parent.mkdir(parents=True)
            private_checkpoint.write_text("Private task state fixture", encoding="utf-8")
            options = installer_core.InstallerOptions(
                repo_root=package,
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
                prompt_profile="minimal",
                backup_dir=home / "backup",
            )
            files = {
                (item.root, item.path): item
                for item in installer_core.build_desired_files(options, [])
            }
            for relative in public_files[:3]:
                with self.subTest(path=relative):
                    installed = files[("be_home", f"current/{relative}")]
                    self.assertEqual(installed.content, (ROOT / relative).read_bytes())
            self.assertEqual(
                files[("codex_home", "AGENTS.md")].content,
                (ROOT / "instructions/global/minimal.md").read_bytes(),
            )
            self.assertFalse(any(".engineering-bible/" in path for _, path in files))
            self.assertFalse((home / "codex").exists())

    def test_install_prompt_reserves_routing_for_ambiguous_or_mixed_tasks(self) -> None:
        text = self.read("templates/agent-implementation-prompt.md")
        self.assertNotIn("обязательной точкой входа", text)
        self.assertIn("самый узкий leaf skill", text)
        self.assertIn("неоднозначных или смешанных задач", text)
        self.assertIn("без повторного роутинга", text)

    def test_index_freshness_includes_uncommitted_changes(self) -> None:
        for relative in (
            "instructions/global/steady.md",
            "instructions/global/minimal.md",
            "skills/core-engineering/SKILL.md",
            "skills/context-pack/SKILL.md",
        ):
            with self.subTest(path=relative):
                text = self.read(relative)
                self.assertIn("uncommitted", text)
                self.assertIn("stale", text)
                self.assertRegex(text, r"hash|fingerprint")

    def test_raw_command_failure_survives_compression(self) -> None:
        text = self.read("skills/core-engineering/SKILL.md")
        self.assertIn("original command's exit code", text)
        self.assertIn("before any filter", text)
        self.assertIn("nonzero test exit remains FAIL", text)
        self.assertIn("intentionally failing test", text)
        self.assertIn("Distill is not sole evidence", text)

    def test_worker_record_separates_requested_and_observed_route(self) -> None:
        text = self.read("skills/subagent-result-merge/SKILL.md")
        block = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        self.assertIsNotNone(block, "result contract must provide a parseable record")
        assert block is not None
        record = json.loads(block.group(1))
        self.assertEqual(
            set(record),
            {
                "task_id",
                "goal",
                "base_commit",
                "snapshot",
                "requested",
                "observed",
                "status",
                "findings",
                "checks",
                "artifacts",
                "open_questions",
                "usage",
            },
        )
        self.assertEqual(set(record["snapshot"]), {"state", "sha256", "files"})
        self.assertEqual(set(record["requested"]), {"provider", "model"})
        self.assertEqual(set(record["observed"]), {"provider", "model", "source", "verification"})
        self.assertEqual(record["observed"]["provider"], "unknown")
        self.assertEqual(record["observed"]["model"], "unknown")
        self.assertEqual(record["usage"], "unknown")
        self.assertEqual(record["status"], "blocked")
        self.assertIn("completed / blocked / failed", text)
        self.assertIn("file_line", text)
        self.assertIn("exit_code", text)
        self.assertIn("raw_artifact", text)
        self.assertIn("Self-description", text)
        self.assertIn("independent proof", text)

    def test_external_workers_have_roles_and_enforced_scope(self) -> None:
        dispatch = self.read("skills/specialist-dispatch/SKILL.md")
        squad = self.read("skills/agent-squad/SKILL.md")
        boundary = self.read("docs/worker-runtime-boundary.md")
        for role in ("scout", "reviewer", "tests-docs", "local-helper"):
            self.assertIn(role, dispatch)
        for phrase in (
            "not a security sandbox",
            "No recursive delegation",
            "two external workers",
            "one local inference process",
            "five minutes",
            "one retry",
        ):
            self.assertIn(phrase, squad)
        self.assertIn("No hidden fallback", dispatch)
        self.assertIn("parent-to-worker", boundary)
        self.assertIn("canary", boundary)
        self.assertIn("approval-bypass", boundary)

    def test_context_pack_has_explicit_export_scope(self) -> None:
        text = self.read("skills/context-pack/SKILL.md")
        for phrase in (
            "explicit allowlist",
            "symlinks",
            "parent environment",
            "base commit",
            "sha256",
            "bytes",
            "not permission to export",
        ):
            self.assertIn(phrase, text)

    def test_wiki_does_not_launch_with_repo_cwd_or_prompt_argv(self) -> None:
        text = self.read("skills/code-wiki-ru/references/opencode-deepseek.md")
        self.assertNotIn('"$(cat', text)
        self.assertNotIn('--dir "$REPO_ROOT"', text)
        self.assertNotIn("deepseek/deepseek-", text)
        self.assertIn("Do not ask DeepSeek to apply patches", text)
        self.assertIn("stdin", text)
        self.assertIn("BLOCKED", text)
        self.assertIn("subagent-result-merge", text)

    def test_memory_separates_durable_facts_from_runtime_evidence(self) -> None:
        text = self.read("skills/session-memory/SKILL.md")
        for phrase in (
            "Beads",
            "QMD",
            "outside tracked files",
            "raw artifact",
            "exit code",
            "source revision",
            "not a verified route",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
