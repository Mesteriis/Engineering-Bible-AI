from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import cast
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scripts import context_cache, worker_snapshot  # noqa: E402


class ContextCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        (self.source / "src").mkdir(parents=True)
        (self.source / "src" / "alpha.py").write_text("VALUE = 'alpha'\n", encoding="utf-8")
        (self.source / "src" / "beta.py").write_text("VALUE = 'beta'\n", encoding="utf-8")
        subprocess.run(["git", "init", "--quiet", str(self.source)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.source),
                "add",
                "src/alpha.py",
                "src/beta.py",
            ],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.source),
                "-c",
                "user.name=Context Test",
                "-c",
                "user.email=context@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
            check=True,
        )

    def request(self) -> dict[str, object]:
        captured = worker_snapshot.capture_snapshot(self.source, ["src/alpha.py", "src/beta.py"])
        snapshot = cast(dict[str, object], captured["snapshot"])
        blocks = [
            {
                "path": entry["path"],
                "text": (self.source / str(entry["path"])).read_text(encoding="utf-8"),
            }
            for entry in cast(list[dict[str, object]], snapshot["files"])
        ]
        return {
            "schema_version": 1,
            "cache_scope": "project-alpha-review",
            "requested": {"provider": "caller-provider", "model": "caller-model"},
            "base_commit": captured["base_commit"],
            "snapshot": snapshot,
            "wire_format": "anthropic_messages",
            "ttl": "5m",
            "blocks": blocks,
            "task_text": "Review this exact task.\nKeep all punctuation!",
        }

    def test_task_changes_reuse_stable_prefix_and_text_is_preserved(self) -> None:
        request = self.request()
        first = context_cache.prepare_request(request, self.source)
        other_task = copy.deepcopy(request)
        other_task["task_text"] = "Different task text, completely unchanged.\n"
        second = context_cache.prepare_request(other_task, self.source)
        self.assertEqual(first["cache_identity"], second["cache_identity"])
        fragment = cast(dict[str, object], first["fragment"])
        messages = cast(list[dict[str, object]], fragment["messages_append"])
        content = cast(list[dict[str, object]], messages[0]["content"])
        source_content = content[:-1]
        system_append = cast(list[dict[str, object]], fragment["system_append"])
        self.assertEqual(content[-1]["text"], request["task_text"])
        self.assertEqual(
            [str(item["text"]).split("\n", 1)[1] for item in source_content],
            [block["text"] for block in cast(list[dict[str, str]], request["blocks"])],
        )
        self.assertEqual(source_content[-1]["cache_control"], {"type": "ephemeral", "ttl": "5m"})
        self.assertNotIn("cache_control", source_content[-2])
        self.assertNotIn("cache_control", content[-1])
        self.assertIn("untrusted", str(system_append[0]["text"]))
        self.assertNotIn("system", fragment)
        self.assertNotIn("messages", fragment)
        self.assertEqual(first["provider_cache_status"], "UNKNOWN")
        self.assertEqual(first["activation_status"], "BLOCKED")

    def test_scope_route_ttl_and_changed_snapshot_change_identity(self) -> None:
        original = self.request()
        identity = context_cache.prepare_request(original, self.source)["cache_identity"]
        variants = []
        changed_scope = copy.deepcopy(original)
        changed_scope["cache_scope"] = "project-beta-review"
        variants.append(changed_scope)
        changed_model = copy.deepcopy(original)
        cast(dict[str, object], changed_model["requested"])["model"] = "different-caller-model"
        variants.append(changed_model)
        changed_provider = copy.deepcopy(original)
        cast(dict[str, object], changed_provider["requested"])["provider"] = "different-provider"
        variants.append(changed_provider)
        changed_ttl = copy.deepcopy(original)
        changed_ttl["ttl"] = "1h"
        variants.append(changed_ttl)
        for variant in variants:
            with self.subTest(variant=variant["cache_scope"], route=variant["requested"]):
                self.assertNotEqual(
                    context_cache.prepare_request(variant, self.source)["cache_identity"], identity
                )
        (self.source / "src" / "alpha.py").write_text("VALUE = 'changed'\n", encoding="utf-8")
        changed_source = self.request()
        self.assertNotEqual(
            context_cache.prepare_request(changed_source, self.source)["cache_identity"], identity
        )

    def test_stale_snapshot_and_corrupted_block_are_rejected(self) -> None:
        request = self.request()
        (self.source / "src" / "alpha.py").write_text("VALUE = 'new'\n", encoding="utf-8")
        with self.assertRaises(context_cache.CacheBlocked):
            context_cache.prepare_request(request, self.source)
        fresh = self.request()
        cast(list[dict[str, object]], fresh["blocks"])[0]["text"] = "altered text\n"
        with self.assertRaisesRegex(context_cache.CacheInputError, "does not match"):
            context_cache.prepare_request(fresh, self.source)

    def test_contract_rejects_unknown_commit_duplicate_paths_and_limits(self) -> None:
        request = self.request()
        request["base_commit"] = "unknown"
        snapshot = cast(dict[str, object], request["snapshot"])
        snapshot["sha256"] = worker_snapshot.snapshot_digest(
            "unknown", cast(list[dict[str, object]], snapshot["files"])
        )
        with self.assertRaises(context_cache.CacheBlocked):
            context_cache.prepare_request(request, self.source)
        missing = copy.deepcopy(request)
        missing["snapshot"] = {"state": "not_created", "sha256": "unknown", "files": []}
        with self.assertRaises(context_cache.CacheBlocked):
            context_cache.prepare_request(missing, self.source)
        duplicate = self.request()
        blocks = cast(list[dict[str, object]], duplicate["blocks"])
        blocks[1]["path"] = blocks[0]["path"]
        with self.assertRaises(context_cache.CacheInputError):
            context_cache.prepare_request(duplicate, self.source)
        oversized = self.request()
        oversized["task_text"] = "x" * (context_cache.MAX_TASK_BYTES + 1)
        with self.assertRaisesRegex(context_cache.CacheInputError, "byte limit"):
            context_cache.prepare_request(oversized, self.source)

    def test_json_rejects_duplicate_keys_nonfinite_values_and_symlinks(self) -> None:
        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"x":1,"x":2}', encoding="utf-8")
        with self.assertRaisesRegex(context_cache.CacheInputError, "duplicate"):
            context_cache.read_json(duplicate)
        nonfinite = self.root / "nonfinite.json"
        nonfinite.write_text('{"x":NaN}', encoding="utf-8")
        with self.assertRaisesRegex(context_cache.CacheInputError, "non-finite"):
            context_cache.read_json(nonfinite)
        target = self.root / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = self.root / "link.json"
        link.symlink_to(target)
        with self.assertRaises(context_cache.CacheInputError):
            context_cache.read_json(link)

    def test_usage_hit_miss_unknown_and_invalid_counts(self) -> None:
        hit = context_cache.interpret_usage(
            {
                "id": "provider-response-id",
                "usage": {"input_tokens": 12, "output_tokens": 3, "cache_read_input_tokens": 8},
            }
        )
        self.assertEqual(hit["provider_cache_status"], "HIT")
        self.assertEqual(hit["usage_status"], "PASS")
        usage = cast(dict[str, object], hit["usage"])
        self.assertIsNone(usage["cache_creation_input_tokens"])
        self.assertEqual(hit["cost_usd"], None)
        actual_shape = context_cache.interpret_usage(
            {
                "usage": {
                    "input_tokens": 2_000,
                    "output_tokens": 10,
                    "cache_read_input_tokens": 1_800,
                    "cache_creation_input_tokens": 248,
                    "cache_creation": {
                        "ephemeral_5m_input_tokens": 148,
                        "ephemeral_1h_input_tokens": 100,
                    },
                    "service_tier": "standard",
                    "inference_geo": "private-provider-value",
                    "iterations": 2,
                }
            }
        )
        self.assertEqual(actual_shape["provider_cache_status"], "HIT")
        normalized = cast(dict[str, object], actual_shape["usage"])
        self.assertEqual(normalized["cache_creation_input_tokens"], 248)
        breakdown = cast(dict[str, object], normalized["cache_creation"])
        self.assertEqual(breakdown["ephemeral_5m_input_tokens"], 148)
        self.assertEqual(breakdown["ephemeral_1h_input_tokens"], 100)
        self.assertNotIn("service_tier", normalized)
        self.assertNotIn("inference_geo", normalized)
        miss = context_cache.interpret_usage(
            {
                "input_tokens": 12,
                "output_tokens": 3,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 12,
            }
        )
        self.assertEqual(miss["provider_cache_status"], "MISS")
        unknown = context_cache.interpret_usage({})
        self.assertEqual(unknown["provider_cache_status"], "UNKNOWN")
        self.assertEqual(unknown["usage_status"], "SKIP")
        for invalid in (
            {"input_tokens": True},
            {"output_tokens": -1},
            {"cache_read_input_tokens": 1.5},
            {"input_tokens": float("inf")},
            {"cache_creation": {"ephemeral_5m_input_tokens": True}},
            {"cache_creation": {"ephemeral_1h_input_tokens": -1}},
            {
                "cache_creation_input_tokens": 248,
                "cache_creation": {
                    "ephemeral_5m_input_tokens": 147,
                    "ephemeral_1h_input_tokens": 100,
                },
            },
        ):
            with self.subTest(invalid=invalid), self.assertRaises(context_cache.CacheInputError):
                context_cache.interpret_usage(invalid)

    def test_cli_exit_codes_and_default_stdout_omit_context(self) -> None:
        request_path = self.root / "request.json"
        request = self.request()
        request_path.write_text(json.dumps(request), encoding="utf-8")
        command = [
            sys.executable,
            str(ROOT / "scripts/context-cache.py"),
            "prepare",
            str(request_path),
            "--source-root",
            str(self.source),
        ]
        prepared = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertNotIn("VALUE =", prepared.stdout)
        exported = subprocess.run(
            [*command, "--export-authorized"], text=True, capture_output=True, check=False
        )
        self.assertEqual(exported.returncode, 0, exported.stderr)
        self.assertIn("VALUE = 'alpha'", exported.stdout)
        unknown_usage_path = self.root / "unknown-usage.json"
        unknown_usage_path.write_text("{}", encoding="utf-8")
        unknown_usage = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/context-cache.py"),
                "usage",
                str(unknown_usage_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(unknown_usage.returncode, 2)
        self.assertEqual(json.loads(unknown_usage.stdout)["usage_status"], "SKIP")
        invalid_path = self.root / "invalid.json"
        invalid_path.write_text('{"x":NaN}', encoding="utf-8")
        invalid = subprocess.run(
            [sys.executable, str(ROOT / "scripts/context-cache.py"), "usage", str(invalid_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(json.loads(invalid.stdout)["preparation_status"], "FAIL")
        mismatch_path = self.root / "mismatch.json"
        mismatch_path.write_text(
            json.dumps(
                {
                    "usage": {
                        "cache_creation_input_tokens": 248,
                        "cache_creation": {
                            "ephemeral_5m_input_tokens": 147,
                            "ephemeral_1h_input_tokens": 100,
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        mismatch = subprocess.run(
            [sys.executable, str(ROOT / "scripts/context-cache.py"), "usage", str(mismatch_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(mismatch.returncode, 1)
        self.assertEqual(json.loads(mismatch.stdout)["preparation_status"], "FAIL")
        malformed_snapshot = copy.deepcopy(request)
        malformed_snapshot["snapshot"] = {}
        request_path.write_text(json.dumps(malformed_snapshot), encoding="utf-8")
        invalid_snapshot = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(invalid_snapshot.returncode, 1)
        self.assertEqual(json.loads(invalid_snapshot.stdout)["preparation_status"], "FAIL")
        request_path.write_text(json.dumps(request), encoding="utf-8")
        (self.source / "src" / "alpha.py").write_text("VALUE = 'stale'\n", encoding="utf-8")
        stale = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(stale.returncode, 2)
        self.assertEqual(json.loads(stale.stdout)["preparation_status"], "BLOCKED")
        unknown_base = copy.deepcopy(request)
        unknown_base["base_commit"] = "unknown"
        unknown_snapshot = cast(dict[str, object], unknown_base["snapshot"])
        unknown_snapshot["sha256"] = worker_snapshot.snapshot_digest(
            "unknown", cast(list[dict[str, object]], unknown_snapshot["files"])
        )
        request_path.write_text(json.dumps(unknown_base), encoding="utf-8")
        blocked = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(json.loads(blocked.stdout)["preparation_status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
