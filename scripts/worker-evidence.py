#!/usr/bin/env python3
"""Fingerprint allowed inputs, validate worker records, and compare recorded runs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys

from worker_results import compare_runs, inspect_record
from worker_control import evaluate_continuation
from worker_snapshot import capture_snapshot, verify_snapshot


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
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("JSON input must be a regular file")
        content = stream.read(MAX_JSON_BYTES + 1)
    if len(content) > MAX_JSON_BYTES:
        raise ValueError("JSON input exceeds byte limit")
    return json.loads(content, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def artifact_issues(record: dict[str, object], root: Path) -> list[str]:
    """Check referenced files exist locally; their contents are never executed."""
    issues: list[str] = []
    if not root.is_dir():
        return ["artifact root must be an existing directory"]
    paths = record["artifacts"]
    assert isinstance(paths, list)
    for relative in paths:
        assert isinstance(relative, str)
        current = root
        try:
            parts = relative.split("/")
            for index, part in enumerate(parts):
                current /= part
                mode = current.lstat().st_mode
                if stat.S_ISLNK(mode):
                    raise ValueError("symlink in artifact path")
                if index < len(parts) - 1 and not stat.S_ISDIR(mode):
                    raise ValueError("artifact parent is not a directory")
            if not stat.S_ISREG(mode):
                raise ValueError("artifact is not a regular file")
        except (OSError, ValueError):
            issues.append(f"artifact unavailable or unsafe: {relative}")
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot", help="Hash only explicitly named source files")
    snapshot.add_argument("--root", type=Path, required=True)
    snapshot.add_argument("--file", action="append", required=True, dest="files")
    validate = commands.add_parser("validate", help="Check one launcher-supplied worker result")
    validate.add_argument("record", type=Path)
    validate.add_argument(
        "--source-root", type=Path, help="Verify source fingerprint against files"
    )
    validate.add_argument(
        "--artifacts-root", type=Path, help="Verify declared artifact files exist"
    )
    compare = commands.add_parser("compare", help="Compare JSON arrays of matched worker results")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    control = commands.add_parser("continue", help="Evaluate the next step of a bounded run")
    control.add_argument("request", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            result = capture_snapshot(args.root, args.files)
        elif args.command == "compare":
            result = compare_runs(read_json(args.baseline), read_json(args.candidate))
        elif args.command == "continue":
            result = evaluate_continuation(read_json(args.request))
        else:
            record = read_json(args.record)
            result = inspect_record(record)
            result.update(source_status="SKIP", artifact_status="SKIP")
            if result["contract_status"] == "PASS":
                assert isinstance(record, dict)
                issues = result["issues"]
                assert isinstance(issues, list)
                if args.source_root:
                    errors = verify_snapshot(
                        args.source_root, record["snapshot"], record["base_commit"]
                    )
                    issues.extend(errors)
                    result["source_status"] = "FAIL" if errors else "PASS"
                if args.artifacts_root:
                    errors = artifact_issues(record, args.artifacts_root)
                    issues.extend(errors)
                    result["artifact_status"] = "FAIL" if errors else "PASS"
                if issues:
                    result["outcome"] = "FAIL"
                elif result["outcome"] == "PASS" and (
                    result["source_status"] == "SKIP" or result["artifact_status"] == "SKIP"
                ):
                    result["outcome"] = "SKIP"
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        if args.command == "continue":
            decision = result["decision"]
            assert isinstance(decision, str)
            return {"continue": 0, "stop": 1, "checkpoint": 2, "blocked": 2}[decision]
        outcome = result.get("outcome", "PASS")
        return 1 if outcome == "FAIL" else 2 if outcome in ("SKIP", "BLOCKED") else 0
    except (OSError, ValueError, RecursionError):
        # Do not echo potentially sensitive raw input, host paths, or log content.
        print(
            "worker-evidence: invalid/duplicate JSON, unsafe input, or unavailable file",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
