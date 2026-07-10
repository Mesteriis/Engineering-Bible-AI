#!/usr/bin/env python3
"""Validate version, changelog, and optional Git tag release invariants."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _read(path: Path, issues: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"cannot read {path.name}: {exc}")
        return ""


def validate(
    root: Path,
    *,
    require_tag: bool = False,
    trigger_tag: str | None = None,
    require_main_ancestor: bool = False,
) -> list[str]:
    issues: list[str] = []
    version = _read(root / "VERSION", issues).strip()
    if not SEMVER.fullmatch(version):
        issues.append("VERSION must contain strict SemVer without a v prefix")
        return issues

    pyproject = _read(root / "pyproject.toml", issues)
    version_match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject, re.MULTILINE)
    if version_match is None:
        issues.append("pyproject.toml is missing project version")
    elif version_match.group(1) != version:
        issues.append(
            f"pyproject.toml version {version_match.group(1)!r} does not match VERSION {version!r}"
        )

    changelog = _read(root / "CHANGELOG.md", issues)
    heading = re.compile(
        rf"^##\s+(?:\[{re.escape(version)}\]|{re.escape(version)})(?:\s|$)", re.MULTILINE
    )
    if not heading.search(changelog):
        issues.append(f"CHANGELOG.md is missing a section for {version}")

    bootstrap = _read(root / "scripts" / "install.sh", issues)
    bootstrap_match = re.search(r'^BOOTSTRAP_VERSION="([^"]+)"$', bootstrap, re.MULTILINE)
    if bootstrap_match is None:
        issues.append("scripts/install.sh is missing BOOTSTRAP_VERSION")
    elif bootstrap_match.group(1) != version:
        issues.append(
            f"scripts/install.sh bootstrap version {bootstrap_match.group(1)!r} does not match VERSION {version!r}"
        )

    expected = f"v{version}"
    if trigger_tag is not None and trigger_tag != expected:
        issues.append(f"release trigger tag {trigger_tag!r} must equal {expected!r}")

    if require_tag:
        result = subprocess.run(
            ["git", "tag", "--points-at", "HEAD"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            issues.append(f"cannot inspect Git tags: {result.stderr.strip()}")
        elif expected not in result.stdout.splitlines():
            issues.append(f"HEAD must be tagged exactly {expected}")
    if require_main_ancestor:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            issues.append("release commit must be reachable from origin/main")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--trigger-tag", help="Tag that triggered the release workflow")
    parser.add_argument("--require-main-ancestor", action="store_true")
    args = parser.parse_args(argv)

    issues = validate(
        args.root.resolve(),
        require_tag=args.require_tag,
        trigger_tag=args.trigger_tag,
        require_main_ancestor=args.require_main_ancestor,
    )
    if issues:
        print("release contract validation failed", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("release contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
