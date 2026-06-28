#!/usr/bin/env python3
"""Validate Code Wiki structure and metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Mapping, Sequence


REQUIRED_WIKI_DIRS = (
    "systems",
    "components",
    "flows",
    "api",
    "data",
    "integrations",
    "operations",
    "decisions",
    "glossary",
    "_meta",
)

REQUIRED_META_FILES = (
    "index.md",
    "policy.yml",
    "repo-index.json",
    "source-map.yml",
    "coverage.yml",
    "drift-report.md",
    "update-plan.md",
    "patch-preview.diff",
    "last-run.json",
)

OBSIDIAN_LINK_RE = re.compile(r"\[\[([^\[\]\n]+)\]\]")
COVERAGE_PATH_RE = re.compile(r"^\s*-\s+path:\s*(.+?)\s*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a generated Code Wiki.")
    parser.add_argument("--repo", required=True, help="Repository root to validate.")
    parser.add_argument(
        "--wiki-path",
        default="docs/wiki",
        help="Wiki path relative to --repo, or an absolute path.",
    )
    parser.add_argument(
        "--meta-path",
        default="docs/wiki/_meta",
        help="Metadata path relative to --repo, or an absolute path.",
    )
    return parser.parse_args()


def resolve_repo(path: str) -> Path:
    return Path(path).expanduser().resolve()


def resolve_repo_path(repo: Path, path: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo / candidate).resolve()


def validate_structure(wiki_path: Path, meta_path: Path) -> list[str]:
    errors: list[str] = []

    if not wiki_path.exists():
        errors.append(f"Wiki path does not exist: {wiki_path}")
    elif not wiki_path.is_dir():
        errors.append(f"Wiki path is not a directory: {wiki_path}")

    for directory in REQUIRED_WIKI_DIRS:
        path = wiki_path / directory
        if not path.exists():
            errors.append(f"Required wiki directory is missing: {path}")
        elif not path.is_dir():
            errors.append(f"Required wiki path is not a directory: {path}")

    if not meta_path.exists():
        errors.append(f"Metadata path does not exist: {meta_path}")
    elif not meta_path.is_dir():
        errors.append(f"Metadata path is not a directory: {meta_path}")

    for file_name in REQUIRED_META_FILES:
        path = meta_path / file_name
        if not path.exists():
            errors.append(f"Required meta file is missing: {path}")
        elif not path.is_file():
            errors.append(f"Required meta path is not a file: {path}")

    return errors


def load_repo_index(meta_path: Path) -> tuple[list[Mapping[str, object]], list[str]]:
    index_path = meta_path / "repo-index.json"
    errors: list[str] = []

    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [], [f"Repository index does not exist: {index_path}"]
    except OSError as exc:
        return [], [f"Repository index cannot be read: {index_path}: {exc}"]
    except json.JSONDecodeError as exc:
        return [], [
            f"Repository index is not valid JSON: {index_path}: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ]

    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list):
        return [], [f"Repository index has no files list: {index_path}"]

    indexed_files: list[Mapping[str, object]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            errors.append(
                f"Repository index file entry files[{index}] is invalid: expected object"
            )
            continue

        label = file_entry_label(index, item)
        path = item.get("path")
        if not isinstance(path, str) or not path:
            errors.append(
                f"Repository index file entry {label} has invalid field path: "
                "expected non-empty string"
            )
        else:
            path_error = source_path_validation_error(path)
            if path_error is not None:
                errors.append(
                    f"Repository index file entry {label} has invalid source path: "
                    f"{path_error}"
                )

        secret_redacted = item.get("secret_redacted")
        if not isinstance(secret_redacted, bool):
            errors.append(
                f"Repository index file entry {label} has invalid field "
                "secret_redacted: expected bool"
            )

        indexed_files.append(item)

    return indexed_files, errors


def file_entry_label(index: int, indexed_file: Mapping[str, object]) -> str:
    path = indexed_file.get("path")
    if isinstance(path, str) and path:
        return path
    return f"files[{index}]"


def markdown_files(wiki_path: Path) -> list[Path]:
    if not wiki_path.is_dir():
        return []
    return sorted(path for path in wiki_path.rglob("*.md") if path.is_file())


def page_keys(wiki_path: Path) -> tuple[set[str], set[str]]:
    paths: set[str] = set()
    stems: set[str] = set()

    for path in markdown_files(wiki_path):
        relative = path.relative_to(wiki_path).with_suffix("").as_posix()
        paths.add(relative)
        stems.add(path.stem)

    return paths, stems


def normalize_link_target(raw_target: str) -> str:
    target = raw_target.split("|", 1)[0].split("#", 1)[0].strip()
    target = target.replace("\\", "/").strip("/")
    if target.endswith(".md"):
        target = target[:-3]
    return normalize_posix(target)


def normalize_posix(path: str) -> str:
    parts: list[str] = []
    for part in PurePosixPath(path).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            else:
                parts.append(part)
            continue
        parts.append(part)
    return "/".join(parts)


def link_resolves(
    *,
    target: str,
    source_page: Path,
    wiki_path: Path,
    known_paths: set[str],
    known_stems: set[str],
) -> bool:
    if not target:
        return False

    if target in known_stems or target in known_paths:
        return True

    try:
        source_relative = source_page.relative_to(wiki_path).with_suffix("")
    except ValueError:
        return False

    source_parent = source_relative.parent.as_posix()
    if source_parent in {"", "."}:
        return target in known_paths

    source_relative_target = normalize_posix(f"{source_parent}/{target}")
    return source_relative_target in known_paths


def validate_obsidian_links(wiki_path: Path) -> list[str]:
    errors: list[str] = []
    known_paths, known_stems = page_keys(wiki_path)

    for path in markdown_files(wiki_path):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"Markdown file is not valid UTF-8: {path}: {exc}")
            continue
        except OSError as exc:
            errors.append(f"Markdown file cannot be read: {path}: {exc}")
            continue

        for match in OBSIDIAN_LINK_RE.finditer(text):
            raw_target = match.group(1)
            target = normalize_link_target(raw_target)
            if not link_resolves(
                target=target,
                source_page=path,
                wiki_path=wiki_path,
                known_paths=known_paths,
                known_stems=known_stems,
            ):
                line_number = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"Unresolved Obsidian link in {path}:{line_number}: "
                    f"[[{raw_target}]]"
                )

    return errors


def validate_mermaid_fences(wiki_path: Path) -> list[str]:
    errors: list[str] = []

    for path in markdown_files(wiki_path):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as exc:
            errors.append(f"Markdown file is not valid UTF-8: {path}: {exc}")
            continue
        except OSError as exc:
            errors.append(f"Markdown file cannot be read: {path}: {exc}")
            continue

        active_fence: tuple[str, int] | None = None
        in_mermaid = False
        mermaid_opening_line = 0
        for line_number, line in enumerate(lines, start=1):
            fence = fence_marker(line)
            if active_fence is not None:
                if (
                    fence is not None
                    and fence[0] == active_fence[0]
                    and fence[1] >= active_fence[1]
                ):
                    active_fence = None
                    in_mermaid = False
                continue

            if fence is None:
                continue

            marker, marker_length, info = fence
            active_fence = (marker, marker_length)
            in_mermaid = is_mermaid_info_string(info)
            if in_mermaid:
                mermaid_opening_line = line_number

        if in_mermaid:
            errors.append(f"Unclosed Mermaid fence in {path}:{mermaid_opening_line}")

    return errors


def fence_marker(line: str) -> tuple[str, int, str] | None:
    match = FENCE_RE.match(line)
    if match is None:
        return None

    marker = match.group(1)
    info = match.group(2).strip()
    return marker[0], len(marker), info


def is_mermaid_info_string(info: str) -> bool:
    if not info:
        return False
    language = info.split(maxsplit=1)[0].strip().lower()
    return language == "mermaid"


def parse_yaml_scalar(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        try:
            decoded = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped.strip('"')
        return decoded if isinstance(decoded, str) else stripped

    if stripped.startswith("'") and stripped.endswith("'"):
        return stripped[1:-1].replace("''", "'")

    return stripped


def coverage_paths(meta_path: Path) -> tuple[set[str], list[str]]:
    coverage_path = meta_path / "coverage.yml"
    try:
        lines = coverage_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return set(), [f"Coverage file does not exist: {coverage_path}"]
    except OSError as exc:
        return set(), [f"Coverage file cannot be read: {coverage_path}: {exc}"]

    paths: set[str] = set()
    for line in lines:
        match = COVERAGE_PATH_RE.match(line)
        if match is not None:
            paths.add(parse_yaml_scalar(match.group(1)))

    return paths, []


def source_exists(repo: Path, source_path: str) -> bool:
    candidate, error = source_candidate(repo, source_path)
    return error is None and candidate is not None and candidate.exists()


def source_path_validation_error(source_path: str) -> str | None:
    normalized = source_path.replace("\\", "/")
    if (
        Path(source_path).is_absolute()
        or PurePosixPath(normalized).is_absolute()
        or PureWindowsPath(source_path).is_absolute()
    ):
        return "expected a repository-relative path"

    if any(part == ".." for part in PurePosixPath(normalized).parts):
        return "path traversal is not allowed"

    return None


def source_candidate(repo: Path, source_path: str) -> tuple[Path | None, str | None]:
    path_error = source_path_validation_error(source_path)
    if path_error is not None:
        return None, path_error

    candidate = (repo / source_path).resolve(strict=False)
    try:
        candidate.relative_to(repo)
    except ValueError:
        return None, "resolved path escapes repository"

    return candidate, None


def validate_coverage_references(
    repo: Path,
    meta_path: Path,
    indexed_files: Sequence[Mapping[str, object]],
) -> list[str]:
    paths, errors = coverage_paths(meta_path)

    for index, indexed_file in enumerate(indexed_files):
        label = file_entry_label(index, indexed_file)
        source_path = indexed_file.get("path")
        secret_redacted = indexed_file.get("secret_redacted")

        if not isinstance(source_path, str) or not source_path:
            continue
        if not isinstance(secret_redacted, bool):
            continue
        if secret_redacted:
            continue

        _, path_error = source_candidate(repo, source_path)
        if path_error is not None:
            errors.append(
                f"Invalid source path in repository index: {source_path}: "
                f"{path_error}"
            )
            continue

        if source_path not in paths:
            errors.append(f"Coverage file does not reference source path: {source_path}")

        if not source_exists(repo, source_path):
            errors.append(f"Indexed source path does not exist: {label}")

    return errors


def collect_errors(repo: Path, wiki_path: Path, meta_path: Path) -> list[str]:
    errors: list[str] = []

    if not repo.exists():
        errors.append(f"Repository does not exist: {repo}")
    elif not repo.is_dir():
        errors.append(f"Repository path is not a directory: {repo}")

    errors.extend(validate_structure(wiki_path, meta_path))
    indexed_files, index_errors = load_repo_index(meta_path)
    errors.extend(index_errors)
    errors.extend(validate_obsidian_links(wiki_path))
    errors.extend(validate_mermaid_fences(wiki_path))

    if indexed_files:
        errors.extend(validate_coverage_references(repo, meta_path, indexed_files))

    return errors


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    wiki_path = resolve_repo_path(repo, args.wiki_path)
    meta_path = resolve_repo_path(repo, args.meta_path)

    errors = collect_errors(repo, wiki_path, meta_path)
    if errors:
        for error in errors:
            print(error)
        return 1

    print("Wiki validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
