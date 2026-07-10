from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "scripts" / "be.py"


class ExtendedBeCliTests(unittest.TestCase):
    def run_be(
        self,
        *args: str,
        tmp: Path,
        stdin: str | None = None,
        path: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CODEX_HOME": str(tmp / "codex"),
                "AGENTS_HOME": str(tmp / "agents"),
                "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
            }
        )
        if path is not None:
            env["PATH"] = path
        return subprocess.run(
            [sys.executable, str(BE), *args],
            cwd=ROOT,
            env=env,
            input=stdin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_mcp_commands_use_runtime_metadata_without_known_tool_names(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            repo = tmp / "repo"
            (repo / ".git" / "info").mkdir(parents=True)
            runtime_id = "runtime_" + "7f1c2b9a"
            payload = {
                "schema_version": 1,
                "source_id": "current-session",
                "status": "online",
                "tools": [
                    {
                        "selector": runtime_id,
                        "display_name": runtime_id,
                        "description": "Read local project documentation",
                        "available": True,
                        "annotations": {
                            "read_only": True,
                            "destructive": False,
                            "open_world": False,
                            "scope": "local",
                        },
                        "input_schema": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                        },
                    }
                ],
            }

            refresh = self.run_be(
                "mcp",
                "refresh",
                "--repo",
                str(repo),
                "--json",
                tmp=tmp,
                stdin=json.dumps(payload),
            )
            status = self.run_be("mcp", "status", "--repo", str(repo), "--json", tmp=tmp)
            candidates = self.run_be(
                "mcp",
                "candidates",
                "--repo",
                str(repo),
                "--task-stdin",
                "--json",
                tmp=tmp,
                stdin="read project documentation",
            )
            self.assertEqual(candidates.returncode, 0, candidates.stderr)
            candidate_payload = json.loads(candidates.stdout)
            opaque_id = candidate_payload[0]["runtime_id"]
            show = self.run_be("mcp", "show", opaque_id, "--json", tmp=tmp)

        for result in (refresh, status, candidates, show):
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(status.stdout)["status"], "online")
        self.assertEqual(candidate_payload[0]["selector"], runtime_id)
        self.assertEqual(json.loads(show.stdout)["selector"], runtime_id)

    def test_tools_plan_has_stable_json_without_package_managers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be(
                "tools",
                "plan",
                "--tool",
                "ty",
                "--json",
                tmp=Path(raw),
                path="/usr/bin:/bin",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload[0]["id"], "ty")
        self.assertEqual(payload[0]["status"], "MISSING")

    def test_installed_update_dry_run_uses_manifest_source_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            install = self.run_be("install", "--group", "wiki", tmp=tmp)
            self.assertEqual(install.returncode, 0, install.stderr)
            wrapper = tmp / "bin" / "be"
            env = os.environ.copy()
            env.update(
                {
                    "CODEX_HOME": str(tmp / "codex"),
                    "AGENTS_HOME": str(tmp / "agents"),
                    "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
                    "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
                }
            )

            result = subprocess.run(
                [str(wrapper), "update", "--dry-run"],
                cwd=tmp,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Current version:", result.stdout)
        self.assertIn("Target source:", result.stdout)
        self.assertIn("Skill groups: wiki", result.stdout)
        self.assertNotIn("REMOVE  codex_home:skills/code-wiki-ru/", result.stdout)


if __name__ == "__main__":
    unittest.main()
