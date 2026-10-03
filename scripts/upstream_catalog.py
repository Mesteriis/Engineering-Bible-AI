"""Portable reviewed upstream skill provenance and dependency selection."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

try:
    from .registry import RegistryError, cast_dict, cast_list, parse_registry
except ImportError:
    from registry import RegistryError, cast_dict, cast_list, parse_registry


class UpstreamError(RuntimeError):
    pass


@dataclass(frozen=True)
class NoticeSpec:
    path: str
    sha256: str


@dataclass(frozen=True)
class SourceSpec:
    id: str
    url: str
    revision: str
    tracking: str
    license: str
    license_sha256: str
    license_path: str = "LICENSE"
    layout: str = "independent"
    skill_roots: tuple[str, ...] = ("skills",)
    notices: tuple[NoticeSpec, ...] = ()


@dataclass(frozen=True)
class SkillSpec:
    id: str
    name: str
    source: str
    path: str
    tree_sha256: str
    requires: tuple[str, ...]
    required_tools: tuple[str, ...]
    optional_tools: tuple[str, ...]
    intents: tuple[str, ...]
    user_invoked: bool


@dataclass(frozen=True)
class Catalog:
    sources: dict[str, SourceSpec]
    skills: dict[str, SkillSpec]
    groups: dict[str, tuple[str, ...]]


IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
REVISION = re.compile(r"[a-f0-9]{40}\Z")
RUNTIME_NAMES = {
    ".git",
    ".engineering-bible",
    "__pycache__",
    ".DS_Store",
    "auth.json",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    "capabilities.json",
}


def unsafe_runtime_path(path: PurePosixPath) -> bool:
    return any(
        part in RUNTIME_NAMES
        or part == ".env"
        or part.startswith(".env.")
        or part.endswith((".pem", ".key", ".p12", ".pfx", ".pyc"))
        for part in path.parts
    )


def overlapping_paths(paths: tuple[str, ...]) -> bool:
    return any(
        left == right or left.startswith(right + "/") or right.startswith(left + "/")
        for index, left in enumerate(paths)
        for right in paths[index + 1 :]
    )


def text_field(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        raise UpstreamError(f"{label} must be a nonempty string without control characters")
    return value


def identifier(value: object, label: str) -> str:
    result = text_field(value, label)
    if not IDENTIFIER.fullmatch(result) or result in {".", ".."}:
        raise UpstreamError(f"invalid {label}")
    return result


def safe_relative_path(value: object, label: str) -> str:
    result = text_field(value, label)
    parts = result.split("/")
    if (
        "\\" in result
        or any(part in {"", ".", ".."} for part in parts)
        or PurePosixPath(result).is_absolute()
    ):
        raise UpstreamError(f"{label} must be a safe repository-relative path")
    return result


def source_repository(url: str) -> tuple[str, str]:
    """Only credential-free public GitHub repository URLs are supported."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment:
        raise UpstreamError("source URL must be credential-free public GitHub HTTPS")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or any(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", part) is None for part in parts
    ):
        raise UpstreamError("source URL must identify one GitHub repository")
    if parts[1].endswith(".git"):
        parts[1] = parts[1][:-4]
    return parts[0], parts[1]


def string_tuple(value: object, label: str, *, ids: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise UpstreamError(f"{label} must be a list")
    values = tuple(identifier(item, label) if ids else text_field(item, label) for item in value)
    if len(set(values)) != len(values):
        raise UpstreamError(f"{label} contains duplicates")
    return values


def fields(record: object, required: set[str], optional: set[str], label: str) -> dict:
    if not isinstance(record, dict):
        raise UpstreamError(f"{label} must be an object")
    missing = required - record.keys()
    unknown = record.keys() - required - optional
    if missing or unknown:
        raise UpstreamError(
            f"{label} fields invalid (missing: {', '.join(sorted(missing))}; unknown: {', '.join(sorted(unknown))})"
        )
    return record


def unique_json_fields(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise UpstreamError("duplicate JSON field in upstream catalog")
        result[key] = value
    return result


def validate_source(source: SourceSpec) -> None:
    identifier(source.id, "source id")
    source_repository(source.url)
    if not REVISION.fullmatch(source.revision):
        raise UpstreamError("source revision must be a reviewed full 40-character commit SHA")
    if not SHA256.fullmatch(source.license_sha256):
        raise UpstreamError("source license_sha256 must be a SHA-256 digest")
    safe_relative_path(source.license_path, "license_path")
    if unsafe_runtime_path(PurePosixPath(source.license_path)):
        raise UpstreamError("source license path contains runtime state")
    if source.layout not in {"independent", "siblings"}:
        raise UpstreamError("source layout must be independent or siblings")
    if not isinstance(source.skill_roots, tuple) or not source.skill_roots:
        raise UpstreamError("source skill_roots must be a nonempty list of narrow skill roots")
    for root in source.skill_roots:
        safe_relative_path(root, "skill root")
        path = PurePosixPath(root)
        if path.name != "skills" or unsafe_runtime_path(path):
            raise UpstreamError("source skill roots must end in skills without runtime state")
    if overlapping_paths(source.skill_roots):
        raise UpstreamError("source skill roots must not duplicate or overlap")
    if not isinstance(source.notices, tuple):
        raise UpstreamError("source notices must be a list of reviewed paths and hashes")
    for notice in source.notices:
        if not isinstance(notice, NoticeSpec):
            raise UpstreamError("invalid reviewed source notice")
        safe_relative_path(notice.path, "notice path")
        if unsafe_runtime_path(PurePosixPath(notice.path)) or not SHA256.fullmatch(notice.sha256):
            raise UpstreamError("notice requires a safe path and reviewed SHA-256 digest")
        if notice.path == "LICENSE" or notice.path.startswith("LICENSE/"):
            raise UpstreamError("notice path conflicts with the retained license")
    if overlapping_paths((source.license_path, *(notice.path for notice in source.notices))):
        raise UpstreamError("source attribution paths must not duplicate or overlap")
    text_field(source.license, "license")
    # Tracking is discovery only; never an install revision or a URL.
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", source.tracking) or ".." in source.tracking:
        raise UpstreamError("source tracking must be a branch or tag name")


def load_catalog(path: Path, registry_path: Path | None = None) -> Catalog:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_json_fields)
    except (OSError, ValueError) as exc:
        raise UpstreamError("cannot read upstream catalog") from exc
    fields(payload, {"schema_version", "sources", "skills"}, set(), "catalog")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise UpstreamError("upstream catalog schema_version must be 1")
    if not isinstance(payload["sources"], list) or not isinstance(payload["skills"], list):
        raise UpstreamError("catalog sources and skills must be lists")

    sources: dict[str, SourceSpec] = {}
    for item in payload["sources"]:
        record = fields(
            item,
            {"id", "url", "revision", "tracking", "license", "license_sha256"},
            {"license_path", "layout", "skill_roots", "notices"},
            "source",
        )
        raw_notices = record.get("notices", [])
        if not isinstance(raw_notices, list):
            raise UpstreamError("source notices must be a list")
        notices = []
        for notice in raw_notices:
            item = fields(notice, {"path", "sha256"}, set(), "notice")
            notices.append(
                NoticeSpec(
                    path=text_field(item["path"], "notice path"),
                    sha256=text_field(item["sha256"], "notice sha256"),
                )
            )
        source = SourceSpec(
            **{
                key: text_field(value, f"source {key}")
                for key, value in record.items()
                if key not in {"skill_roots", "notices"}
            },
            skill_roots=string_tuple(
                record.get("skill_roots", ["skills"]), "skill_roots", ids=False
            ),
            notices=tuple(notices),
        )
        validate_source(source)
        if source.id in sources:
            raise UpstreamError(f"duplicate source id: {source.id}")
        sources[source.id] = source

    skills: dict[str, SkillSpec] = {}
    names: set[str] = set()
    for item in payload["skills"]:
        record = fields(
            item,
            {
                "id",
                "name",
                "source",
                "path",
                "tree_sha256",
                "requires",
                "required_tools",
                "optional_tools",
                "intents",
                "user_invoked",
            },
            set(),
            "skill",
        )
        skill_path = safe_relative_path(record["path"], "skill path")
        skill_name = text_field(record["name"], "skill name")
        if not SKILL_NAME.fullmatch(skill_name) or PurePosixPath(skill_path).name != skill_name:
            raise UpstreamError(
                "skill name must use lowercase hyphen naming and match its source directory"
            )
        digest = text_field(record["tree_sha256"], "tree_sha256")
        if not SHA256.fullmatch(digest):
            raise UpstreamError("tree_sha256 must be a SHA-256 digest")
        if type(record["user_invoked"]) is not bool:
            raise UpstreamError("user_invoked must be a boolean")
        skill = SkillSpec(
            id=identifier(record["id"], "skill id"),
            name=skill_name,
            source=identifier(record["source"], "skill source"),
            path=skill_path,
            tree_sha256=digest,
            requires=string_tuple(record["requires"], "requires"),
            required_tools=string_tuple(record["required_tools"], "required_tools"),
            optional_tools=string_tuple(record["optional_tools"], "optional_tools"),
            intents=string_tuple(record["intents"], "intents", ids=False),
            user_invoked=record["user_invoked"],
        )
        if skill.source not in sources:
            raise UpstreamError(f"unknown source for skill: {skill.id}")
        if not any(skill.path.startswith(root + "/") for root in sources[skill.source].skill_roots):
            raise UpstreamError("skill path must be under a declared source skill root")
        if skill.id in skills or skill.name in names:
            raise UpstreamError(f"duplicate skill identity or author name: {skill.id}")
        if set(skill.required_tools) & set(skill.optional_tools):
            raise UpstreamError(f"required and optional tool overlap: {skill.id}")
        skills[skill.id] = skill
        names.add(skill.name)

    groups: dict[str, tuple[str, ...]] = {}
    if registry_path is None:
        candidate = path.parent.parent / "skills/registry.yml"
        if candidate.is_file():
            registry_path = candidate
    if registry_path is not None:
        try:
            registry = parse_registry(registry_path)
            for group, members in cast_dict(registry["upstream"]).items():
                groups[identifier(group, "upstream group")] = tuple(cast_list(members))
        except RegistryError as exc:
            raise UpstreamError(f"invalid upstream registry: {exc}") from exc
        members = [item for group in groups.values() for item in group]
        if len(members) != len(set(members)):
            raise UpstreamError("duplicate upstream skill membership in registry")
        if set(members) != set(skills):
            raise UpstreamError("registry upstream membership must match catalog skill identities")
    catalog = Catalog(sources, skills, groups)
    if skills:
        select_skills(catalog, [], [], True)
    return catalog


def select_skills(
    catalog: Catalog, skill_ids: list[str], groups: list[str], include_all: bool
) -> list[SkillSpec]:
    if include_all:
        selected = (
            [item for members in catalog.groups.values() for item in members]
            if catalog.groups
            else list(catalog.skills)
        )
        selected.extend(skill_ids)
    else:
        selected = list(skill_ids)
    for group in groups:
        if group not in catalog.groups:
            raise UpstreamError(f"unknown upstream group: {group}")
        selected.extend(catalog.groups[group])
    if not selected:
        raise UpstreamError("select at least one upstream skill or group")
    result: list[SkillSpec] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(skill_id: str) -> None:
        if skill_id not in catalog.skills:
            raise UpstreamError(f"unknown upstream skill: {skill_id}")
        if skill_id in visiting:
            raise UpstreamError(f"upstream dependency cycle: {skill_id}")
        if skill_id in visited:
            return
        visiting.add(skill_id)
        for required in catalog.skills[skill_id].requires:
            visit(required)
        visiting.remove(skill_id)
        visited.add(skill_id)
        result.append(catalog.skills[skill_id])

    for selected_id in selected:
        visit(selected_id)
    return result


def fingerprint_tree(root: Path) -> str:
    """Public catalog interface; implementation shares the source safety rules."""
    try:
        from .upstream_sources import fingerprint_tree as fingerprint
    except ImportError:
        from upstream_sources import fingerprint_tree as fingerprint
    return fingerprint(root)
