#!/usr/bin/env python3
"""Plan Code Wiki update chunks from repository index metadata."""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, cast


INDEX_FILE_NAME = "repo-index.json"
PLAN_FILE_NAME = "update-plan.md"
LAST_RUN_FILE_NAME = "last-run.json"
PATCH_PREVIEW_FILE_NAME = "patch-preview.diff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan Code Wiki update chunks from repo-index.json."
    )
    parser.add_argument("--repo", required=True, help="Repository root to plan.")
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
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=10,
        help="Maximum number of update chunks to emit.",
    )
    return parser.parse_args()


def resolve_repo(path: str) -> Path:
    repo = Path(path).expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"Repository does not exist: {repo}")
    if not repo.is_dir():
        raise SystemExit(f"Repository path is not a directory: {repo}")
    return repo


def resolve_repo_path(repo: Path, path: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo / candidate).resolve()


def load_repo_index(meta_path: Path) -> list[Mapping[str, object]]:
    index_path = meta_path / INDEX_FILE_NAME
    if not index_path.exists():
        raise SystemExit(f"Repository index does not exist: {index_path}")

    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Repository index is not valid JSON: {index_path}") from exc

    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list):
        raise SystemExit(f"Repository index has no files list: {index_path}")

    indexed_files: list[Mapping[str, object]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise SystemExit(
                f"Repository index file entry files[{index}] is invalid: "
                "expected object"
            )
        validate_file_entry(item, index)
        indexed_files.append(item)
    return indexed_files


def file_entry_label(index: int, indexed_file: Mapping[str, object]) -> str:
    path = indexed_file.get("path")
    if isinstance(path, str) and path:
        return path
    return f"files[{index}]"


def validate_file_entry(indexed_file: Mapping[str, object], index: int) -> None:
    label = file_entry_label(index, indexed_file)

    path = indexed_file.get("path")
    if not isinstance(path, str) or not path:
        raise SystemExit(
            f"Repository index file entry {label} has invalid field path: "
            "expected non-empty string"
        )

    role = indexed_file.get("role")
    if not isinstance(role, str) or not role:
        raise SystemExit(
            f"Repository index file entry {label} has invalid field role: "
            "expected non-empty string"
        )

    secret_redacted = indexed_file.get("secret_redacted")
    if not isinstance(secret_redacted, bool):
        raise SystemExit(
            f"Repository index file entry {label} has invalid field "
            "secret_redacted: expected bool"
        )


def source_path_for(indexed_file: Mapping[str, object]) -> str:
    return cast(str, indexed_file["path"])


def role_for(indexed_file: Mapping[str, object]) -> str:
    return cast(str, indexed_file["role"])


def secret_redacted_for(indexed_file: Mapping[str, object]) -> bool:
    return cast(bool, indexed_file["secret_redacted"])


def top_level_group(source_path: str) -> str:
    parts = Path(source_path).parts
    if not parts:
        return "root"
    if len(parts) == 1:
        stem = Path(parts[0]).stem
        return stem or parts[0]
    return parts[0]


def page_segment(group: str) -> str:
    segment = re.sub(r"[^A-Za-z0-9._-]+", "-", group.strip()).strip("-._")
    return segment or "root"


def target_page_for(group: str, role: str) -> str:
    if role == "adr":
        return "decisions/adr-index.md"
    if role == "doc":
        return "operations/documentation-map.md"
    if role == "test":
        return f"operations/{page_segment(group)}-tests.md"
    if role == "config":
        return "operations/configuration.md"
    return f"components/{page_segment(group)}.md"


def chunk_id_for(ordinal: int, group: str, role: str) -> str:
    return f"{ordinal:03d}-{page_segment(role)}-{page_segment(group)}"


def non_redacted_files(
    indexed_files: Iterable[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    return [
        indexed_file
        for indexed_file in indexed_files
        if not secret_redacted_for(indexed_file)
    ]


def build_chunks(
    indexed_files: Iterable[Mapping[str, object]], max_chunks: int
) -> list[dict[str, object]]:
    if max_chunks < 1:
        raise SystemExit("--max-chunks must be greater than zero")

    grouped: OrderedDict[tuple[str, str], list[str]] = OrderedDict()
    for indexed_file in sorted(non_redacted_files(indexed_files), key=source_path_for):
        source_path = source_path_for(indexed_file)
        role = role_for(indexed_file)
        group = top_level_group(source_path)
        grouped.setdefault((group, role), []).append(source_path)

    chunks: list[dict[str, object]] = []
    for ordinal, ((group, role), source_paths) in enumerate(grouped.items(), start=1):
        if len(chunks) >= max_chunks:
            break
        chunks.append(
            {
                "id": chunk_id_for(ordinal, group, role),
                "group": group,
                "role": role,
                "status": "pending",
                "target_pages": [target_page_for(group, role)],
                "source_paths": source_paths,
            }
        )
    return chunks


def markdown_list(values: Iterable[str], indent: int = 0) -> list[str]:
    prefix = " " * indent
    return [f"{prefix}- `{value}`" for value in values]


def render_update_plan(
    *,
    repo: Path,
    wiki_path: Path,
    meta_path: Path,
    generated_at: str,
    chunks: list[dict[str, object]],
) -> str:
    lines = [
        "# Wiki Update Plan",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Repository: `{repo}`",
        f"- Wiki path: `{wiki_path}`",
        f"- Metadata path: `{meta_path}`",
        f"- Chunks: `{len(chunks)}`",
        "",
    ]

    if not chunks:
        lines.extend(["No update chunks were planned.", ""])
        return "\n".join(lines)

    for chunk in chunks:
        lines.extend(
            [
                f"## {chunk['id']}",
                "",
                f"- Group: `{chunk['group']}`",
                f"- Role: `{chunk['role']}`",
                f"- Status: `{chunk['status']}`",
                "- Target pages:",
            ]
        )
        lines.extend(markdown_list(_string_list(chunk["target_pages"]), indent=2))
        lines.append("- Source paths:")
        lines.extend(markdown_list(_string_list(chunk["source_paths"]), indent=2))
        lines.append("")

    return "\n".join(lines)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SystemExit("Internal error: expected a list of strings")
    return cast(list[str], value)


def write_artifacts(
    *,
    repo: Path,
    wiki_path: Path,
    meta_path: Path,
    generated_at: str,
    chunks: list[dict[str, object]],
) -> None:
    meta_path.mkdir(parents=True, exist_ok=True)
    (meta_path / "drafts").mkdir(parents=True, exist_ok=True)

    plan = render_update_plan(
        repo=repo,
        wiki_path=wiki_path,
        meta_path=meta_path,
        generated_at=generated_at,
        chunks=chunks,
    )
    (meta_path / PLAN_FILE_NAME).write_text(plan, encoding="utf-8")

    last_run = {
        "phase": "plan",
        "repo": str(repo),
        "wiki_path": str(wiki_path),
        "meta_path": str(meta_path),
        "generated_at": generated_at,
        "chunks": chunks,
    }
    (meta_path / LAST_RUN_FILE_NAME).write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (meta_path / PATCH_PREVIEW_FILE_NAME).write_text("", encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    wiki_path = resolve_repo_path(repo, args.wiki_path)
    meta_path = resolve_repo_path(repo, args.meta_path)

    indexed_files = load_repo_index(meta_path)
    chunks = build_chunks(indexed_files, args.max_chunks)
    generated_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    write_artifacts(
        repo=repo,
        wiki_path=wiki_path,
        meta_path=meta_path,
        generated_at=generated_at,
        chunks=chunks,
    )

    summary = {"chunks": len(chunks), "meta_path": str(meta_path)}
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
