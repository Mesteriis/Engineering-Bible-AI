#!/usr/bin/env python3
"""Minimal markdown lint checks used by local validation.

The checks here are intentionally small and stable:
* no trailing whitespace,
* no tab characters,
* heading markers are followed by text.
"""

from __future__ import annotations

from pathlib import Path
import sys


TRAILING_WHITESPACE = "trailing whitespace"
TAB_CHAR = "tab character"
EMPTY_HEADING = "empty heading"


def iter_markdown_files(root: Path) -> list[Path]:
    skipped_dirs = {
        ".engineering-bible",
        ".git",
        ".serena",
        ".worktrees",
        "__pycache__",
        ".venv",
        "node_modules",
    }
    files: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in skipped_dirs for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def validate_file(path: Path) -> list[str]:
    issues: list[str] = []
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if raw_line.rstrip("\r\n") != raw_line.rstrip():
            issues.append(f"{path}:{index}: {TRAILING_WHITESPACE}")
        if "\t" in raw_line:
            issues.append(f"{path}:{index}: {TAB_CHAR}")
        if raw_line.strip().startswith("#") and not raw_line.strip().lstrip("#").strip():
            issues.append(f"{path}:{index}: {EMPTY_HEADING}")
    return issues


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: validate-markdown-style.py [root]")
        return 1
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    issues: list[str] = []
    for path in iter_markdown_files(root):
        issues.extend(validate_file(path))

    if issues:
        for issue in issues:
            print(issue)
        print(f"markdown style check failed: {len(issues)} issue(s)")
        return 1

    print("markdown style check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
