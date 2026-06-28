#!/usr/bin/env python3
"""Build initial Code Wiki metadata for a repository."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


WIKI_DIRS = (
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

SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "caches",
    "coverage",
    "dist",
    "node_modules",
    "site-packages",
    "target",
    "venv",
}

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
        r"(^|[./_-])(?:passwords?|passwd|passphrase)([./_-]|$)", re.IGNORECASE
    ),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"private[-_ ]?key", re.IGNORECASE),
    re.compile(r"\.(cer|cert|crt|key|p12|pem|pfx)$", re.IGNORECASE),
)

CONFIG_NAMES = {
    ".editorconfig",
    ".gitignore",
    ".pre-commit-config.yaml",
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "makefile",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
    "tox.ini",
}

CONFIG_SUFFIXES = {
    ".cfg",
    ".conf",
    ".ini",
    ".json",
    ".lock",
    ".toml",
    ".yaml",
    ".yml",
}

SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".py",
    ".rs",
    ".sh",
    ".ts",
    ".tsx",
}

LANGUAGES_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".conf": "config",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".ini": "config",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "javascript",
    ".kt": "kotlin",
    ".lock": "lockfile",
    ".md": "markdown",
    ".mjs": "javascript",
    ".py": "python",
    ".rs": "rust",
    ".sh": "shell",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".yaml": "yaml",
    ".yml": "yaml",
}

JS_TS_SYMBOL_PATTERNS = (
    re.compile(r"\bexport\s+(?:default\s+)?class\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\bexport\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"\bexport\s+const\s+([A-Za-z_$][\w$]*)\s*="),
    re.compile(r"\bconst\s+([A-Za-z_$][\w$]*)\s*="),
)


@dataclass(frozen=True)
class IndexedFile:
    path: str
    role: str
    language: str
    size_bytes: int
    sha256: str | None
    secret_redacted: bool
    symbols: list[str]
    headings: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize Code Wiki metadata for a repository."
    )
    parser.add_argument("--repo", required=True, help="Repository root to index.")
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


def relative_posix(repo: Path, path: Path) -> str:
    return path.relative_to(repo).as_posix()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def has_symlink_component(repo: Path, path: Path) -> bool:
    current = repo
    for part in path.relative_to(repo).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def walk_files(repo: Path) -> Iterable[Path]:
    for path in sorted(repo.rglob("*")):
        if has_symlink_component(repo, path):
            continue
        if not path.is_file():
            continue
        relative_parts = path.relative_to(repo).parts
        if any(part in SKIP_DIRS for part in relative_parts[:-1]):
            continue
        yield path


def is_secret_path(relative_path: str) -> bool:
    path = Path(relative_path)
    name = path.name.lower()
    if name in SECRET_NAMES:
        return True
    if any(part.lower() in SECRET_COMPONENTS for part in path.parts):
        return True
    return any(pattern.search(relative_path) for pattern in SECRET_PATTERNS)


def detect_language(relative_path: str) -> str:
    path = Path(relative_path)
    return LANGUAGES_BY_SUFFIX.get(path.suffix.lower(), "unknown")


def detect_role(relative_path: str) -> str:
    path = Path(relative_path)
    parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()
    suffix = path.suffix.lower()

    if "adr" in parts or ("docs" in parts and "adr" in parts):
        return "adr"
    if "tests" in parts or "test" in parts or name.startswith("test_"):
        return "test"
    if suffix == ".md":
        return "doc"
    if name in CONFIG_NAMES or suffix in CONFIG_SUFFIXES:
        return "config"
    if suffix in SOURCE_SUFFIXES:
        return "source"
    return "other"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text_lossy(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_python_symbols(path: Path) -> list[str]:
    try:
        tree = ast.parse(read_text_lossy(path), filename=str(path))
    except SyntaxError:
        return []

    symbols: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            symbols.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(f"function {node.name}")
    return sorted(set(symbols))


def extract_js_ts_symbols(path: Path) -> list[str]:
    text = read_text_lossy(path)
    symbols: list[str] = []
    for pattern in JS_TS_SYMBOL_PATTERNS:
        for match in pattern.finditer(text):
            symbol = match.group(1)
            prefix = "class" if "class" in pattern.pattern else "symbol"
            if "function" in pattern.pattern:
                prefix = "function"
            elif "const" in pattern.pattern:
                prefix = "const"
            symbols.append(f"{prefix} {symbol}")
    return sorted(set(symbols))


def extract_symbols(path: Path, language: str) -> list[str]:
    if language == "python":
        return extract_python_symbols(path)
    if language in {"javascript", "typescript"}:
        return extract_js_ts_symbols(path)
    return []


def extract_markdown_headings(path: Path) -> list[str]:
    headings: list[str] = []
    for line in read_text_lossy(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading = stripped.lstrip("#").strip()
        if heading:
            headings.append(heading)
    return headings


def index_file(repo: Path, path: Path) -> IndexedFile:
    relative_path = relative_posix(repo, path)
    secret_redacted = is_secret_path(relative_path)
    stat = path.stat()
    role = detect_role(relative_path)
    language = detect_language(relative_path)

    if secret_redacted:
        return IndexedFile(
            path=relative_path,
            role=role,
            language=language,
            size_bytes=stat.st_size,
            sha256=None,
            secret_redacted=True,
            symbols=[],
            headings=[],
        )

    symbols = extract_symbols(path, language)
    headings = extract_markdown_headings(path) if language == "markdown" else []
    return IndexedFile(
        path=relative_path,
        role=role,
        language=language,
        size_bytes=stat.st_size,
        sha256=sha256_file(path),
        secret_redacted=False,
        symbols=symbols,
        headings=headings,
    )


def wiki_target_for(indexed_file: IndexedFile) -> str:
    source = Path(indexed_file.path)
    stem = source.with_suffix("").as_posix().strip("/")
    if not stem:
        stem = "index"

    if indexed_file.role == "adr":
        return f"decisions/{source.stem}.md"
    if indexed_file.role == "doc":
        return f"operations/{stem}.md"
    if indexed_file.role == "config":
        return f"operations/config/{stem}.md"
    if indexed_file.role == "test":
        return f"operations/tests/{stem}.md"
    if indexed_file.role == "source":
        return f"components/{stem}.md"
    return f"_meta/unmapped/{stem}.md"


def yaml_scalar(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def yaml_list(values: Iterable[object], indent: int = 0) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    for value in values:
        lines.append(f"{prefix}- {yaml_scalar(value)}")
    if not lines:
        lines.append(f"{prefix}[]")
    return lines


def write_default_wiki(wiki_path: Path, meta_path: Path) -> None:
    for directory in WIKI_DIRS:
        (wiki_path / directory).mkdir(parents=True, exist_ok=True)
    meta_path.mkdir(parents=True, exist_ok=True)

    index_path = wiki_path / "index.md"
    if not index_path.exists():
        index_path.write_text(
            "# Code Wiki\n\n"
            "Индекс архитектурной документации репозитория.\n",
            encoding="utf-8",
        )

    meta_index_path = meta_path / "index.md"
    if not meta_index_path.exists():
        meta_index_path.write_text(
            "# Wiki Metadata\n\n"
            "Служебные файлы индексации и покрытия документации.\n",
            encoding="utf-8",
        )

    policy_path = meta_path / "policy.yml"
    if not policy_path.exists():
        policy_path.write_text(
            "\n".join(
                (
                    "version: 1",
                    'language: "ru"',
                    "secrets:",
                    '  default: "redact"',
                    "  redacted_markers:",
                    '    - "secret_redacted"',
                    "wiki:",
                    '  root: "docs/wiki"',
                    "  generated_metadata:",
                    '    - "repo-index.json"',
                    '    - "source-map.yml"',
                    '    - "coverage.yml"',
                    "",
                )
            ),
            encoding="utf-8",
        )


def write_repo_index(meta_path: Path, files: list[IndexedFile]) -> None:
    payload = {
        "version": 1,
        "files": [asdict(indexed_file) for indexed_file in files],
    }
    (meta_path / "repo-index.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def source_map_entries(files: list[IndexedFile]) -> list[IndexedFile]:
    allowed_roles = {"source", "doc", "test", "config", "adr"}
    return [
        indexed_file
        for indexed_file in files
        if not indexed_file.secret_redacted and indexed_file.role in allowed_roles
    ]


def write_source_map(meta_path: Path, files: list[IndexedFile]) -> None:
    lines = ["version: 1", "sources:"]
    entries = source_map_entries(files)
    if not entries:
        lines.append("  []")
    for indexed_file in entries:
        lines.extend(
            (
                f"  - path: {yaml_scalar(indexed_file.path)}",
                f"    role: {yaml_scalar(indexed_file.role)}",
                f"    language: {yaml_scalar(indexed_file.language)}",
                f"    target: {yaml_scalar(wiki_target_for(indexed_file))}",
            )
        )
    lines.append("")
    (meta_path / "source-map.yml").write_text("\n".join(lines), encoding="utf-8")


def write_coverage(meta_path: Path, files: list[IndexedFile]) -> None:
    lines = ["version: 1", "files:"]
    if not files:
        lines.append("  []")
    for indexed_file in files:
        status = "redacted" if indexed_file.secret_redacted else "missing"
        lines.extend(
            (
                f"  - path: {yaml_scalar(indexed_file.path)}",
                f"    role: {yaml_scalar(indexed_file.role)}",
                f"    status: {yaml_scalar(status)}",
            )
        )
        if indexed_file.sha256 is not None:
            lines.append(f"    last_seen_hash: {yaml_scalar(indexed_file.sha256)}")
        if indexed_file.symbols:
            lines.append("    symbols:")
            lines.extend(yaml_list(indexed_file.symbols, indent=6))
        else:
            lines.append("    symbols: []")
    lines.append("")
    (meta_path / "coverage.yml").write_text("\n".join(lines), encoding="utf-8")


def build_index(repo: Path, wiki_path: Path, meta_path: Path) -> list[IndexedFile]:
    write_default_wiki(wiki_path, meta_path)

    files: list[IndexedFile] = []
    for path in walk_files(repo):
        if is_within(path, wiki_path) or is_within(path, meta_path):
            continue
        files.append(index_file(repo, path))

    files.sort(key=lambda indexed_file: indexed_file.path)
    write_repo_index(meta_path, files)
    write_source_map(meta_path, files)
    write_coverage(meta_path, files)
    return files


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    wiki_path = resolve_repo_path(repo, args.wiki_path)
    meta_path = resolve_repo_path(repo, args.meta_path)

    files = build_index(repo, wiki_path, meta_path)
    redacted = sum(1 for indexed_file in files if indexed_file.secret_redacted)
    summary = {
        "files": len(files),
        "redacted": redacted,
        "meta_path": str(meta_path),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
