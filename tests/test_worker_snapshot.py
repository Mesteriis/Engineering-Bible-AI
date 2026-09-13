from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import TypedDict, cast
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "worker_snapshot.py"
SPEC = importlib.util.spec_from_file_location("worker_snapshot", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
snapshot = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = snapshot
SPEC.loader.exec_module(snapshot)


class Manifest(TypedDict):
    state: str
    sha256: str
    files: list[dict[str, object]]


class CapturedSnapshot(TypedDict):
    base_commit: str
    snapshot: Manifest


class WorkerSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("answer = 42\n", encoding="utf-8")
        (self.root / "notes.txt").write_text("local notes\n", encoding="utf-8")

    def capture(self) -> CapturedSnapshot:
        return cast(
            CapturedSnapshot, snapshot.capture_snapshot(self.root, ["src/a.py", "notes.txt"])
        )

    def test_deterministic_allowlisted_capture_without_git(self) -> None:
        actual = self.capture()
        self.assertEqual(actual["base_commit"], "unknown")
        self.assertEqual(actual, snapshot.capture_snapshot(self.root, ["notes.txt", "src/a.py"]))
        self.assertEqual(actual, snapshot.capture_snapshot(self.root, ["./notes.txt", "src//a.py"]))
        manifest = actual["snapshot"]
        self.assertIsInstance(manifest, dict)
        self.assertEqual([entry["path"] for entry in manifest["files"]], ["notes.txt", "src/a.py"])
        self.assertEqual(manifest["files"][1]["bytes"], 12)
        canonical = json.dumps(
            {"base_commit": "unknown", "files": manifest["files"]},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(manifest["sha256"], hashlib.sha256(canonical).hexdigest())
        serialized = json.dumps(actual)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("answer =", serialized)
        self.assertEqual(snapshot.verify_snapshot(self.root, manifest, actual["base_commit"]), [])
        (self.root / "not-allowlisted.txt").write_text("unrelated")
        self.assertEqual(self.capture(), actual)

    def test_changed_untracked_content_with_same_head_is_detected(self) -> None:
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Snapshot Test",
                "-c",
                "user.email=snapshot@example.invalid",
                "commit",
                "--quiet",
                "--allow-empty",
                "-m",
                "base",
            ],
            check=True,
        )
        actual = self.capture()
        self.assertRegex(actual["base_commit"], r"^[0-9a-f]{40,64}$")
        (self.root / "src" / "a.py").write_text("answer = 43\n", encoding="utf-8")
        changed = self.capture()
        self.assertEqual(actual["base_commit"], changed["base_commit"])
        self.assertNotEqual(actual["snapshot"], changed["snapshot"])
        self.assertTrue(
            snapshot.verify_snapshot(self.root, actual["snapshot"], actual["base_commit"])
        )

    def test_changed_head_is_detected(self) -> None:
        actual = self.capture()
        with patch.object(snapshot, "_base_commit", return_value="a" * 40):
            self.assertTrue(
                snapshot.verify_snapshot(self.root, actual["snapshot"], actual["base_commit"])
            )

    def test_manifest_tampering_and_malformed_values_are_rejected(self) -> None:
        original = self.capture()["snapshot"]
        changed_hash = copy.deepcopy(original)
        changed_hash["files"][0]["sha256"] = "0" * 64
        reordered = copy.deepcopy(original)
        reordered["files"].reverse()
        duplicate = copy.deepcopy(original)
        duplicate["files"].append(duplicate["files"][0])
        alias = copy.deepcopy(original)
        alias["files"][0]["path"] = "./notes.txt"
        boolean_bytes = copy.deepcopy(original)
        boolean_bytes["files"][0]["bytes"] = True
        unknown_field = dict(original)
        unknown_field["root"] = str(self.root)
        for bad in (
            None,
            [],
            {},
            {"state": "not_created"},
            changed_hash,
            reordered,
            duplicate,
            alias,
            boolean_bytes,
            unknown_field,
        ):
            with self.subTest(value=bad):
                self.assertTrue(snapshot.validate_snapshot_manifest(bad, "unknown"))
                self.assertTrue(snapshot.verify_snapshot(self.root, bad, "unknown"))
        for bad_base in (None, "main", "A" * 40, True):
            self.assertTrue(snapshot.validate_snapshot_manifest(original, bad_base))

    def test_missing_file_and_root_return_verification_diagnostics(self) -> None:
        actual = self.capture()
        (self.root / "notes.txt").unlink()
        self.assertTrue(snapshot.verify_snapshot(self.root, actual["snapshot"], "unknown"))
        errors = snapshot.verify_snapshot(self.root / "missing", actual["snapshot"], "unknown")
        self.assertTrue(errors)
        self.assertNotIn(str(self.root), " ".join(errors))

    def test_unsafe_paths_and_secret_names_are_rejected(self) -> None:
        paths = [
            "../escape",
            "src/../notes.txt",
            str(self.root / "notes.txt"),
            "C:/secret",
            "src\\a.py",
            "",
            ".",
            ".git/HEAD",
            ".env",
            ".env.example",
            ".engineering-bible/runtime/catalog.json",
            "id_rsa",
            "credentials.json",
            "private.pem",
            "auth.json",
            ".aws/config",
        ]
        for path in paths:
            with self.subTest(path=path), self.assertRaises(snapshot.SnapshotError):
                snapshot.capture_snapshot(self.root, [path])

    def test_explicit_nonempty_list_and_unique_paths_required(self) -> None:
        for files in ([], "notes.txt", ["notes.txt", "./notes.txt"], ["src/a.py", "src//a.py"]):
            with self.subTest(files=files), self.assertRaises(snapshot.SnapshotError):
                snapshot.capture_snapshot(self.root, files)
        os.link(self.root / "notes.txt", self.root / "alias.txt")
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.capture_snapshot(self.root, ["notes.txt", "alias.txt"])

    def test_symlink_components_directories_and_fifo_rejected(self) -> None:
        (self.root / "linked.txt").symlink_to(self.root / "notes.txt")
        (self.root / "linked-dir").symlink_to(self.root / "src", target_is_directory=True)
        os.mkfifo(self.root / "pipe")
        for path in ("linked.txt", "linked-dir/a.py", "src", "pipe"):
            with self.subTest(path=path), self.assertRaises(snapshot.SnapshotError):
                snapshot.capture_snapshot(self.root, [path])

    def test_file_count_and_byte_bounds_are_enforced(self) -> None:
        with patch.object(snapshot, "MAX_FILES", 1), self.assertRaises(snapshot.SnapshotError):
            self.capture()
        with patch.object(snapshot, "MAX_FILE_BYTES", 3), self.assertRaises(snapshot.SnapshotError):
            self.capture()
        with (
            patch.object(snapshot, "MAX_TOTAL_BYTES", 15),
            self.assertRaises(snapshot.SnapshotError),
        ):
            self.capture()
        actual = self.capture()["snapshot"]
        with patch.object(snapshot, "MAX_TOTAL_BYTES", 15):
            self.assertTrue(snapshot.validate_snapshot_manifest(actual, "unknown"))

    def test_change_between_capture_passes_is_detected(self) -> None:
        original = snapshot._capture_pass
        calls = 0

        def changing(*args: object) -> object:
            nonlocal calls
            result = original(*args)
            calls += 1
            if calls == 1:
                (self.root / "notes.txt").write_text("changed after first pass\n", encoding="utf-8")
            return result

        with patch.object(snapshot, "_capture_pass", side_effect=changing):
            with self.assertRaisesRegex(snapshot.SnapshotError, "changed"):
                self.capture()

    def test_change_during_file_read_is_detected(self) -> None:
        original = snapshot.os.read
        changed = False

        def changing(descriptor: int, size: int) -> bytes:
            nonlocal changed
            result = original(descriptor, size)
            if not changed:
                changed = True
                (self.root / "notes.txt").write_text("changed while reading\n", encoding="utf-8")
            return result

        with (
            patch.object(snapshot, "_base_commit", return_value="unknown"),
            patch.object(snapshot.os, "read", side_effect=changing),
        ):
            with self.assertRaisesRegex(snapshot.SnapshotError, "changed"):
                self.capture()

    def test_unavailable_git_is_reported_as_unknown(self) -> None:
        with patch.object(snapshot.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual(self.capture()["base_commit"], "unknown")


if __name__ == "__main__":
    unittest.main()
