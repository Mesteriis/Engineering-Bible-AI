#!/usr/bin/env python3
"""Skill registry reader and validator for Engineering Bible AI."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path
import sys
from typing import cast


GENERATED_BEGIN = "<!-- BEGIN GENERATED SKILL REGISTRY -->"
GENERATED_END = "<!-- END GENERATED SKILL REGISTRY -->"
GENERATED_DOCS = {
    "README.md": ("Default groups", "Optional groups"),
    "README.ru.md": ("Группы по умолчанию", "Опциональные группы"),
    "MANIFEST.md": ("Default groups", "Optional groups"),
}


class RegistryError(RuntimeError):
    pass


def parse_registry(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise RegistryError(f"missing registry: {path}")

    payload: dict[str, object] = {
        "default_groups": [],
        "groups": {},
        "optional": {},
    }
    section: str | None = None
    current_group: str | None = None

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0:
            current_group = None
            if stripped.endswith(":"):
                section = stripped[:-1]
                if section not in {"default_groups", "groups", "optional"}:
                    payload[section] = {}
                continue
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                payload[key.strip()] = parse_scalar(value.strip())
                section = None
                continue
            raise RegistryError(f"{path}:{line_number}: unsupported top-level line: {raw_line}")

        if section == "default_groups" and indent == 2 and stripped.startswith("- "):
            cast_list(payload["default_groups"]).append(stripped[2:].strip())
            continue

        if section in {"groups", "optional"} and indent == 2 and stripped.endswith(":"):
            current_group = stripped[:-1]
            cast_dict(payload[section])[current_group] = []
            continue

        if (
            section in {"groups", "optional"}
            and current_group is not None
            and indent == 4
            and stripped.startswith("- ")
        ):
            cast_list(cast_dict(payload[section])[current_group]).append(stripped[2:].strip())
            continue

        raise RegistryError(f"{path}:{line_number}: unsupported registry line: {raw_line}")

    return payload


def parse_scalar(value: str) -> object:
    if value.isdigit():
        return int(value)
    return value.strip('"').strip("'")


def cast_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise RegistryError(f"expected list, got {type(value).__name__}")
    return cast(list[str], value)


def cast_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RegistryError(f"expected mapping, got {type(value).__name__}")
    return cast(dict[str, object], value)


def registry_path(root: Path) -> Path:
    return root / "skills" / "registry.yml"


def load_registry(root: Path) -> dict[str, object]:
    return parse_registry(registry_path(root))


def unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def group_map(registry: dict[str, object], *, include_optional: bool) -> dict[str, list[str]]:
    groups = {name: cast_list(skills) for name, skills in cast_dict(registry["groups"]).items()}
    if include_optional:
        for name, skills in cast_dict(registry["optional"]).items():
            groups[name] = cast_list(skills)
            groups[f"optional.{name}"] = cast_list(skills)
    return groups


def default_group_names(registry: dict[str, object]) -> list[str]:
    return cast_list(registry["default_groups"])


def selected_skills(
    registry: dict[str, object],
    *,
    groups: list[str],
    include_all: bool,
) -> list[str]:
    available = group_map(registry, include_optional=True)
    if include_all:
        selected_groups = list(cast_dict(registry["groups"])) + list(
            cast_dict(registry["optional"])
        )
    else:
        selected_groups = default_group_names(registry) + groups

    missing_groups = [name for name in selected_groups if name not in available]
    if missing_groups:
        raise RegistryError("unknown skill group(s): " + ", ".join(missing_groups))

    skills: list[str] = []
    for name in selected_groups:
        skills.extend(available[name])
    return unique(skills)


def all_registered_skills(registry: dict[str, object]) -> list[str]:
    skills: list[str] = []
    for value in cast_dict(registry["groups"]).values():
        skills.extend(cast_list(value))
    for value in cast_dict(registry["optional"]).values():
        skills.extend(cast_list(value))
    return unique(skills)


def render_group(name: str, skills: list[str]) -> str:
    rendered_skills = ", ".join(f"`{skill}`" for skill in skills)
    return f"- **{name}:** {rendered_skills}."


def render_generated_block(
    registry: dict[str, object],
    *,
    default_heading: str,
    optional_heading: str,
) -> str:
    groups = {name: cast_list(skills) for name, skills in cast_dict(registry["groups"]).items()}
    optional = {name: cast_list(skills) for name, skills in cast_dict(registry["optional"]).items()}
    default_lines = [render_group(name, groups[name]) for name in default_group_names(registry)]
    optional_lines = [render_group(name, skills) for name, skills in optional.items()]
    if not default_lines:
        default_lines = ["- None."]
    if not optional_lines:
        optional_lines = ["- None."]
    return "\n".join(
        [
            GENERATED_BEGIN,
            f"### {default_heading}",
            "",
            *default_lines,
            "",
            f"### {optional_heading}",
            "",
            *optional_lines,
            GENERATED_END,
        ]
    )


def replace_generated_block(text: str, block: str, *, document: str) -> str:
    if text.count(GENERATED_BEGIN) != 1 or text.count(GENERATED_END) != 1:
        raise RegistryError(
            f"{document} must contain exactly one generated skill registry marker pair"
        )
    start = text.index(GENERATED_BEGIN)
    end = text.index(GENERATED_END, start) + len(GENERATED_END)
    return text[:start] + block + text[end:]


def expected_generated_doc(root: Path, doc_name: str) -> str:
    headings = GENERATED_DOCS[doc_name]
    registry = load_registry(root)
    block = render_generated_block(
        registry,
        default_heading=headings[0],
        optional_heading=headings[1],
    )
    path = root / doc_name
    if not path.is_file():
        raise RegistryError(f"missing documentation file: {doc_name}")
    return replace_generated_block(
        path.read_text(encoding="utf-8"),
        block,
        document=doc_name,
    )


def validate_generated_docs(root: Path) -> list[str]:
    issues: list[str] = []
    for doc_name in GENERATED_DOCS:
        path = root / doc_name
        try:
            expected = expected_generated_doc(root, doc_name)
        except RegistryError as exc:
            issues.append(str(exc))
            continue
        if path.read_text(encoding="utf-8") != expected:
            issues.append(f"{doc_name}: generated skill registry block is stale")
    return issues


def update_generated_docs(root: Path) -> list[Path]:
    changed: list[Path] = []
    for doc_name in GENERATED_DOCS:
        path = root / doc_name
        expected = expected_generated_doc(root, doc_name)
        if path.read_text(encoding="utf-8") == expected:
            continue
        path.write_text(expected, encoding="utf-8")
        changed.append(path)
    return changed


def validate_registry(root: Path) -> list[str]:
    registry = load_registry(root)
    errors: list[str] = []

    for group in default_group_names(registry):
        if group not in group_map(registry, include_optional=False):
            errors.append(f"default group is not defined under groups: {group}")

    registered = set(all_registered_skills(registry))
    for skill in sorted(registered):
        if not (root / "skills" / skill / "SKILL.md").is_file():
            errors.append(f"registry skill is missing SKILL.md: {skill}")

    actual = {path.parent.name for path in (root / "skills").glob("*/SKILL.md") if path.is_file()}
    for skill in sorted(actual - registered):
        errors.append(f"skill exists but is missing from registry: {skill}")

    for doc_name in GENERATED_DOCS:
        doc_path = root / doc_name
        if not doc_path.is_file():
            errors.append(f"missing documentation file: {doc_name}")
            continue
        text = doc_path.read_text(encoding="utf-8")
        if "skills/registry.yml" not in text:
            errors.append(f"{doc_name} does not mention skills/registry.yml")
        for skill in sorted(registered):
            if skill not in text:
                errors.append(f"{doc_name} does not mention registered skill: {skill}")

    errors.extend(validate_generated_docs(root))

    return errors


def command_skills(args: argparse.Namespace) -> int:
    registry = load_registry(args.root)
    skills = selected_skills(registry, groups=args.group, include_all=args.all)
    for skill in skills:
        print(skill)
    return 0


def command_groups(args: argparse.Namespace) -> int:
    registry = load_registry(args.root)
    for name in group_map(registry, include_optional=args.include_optional):
        print(name)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    errors = validate_registry(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("skill registry validation passed")
    return 0


def command_docs(args: argparse.Namespace) -> int:
    if args.write:
        changed = update_generated_docs(args.root)
        for path in changed:
            print(f"updated {path.relative_to(args.root)}")
        if not changed:
            print("generated skill registry blocks are current")
        return 0

    issues = validate_generated_docs(args.root)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print("generated skill registry blocks are current")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and validate skills/registry.yml")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository or installed package root containing skills/registry.yml",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    skills = subparsers.add_parser("skills", help="Print selected skill names")
    skills.add_argument("--group", action="append", default=[], help="Additional group to include")
    skills.add_argument("--all", action="store_true", help="Include optional groups too")
    skills.set_defaults(func=command_skills)

    groups = subparsers.add_parser("groups", help="Print group names")
    groups.add_argument("--include-optional", action="store_true")
    groups.set_defaults(func=command_groups)

    validate = subparsers.add_parser("validate", help="Validate registry and docs")
    validate.set_defaults(func=command_validate)

    docs = subparsers.add_parser("docs", help="Check or update generated registry blocks")
    docs_mode = docs.add_mutually_exclusive_group()
    docs_mode.add_argument(
        "--check",
        action="store_true",
        help="Check generated blocks (default)",
    )
    docs_mode.add_argument("--write", action="store_true", help="Update generated blocks in place")
    docs.set_defaults(func=command_docs)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.root = args.root.expanduser().resolve()
    try:
        return int(args.func(args))
    except RegistryError as exc:
        print(f"registry: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
