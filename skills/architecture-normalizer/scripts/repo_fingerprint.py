#!/usr/bin/env python3
"""Compute a deterministic repository fingerprint for architecture manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Iterable


ALGORITHM = "architecture-normalizer-repo-fingerprint-v1"
EXCLUDED_DIRS = {
    ".architecture",
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )


def resolve_root(path: Path) -> Path:
    candidate = path.resolve()
    result = run_git(candidate, ["rev-parse", "--show-toplevel"])
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return candidate


def is_excluded(rel_path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in rel_path.parts)


def git_file_list(root: Path) -> list[Path] | None:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None

    paths: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        rel = Path(raw.decode("utf-8", errors="surrogateescape"))
        if is_excluded(rel):
            continue
        full_path = root / rel
        try:
            full_path.lstat()
        except FileNotFoundError:
            continue
        if full_path.is_file() or full_path.is_symlink():
            paths.append(rel)
    return sorted(paths, key=lambda item: item.as_posix())


def walked_file_list(root: Path) -> list[Path]:
    paths: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dir_path = Path(dirpath)
        rel_dir = dir_path.relative_to(root)
        dirnames[:] = sorted(name for name in dirnames if name not in EXCLUDED_DIRS)
        if rel_dir != Path(".") and is_excluded(rel_dir):
            continue
        for filename in sorted(filenames):
            full_path = dir_path / filename
            rel = full_path.relative_to(root)
            if not is_excluded(rel) and (full_path.is_file() or full_path.is_symlink()):
                paths.append(rel)
    return sorted(paths, key=lambda item: item.as_posix())


def iter_files(root: Path) -> Iterable[Path]:
    git_paths = git_file_list(root)
    if git_paths is not None:
        return git_paths
    return walked_file_list(root)


def content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        return digest.hexdigest()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(root: Path, include_files: bool) -> dict[str, object]:
    entries: list[dict[str, str]] = []
    overall = hashlib.sha256()

    for rel in iter_files(root):
        full_path = root / rel
        st = full_path.lstat()
        mode = oct(stat.S_IMODE(st.st_mode))
        file_hash = content_hash(full_path)
        rel_posix = rel.as_posix()
        entries.append({"path": rel_posix, "mode": mode, "sha256": f"sha256:{file_hash}"})
        overall.update(rel_posix.encode("utf-8", errors="surrogateescape"))
        overall.update(b"\0")
        overall.update(mode.encode("ascii"))
        overall.update(b"\0")
        overall.update(file_hash.encode("ascii"))
        overall.update(b"\n")

    payload: dict[str, object] = {
        "algorithm": ALGORITHM,
        "root": str(root),
        "value": f"sha256:{overall.hexdigest()}",
        "file_count": len(entries),
        "excluded_dirs": sorted(EXCLUDED_DIRS),
    }
    if include_files:
        payload["files"] = entries
    return payload


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository path")
    parser.add_argument("--json", action="store_true", help="Print JSON payload instead of hash only")
    parser.add_argument("--files", action="store_true", help="Include per-file hashes in JSON output")
    args = parser.parse_args(argv)

    root = resolve_root(Path(args.repo))
    payload = fingerprint(root, include_files=args.files)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["value"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
