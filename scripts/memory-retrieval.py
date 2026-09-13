#!/usr/bin/env python3
"""Plan optional search variants or fuse caller-supplied ranked document evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys

from memory_retrieval import fuse_rankings, query_plan


MAX_JSON_BYTES = 8 * 1024 * 1024


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError("non-finite JSON number")


def read_json(path: Path) -> object:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise ValueError("safe JSON file descriptors are unavailable on this platform")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("JSON input must be a regular file")
        content = stream.read(MAX_JSON_BYTES + 1)
    if len(content) > MAX_JSON_BYTES:
        raise ValueError("JSON input exceeds byte limit")
    return json.loads(content, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="Emit original and optional content-word query")
    plan.add_argument("query")
    fuse = commands.add_parser("fuse", help="Fuse ranked JSON results with source provenance")
    fuse.add_argument("rankings", type=Path)
    fuse.add_argument("--limit", type=int, default=5)
    fuse.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = query_plan(args.query)
            exit_code = 0
        else:
            result = fuse_rankings(
                read_json(args.rankings), limit=args.limit, source_root=args.source_root
            )
            exit_code = {"PASS": 0, "FAIL": 1, "SKIP": 2}[str(result["outcome"])]
    except (ValueError, OSError, RecursionError) as exc:
        result = {"outcome": "FAIL", "issues": [str(exc)]}
        exit_code = 1
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
