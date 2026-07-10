"""Private filesystem projections for the dynamic runtime capability catalog."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import html
import json
import os
from pathlib import Path
import tempfile

from mcp_catalog import (
    CATALOG_SCHEMA_VERSION,
    MAX_CANDIDATES,
    CatalogError,
    JsonObject,
    _catalog_tools,
    _expect_mapping,
    candidate_capabilities,
    catalog_status,
    validate_catalog_integrity,
)


PRIVATE_FILE_MODE = 0o600
PRIVATE_DIRECTORY_MODE = 0o700
MAX_PRIVATE_FILE_BYTES = 32 * 1024 * 1024


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _prepare_private_directory(base: Path, relative: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIRECTORY_MODE)
    if not base.is_dir():
        raise CatalogError(f"catalog base is not a directory: {base}")
    resolved_base = base.resolve()
    current = base
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CatalogError(f"refusing symlink in catalog path: {current}")
        current.mkdir(exist_ok=True, mode=PRIVATE_DIRECTORY_MODE)
        if not current.is_dir():
            raise CatalogError(f"catalog path is not a directory: {current}")
        if not _is_within(current.resolve(), resolved_base):
            raise CatalogError(f"catalog path escapes configured root: {current}")
        try:
            current.chmod(PRIVATE_DIRECTORY_MODE)
        except PermissionError as exc:
            raise CatalogError(f"cannot secure catalog directory: {current}") from exc
    return current


def _atomic_private_write(path: Path, content: str) -> None:
    if path.is_symlink():
        raise CatalogError(f"refusing to replace symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    descriptor_open = True
    try:
        os.fchmod(descriptor, PRIVATE_FILE_MODE)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor_open = False
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        path.chmod(PRIVATE_FILE_MODE)
    except OSError as exc:
        raise CatalogError(f"cannot write private catalog file: {path}") from exc
    finally:
        if descriptor_open:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _json_document(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _repository_tags(repo: Path) -> list[str]:
    suffix_tags = {
        ".c": "native",
        ".cpp": "native",
        ".go": "go",
        ".java": "jvm",
        ".js": "javascript",
        ".kt": "jvm",
        ".md": "documentation",
        ".py": "python",
        ".rb": "ruby",
        ".rs": "rust",
        ".swift": "swift",
        ".ts": "typescript",
        ".yaml": "configuration",
        ".yml": "configuration",
    }
    filename_tags = {
        "dockerfile": "containers",
        "makefile": "build",
        "package.json": "javascript",
        "pyproject.toml": "python",
        "readme.md": "documentation",
    }
    tags: set[str] = set()
    seen = 0
    for current, directories, filenames in os.walk(repo, followlinks=False):
        directories[:] = [
            name
            for name in directories
            if name not in {".engineering-bible", ".git", "__pycache__"}
            and not (Path(current) / name).is_symlink()
        ]
        for filename in filenames:
            seen += 1
            if seen > 5_000:
                return sorted(tags)
            lower = filename.lower()
            tag = filename_tags.get(lower)
            if tag:
                tags.add(tag)
            suffix = Path(lower).suffix
            if suffix in suffix_tags:
                tags.add(suffix_tags[suffix])
    if (repo / ".git").exists():
        tags.add("version-control")
    return sorted(tags)


def _repository_ref(repo: Path) -> str:
    digest = hashlib.sha256(str(repo.resolve()).encode("utf-8")).hexdigest()
    return "repo_" + digest[:16]


def _compact_index(catalog: Mapping[str, object], repo: Path) -> JsonObject:
    tools = _catalog_tools(catalog)
    compact_tools = [
        {
            key: tool.get(key)
            for key in (
                "runtime_id",
                "selector",
                "display_name",
                "description",
                "available",
                "schema_hash",
                "capability_tags",
                "risk",
                "requires_confirmation",
                "evidence",
            )
        }
        for tool in tools
    ]
    return {
        **catalog_status(catalog),
        "repository_ref": _repository_ref(repo),
        "repository_tags": _repository_tags(repo),
        "tools": compact_tools,
    }


def _markdown_escape(value: object) -> str:
    text = html.escape(str(value), quote=False)
    replacements = {
        "`": "&#96;",
        "[": "&#91;",
        "]": "&#93;",
        "(": "&#40;",
        ")": "&#41;",
        "|": "\\|",
    }
    for character, replacement in replacements.items():
        text = text.replace(character, replacement)
    return text


def _render_recommendations(catalog: Mapping[str, object], repo: Path) -> str:
    repository_tags = _repository_tags(repo)
    task = " ".join(repository_tags) or "repository capability"
    recommendations = candidate_capabilities(catalog, task, limit=MAX_CANDIDATES)
    tools = _catalog_tools(catalog)

    lines = [
        "# Runtime Tool Capabilities",
        "",
        "> Generated local runtime state. Do not commit this file.",
        "",
        f"- Status: `{_markdown_escape(catalog.get('status', 'unknown'))}`",
        f"- Fingerprint: `{_markdown_escape(catalog.get('fingerprint', ''))}`",
        f"- Captured: `{_markdown_escape(catalog.get('captured_at', ''))}`",
        f"- Repository signals: `{_markdown_escape(', '.join(repository_tags) or 'none')}`",
        "",
        "## Recommended For This Repository",
        "",
    ]
    if recommendations:
        for capability in recommendations:
            lines.append(
                "- `{}` — risk `{}`, score {}: {}".format(
                    _markdown_escape(capability.get("selector", "")),
                    _markdown_escape(capability.get("risk", "UNKNOWN")),
                    _markdown_escape(capability.get("score", 0)),
                    _markdown_escape(capability.get("description", "")),
                )
            )
    else:
        lines.append("No relevant available capability was identified from current metadata.")

    lines.extend(("", "## Current Catalog", ""))
    if tools:
        for tool in tools:
            availability = "available" if tool.get("available") is True else "unavailable"
            lines.append(
                "- `{}` — `{}` / `{}`: {}".format(
                    _markdown_escape(tool.get("selector", "")),
                    _markdown_escape(tool.get("risk", "UNKNOWN")),
                    availability,
                    _markdown_escape(tool.get("description", "")),
                )
            )
    else:
        lines.append("No capabilities were supplied by the current runtime.")
    lines.extend(
        (
            "",
            "## Safety",
            "",
            "- Discovery does not invoke capabilities.",
            "- `R2`, `R3`, and `UNKNOWN` require authorization before execution.",
            "- An offline entry must not be treated as available.",
            "",
        )
    )
    return "\n".join(lines)


def _git_directory(repo: Path) -> Path | None:
    marker = repo / ".git"
    if marker.is_symlink():
        raise CatalogError(f"refusing symlinked Git metadata marker: {marker}")
    if marker.is_dir():
        return marker.resolve()
    if not marker.is_file():
        return None
    content = marker.read_text(encoding="utf-8")
    if len(content) > 4096 or "\x00" in content:
        raise CatalogError(f"invalid Git metadata marker: {marker}")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) != 1 or not lines[0].startswith("gitdir:"):
        raise CatalogError(f"invalid Git metadata marker: {marker}")
    raw_path = lines[0].split(":", 1)[1].strip()
    if not raw_path:
        raise CatalogError(f"invalid Git metadata marker: {marker}")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    if not resolved.is_dir():
        raise CatalogError(f"Git metadata directory is missing: {resolved}")
    common_marker = resolved / "commondir"
    if common_marker.is_symlink():
        raise CatalogError(f"refusing symlinked Git common-directory marker: {common_marker}")
    if common_marker.is_file():
        common_content = common_marker.read_text(encoding="utf-8")
        common_lines = [line.strip() for line in common_content.splitlines() if line.strip()]
        if len(common_lines) != 1 or "\x00" in common_lines[0]:
            raise CatalogError(f"invalid Git common-directory marker: {common_marker}")
        common_directory = Path(common_lines[0])
        if not common_directory.is_absolute():
            common_directory = resolved / common_directory
        resolved = common_directory.resolve()
        if not resolved.is_dir():
            raise CatalogError(f"Git common directory is missing: {resolved}")
    return resolved


def ensure_local_git_exclude(repo: Path) -> bool:
    git_directory = _git_directory(repo)
    if git_directory is None:
        return False
    info = _prepare_private_directory(git_directory, Path("info"))
    exclude = info / "exclude"
    if exclude.is_symlink():
        raise CatalogError(f"refusing symlinked Git exclude file: {exclude}")
    if exclude.is_file() and exclude.stat().st_size > MAX_PRIVATE_FILE_BYTES:
        raise CatalogError(f"Git exclude file exceeds the accepted size: {exclude}")
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    marker = ".engineering-bible/"
    if marker in {line.strip() for line in existing.splitlines()}:
        return True
    content = existing
    if content and not content.endswith("\n"):
        content += "\n"
    content += marker + "\n"
    _atomic_private_write(exclude, content)
    return True


def persist_catalog(
    catalog: Mapping[str, object],
    *,
    engineering_home: Path,
    repo: Path,
) -> dict[str, Path]:
    """Atomically persist global and repo-local private catalog projections."""

    validate_catalog_integrity(catalog)
    home = engineering_home.expanduser()
    repository = repo.expanduser().resolve(strict=True)
    if not repository.is_dir():
        raise CatalogError(f"repository is not a directory: {repository}")

    runtime_directory = _prepare_private_directory(home, Path("runtime") / "mcp")
    repository_directory = _prepare_private_directory(
        repository,
        Path(".engineering-bible") / "mcp",
    )
    global_catalog = runtime_directory / "catalog.json"
    index = repository_directory / "index.json"
    recommendations = repository_directory / "MCP_CAPABILITIES.md"

    if not ensure_local_git_exclude(repository):
        raise CatalogError("repository has no local Git metadata for private catalog exclusion")
    _atomic_private_write(global_catalog, _json_document(catalog))
    _atomic_private_write(index, _json_document(_compact_index(catalog, repository)))
    _atomic_private_write(recommendations, _render_recommendations(catalog, repository))
    return {
        "catalog": global_catalog,
        "index": index,
        "recommendations": recommendations,
    }


def load_catalog(engineering_home: Path) -> JsonObject:
    path = engineering_home.expanduser() / "runtime" / "mcp" / "catalog.json"
    if path.is_symlink():
        raise CatalogError(f"refusing symlinked catalog: {path}")
    if not path.is_file():
        raise CatalogError(f"catalog is missing: {path}")
    if path.stat().st_size > MAX_PRIVATE_FILE_BYTES:
        raise CatalogError(f"catalog exceeds the accepted size: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"catalog cannot be read: {path}") from exc
    catalog = dict(_expect_mapping(payload, "catalog"))
    validate_catalog_integrity(catalog)
    return catalog


def repository_projection_status(
    catalog: Mapping[str, object],
    repo: Path,
) -> JsonObject:
    repository = repo.expanduser().resolve(strict=True)
    index = repository / ".engineering-bible" / "mcp" / "index.json"
    result: JsonObject = {"status": "missing", "path": str(index)}
    if index.is_symlink():
        result["status"] = "invalid"
        result["reason"] = "projection is a symlink"
        return result
    if not index.is_file():
        return result
    if index.stat().st_size > MAX_PRIVATE_FILE_BYTES:
        result["status"] = "invalid"
        result["reason"] = "projection exceeds the accepted size"
        return result
    try:
        payload = _expect_mapping(json.loads(index.read_text(encoding="utf-8")), "projection")
    except (OSError, json.JSONDecodeError, CatalogError) as exc:
        result["status"] = "invalid"
        result["reason"] = str(exc)
        return result
    if payload.get("schema_version") != CATALOG_SCHEMA_VERSION:
        result["status"] = "invalid"
        result["reason"] = "projection schema version mismatch"
        return result
    if payload.get("repository_ref") != _repository_ref(repository):
        result["status"] = "invalid"
        result["reason"] = "projection belongs to a different repository"
        return result
    result["fingerprint"] = payload.get("fingerprint")
    if payload.get("fingerprint") != catalog.get("fingerprint"):
        result["status"] = "stale"
        return result
    result["status"] = "current"
    return result


def require_current_projection(catalog: Mapping[str, object], repo: Path) -> None:
    projection = repository_projection_status(catalog, repo)
    if projection["status"] != "current":
        raise CatalogError(
            f"repository projection is {projection['status']}; refresh the runtime catalog first"
        )
