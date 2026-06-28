#!/usr/bin/env python3
"""Validate repository-local Codex skill frontmatter."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter marker")

    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return metadata
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = strip_quotes(value)

    raise ValueError("missing closing frontmatter marker")


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [f"{skill_dir}: missing SKILL.md"]

    try:
        metadata = parse_frontmatter(skill_file)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return [f"{skill_file}: {exc}"]

    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if name != skill_dir.name:
        errors.append(f"{skill_file}: name {name!r} does not match directory {skill_dir.name!r}")
    if not description:
        errors.append(f"{skill_file}: missing description")
    if len(description) > 1000:
        errors.append(f"{skill_file}: description exceeds 1000 characters")

    body = skill_file.read_text(encoding="utf-8")
    if re.search(r"(?im)^\s*(TODO|TBD|FIXME|REPLACE_ME)\b", body):
        errors.append(f"{skill_file}: contains placeholder text")

    agent_file = skill_dir / "agents" / "openai.yaml"
    if agent_file.exists():
        agent_text = agent_file.read_text(encoding="utf-8")
        if "interface:" not in agent_text:
            errors.append(f"{agent_file}: missing interface block")
        if f"${skill_dir.name}" not in agent_text:
            errors.append(f"{agent_file}: default prompt does not mention ${skill_dir.name}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SKILL.md frontmatter.")
    parser.add_argument("skills_root", nargs="?", default="skills")
    args = parser.parse_args()

    skills_root = Path(args.skills_root)
    if not skills_root.is_dir():
        print(f"missing skills root: {skills_root}", file=sys.stderr)
        return 2

    errors: list[str] = []
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        errors.extend(validate_skill(skill_dir))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("skill frontmatter validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
