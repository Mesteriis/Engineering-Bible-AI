#!/usr/bin/env python3
"""Validate router fixtures and an optional configured runtime evaluator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import cast

from registry import all_registered_skills, load_registry


class RouterCaseError(RuntimeError):
    pass


def parse_router_cases(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise RouterCaseError(f"missing router cases: {path}")

    cases: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    section: str | None = None
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 2 and stripped.startswith("- id: "):
            current = {"id": stripped[len("- id: ") :].strip(), "skills": []}
            cases.append(current)
            section = None
            continue
        if current is None:
            continue
        if indent == 4 and stripped.startswith("prompt: "):
            current["prompt"] = stripped[len("prompt: ") :].strip().strip('"')
            continue
        if indent == 6 and stripped == "skills:":
            section = "skills"
            continue
        if indent == 8 and section == "skills" and stripped.startswith("- "):
            skills = current["skills"]
            if not isinstance(skills, list):
                raise RouterCaseError(f"{path}:{line_number}: invalid skills section")
            cast(list[str], skills).append(stripped[2:].strip())
            continue

    return cases


def validate_fixtures(root: Path) -> int:
    registry = load_registry(root)
    registered = set(all_registered_skills(registry))
    errors: list[str] = []
    cases = parse_router_cases(root / "tests" / "router-cases.yml")

    if not cases:
        errors.append("no router cases found")

    seen_ids: set[str] = set()
    for case in cases:
        case_id = str(case.get("id", ""))
        if not case_id:
            errors.append("router case without id")
        if case_id in seen_ids:
            errors.append(f"duplicate router case id: {case_id}")
        seen_ids.add(case_id)
        if not case.get("prompt"):
            errors.append(f"{case_id}: missing prompt")
        skills = case.get("skills", [])
        if not isinstance(skills, list) or not skills:
            errors.append(f"{case_id}: missing expected skills")
            continue
        for skill in skills:
            if skill not in registered:
                errors.append(f"{case_id}: expected skill is not registered: {skill}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("router case fixture validation passed")
    return 0


def validate_runtime(root: Path, evaluator: str | None) -> int:
    configured = evaluator or os.environ.get("ENGINEERING_BIBLE_ROUTER_EVALUATOR")
    if not configured:
        print("SKIP: runtime router evaluator is not configured")
        return 2
    executable = shutil.which(configured)
    if executable is None:
        candidate = Path(configured).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            executable = str(candidate.resolve())
    if executable is None:
        print(f"SKIP: runtime router evaluator is unavailable: {configured}")
        return 2

    cases = parse_router_cases(root / "tests" / "router-cases.yml")
    payload = {
        "schema_version": 1,
        "cases": [
            {"id": str(case.get("id", "")), "prompt": str(case.get("prompt", ""))} for case in cases
        ],
    }
    try:
        result = subprocess.run(
            [executable],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"runtime router evaluator failed: {exc}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(
            f"runtime router evaluator exited {result.returncode}: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return 1
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"runtime router evaluator returned invalid JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(response, dict) or response.get("schema_version") != 1:
        print("runtime router evaluator returned an unsupported response", file=sys.stderr)
        return 1
    raw_results = response.get("results")
    if not isinstance(raw_results, list):
        print("runtime router evaluator response has no results array", file=sys.stderr)
        return 1

    observed: dict[str, list[str]] = {}
    for index, item in enumerate(raw_results):
        if not isinstance(item, dict):
            print(f"runtime result {index} is not an object", file=sys.stderr)
            return 1
        case_id = item.get("id")
        skills = item.get("skills")
        if not isinstance(case_id, str) or not case_id or case_id in observed:
            print(f"runtime result {index} is invalid", file=sys.stderr)
            return 1
        if not isinstance(skills, list):
            print(f"runtime result {index} is invalid", file=sys.stderr)
            return 1
        normalized_skills: list[str] = []
        for skill in skills:
            if not isinstance(skill, str):
                print(f"runtime result {index} is invalid", file=sys.stderr)
                return 1
            normalized_skills.append(skill)
        observed[case_id] = normalized_skills

    errors: list[str] = []
    for case in cases:
        case_id = str(case.get("id", ""))
        expected_skills = case.get("skills", [])
        actual = observed.pop(case_id, None)
        if actual is None:
            errors.append(f"{case_id}: evaluator returned no result")
        elif actual != expected_skills:
            errors.append(f"{case_id}: expected {expected_skills!r}, evaluator returned {actual!r}")
    if observed:
        errors.append("evaluator returned unknown case ids: " + ", ".join(sorted(observed)))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("runtime router evaluation passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate router case fixtures")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Validate fixture structure and registry references",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Deprecated alias for --fixtures",
    )
    parser.add_argument("--runtime", action="store_true", help="Run the configured evaluator")
    parser.add_argument(
        "--runtime-evaluator",
        metavar="PATH",
        help="Executable implementing the JSON runtime-evaluator protocol",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.fixtures and not args.static and not args.runtime:
        parser.error("choose --fixtures, --runtime, or both")
    if args.static:
        print("warning: --static is deprecated; use --fixtures", file=sys.stderr)
    root = args.root.expanduser().resolve()
    try:
        result = 0
        if args.fixtures or args.static:
            result = validate_fixtures(root) or result
        if args.runtime:
            result = validate_runtime(root, args.runtime_evaluator) or result
        return result
    except RouterCaseError as exc:
        print(f"router-cases: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
