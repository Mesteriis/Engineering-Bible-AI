#!/usr/bin/env python3
"""Fingerprint an explicit allowlist of source files without exporting contents.

The snapshot SHA-256 hashes UTF-8 JSON of ``{"base_commit": ..., "files": ...}``,
using ``ensure_ascii=False, sort_keys=True, separators=(",", ":")``. Files are
sorted by normalized POSIX path; each entry contains only path, sha256 and bytes.
Two full passes compare hashes and metadata, with a HEAD check on both sides.
This detects observed changes, but does not provide an atomic filesystem snapshot
or prove that a worker actually used the listed files.
"""

from __future__ import annotations

from collections.abc import Sequence
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess


MAX_FILES = 256
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_PATH_BYTES = 4096
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64}|unknown)\Z")
_PRIVATE_NAMES = {
    ".aws",
    ".azure",
    ".ssh",
    ".gnupg",
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".git-credentials",
    "auth.json",
    "credentials",
    "credentials.json",
    "credentials.yml",
    "credentials.yaml",
    "credential.json",
    "secrets.json",
    "secrets.yml",
    "secrets.yaml",
    "private_key",
    "private-key",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}


class SnapshotError(ValueError):
    """The requested snapshot cannot be safely captured or validated."""


def _normalized_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise SnapshotError("snapshot paths must be nonempty strings")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise SnapshotError("snapshot path contains control characters")
    try:
        path_size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise SnapshotError("snapshot path must be valid UTF-8") from exc
    if path_size > MAX_PATH_BYTES or "\\" in value or PureWindowsPath(value).drive:
        raise SnapshotError("snapshot path is too long or is not a relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise SnapshotError("snapshot paths must stay inside the selected root")
    lowered = tuple(part.lower() for part in path.parts)
    for part in lowered:
        if (
            part == ".git"
            or part.startswith(".env")
            or part in _PRIVATE_NAMES
            or part.endswith((".pem", ".key", ".p12", ".pfx"))
        ):
            raise SnapshotError("snapshot path selects private or Git metadata")
    if any(
        lowered[index : index + 2] == (".engineering-bible", "runtime")
        for index in range(len(lowered) - 1)
    ):
        raise SnapshotError("snapshot path selects private runtime data")
    return path.as_posix()


def snapshot_digest(base_commit: str, files: list[dict[str, object]]) -> str:
    """Hash the canonical commit and sorted file manifest; validate separately."""
    canonical = json.dumps(
        {"base_commit": base_commit, "files": sorted(files, key=lambda item: str(item["path"]))},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _base_commit(root: Path) -> str:
    # Ignore Git environment overrides so HEAD belongs to the selected root.
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    value = result.stdout.decode("ascii", errors="replace").strip()
    return value if result.returncode == 0 and _COMMIT.fullmatch(value) else "unknown"


def _metadata(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _read_file(
    root_fd: int, path: str, remaining_bytes: int
) -> tuple[dict[str, object], tuple[int, ...]]:
    parent_fd = os.dup(root_fd)
    try:
        parts = PurePosixPath(path).parts
        for part in parts[:-1]:
            child_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child_fd
        initial = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(initial.st_mode):
            raise SnapshotError("snapshot entries must be regular files without symlinks")
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent_fd,
        )
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or _metadata(initial) != _metadata(before):
                raise SnapshotError("selected file changed before reading")
            if before.st_size > MAX_FILE_BYTES:
                raise SnapshotError("snapshot file exceeds byte limit")
            if before.st_size > remaining_bytes:
                raise SnapshotError("snapshot exceeds total byte limit")
            digest = hashlib.sha256()
            size = 0
            while True:
                chunk = os.read(
                    descriptor, min(65536, min(MAX_FILE_BYTES, remaining_bytes) - size + 1)
                )
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise SnapshotError("snapshot file exceeds byte limit")
                if size > remaining_bytes:
                    raise SnapshotError("snapshot exceeds total byte limit")
                digest.update(chunk)
            after = os.fstat(descriptor)
            if _metadata(before) != _metadata(after) or size != after.st_size:
                raise SnapshotError("selected file changed while reading")
            return {"path": path, "sha256": digest.hexdigest(), "bytes": size}, _metadata(after)
        finally:
            os.close(descriptor)
    finally:
        os.close(parent_fd)


def _capture_pass(
    root_fd: int,
    paths: list[str],
) -> tuple[list[dict[str, object]], list[tuple[int, ...]]]:
    entries: list[dict[str, object]] = []
    metadata: list[tuple[int, ...]] = []
    identities: set[tuple[int, int]] = set()
    total = 0
    for path in paths:
        entry, attributes = _read_file(root_fd, path, MAX_TOTAL_BYTES - total)
        identity = (attributes[0], attributes[1])
        if identity in identities:
            raise SnapshotError("snapshot contains duplicate filesystem aliases")
        identities.add(identity)
        total += attributes[2]
        if total > MAX_TOTAL_BYTES:
            raise SnapshotError("snapshot exceeds total byte limit")
        entries.append(entry)
        metadata.append(attributes)
    return entries, metadata


def capture_snapshot(root: Path, files: Sequence[str]) -> dict[str, object]:
    """Capture only named files; reject links, private paths and unbounded input."""
    if isinstance(files, (str, bytes)) or not isinstance(files, Sequence):
        raise SnapshotError("snapshot requires an explicit list of files")
    if not 1 <= len(files) <= MAX_FILES:
        raise SnapshotError("snapshot file count must be between 1 and the configured limit")
    paths = sorted(_normalized_path(path) for path in files)
    if len(set(paths)) != len(paths):
        raise SnapshotError("snapshot contains duplicate normalized paths")
    if not all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_NONBLOCK", "O_DIRECTORY")):
        raise SnapshotError("safe file descriptors are unavailable on this platform")
    try:
        resolved = root.resolve(strict=True)
        root_fd = os.open(resolved, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            base_commit = _base_commit(resolved)
            first = _capture_pass(root_fd, paths)
            second = _capture_pass(root_fd, paths)
            if first != second or base_commit != _base_commit(resolved):
                raise SnapshotError("selected files or base commit changed during capture")
            entries = first[0]
            return {
                "base_commit": base_commit,
                "snapshot": {
                    "state": "captured",
                    "sha256": snapshot_digest(base_commit, entries),
                    "files": entries,
                },
            }
        finally:
            os.close(root_fd)
    except (OSError, RuntimeError, NotImplementedError) as exc:
        raise SnapshotError("unable to safely read selected root or file") from exc


def validate_snapshot_manifest(expected: object, base_commit: object) -> list[str]:
    """Validate captured manifest shape and integrity without filesystem access."""
    if not isinstance(base_commit, str) or not _COMMIT.fullmatch(base_commit):
        return ["base_commit must be a full lowercase Git object ID or unknown"]
    if not isinstance(expected, dict) or set(expected) != {"state", "sha256", "files"}:
        return ["snapshot must contain exactly state, sha256 and files"]
    if expected["state"] != "captured":
        return ["snapshot state must be captured"]
    digest = expected["sha256"]
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        return ["snapshot sha256 must be 64 lowercase hexadecimal characters"]
    entries = expected["files"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
        return ["snapshot files must be a nonempty bounded list"]
    paths: list[str] = []
    total = 0
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "bytes"}:
            return ["snapshot file must contain exactly path, sha256 and bytes"]
        try:
            path = _normalized_path(entry["path"])
        except SnapshotError as exc:
            return [str(exc)]
        if entry["path"] != path:
            return ["snapshot file paths must already be normalized"]
        paths.append(path)
        file_digest, size = entry["sha256"], entry["bytes"]
        if not isinstance(file_digest, str) or not _SHA256.fullmatch(file_digest):
            return ["snapshot file sha256 must be 64 lowercase hexadecimal characters"]
        if type(size) is not int or not 0 <= size <= MAX_FILE_BYTES:
            return ["snapshot file bytes must be an integer within the file byte limit"]
        total += size
        if total > MAX_TOTAL_BYTES:
            return ["snapshot exceeds total byte limit"]
    if paths != sorted(set(paths)):
        return ["snapshot files must be sorted and unique"]
    if digest != snapshot_digest(base_commit, entries):
        return ["snapshot digest does not match base commit and file manifest"]
    return []


def verify_snapshot(root: Path, expected: object, base_commit: object) -> list[str]:
    """Recapture a valid manifest's listed files, returning diagnostics on failure."""
    errors = validate_snapshot_manifest(expected, base_commit)
    if errors:
        return errors
    assert isinstance(expected, dict)
    entries = expected["files"]
    assert isinstance(entries, list)
    try:
        actual = capture_snapshot(root, [entry["path"] for entry in entries])
    except SnapshotError as exc:
        return [str(exc)]
    errors = []
    if actual["base_commit"] != base_commit:
        errors.append("base commit changed since snapshot capture")
    if actual["snapshot"] != expected:
        errors.append("snapshot does not match the current selected files and base commit")
    return errors
