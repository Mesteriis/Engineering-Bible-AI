#!/usr/bin/env python3
"""Validate static router case fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

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
            skills.append(stripped[2:].strip())
            continue

    return cases


def validate_static(root: Path) -> int:
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
    print("router cases static validation passed")
    return 0


def validate_runtime(root: Path) -> int:
    if not shutil.which("codex"):
        print("SKIP: codex CLI is unavailable; runtime router cases not run")
        return 0
    if not (root / "skills" / "workflow-router" / "SKILL.md").is_file():
        print("SKIP: workflow-router skill is unavailable; runtime router cases not run")
        return 0
    if not sys.stdin.isatty():
        print("SKIP: runtime router harness is interactive-only in this package")
        return 0
    subprocess.run(["codex", "--version"], check=False)
    print("SKIP: runtime router harness is not configured for non-interactive CI")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate router case fixtures")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--static", action="store_true", help="Validate fixtures and registry references")
    parser.add_argument("--runtime", action="store_true", help="Best-effort runtime router smoke")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.static and not args.runtime:
        parser.error("choose --static, --runtime, or both")
    root = args.root.expanduser().resolve()
    try:
        result = 0
        if args.static:
            result = validate_static(root) or result
        if args.runtime:
            result = validate_runtime(root) or result
        return result
    except RouterCaseError as exc:
        print(f"router-cases: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
