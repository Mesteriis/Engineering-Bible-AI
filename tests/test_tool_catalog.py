from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "tool_catalog.py"
SPEC = importlib.util.spec_from_file_location("tool_catalog", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
tool_catalog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool_catalog
SPEC.loader.exec_module(tool_catalog)


def write_catalog(root: Path, tools: list[dict[str, object]]) -> Path:
    path = root / "tools.json"
    normalized = []
    for entry in tools:
        enriched = dict(entry)
        enriched.setdefault("source", f"https://example.invalid/{entry.get('id', 'tool')}")
        enriched.setdefault("platforms", ["linux", "macos"])
        normalized.append(enriched)
    path.write_text(
        json.dumps({"schema_version": 1, "tools": normalized}),
        encoding="utf-8",
    )
    return path


class ToolCatalogTests(unittest.TestCase):
    def test_repository_catalog_contains_pinned_setup_metadata(self) -> None:
        tools = tool_catalog.load_catalog(ROOT / "config" / "tools.json")
        by_id = {tool.id: tool for tool in tools}
        self.assertEqual(by_id["agent-browser"].version, "0.31.1")
        self.assertTrue(by_id["agent-browser"].integrity.startswith("sha512-"))
        self.assertEqual(by_id["beads"].capabilities, ("persistent-task-state",))
        self.assertEqual(by_id["context7-cli"].setup[0]["id"], "login-no-browser")

    def test_setup_requires_declared_side_effect_permission(self) -> None:
        tool = tool_catalog.ToolSpec(
            "synthetic",
            "npm",
            "synthetic",
            "synthetic",
            ("core",),
            "1.0.0",
            False,
            None,
            setup=({"id": "write", "args": ["init"], "effects": ["repo-write"]},),
        )
        with mock.patch.object(tool_catalog.shutil, "which", return_value="/bin/synthetic"):
            with self.assertRaisesRegex(tool_catalog.CatalogError, "explicit permissions"):
                tool_catalog.run_setup(tool, "write", allow_effects=set(), dry_run=True)

    def test_setup_dry_run_never_invokes_executable(self) -> None:
        tool = tool_catalog.ToolSpec(
            "synthetic",
            "npm",
            "synthetic",
            "synthetic",
            ("core",),
            "1.0.0",
            False,
            None,
            setup=({"id": "read", "args": ["doctor"], "effects": []},),
        )
        with (
            mock.patch.object(tool_catalog.shutil, "which", return_value="/bin/synthetic"),
            mock.patch.object(tool_catalog.subprocess, "run") as run,
        ):
            result = tool_catalog.run_setup(tool, "read", allow_effects=set(), dry_run=True)
        self.assertEqual(result, 0)
        run.assert_not_called()

    def test_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "duplicate",
                        "manager": "uv",
                        "package": "package-one",
                        "executable": "one",
                        "version": "1.0.0",
                        "groups": ["core"],
                    },
                    {
                        "id": "duplicate",
                        "manager": "npm",
                        "package": "package-two",
                        "executable": "two",
                        "version": "2.0.0",
                        "groups": ["core"],
                    },
                ],
            )

            with self.assertRaisesRegex(tool_catalog.CatalogError, "duplicate tool id"):
                tool_catalog.load_catalog(path)

    def test_pinned_managers_require_exact_version(self) -> None:
        for manager in ("uv", "npm"):
            with self.subTest(manager=manager), tempfile.TemporaryDirectory() as raw:
                path = write_catalog(
                    Path(raw),
                    [
                        {
                            "id": "missing-version",
                            "manager": manager,
                            "package": "package",
                            "executable": "command",
                            "groups": ["core"],
                        }
                    ],
                )

                with self.assertRaisesRegex(tool_catalog.CatalogError, "exact version"):
                    tool_catalog.load_catalog(path)

    def test_brew_entries_must_be_explicitly_unpinned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "rolling",
                        "manager": "brew",
                        "package": "rolling-package",
                        "executable": "rolling",
                        "groups": ["core"],
                    }
                ],
            )

            with self.assertRaisesRegex(tool_catalog.CatalogError, "unpinned"):
                tool_catalog.load_catalog(path)

    def test_provenance_requires_https_source_and_supported_platforms(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "unsafe-source",
                        "manager": "uv",
                        "package": "package",
                        "executable": "command",
                        "version": "1.0.0",
                        "groups": ["core"],
                        "source": "http://registry.invalid/package",
                        "platforms": [],
                    }
                ],
            )

            with self.assertRaisesRegex(tool_catalog.CatalogError, "HTTPS source"):
                tool_catalog.load_catalog(path)

    def test_selection_requires_explicit_selector(self) -> None:
        tools = [
            tool_catalog.ToolSpec(
                id="one",
                manager="uv",
                package="one",
                executable="one",
                groups=("core",),
                version="1.0.0",
                unpinned=False,
                python=None,
            )
        ]

        with self.assertRaisesRegex(tool_catalog.CatalogError, "selector"):
            tool_catalog.select_tools(tools, groups=[], tool_ids=[], select_all=False)

    def test_selection_supports_groups_and_ids_without_duplicates(self) -> None:
        tools = [
            tool_catalog.ToolSpec("one", "uv", "one", "one", ("core",), "1.0.0", False, None),
            tool_catalog.ToolSpec("two", "npm", "two", "two", ("extra",), "2.0.0", False, None),
        ]

        selected = tool_catalog.select_tools(
            tools,
            groups=["core"],
            tool_ids=["one", "two"],
            select_all=False,
        )

        self.assertEqual([tool.id for tool in selected.tools], ["one", "two"])
        self.assertEqual([tool.id for tool in selected.supported], ["one", "two"])
        self.assertEqual(selected.unsupported, ())

    def test_selection_partitions_tools_for_the_requested_platform(self) -> None:
        tools = [
            tool_catalog.ToolSpec(
                "mac-only",
                "brew",
                "mac-only",
                "mac-only",
                ("core",),
                None,
                True,
                None,
                platforms=("macos",),
            ),
            tool_catalog.ToolSpec(
                "portable",
                "uv",
                "portable",
                "portable",
                ("core",),
                "1.0.0",
                False,
                None,
                platforms=("linux", "macos"),
            ),
        ]

        selected = tool_catalog.select_tools(
            tools,
            groups=["core"],
            tool_ids=[],
            select_all=False,
            platform="linux",
        )

        self.assertEqual(selected.platform, "linux")
        self.assertEqual([tool.id for tool in selected.supported], ["portable"])
        self.assertEqual([tool.id for tool in selected.unsupported], ["mac-only"])

    def test_build_install_commands_are_argv_not_shell_strings(self) -> None:
        uv_tool = tool_catalog.ToolSpec(
            "python-tool", "uv", "python-package", "python-tool", ("core",), "1.2.3", False, "3.13"
        )
        npm_tool = tool_catalog.ToolSpec(
            "node-tool", "npm", "@scope/node-package", "node-tool", ("core",), "4.5.6", False, None
        )
        brew_tool = tool_catalog.ToolSpec(
            "rolling-tool", "brew", "rolling-package", "rolling-tool", ("core",), None, True, None
        )

        self.assertEqual(
            tool_catalog.build_install_command(uv_tool),
            ["uv", "tool", "install", "-p", "3.13", "python-package==1.2.3"],
        )
        self.assertEqual(
            tool_catalog.build_install_command(uv_tool, upgrade=True),
            [
                "uv",
                "tool",
                "install",
                "--force",
                "-p",
                "3.13",
                "python-package==1.2.3",
            ],
        )
        self.assertEqual(
            tool_catalog.build_install_command(npm_tool),
            ["npm", "install", "-g", "@scope/node-package@4.5.6"],
        )
        self.assertEqual(
            tool_catalog.build_install_command(brew_tool),
            ["brew", "install", "rolling-package"],
        )

    def test_classification_distinguishes_ok_mismatch_and_unpinned(self) -> None:
        pinned = tool_catalog.ToolSpec(
            "pinned", "uv", "pinned", "pinned", ("core",), "1.2.3", False, None
        )
        rolling = tool_catalog.ToolSpec(
            "rolling", "brew", "rolling", "rolling", ("core",), None, True, None
        )

        self.assertEqual(tool_catalog.classify_tool(pinned, "1.2.3").status, "OK")
        self.assertEqual(tool_catalog.classify_tool(pinned, "9.9.9").status, "MISMATCH")
        self.assertEqual(tool_catalog.classify_tool(pinned, None).status, "MISSING")
        self.assertEqual(tool_catalog.classify_tool(rolling, "2026.07").status, "UNPINNED")

    def test_tool_states_do_not_probe_unsupported_tools(self) -> None:
        mac_only = tool_catalog.ToolSpec(
            "mac-only",
            "brew",
            "mac-only",
            "mac-only",
            ("core",),
            None,
            True,
            None,
            platforms=("macos",),
        )
        portable = tool_catalog.ToolSpec(
            "portable",
            "uv",
            "portable",
            "portable",
            ("core",),
            "1.0.0",
            False,
            None,
        )

        with mock.patch.object(
            tool_catalog,
            "installed_versions",
            return_value={"portable": None},
        ) as versions:
            states = tool_catalog.tool_states([mac_only, portable], platform="linux")

        versions.assert_called_once_with([portable])
        self.assertEqual([state.status for state in states], ["UNSUPPORTED", "MISSING"])

    def test_install_skips_unsupported_group_tools_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "platform-specific",
                        "manager": "brew",
                        "package": "platform-specific",
                        "executable": "platform-specific",
                        "groups": ["core"],
                        "unpinned": True,
                        "platforms": ["macos"],
                    }
                ],
            )
            stdout = io.StringIO()
            with (
                mock.patch.object(tool_catalog.sys, "platform", "linux"),
                mock.patch.object(tool_catalog.subprocess, "run") as run,
                redirect_stdout(stdout),
            ):
                result = tool_catalog.main(["--catalog", str(path), "install", "--group", "core"])

        self.assertEqual(result, 0)
        self.assertIn("TOOL-SKIP platform-specific (UNSUPPORTED on linux)", stdout.getvalue())
        run.assert_not_called()

    def test_explicit_unsupported_install_is_an_error_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "platform-specific",
                        "manager": "brew",
                        "package": "platform-specific",
                        "executable": "platform-specific",
                        "groups": ["core"],
                        "unpinned": True,
                        "platforms": ["macos"],
                    }
                ],
            )
            stderr = io.StringIO()
            with (
                mock.patch.object(tool_catalog.sys, "platform", "linux"),
                mock.patch.object(tool_catalog.subprocess, "run") as run,
                redirect_stderr(stderr),
            ):
                result = tool_catalog.main(
                    ["--catalog", str(path), "install", "--tool", "platform-specific"]
                )

        self.assertEqual(result, 1)
        self.assertIn("unsupported on linux", stderr.getvalue())
        run.assert_not_called()

    def test_uv_upgrade_executes_force_install_with_exact_version(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "versioned-tool",
                        "manager": "uv",
                        "package": "versioned-package",
                        "executable": "versioned-tool",
                        "groups": ["core"],
                        "version": "1.2.3",
                    }
                ],
            )
            stdout = io.StringIO()
            completed = tool_catalog.subprocess.CompletedProcess([], 0)
            with (
                mock.patch.object(
                    tool_catalog,
                    "installed_versions",
                    return_value={"versioned-tool": "9.9.9"},
                ),
                mock.patch.object(tool_catalog.shutil, "which", return_value="/usr/bin/uv"),
                mock.patch.object(tool_catalog.subprocess, "run", return_value=completed) as run,
                redirect_stdout(stdout),
            ):
                result = tool_catalog.main(
                    [
                        "--catalog",
                        str(path),
                        "install",
                        "--tool",
                        "versioned-tool",
                        "--upgrade",
                    ]
                )

        self.assertEqual(result, 0)
        run.assert_called_once_with(
            ["uv", "tool", "install", "--force", "versioned-package==1.2.3"],
            check=False,
        )
        self.assertIn('"versioned-package==1.2.3"', stdout.getvalue())

    def test_install_all_is_pinned_only_without_explicit_unpinned_permission(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "rolling-tool",
                        "manager": "brew",
                        "package": "rolling-package",
                        "executable": "rolling-tool",
                        "groups": ["core"],
                        "unpinned": True,
                        "platforms": ["macos"],
                    },
                    {
                        "id": "versioned-tool",
                        "manager": "uv",
                        "package": "versioned-package",
                        "executable": "versioned-tool",
                        "groups": ["core"],
                        "version": "1.2.3",
                    },
                ],
            )
            stdout = io.StringIO()
            completed = tool_catalog.subprocess.CompletedProcess([], 0)
            with (
                mock.patch.object(tool_catalog.sys, "platform", "darwin"),
                mock.patch.object(
                    tool_catalog,
                    "installed_versions",
                    return_value={"rolling-tool": None, "versioned-tool": None},
                ),
                mock.patch.object(tool_catalog.shutil, "which", return_value="/usr/bin/manager"),
                mock.patch.object(tool_catalog.subprocess, "run", return_value=completed) as run,
                redirect_stdout(stdout),
            ):
                result = tool_catalog.main(["--catalog", str(path), "install", "--all"])

        self.assertEqual(result, 0)
        self.assertIn("TOOL-SKIP rolling-tool (requires --allow-unpinned)", stdout.getvalue())
        run.assert_called_once_with(
            ["uv", "tool", "install", "versioned-package==1.2.3"],
            check=False,
        )

    def test_explicit_unpinned_install_requires_permission_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "rolling-tool",
                        "manager": "brew",
                        "package": "rolling-package",
                        "executable": "rolling-tool",
                        "groups": ["core"],
                        "unpinned": True,
                        "platforms": ["macos"],
                    }
                ],
            )
            stderr = io.StringIO()
            with (
                mock.patch.object(tool_catalog.sys, "platform", "darwin"),
                mock.patch.object(
                    tool_catalog,
                    "installed_versions",
                    return_value={"rolling-tool": None},
                ),
                mock.patch.object(tool_catalog.shutil, "which") as which,
                mock.patch.object(tool_catalog.subprocess, "run") as run,
                redirect_stderr(stderr),
            ):
                result = tool_catalog.main(
                    ["--catalog", str(path), "install", "--tool", "rolling-tool"]
                )

        self.assertEqual(result, 1)
        self.assertIn("requires --allow-unpinned", stderr.getvalue())
        which.assert_not_called()
        run.assert_not_called()

    def test_legacy_installer_does_not_implicitly_allow_unpinned_sources(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fake_python = Path(raw) / "python-capture"
            fake_python.write_text(
                "#!/usr/bin/env bash\nprintf '%s\\n' \"$@\"\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            environment = dict(os.environ)
            environment["ENGINEERING_BIBLE_PYTHON"] = str(fake_python)

            result = tool_catalog.subprocess.run(
                ["bash", str(ROOT / "scripts" / "install-tools.sh"), "--install"],
                text=True,
                stdout=tool_catalog.subprocess.PIPE,
                stderr=tool_catalog.subprocess.PIPE,
                check=False,
                env=environment,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("install\n", result.stdout)
        self.assertNotIn("--all", result.stdout)
        self.assertNotIn("--allow-unpinned", result.stdout)
        self.assertIn("explicit selector", result.stderr)

    def test_plan_reports_unsupported_without_an_install_action(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = write_catalog(
                Path(raw),
                [
                    {
                        "id": "platform-specific",
                        "manager": "brew",
                        "package": "platform-specific",
                        "executable": "platform-specific",
                        "groups": ["core"],
                        "unpinned": True,
                        "platforms": ["macos"],
                    }
                ],
            )
            stdout = io.StringIO()
            with mock.patch.object(tool_catalog.sys, "platform", "linux"), redirect_stdout(stdout):
                result = tool_catalog.main(["--catalog", str(path), "plan", "--all"])

        self.assertEqual(result, 0)
        self.assertIn("UNSUPPORTED", stdout.getvalue())
        self.assertNotIn("INSTALL [", stdout.getvalue())

    def test_install_does_not_advertise_unsupported_json_output(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                tool_catalog.main(["install", "--all", "--json"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("unrecognized arguments: --json", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
