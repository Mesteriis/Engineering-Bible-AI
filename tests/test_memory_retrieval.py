from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SPEC = importlib.util.spec_from_file_location(
    "memory_retrieval", ROOT / "scripts/memory_retrieval.py"
)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
RetrievalError = module.RetrievalError
fuse_rankings = module.fuse_rankings
query_plan = module.query_plan
SNAPSHOT_SPEC = importlib.util.spec_from_file_location(
    "worker_snapshot", ROOT / "scripts/worker_snapshot.py"
)
assert SNAPSHOT_SPEC is not None and SNAPSHOT_SPEC.loader is not None
snapshot_module = importlib.util.module_from_spec(SNAPSHOT_SPEC)
SNAPSHOT_SPEC.loader.exec_module(snapshot_module)
capture_snapshot = snapshot_module.capture_snapshot


class MemoryRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in ("a.md", "b.md", "c.md"):
            (self.root / name).write_text(f"Content of {name}\n", encoding="utf-8")
        self.source = capture_snapshot(self.root, ["a.md", "b.md", "c.md"])

    def payload(self) -> dict:
        manifest = self.source["snapshot"]
        hashes = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
        variants = query_plan("How can I compare recorded worker workloads?")["variants"]
        results = [
            {"id": name, "path": name, "sha256": hashes[name], "score": 1 - index / 10}
            for index, name in enumerate(("a.md", "b.md", "c.md"))
        ]
        return {
            "query": "How can I compare recorded worker workloads?",
            "source": deepcopy(self.source),
            "rankings": [
                {
                    "query": query,
                    "snapshot_sha256": manifest["sha256"],
                    "results": deepcopy(results if index == 0 else [results[1], results[2]]),
                }
                for index, query in enumerate(variants)
            ],
        }

    def test_plan_retains_primary_and_extracts_content_words(self) -> None:
        plan = query_plan(" How can I compare recorded worker workloads? ")
        self.assertEqual(plan["query"], "How can I compare recorded worker workloads?")
        self.assertEqual(plan["variants"][0], plan["query"])
        self.assertIn("compare recorded worker workloads", plan["variants"])
        self.assertLessEqual(len(plan["variants"]), 3)

    def test_unicode_words_are_not_discarded(self) -> None:
        plan = query_plan("Где хранятся решения café 中文?")
        self.assertIn("хранятся решения café 中文", plan["variants"])
        self.assertNotIn("café", plan["variants"])

    def test_short_keyword_query_does_not_fan_out(self) -> None:
        self.assertEqual(query_plan("worker evidence")["variants"], ["worker evidence"])

    def test_stopwords_only_keep_original(self) -> None:
        self.assertEqual(query_plan("how do I")["variants"], ["how do I"])

    def test_unicode_case_expansion_cannot_exceed_variant_byte_bound(self) -> None:
        query = "ŉ" * 511 + "?"
        plan = query_plan(query)
        self.assertEqual(plan["variants"], [query])
        self.assertTrue(all(len(variant.encode("utf-8")) <= 1024 for variant in plan["variants"]))

    def test_invalid_queries_fail_before_planning(self) -> None:
        for query in (None, "", "   ", "a\nsecret", "a\0", "a" * 1025, "😀" * 300):
            with self.subTest(query=repr(query)[:30]), self.assertRaises(RetrievalError):
                query_plan(query)

    def test_rrf_rewards_independent_rankings_and_preserves_baseline(self) -> None:
        payload = self.payload()
        before = deepcopy(payload)
        result = fuse_rankings(payload, limit=2)
        self.assertEqual([item["id"] for item in result["results"]], ["b.md", "c.md"])
        self.assertAlmostEqual(result["results"][0]["rrf_score"], 1 / 62 + 1 / 61)
        self.assertEqual(result["baseline"], payload["rankings"][0]["results"])
        self.assertEqual(len(result["results"][0]["provenance"]), 2)
        self.assertEqual(result["results"][0]["provenance"][0]["rank"], 2)
        self.assertEqual(payload, before)

    def test_no_source_root_never_claims_freshness(self) -> None:
        result = fuse_rankings(self.payload())
        self.assertEqual(result["contract_status"], "PASS")
        self.assertEqual(result["source_status"], "SKIP")
        self.assertEqual(result["outcome"], "SKIP")

    def test_matching_selected_source_passes_even_without_git(self) -> None:
        result = fuse_rankings(self.payload(), source_root=self.root)
        self.assertEqual(result["outcome"], "PASS")
        self.assertEqual(result["source_status"], "PASS")
        self.assertEqual(result["source"]["base_commit"], "unknown")

    def test_stale_file_suppresses_results_including_baseline(self) -> None:
        payload = self.payload()
        (self.root / "c.md").write_text("Changed since indexing", encoding="utf-8")
        result = fuse_rankings(payload, source_root=self.root)
        self.assertEqual(result["outcome"], "FAIL")
        self.assertEqual(result["source_status"], "FAIL")
        self.assertEqual(result["results"], [])
        self.assertEqual(result["baseline"], [])

    def test_symlink_source_fails_closed(self) -> None:
        payload = self.payload()
        (self.root / "a.md").unlink()
        (self.root / "a.md").symlink_to(self.root / "b.md")
        self.assertEqual(fuse_rankings(payload, source_root=self.root)["outcome"], "FAIL")

    def test_ranking_order_does_not_change_fusion_or_tie_break(self) -> None:
        payload = self.payload()
        result = fuse_rankings(payload)
        payload["rankings"].reverse()
        self.assertEqual(fuse_rankings(payload), result)

    def test_empty_rankings_return_no_results_without_inventing_evidence(self) -> None:
        payload = self.payload()
        for ranking in payload["rankings"]:
            ranking["results"] = []
        self.assertEqual(fuse_rankings(payload, source_root=self.root)["results"], [])

    def test_missing_duplicate_or_unplanned_variants_are_rejected(self) -> None:
        for kind in ("missing", "duplicate", "unplanned"):
            payload = self.payload()
            if kind == "missing":
                payload["rankings"].pop(0)
            elif kind == "duplicate":
                payload["rankings"].append(deepcopy(payload["rankings"][0]))
            else:
                payload["rankings"][0]["query"] = "unplanned query"
            with self.subTest(kind=kind), self.assertRaises(RetrievalError):
                fuse_rankings(payload)

    def test_mixed_snapshot_or_file_hash_is_rejected(self) -> None:
        for kind in ("snapshot", "file"):
            payload = self.payload()
            if kind == "snapshot":
                payload["rankings"][1]["snapshot_sha256"] = "0" * 64
            else:
                payload["rankings"][1]["results"][0]["sha256"] = "0" * 64
            with self.subTest(kind=kind), self.assertRaises(RetrievalError):
                fuse_rankings(payload)

    def test_malformed_source_manifest_is_rejected(self) -> None:
        payload = self.payload()
        payload["source"]["snapshot"]["sha256"] = "0" * 64
        with self.assertRaises(RetrievalError):
            fuse_rankings(payload)

    def test_paths_must_be_allowlisted_and_canonical(self) -> None:
        for path in ("../a.md", "/a.md", "./a.md", "docs//a.md", "missing.md", ".env"):
            payload = self.payload()
            payload["rankings"][0]["results"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(RetrievalError):
                fuse_rankings(payload)

    def test_duplicate_id_in_one_ranking_is_not_double_counted(self) -> None:
        payload = self.payload()
        payload["rankings"][0]["results"].append(deepcopy(payload["rankings"][0]["results"][0]))
        with self.assertRaises(RetrievalError):
            fuse_rankings(payload)

    def test_reused_id_for_another_path_or_path_alias_is_rejected(self) -> None:
        for kind in ("id", "path"):
            payload = self.payload()
            payload["rankings"][1]["results"][0]["id"] = "a.md" if kind == "id" else "alias"
            with self.subTest(kind=kind), self.assertRaises(RetrievalError):
                fuse_rankings(payload)

    def test_scores_must_be_finite_real_numbers(self) -> None:
        for score in (math.nan, math.inf, -math.inf, True, None, "1", 10**500):
            payload = self.payload()
            payload["rankings"][0]["results"][0]["score"] = score
            with self.subTest(score=str(score)[:30]), self.assertRaises(RetrievalError):
                fuse_rankings(payload)

    def test_unknown_fields_are_rejected(self) -> None:
        payload = self.payload()
        payload["rankings"][0]["results"][0]["execute"] = "anything"
        with self.assertRaises(RetrievalError):
            fuse_rankings(payload)

    def test_limits_are_positive_bounded_integers(self) -> None:
        for limit in (0, -1, True, 51, 1.5):
            with self.subTest(limit=limit), self.assertRaises(RetrievalError):
                fuse_rankings(self.payload(), limit=limit)

    def test_oversized_ranking_is_rejected_before_fusion(self) -> None:
        payload = self.payload()
        payload["rankings"][0]["results"] *= 34
        with self.assertRaises(RetrievalError):
            fuse_rankings(payload)

    def test_single_variant_preserves_host_rank_instead_of_sorting_raw_scores(self) -> None:
        payload = self.payload()
        payload["query"] = "worker evidence"
        payload["rankings"] = [payload["rankings"][0]]
        payload["rankings"][0]["query"] = "worker evidence"
        payload["rankings"][0]["results"][0]["score"] = -100
        result = fuse_rankings(payload)
        self.assertEqual([item["id"] for item in result["results"]], ["a.md", "b.md", "c.md"])

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/memory-retrieval.py"), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_plan_and_fuse_exit_codes_reflect_freshness(self) -> None:
        path = self.root / "rankings.json"
        path.write_text(json.dumps(self.payload()), encoding="utf-8")
        self.assertEqual(self.cli("plan", "worker evidence").returncode, 0)
        skipped = self.cli("fuse", str(path))
        self.assertEqual(skipped.returncode, 2, skipped.stderr)
        self.assertEqual(json.loads(skipped.stdout)["source_status"], "SKIP")
        passed = self.cli("fuse", str(path), "--source-root", str(self.root))
        self.assertEqual(passed.returncode, 0, passed.stderr)
        (self.root / "a.md").write_text("stale", encoding="utf-8")
        self.assertEqual(self.cli("fuse", str(path), "--source-root", str(self.root)).returncode, 1)

    def test_cli_rejects_duplicate_json_keys_and_nonfinite_values(self) -> None:
        path = self.root / "invalid.json"
        for text in ('{"query":"x","query":"y"}', '{"score":NaN}'):
            path.write_text(text, encoding="utf-8")
            result = self.cli("fuse", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["outcome"], "FAIL")

    def test_cli_rejects_symlink_and_oversized_json(self) -> None:
        path = self.root / "rankings.json"
        path.write_text(json.dumps(self.payload()), encoding="utf-8")
        link = self.root / "linked.json"
        link.symlink_to(path)
        self.assertEqual(self.cli("fuse", str(link)).returncode, 1)
        path.write_bytes(b" " * (8 * 1024 * 1024 + 1))
        self.assertEqual(self.cli("fuse", str(path)).returncode, 1)


if __name__ == "__main__":
    unittest.main()
