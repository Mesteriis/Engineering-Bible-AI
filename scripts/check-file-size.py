#!/usr/bin/env python3
"""Check human-authored source files for excessive line counts.

Default policy:
- warn above 800 logical lines
- soft violation above 1,500 logical lines
- hard violation above 10,000 logical lines

Generated/vendor/lock/build folders are ignored by default.
Because apparently we need a script to tell us that a 10k-line source file is not a personality trait.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Iterable

DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "target",
    "out",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "vendor",
    "third_party",
    "external",
    ".terraform",
}

DEFAULT_IGNORED_SUFFIXES = {
    ".lock",
    ".min.js",
    ".map",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".xz",
    ".7z",
    ".bin",
    ".wasm",
}

SOURCE_EXTENSIONS = {
    ".py", ".pyi",
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".rs",
    ".go",
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx",
    ".yaml", ".yml",
    ".toml", ".json", ".md",
}


def is_ignored_path(path: Path, root: Path, ignored_dirs: set[str]) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return any(part in ignored_dirs for part in rel.parts)


def has_ignored_suffix(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in DEFAULT_IGNORED_SUFFIXES)


def iter_files(root: Path, ignored_dirs: set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
        if is_ignored_path(current, root, ignored_dirs):
            continue
        for filename in filenames:
            path = current / filename
            if has_ignored_suffix(path):
                continue
            if path.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            yield path


def count_logical_lines(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    except UnicodeDecodeError:
        return None
    except OSError as exc:
        print(f"WARN: cannot read {path}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check source file line-count limits.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan")
    parser.add_argument("--warn", type=int, default=800, help="Warning threshold")
    parser.add_argument("--soft", type=int, default=1500, help="Soft violation threshold")
    parser.add_argument("--hard", type=int, default=10000, help="Hard failure threshold")
    parser.add_argument("--fail-soft", action="store_true", help="Exit non-zero on soft violations too")
    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        help="Additional directory name to ignore; may be repeated",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ignored_dirs = DEFAULT_IGNORED_DIRS | set(args.ignore_dir)

    warnings: list[tuple[int, Path]] = []
    soft: list[tuple[int, Path]] = []
    hard: list[tuple[int, Path]] = []

    for path in iter_files(root, ignored_dirs):
        count = count_logical_lines(path)
        if count is None:
            continue
        if count > args.hard:
            hard.append((count, path))
        elif count > args.soft:
            soft.append((count, path))
        elif count > args.warn:
            warnings.append((count, path))

    def print_group(title: str, rows: list[tuple[int, Path]]) -> None:
        if not rows:
            return
        print(f"\n{title}")
        for count, path in sorted(rows, reverse=True):
            rel = path.relative_to(root)
            print(f"  {count:>6}  {rel}")

    print_group(f"WARN > {args.warn} logical lines", warnings)
    print_group(f"SOFT > {args.soft} logical lines", soft)
    print_group(f"HARD > {args.hard} logical lines", hard)

    if hard:
        print("\nResult: failed hard line-count policy.")
        return 2
    if soft and args.fail_soft:
        print("\nResult: failed soft line-count policy.")
        return 1

    print("\nResult: passed configured hard line-count policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
