#!/usr/bin/env python3
"""Render a bounded DeepSeek context pack for one Code Wiki update chunk."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Mapping, cast


LAST_RUN_FILE_NAME = "last-run.json"
MAX_FILE_CHARS = 12_000

SECRET_NAMES = {
    ".env",
    ".env.local",
    ".envrc",
    ".netrc",
    ".npmrc",
    "id_ed25519",
    "id_rsa",
    "known_hosts",
}

SECRET_COMPONENTS = {
    "auth",
    "cert",
    "certs",
    "certificate",
    "certificates",
    "credentials",
    "key",
    "keys",
    "p12",
    "passphrase",
    "password",
    "passwords",
    "pem",
    "pfx",
    "private",
    "secrets",
}

SECRET_PATTERNS = (
    re.compile(r"(^|/)\.env(?:rc|\..*)?$", re.IGNORECASE),
    re.compile(r"(^|[./_-])auth([./_-]|$)", re.IGNORECASE),
    re.compile(
        r"(^|[./_-])(?:passwords?|passwd|passphrase)([./_-]|$)",
        re.IGNORECASE,
    ),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"private[-_ ]?key", re.IGNORECASE),
    re.compile(r"\.(cer|cert|crt|key|p12|pem|pfx)$", re.IGNORECASE),
)

LANGUAGE_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".conf": "ini",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".ini": "ini",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "javascript",
    ".kt": "kotlin",
    ".lock": "text",
    ".md": "markdown",
    ".mjs": "javascript",
    ".py": "python",
    ".rs": "rust",
    ".sh": "bash",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a DeepSeek context pack for one Code Wiki chunk."
    )
    parser.add_argument("--repo", required=True, help="Repository root.")
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
    parser.add_argument("--chunk-id", required=True, help="Chunk id to render.")
    parser.add_argument("--output", required=True, help="Context pack output path.")
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


def resolve_output_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def is_secret_path(relative_path: str) -> bool:
    path = Path(relative_path)
    name = path.name.lower()
    if name in SECRET_NAMES:
        return True
    if any(part.lower() in SECRET_COMPONENTS for part in path.parts):
        return True
    return any(pattern.search(relative_path) for pattern in SECRET_PATTERNS)


def load_last_run(meta_path: Path) -> Mapping[str, object]:
    last_run_path = meta_path / LAST_RUN_FILE_NAME
    if not last_run_path.exists():
        raise SystemExit(f"last-run metadata does not exist: {last_run_path}")

    try:
        payload = json.loads(last_run_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"last-run metadata is not valid JSON: {last_run_path}") from exc

    if not isinstance(payload, dict):
        raise SystemExit(f"last-run metadata must be a JSON object: {last_run_path}")
    return cast(Mapping[str, object], payload)


def chunks_from(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    chunks = payload.get("chunks")
    if not isinstance(chunks, list):
        raise SystemExit("last-run metadata has invalid field chunks: expected list")

    validated_chunks: list[Mapping[str, object]] = []
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise SystemExit(
                f"last-run metadata has invalid chunk at chunks[{index}]: "
                "expected object"
            )
        validated_chunks.append(cast(Mapping[str, object], chunk))
    return validated_chunks


def find_chunk(
    chunks: list[Mapping[str, object]], requested_chunk_id: str
) -> Mapping[str, object]:
    for chunk in chunks:
        chunk_id = chunk.get("id")
        if isinstance(chunk_id, str) and chunk_id == requested_chunk_id:
            return chunk
    raise SystemExit(f"Unknown chunk id: {requested_chunk_id}")


def required_string(chunk: Mapping[str, object], field: str) -> str:
    value = chunk.get(field)
    if not isinstance(value, str) or not value:
        chunk_label = chunk_label_for_error(chunk)
        raise SystemExit(
            f"Chunk {chunk_label} has invalid field {field}: "
            "expected non-empty string"
        )
    return value


def required_string_list(chunk: Mapping[str, object], field: str) -> list[str]:
    value = chunk.get(field)
    chunk_label = chunk_label_for_error(chunk)
    if not isinstance(value, list):
        raise SystemExit(
            f"Chunk {chunk_label} has invalid field {field}: expected list of strings"
        )

    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise SystemExit(
                f"Chunk {chunk_label} has invalid field {field}[{index}]: "
                "expected non-empty string"
            )
        items.append(item)
    return items


def chunk_label_for_error(chunk: Mapping[str, object]) -> str:
    chunk_id = chunk.get("id")
    if isinstance(chunk_id, str) and chunk_id:
        return chunk_id
    return "<unknown>"


def validate_target_page(path: str) -> None:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise SystemExit(f"Invalid target page path in chunk metadata: {path}")


def validate_chunk(chunk: Mapping[str, object]) -> dict[str, object]:
    chunk_id = required_string(chunk, "id")
    group = required_string(chunk, "group")
    role = required_string(chunk, "role")
    status = required_string(chunk, "status")
    target_pages = required_string_list(chunk, "target_pages")
    source_paths = required_string_list(chunk, "source_paths")

    for target_page in target_pages:
        validate_target_page(target_page)

    return {
        "id": chunk_id,
        "group": group,
        "role": role,
        "status": status,
        "target_pages": target_pages,
        "source_paths": source_paths,
    }


def resolve_source_path(repo: Path, source_path: str) -> Path:
    if Path(source_path).is_absolute():
        raise SystemExit(
            f"Refusing to read absolute source path from chunk metadata: {source_path}"
        )
    if is_secret_path(source_path):
        raise SystemExit(f"Refusing to read secret-like source path: {source_path}")

    resolved = (repo / source_path).resolve()
    try:
        normalized_relative = resolved.relative_to(repo).as_posix()
    except ValueError as exc:
        raise SystemExit(
            f"Refusing to read source path outside repository: {source_path}"
        ) from exc

    if is_secret_path(normalized_relative):
        raise SystemExit(
            f"Refusing to read secret-like source path: {normalized_relative}"
        )
    if not resolved.exists():
        raise SystemExit(f"Source file does not exist: {source_path}")
    if not resolved.is_file():
        raise SystemExit(f"Source path is not a file: {source_path}")
    return resolved


def read_source_file(path: Path) -> tuple[str, bool]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SystemExit(f"Unable to read source file {path}: {exc}") from exc

    if len(text) <= MAX_FILE_CHARS:
        return text, False
    return text[:MAX_FILE_CHARS], True


def markdown_inline_code(value: str) -> str:
    escaped = value.replace("`", "\\`")
    return f"`{escaped}`"


def markdown_fence_for(text: str) -> str:
    longest_run = 0
    current_run = 0
    for character in text:
        if character == "`":
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    return "`" * max(3, longest_run + 1)


def language_for(path: str) -> str:
    return LANGUAGE_BY_SUFFIX.get(Path(path).suffix.lower(), "text")


def markdown_list(values: list[str]) -> list[str]:
    if not values:
        return ["- _None / Нет_"]
    return [f"- {markdown_inline_code(value)}" for value in values]


def render_context_pack(
    *,
    repo: Path,
    wiki_path: Path,
    meta_path: Path,
    last_run: Mapping[str, object],
    chunk: Mapping[str, object],
) -> str:
    chunk_id = cast(str, chunk["id"])
    source_paths = cast(list[str], chunk["source_paths"])
    target_pages = cast(list[str], chunk["target_pages"])
    generated_at = last_run.get("generated_at")
    generated_at_text = generated_at if isinstance(generated_at, str) else "unknown"

    lines = [
        "# Задача для DeepSeek: обновить русскую Obsidian wiki",
        "",
        "## Safety instructions / Инструкции безопасности",
        "",
        "- Do not print, infer, summarize, or request secrets. / Не печатай, не выводи, не пересказывай и не запрашивай секреты.",
        "- Treat `.env`, credential, token, key, certificate, and private paths as redacted even if referenced. / Считай `.env`, учетные данные, токены, ключи, сертификаты и приватные пути редактированными.",
        "- Keep code identifiers, file paths, commands, package names, API names, and ADR titles exactly as written. / Сохраняй идентификаторы кода, пути, команды, имена пакетов, API и названия ADR без изменений.",
        "- Write wiki prose in Russian and keep Markdown Obsidian-compatible. / Пиши текст wiki на русском и сохраняй совместимость с Obsidian Markdown.",
        "- Do not invent source facts. If the context is insufficient, state that explicitly. / Не выдумывай факты об исходниках. Если контекста недостаточно, напиши это явно.",
        "",
        "## Chunk details / Детали чанка",
        "",
        f"- Chunk ID / ID чанка: {markdown_inline_code(chunk_id)}",
        f"- Group / Группа: {markdown_inline_code(cast(str, chunk['group']))}",
        f"- Role / Роль: {markdown_inline_code(cast(str, chunk['role']))}",
        f"- Status / Статус: {markdown_inline_code(cast(str, chunk['status']))}",
        f"- Repository / Репозиторий: {markdown_inline_code(str(repo))}",
        f"- Wiki path / Путь wiki: {markdown_inline_code(str(wiki_path))}",
        f"- Metadata path / Путь metadata: {markdown_inline_code(str(meta_path))}",
        f"- Plan generated at / План создан: {markdown_inline_code(generated_at_text)}",
        f"- Per-file source limit / Лимит источника на файл: {markdown_inline_code(str(MAX_FILE_CHARS))} characters",
        "",
        "## Target pages / Целевые страницы",
        "",
    ]
    lines.extend(markdown_list(target_pages))
    lines.extend(
        [
            "",
            "## Required Output / Требуемый результат",
            "",
            "Return one Markdown response with these sections and no extra wrapper text. / Верни один Markdown-ответ с этими разделами и без дополнительной обертки.",
            "",
            "### Summary / Резюме",
            "",
            "Briefly describe what should change in the Russian wiki and why. / Кратко опиши, что нужно изменить в русской wiki и почему.",
            "",
            "### Proposed pages / Предлагаемые страницы",
            "",
            "For each target page, provide the wiki-relative path and full proposed Obsidian-compatible Markdown content. / Для каждой целевой страницы укажи путь относительно wiki и полный предложенный Markdown, совместимый с Obsidian.",
            "",
            "### Source coverage / Покрытие источников",
            "",
            "List each source file and the facts from it that the proposed pages cover. / Перечисли каждый исходный файл и факты из него, покрытые предложенными страницами.",
            "",
            "### Drift candidates / Кандидаты на drift",
            "",
            "List possible code/docs/ADR drift found in this chunk, or state that none is visible from the provided context. / Перечисли возможные расхождения кода, документации и ADR в этом чанке либо укажи, что из данного контекста они не видны.",
            "",
            "## Source Files / Исходные файлы",
            "",
        ]
    )

    for source_path in source_paths:
        resolved_source = resolve_source_path(repo, source_path)
        text, truncated = read_source_file(resolved_source)
        fence = markdown_fence_for(text)
        included_chars = len(text)
        original_size = resolved_source.stat().st_size
        lines.extend(
            [
                f"### {markdown_inline_code(source_path)}",
                "",
                f"- Resolved path / Полный путь: {markdown_inline_code(str(resolved_source))}",
                f"- Size bytes / Размер в байтах: {markdown_inline_code(str(original_size))}",
                f"- Included characters / Включено символов: {markdown_inline_code(str(included_chars))}",
                f"- Truncated / Обрезано: {markdown_inline_code('yes' if truncated else 'no')}",
                "",
                f"{fence}{language_for(source_path)}",
                text.rstrip("\n"),
                fence,
            ]
        )
        if truncated:
            lines.append(
                f"_Source file truncated after {MAX_FILE_CHARS} characters. / "
                f"Исходный файл обрезан после {MAX_FILE_CHARS} символов._"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_context_pack(output_path: Path, content: str) -> None:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Unable to write context pack {output_path}: {exc}") from exc


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    wiki_path = resolve_repo_path(repo, args.wiki_path)
    meta_path = resolve_repo_path(repo, args.meta_path)
    output_path = resolve_output_path(args.output)

    last_run = load_last_run(meta_path)
    raw_chunk = find_chunk(chunks_from(last_run), args.chunk_id)
    chunk = validate_chunk(raw_chunk)
    content = render_context_pack(
        repo=repo,
        wiki_path=wiki_path,
        meta_path=meta_path,
        last_run=last_run,
        chunk=chunk,
    )
    write_context_pack(output_path, content)

    summary = {"chunk_id": cast(str, chunk["id"]), "output_path": str(output_path)}
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
