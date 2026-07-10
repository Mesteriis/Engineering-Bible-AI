from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path
import random
import stat
import string
import subprocess
import sys
import tempfile
from typing import cast
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "mcp_catalog.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("mcp_catalog", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mcp_catalog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mcp_catalog
SPEC.loader.exec_module(mcp_catalog)

CatalogError = mcp_catalog.CatalogError
build_catalog = mcp_catalog.build_catalog
candidate_capabilities = mcp_catalog.candidate_capabilities
load_catalog = mcp_catalog.load_catalog
persist_catalog = mcp_catalog.persist_catalog
show_capability = mcp_catalog.show_capability
repository_projection_status = mcp_catalog.repository_projection_status


def synthetic_identifier(rng: random.Random, prefix: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    suffix = "".join(rng.choice(alphabet) for _ in range(18))
    return f"{prefix}_{suffix}"


def runtime_payload(
    tools: list[dict[str, object]],
    *,
    status: str = "online",
    source_id: str = "runtime_synthetic",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_id": source_id,
        "status": status,
        "tools": tools,
    }


def read_only_tool(
    selector: str,
    *,
    description: str = "Read local source documentation",
    scope: str = "local",
    available: bool = True,
    input_schema: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "selector": selector,
        "display_name": selector,
        "description": description,
        "available": available,
        "annotations": {
            "read_only": True,
            "destructive": False,
            "open_world": scope == "remote",
            "scope": scope,
        },
        "input_schema": input_schema
        or {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search phrase",
                }
            },
            "required": ["query"],
        },
    }


class ExplodingValue:
    def __str__(self) -> str:
        raise AssertionError("ignored runtime fields must never be inspected or invoked")

    def __call__(self) -> None:
        raise AssertionError("discovery must never invoke a tool")


class McpCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rng = random.Random(20260710)

    def test_persists_private_global_and_untracked_repository_catalogs(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        catalog = build_catalog(
            runtime_payload([read_only_tool(selector)]),
            captured_at="2026-07-10T12:00:00Z",
        )

        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            (repo / ".git" / "info").mkdir(parents=True)
            engineering_home = base / "home"

            paths = persist_catalog(
                catalog,
                engineering_home=engineering_home,
                repo=repo,
            )
            persist_catalog(catalog, engineering_home=engineering_home, repo=repo)

            stored = load_catalog(engineering_home)
            index = json.loads(paths["index"].read_text(encoding="utf-8"))
            recommendations = paths["recommendations"].read_text(encoding="utf-8")
            exclude = (repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            modes = [stat.S_IMODE(path.stat().st_mode) for path in paths.values()]

        self.assertEqual(stored["fingerprint"], catalog["fingerprint"])
        self.assertEqual(index["fingerprint"], catalog["fingerprint"])
        self.assertIn(selector, recommendations)
        self.assertEqual(exclude.count(".engineering-bible/"), 1)
        self.assertEqual(modes, [0o600, 0o600, 0o600])

    def test_fingerprint_changes_for_composition_metadata_and_schema(self) -> None:
        first = synthetic_identifier(self.rng, "tool")
        second = synthetic_identifier(self.rng, "tool")
        initial = build_catalog(runtime_payload([read_only_tool(first)]))
        added = build_catalog(runtime_payload([read_only_tool(first), read_only_tool(second)]))
        metadata_changed = build_catalog(
            runtime_payload([read_only_tool(first, description="Read local test reports")])
        )
        schema_changed = build_catalog(
            runtime_payload(
                [
                    read_only_tool(
                        first,
                        input_schema={
                            "type": "object",
                            "properties": {"query": {"type": "integer"}},
                        },
                    )
                ]
            )
        )
        annotation_tool = read_only_tool(first)
        annotation_tool["annotations"] = {
            "read_only": True,
            "destructive": False,
            "open_world": False,
            "scope": "local",
            "idempotent": True,
        }
        annotation_changed = build_catalog(runtime_payload([annotation_tool]))

        fingerprints = {
            initial["fingerprint"],
            added["fingerprint"],
            metadata_changed["fingerprint"],
            schema_changed["fingerprint"],
            annotation_changed["fingerprint"],
        }
        self.assertEqual(len(fingerprints), 5)

    def test_discovery_ignores_invocation_and_transport_fields(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        tool = read_only_tool(selector)
        tool.update(
            {
                "invoke": ExplodingValue(),
                "command": ExplodingValue(),
                "arguments": ExplodingValue(),
                "headers": ExplodingValue(),
                "environment": ExplodingValue(),
            }
        )

        catalog = build_catalog(runtime_payload([tool]))

        serialized = json.dumps(catalog)
        self.assertNotIn("invoke", serialized)
        self.assertNotIn("command", serialized)
        self.assertNotIn("headers", serialized)
        self.assertEqual(catalog["tool_count"], 1)

    def test_malicious_metadata_is_redacted_from_every_generated_file(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        tool = read_only_tool(
            selector,
            description=(
                "Read https://internal.invalid/path at 192.0.2.10 with "
                "Authorization: Bearer synthetic-secret-value and "
                "api_key=synthetic-key-value"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Credential for user@example.invalid",
                        "default": "synthetic-default-secret",
                    }
                },
            },
        )
        payload = runtime_payload([tool])
        payload["endpoint"] = "https://ignored.invalid/runtime"
        payload["environment"] = {"SECRET": "synthetic-runtime-secret"}
        catalog = build_catalog(payload)

        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            (repo / ".git" / "info").mkdir(parents=True)
            paths = persist_catalog(catalog, engineering_home=base / "home", repo=repo)
            generated = "\n".join(path.read_text(encoding="utf-8") for path in paths.values())

        for forbidden in (
            "internal.invalid",
            "192.0.2.10",
            "synthetic-secret-value",
            "synthetic-key-value",
            "synthetic-default-secret",
            "user@example.invalid",
            "ignored.invalid",
            "synthetic-runtime-secret",
        ):
            self.assertNotIn(forbidden, generated)
        self.assertIn("[REDACTED", generated)

        unsafe_selector = read_only_tool("https://selector.invalid/runtime")
        with self.assertRaises(CatalogError):
            build_catalog(runtime_payload([unsafe_selector]))

    def test_contradictory_read_only_annotation_cannot_lower_destructive_risk(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        tool = read_only_tool(
            selector,
            description="Permanently delete selected resources",
        )

        catalog = build_catalog(runtime_payload([tool]))
        capability = catalog["tools"][0]

        self.assertEqual(capability["risk"], "R3")
        self.assertTrue(capability["requires_confirmation"])
        self.assertIn("metadata.signal=destructive", capability["evidence"])

    def test_unknown_capability_is_deny_by_default(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        payload = runtime_payload(
            [
                {
                    "selector": selector,
                    "display_name": selector,
                    "description": "Specialized capability",
                    "available": True,
                    "annotations": {},
                    "input_schema": {"type": "object", "properties": {}},
                }
            ]
        )

        catalog = build_catalog(payload)
        capability = catalog["tools"][0]

        self.assertEqual(capability["risk"], "UNKNOWN")
        self.assertTrue(capability["requires_confirmation"])

    def test_incomplete_safety_annotations_cannot_produce_r0(self) -> None:
        for omitted in ("destructive", "open_world", "scope"):
            with self.subTest(omitted=omitted):
                selector = synthetic_identifier(self.rng, "tool")
                tool = read_only_tool(selector)
                annotations = cast(dict[str, object], tool["annotations"])
                annotations.pop(omitted)

                catalog = build_catalog(runtime_payload([tool]))
                capability = catalog["tools"][0]

                self.assertEqual(capability["risk"], "UNKNOWN")
                self.assertTrue(capability["requires_confirmation"])

    def test_execution_parameter_overrides_read_only_annotations(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        tool = read_only_tool(
            selector,
            input_schema={
                "type": "object",
                "properties": {"command": {"type": "string"}},
            },
        )

        catalog = build_catalog(runtime_payload([tool]))
        capability = catalog["tools"][0]

        self.assertEqual(capability["risk"], "R3")
        self.assertTrue(capability["requires_confirmation"])
        self.assertIn("schema.parameter=execution", capability["evidence"])

    def test_annotation_values_are_typed_before_catalog_persistence(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        tool = read_only_tool(selector)
        annotations = cast(dict[str, object], tool["annotations"])
        annotations["idempotent"] = "token=synthetic-secret-value"

        with self.assertRaises(CatalogError):
            build_catalog(runtime_payload([tool]))

    def test_offline_and_partial_snapshots_never_claim_missing_tools_available(self) -> None:
        offline_selector = synthetic_identifier(self.rng, "tool")
        offline = build_catalog(
            runtime_payload([read_only_tool(offline_selector)], status="offline")
        )
        self.assertFalse(offline["tools"][0]["available"])
        self.assertEqual(candidate_capabilities(offline, "read source"), [])

        available_selector = synthetic_identifier(self.rng, "tool")
        unavailable_selector = synthetic_identifier(self.rng, "tool")
        partial = build_catalog(
            runtime_payload(
                [
                    read_only_tool(available_selector, available=True),
                    read_only_tool(unavailable_selector, available=False),
                ],
                status="partial",
            )
        )
        candidates = candidate_capabilities(partial, "read source")
        selectors = {candidate["selector"] for candidate in candidates}
        self.assertIn(available_selector, selectors)
        self.assertNotIn(unavailable_selector, selectors)

    def test_candidate_results_are_limited_and_expand_at_most_three_parameter_sets(self) -> None:
        tools = [
            read_only_tool(
                synthetic_identifier(self.rng, "tool"),
                description="Read source quality reports",
            )
            for _ in range(12)
        ]
        catalog = build_catalog(runtime_payload(tools))

        candidates = candidate_capabilities(catalog, "read source quality", limit=99)

        self.assertEqual(len(candidates), 8)
        expanded = [candidate for candidate in candidates if "parameters" in candidate]
        self.assertEqual(len(expanded), 3)
        self.assertTrue(all(len(candidate["parameters"]) == 1 for candidate in expanded))

    def test_show_uses_opaque_id_and_returns_parameter_details(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        catalog = build_catalog(runtime_payload([read_only_tool(selector)]))
        opaque_id = catalog["tools"][0]["runtime_id"]

        shown = show_capability(catalog, opaque_id)

        self.assertEqual(shown["selector"], selector)
        self.assertEqual(shown["parameters"][0]["name"], "query")
        with self.assertRaises(CatalogError):
            show_capability(catalog, synthetic_identifier(self.rng, "missing"))

    def test_duplicate_selectors_and_unsafe_repository_symlink_are_rejected(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        with self.assertRaises(CatalogError):
            build_catalog(runtime_payload([read_only_tool(selector), read_only_tool(selector)]))

        catalog = build_catalog(runtime_payload([read_only_tool(selector)]))
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            outside = base / "outside"
            repo.mkdir()
            outside.mkdir()
            os.symlink(outside, repo / ".engineering-bible")
            with self.assertRaises(CatalogError):
                persist_catalog(catalog, engineering_home=base / "home", repo=repo)

    def test_worktree_git_exclude_is_written_to_common_metadata(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        catalog = build_catalog(runtime_payload([read_only_tool(selector)]))
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            common = base / "common"
            worktree_metadata = common / "worktrees" / "branch-a"
            worktree_metadata.mkdir(parents=True)
            (worktree_metadata / "commondir").write_text("../..\n", encoding="utf-8")
            repo = base / "repo"
            repo.mkdir()
            (repo / ".git").write_text(
                f"gitdir: {worktree_metadata}\n",
                encoding="utf-8",
            )

            persist_catalog(catalog, engineering_home=base / "home", repo=repo)

            common_exclude = (common / "info" / "exclude").read_text(encoding="utf-8")

        self.assertEqual(common_exclude, ".engineering-bible/\n")

    def test_projection_is_not_written_when_git_exclude_is_unsafe(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        catalog = build_catalog(runtime_payload([read_only_tool(selector)]))
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            info = repo / ".git" / "info"
            info.mkdir(parents=True)
            victim = base / "exclude-victim"
            victim.write_text("unmanaged\n", encoding="utf-8")
            os.symlink(victim, info / "exclude")
            engineering_home = base / "home"

            with self.assertRaises(CatalogError):
                persist_catalog(catalog, engineering_home=engineering_home, repo=repo)

            self.assertEqual(victim.read_text(encoding="utf-8"), "unmanaged\n")
            self.assertFalse((repo / ".engineering-bible" / "mcp" / "index.json").exists())
            self.assertFalse((repo / ".engineering-bible" / "mcp" / "MCP_CAPABILITIES.md").exists())
            self.assertFalse((engineering_home / "runtime" / "mcp" / "catalog.json").exists())

    def test_synthetic_example_is_accepted_without_transport_metadata(self) -> None:
        example_path = ROOT / "examples" / "runtime-capabilities.synthetic.json"
        payload = json.loads(example_path.read_text(encoding="utf-8"))

        catalog = build_catalog(payload)

        self.assertEqual(catalog["tool_count"], 2)
        serialized = json.dumps(catalog)
        for forbidden_key in ("endpoint", "command", "arguments", "headers", "environment"):
            self.assertNotIn(f'"{forbidden_key}"', serialized)

    def test_invalid_nested_schema_key_returns_safe_catalog_error(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        tool = read_only_tool(
            selector,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        7: "invalid",
                    }
                },
            },
        )

        with self.assertRaises(CatalogError):
            build_catalog(runtime_payload([tool]))

    def test_projection_status_detects_current_stale_and_wrong_repository(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        catalog = build_catalog(runtime_payload([read_only_tool(selector)]))
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            (repo / ".git" / "info").mkdir(parents=True)
            paths = persist_catalog(catalog, engineering_home=base / "home", repo=repo)

            current = repository_projection_status(catalog, repo)
            index = json.loads(paths["index"].read_text(encoding="utf-8"))
            index["fingerprint"] = "0" * 64
            paths["index"].write_text(json.dumps(index), encoding="utf-8")
            stale = repository_projection_status(catalog, repo)

            other_repo = base / "other-repo"
            other_index = other_repo / ".engineering-bible" / "mcp" / "index.json"
            other_index.parent.mkdir(parents=True)
            original_index = json.loads(paths["catalog"].read_text(encoding="utf-8"))
            original_index = {
                "schema_version": 1,
                "fingerprint": original_index["fingerprint"],
                "repository_ref": index["repository_ref"],
            }
            other_index.write_text(json.dumps(original_index), encoding="utf-8")
            wrong_repository = repository_projection_status(catalog, other_repo)

        self.assertEqual(current["status"], "current")
        self.assertEqual(stale["status"], "stale")
        self.assertEqual(wrong_repository["status"], "invalid")

    def test_tampered_private_catalog_fails_integrity_validation(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        catalog = build_catalog(runtime_payload([read_only_tool(selector)]))
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            (repo / ".git" / "info").mkdir(parents=True)
            paths = persist_catalog(catalog, engineering_home=base / "home", repo=repo)
            stored = json.loads(paths["catalog"].read_text(encoding="utf-8"))
            stored["tools"][0]["description"] = "Tampered metadata"
            paths["catalog"].write_text(json.dumps(stored), encoding="utf-8")

            with self.assertRaisesRegex(CatalogError, "fingerprint"):
                load_catalog(base / "home")

    def test_module_cli_requires_repo_and_uses_current_projection(self) -> None:
        selector = synthetic_identifier(self.rng, "tool")
        payload = runtime_payload([read_only_tool(selector)])
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            (repo / ".git" / "info").mkdir(parents=True)
            home = base / "home"
            refresh = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--engineering-home",
                    str(home),
                    "refresh",
                    "--repo",
                    str(repo),
                    "--json",
                ],
                input=json.dumps(payload),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            status_result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--engineering-home",
                    str(home),
                    "status",
                    "--repo",
                    str(repo),
                    "--json",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            candidates = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--engineering-home",
                    str(home),
                    "candidates",
                    "--repo",
                    str(repo),
                    "--task-stdin",
                    "--json",
                ],
                input="read source",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(refresh.returncode, 0, refresh.stderr)
        self.assertEqual(status_result.returncode, 0, status_result.stderr)
        self.assertEqual(
            json.loads(status_result.stdout)["repository_projection"]["status"],
            "current",
        )
        self.assertEqual(candidates.returncode, 0, candidates.stderr)
        self.assertEqual(json.loads(candidates.stdout)[0]["selector"], selector)


if __name__ == "__main__":
    unittest.main()
