#!/usr/bin/env python3
"""Build immutable release artifacts and a checksum manifest from Git HEAD."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ReleaseBuildError(RuntimeError):
    pass


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ReleaseBuildError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(root: Path, output: Path) -> Path:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        raise ReleaseBuildError("VERSION must contain strict SemVer")
    dirty = run_git(root, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise ReleaseBuildError("release artifacts require a clean working tree")
    revision = run_git(root, "rev-parse", "HEAD")
    output.mkdir(parents=True, exist_ok=True)

    archive = output / f"engineering-bible-ai-{version}.tar.gz"
    archive_result = subprocess.run(
        [
            "git",
            "archive",
            "--format=tar.gz",
            f"--prefix=engineering-bible-ai-{version}/",
            f"--output={archive}",
            revision,
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if archive_result.returncode != 0:
        raise ReleaseBuildError(archive_result.stderr.strip() or "git archive failed")

    bootstrap = output / "install.sh"
    shutil.copy2(root / "scripts" / "install.sh", bootstrap)
    bootstrap.chmod(0o755)

    artifacts = {}
    for artifact in (archive, bootstrap):
        artifacts[artifact.name] = {
            "sha256": sha256_file(artifact),
            "size": artifact.stat().st_size,
        }
    manifest = output / "release-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "version": version,
                "tag": f"v{version}",
                "commit": revision,
                "artifacts": artifacts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    try:
        manifest = build(args.root.resolve(), args.output.resolve())
    except (OSError, ReleaseBuildError) as exc:
        print(f"release build failed: {exc}", file=sys.stderr)
        return 1
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
