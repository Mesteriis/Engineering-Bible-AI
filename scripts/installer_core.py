#!/usr/bin/env python3
"""Ownership-safe, transactional installer for Engineering Bible AI."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import uuid

from registry import default_group_names, load_registry


MANIFEST_SCHEMA = 1
PACKAGE_NAME = "engineering-bible-ai"
ROOT_NAMES = ("be_home", "codex_home", "agents_home", "bin_dir")
MUTATING_STATUSES = {"ADD", "UPDATE", "MODE", "REMOVE"}
INSTALLED_STATUSES = {"ADD", "UPDATE", "MODE", "UNCHANGED", "ADOPT"}
CONFLICT_STATUSES = {"CONFLICT", "UNMANAGED"}

IGNORE_DIRS = {
    ".git",
    ".worktrees",
    ".serena",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    ".engineering-bible",
    "graphify-out",
    "node_modules",
    "__pycache__",
}
IGNORE_SUFFIXES = {".pyc", ".pyo"}
SNAPSHOT_DIRS = (
    ".github",
    "config",
    "docs",
    "engineering",
    "examples",
    "instructions",
    "reference",
    "schemas",
    "scripts",
    "skills",
    "templates",
    "tests",
)
SNAPSHOT_FILES = (
    ".gitignore",
    ".python-version",
    ".secret-sanity-allowlist",
    "AGENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "LICENSE",
    "MANIFEST.md",
    "Makefile",
    "README.md",
    "README.ru.md",
    "SECURITY.md",
    "SUPPORT.md",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "pyproject.toml",
)
EXECUTABLES = {
    "scripts/audit-quality-gates.py",
    "scripts/be.py",
    "scripts/check-file-size.py",
    "scripts/install-codex.sh",
    "scripts/install-tools.sh",
    "scripts/install.sh",
    "scripts/install_codex.py",
    "scripts/registry.py",
    "scripts/secret-sanity.sh",
    "scripts/validate.py",
    "scripts/validate-acceptance.py",
    "scripts/validate-installed-tree.sh",
    "scripts/validate-markdown-style.py",
    "scripts/validate-repo-tree.sh",
    "scripts/validate-router-cases.py",
    "scripts/validate-skill-frontmatter.py",
    "scripts/validate-skill-tree.sh",
    "skills/workflow-router/scripts/validate-routing.sh",
}


class InstallError(RuntimeError):
    """An install cannot be completed without risking managed state."""


@dataclass(frozen=True)
class InstallerOptions:
    repo_root: Path
    codex_home: Path
    agents_home: Path
    be_home: Path
    bin_dir: Path
    dry_run: bool
    backup_only: bool
    no_overwrite: bool
    force: bool
    diff: bool
    groups: list[str]
    all_groups: bool
    install_tools: bool
    migrate_legacy: bool
    prompt_profile: str
    backup_dir: Path

    def roots(self) -> dict[str, Path]:
        return {
            "be_home": self.be_home,
            "codex_home": self.codex_home,
            "agents_home": self.agents_home,
            "bin_dir": self.bin_dir,
        }

    @property
    def manifest_path(self) -> Path:
        return self.be_home / "install-manifest.json"


@dataclass(frozen=True)
class DesiredFile:
    root: str
    path: str
    content: bytes
    sha256: str
    mode: int


@dataclass(frozen=True)
class OwnedFile:
    root: str
    path: str
    sha256: str
    mode: int


@dataclass(frozen=True)
class FileState:
    kind: str
    sha256: str | None = None
    mode: int | None = None


@dataclass(frozen=True)
class PlannedAction:
    root: str
    path: str
    target: Path
    status: str
    observed: FileState
    desired: DesiredFile | None = None
    prior: OwnedFile | None = None

    @property
    def relative(self) -> str:
        return f"{self.root}:{self.path}"


@dataclass(frozen=True)
class ManifestState:
    payload: dict[str, object]
    files: dict[tuple[str, str], OwnedFile]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def mode_string(mode: int) -> str:
    return f"{mode:04o}"


def parse_mode(value: object, *, context: str) -> int:
    if not isinstance(value, str) or len(value) != 4 or value[0] != "0":
        raise InstallError(f"invalid mode in install manifest for {context}")
    if any(character not in "01234567" for character in value):
        raise InstallError(f"invalid mode in install manifest for {context}")
    return int(value, 8)


def normalize_relative(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InstallError(f"invalid relative path in install manifest for {context}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise InstallError(f"unsafe relative path in install manifest for {context}: {value!r}")
    return value


def safe_target(root: Path, relative: str) -> Path:
    normalized = normalize_relative(relative, context="target")
    resolved_root = root.resolve()
    candidate = root / PurePosixPath(normalized)
    resolved_candidate = candidate.resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise InstallError(f"target escapes managed root: {root}:{relative}") from exc
    return candidate


def ignored(relative: Path) -> bool:
    return any(part in IGNORE_DIRS for part in relative.parts) or relative.suffix in IGNORE_SUFFIXES


def iter_source_files(source: Path) -> Iterator[Path]:
    if source.is_symlink():
        raise InstallError(f"symbolic links are not allowed in the portable package: {source}")
    if source.is_file():
        yield source
        return
    if not source.is_dir():
        raise InstallError(f"missing package source: {source}")
    for candidate in sorted(source.rglob("*")):
        relative = candidate.relative_to(source)
        if ignored(relative):
            continue
        if candidate.is_symlink():
            raise InstallError(
                f"symbolic links are not allowed in the portable package: {candidate}"
            )
        if candidate.is_file():
            yield candidate


def desired_mode(repo_relative: str, source: Path) -> int:
    if repo_relative in EXECUTABLES:
        return 0o755
    return 0o755 if stat.S_IMODE(source.stat().st_mode) & 0o111 else 0o644


def make_desired(root: str, path: str, content: bytes, mode: int) -> DesiredFile:
    normalized = normalize_relative(path, context=f"desired {root}")
    return DesiredFile(
        root=root,
        path=normalized,
        content=content,
        sha256=sha256_bytes(content),
        mode=mode,
    )


def wrapper_content(be_home: Path) -> bytes:
    import shlex

    target_script = be_home / "current" / "scripts" / "be.py"
    quoted_target = shlex.quote(str(target_script))
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'python_bin="${ENGINEERING_BIBLE_PYTHON:-}"\n'
        'if [[ -z "$python_bin" ]]; then\n'
        "    if command -v python3.11 >/dev/null 2>&1; then\n"
        "        python_bin=python3.11\n"
        "    else\n"
        "        python_bin=python3\n"
        "    fi\n"
        "fi\n"
        'if ! command -v "$python_bin" >/dev/null 2>&1; then\n'
        '    echo "Python interpreter not found: $python_bin" >&2\n'
        "    exit 1\n"
        "fi\n"
        '"$python_bin" -c \'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else "Python 3.11+ is required")\'\n'
        f'exec "$python_bin" {quoted_target} "$@"\n'
    ).encode()


def prompt_source(options: InstallerOptions) -> Path:
    candidate = options.repo_root / "instructions" / "global" / f"{options.prompt_profile}.md"
    if candidate.is_file():
        return candidate
    if options.prompt_profile == "full":
        return options.repo_root / "AGENTS.md"
    raise InstallError(f"prompt profile is not available: {options.prompt_profile}")


def build_desired_files(options: InstallerOptions, skills: list[str]) -> list[DesiredFile]:
    desired: dict[tuple[str, str], DesiredFile] = {}

    def add_bytes(root: str, relative: str, content: bytes, mode: int) -> None:
        item = make_desired(root, relative, content, mode)
        key = (root, item.path)
        if key in desired:
            raise InstallError(f"duplicate managed target: {root}:{item.path}")
        safe_target(options.roots()[root], item.path)
        desired[key] = item

    def add_file(source: Path, root: str, relative: str, repo_relative: str) -> None:
        if source.is_symlink() or not source.is_file():
            raise InstallError(f"missing or unsafe package source: {repo_relative}")
        add_bytes(root, relative, source.read_bytes(), desired_mode(repo_relative, source))

    def add_tree(source_relative: str, root: str, target_prefix: str) -> None:
        source_root = options.repo_root / source_relative
        if not source_root.exists():
            return
        for source in iter_source_files(source_root):
            source_child = source.relative_to(source_root).as_posix()
            repo_relative = f"{source_relative}/{source_child}"
            target_relative = f"{target_prefix}/{source_child}"
            add_file(source, root, target_relative, repo_relative)

    for filename in SNAPSHOT_FILES:
        source = options.repo_root / filename
        if source.is_file():
            add_file(source, "be_home", f"current/{filename}", filename)
    for directory in SNAPSHOT_DIRS:
        add_tree(directory, "be_home", f"current/{directory}")

    global_instructions = prompt_source(options)
    instructions_relative = global_instructions.relative_to(options.repo_root).as_posix()
    add_file(global_instructions, "codex_home", "AGENTS.md", instructions_relative)
    add_file(
        options.repo_root / "skills" / "registry.yml",
        "codex_home",
        "skills/registry.yml",
        "skills/registry.yml",
    )
    add_file(
        options.repo_root / "skills" / "registry.yml",
        "agents_home",
        "skills/registry.yml",
        "skills/registry.yml",
    )
    add_tree("engineering", "agents_home", "engineering")
    for skill in skills:
        add_tree(f"skills/{skill}", "codex_home", f"skills/{skill}")

    add_bytes("bin_dir", "be", wrapper_content(options.be_home), 0o755)
    return [desired[key] for key in sorted(desired)]


def file_state(path: Path) -> FileState:
    if path.is_symlink():
        return FileState("symlink")
    try:
        file_stat = path.stat()
    except FileNotFoundError:
        return FileState("missing")
    if not stat.S_ISREG(file_stat.st_mode):
        return FileState("other")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return FileState("file", digest.hexdigest(), stat.S_IMODE(file_stat.st_mode))


def root_strings(options: InstallerOptions) -> dict[str, str]:
    return {name: str(path.resolve()) for name, path in options.roots().items()}


def load_manifest(options: InstallerOptions) -> ManifestState | None:
    path = options.manifest_path
    if path.is_symlink():
        raise InstallError(f"install manifest must not be a symbolic link: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise InstallError(f"install manifest is not a regular file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"invalid install manifest: {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != MANIFEST_SCHEMA:
        raise InstallError(f"unsupported install manifest schema: {path}")

    roots = payload.get("roots")
    if not isinstance(roots, dict) or roots != root_strings(options):
        raise InstallError(
            "install manifest roots differ from the requested roots; "
            "rerun with the original CODEX_HOME/AGENTS_HOME/ENGINEERING_BIBLE_BIN_DIR"
        )
    raw_files = payload.get("files")
    if not isinstance(raw_files, list):
        raise InstallError(f"install manifest has no file inventory: {path}")

    files: dict[tuple[str, str], OwnedFile] = {}
    for index, raw in enumerate(raw_files):
        context = f"files[{index}]"
        if not isinstance(raw, dict):
            raise InstallError(f"invalid install manifest entry: {context}")
        raw_root = raw.get("root")
        if not isinstance(raw_root, str) or raw_root not in ROOT_NAMES:
            raise InstallError(f"invalid root in install manifest for {context}")
        root = raw_root
        relative = normalize_relative(raw.get("path"), context=context)
        digest = raw.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise InstallError(f"invalid sha256 in install manifest for {context}")
        mode = parse_mode(raw.get("mode"), context=context)
        key = (root, relative)
        if key in files:
            raise InstallError(f"duplicate install manifest entry: {root}:{relative}")
        safe_target(options.roots()[root], relative)
        files[key] = OwnedFile(root, relative, digest, mode)
    return ManifestState(payload=payload, files=files)


def state_matches(state: FileState, digest: str, mode: int) -> bool:
    return state.kind == "file" and state.sha256 == digest and state.mode == mode


def legacy_signature_matches(
    options: InstallerOptions, root: str, path: str, state: FileState
) -> bool:
    signature_path = options.repo_root / "config" / "legacy-install-signatures.json"
    if not options.migrate_legacy or not signature_path.is_file():
        return False
    try:
        payload = json.loads(signature_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"invalid legacy signature manifest: {signature_path}: {exc}") from exc
    entries = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise InstallError(f"legacy signature manifest has no files: {signature_path}")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("root") != root or entry.get("path") != path:
            continue
        digest = entry.get("sha256")
        mode = entry.get("mode")
        if isinstance(digest, str) and isinstance(mode, str):
            return state_matches(state, digest, int(mode, 8))
    return False


def build_actions(
    desired_files: Iterable[DesiredFile],
    previous: ManifestState | None,
    options: InstallerOptions,
) -> list[PlannedAction]:
    prior_files = previous.files if previous else {}
    desired = {(item.root, item.path): item for item in desired_files}
    actions: list[PlannedAction] = []

    for key in sorted(desired):
        item = desired[key]
        prior = prior_files.get(key)
        target = safe_target(options.roots()[item.root], item.path)
        observed = file_state(target)
        if observed.kind == "missing":
            status = "ADD"
        elif prior is None:
            if options.migrate_legacy and state_matches(observed, item.sha256, item.mode):
                status = "ADOPT"
            elif legacy_signature_matches(options, item.root, item.path, observed):
                status = "UPDATE"
            elif options.no_overwrite:
                status = "SKIP"
            else:
                status = "UNMANAGED"
        elif observed.kind != "file":
            status = "CONFLICT"
        elif observed.sha256 == item.sha256 and observed.mode == item.mode:
            status = "UNCHANGED"
        elif observed.sha256 == item.sha256:
            status = "MODE"
        elif options.no_overwrite:
            status = "SKIP"
        elif options.force:
            status = "UPDATE"
        else:
            status = "CONFLICT"
        actions.append(
            PlannedAction(
                root=item.root,
                path=item.path,
                target=target,
                status=status,
                observed=observed,
                desired=item,
                prior=prior,
            )
        )

    for key in sorted(set(prior_files) - set(desired)):
        prior = prior_files[key]
        target = safe_target(options.roots()[prior.root], prior.path)
        observed = file_state(target)
        if observed.kind == "missing":
            status = "MISSING"
        elif observed.kind != "file":
            status = "CONFLICT"
        elif state_matches(observed, prior.sha256, prior.mode):
            status = "REMOVE"
        elif options.no_overwrite:
            status = "SKIP"
        elif options.force:
            status = "REMOVE"
        else:
            status = "CONFLICT"
        actions.append(
            PlannedAction(
                root=prior.root,
                path=prior.path,
                target=target,
                status=status,
                observed=observed,
                prior=prior,
            )
        )
    return actions


def backup_actions(
    desired_files: Iterable[DesiredFile],
    previous: ManifestState | None,
    options: InstallerOptions,
) -> list[PlannedAction]:
    keys: dict[tuple[str, str], DesiredFile | OwnedFile] = {
        (item.root, item.path): item for item in desired_files
    }
    if previous:
        keys.update(previous.files)
    actions: list[PlannedAction] = []
    for key in sorted(keys):
        item = keys[key]
        target = safe_target(options.roots()[item.root], item.path)
        observed = file_state(target)
        status = "BACKUP" if observed.kind == "file" else "MISSING"
        if observed.kind not in {"file", "missing"}:
            status = "CONFLICT"
        actions.append(
            PlannedAction(
                root=item.root,
                path=item.path,
                target=target,
                status=status,
                observed=observed,
                desired=item if isinstance(item, DesiredFile) else None,
                prior=item if isinstance(item, OwnedFile) else None,
            )
        )
    return actions


def manifest_entry(item: DesiredFile | OwnedFile) -> dict[str, str]:
    return {
        "root": item.root,
        "path": item.path,
        "sha256": item.sha256,
        "mode": mode_string(item.mode),
    }


def final_owned_files(actions: Iterable[PlannedAction]) -> list[DesiredFile | OwnedFile]:
    final: dict[tuple[str, str], DesiredFile | OwnedFile] = {}
    for action in actions:
        key = (action.root, action.path)
        if action.desired is not None and action.status in INSTALLED_STATUSES:
            final[key] = action.desired
        elif action.status == "SKIP" and action.prior is not None:
            final[key] = action.prior
    return [final[key] for key in sorted(final)]


def package_digest(desired_files: Iterable[DesiredFile]) -> str:
    inventory = [manifest_entry(item) for item in desired_files]
    payload = json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{sha256_bytes(payload)}"


def read_version(repo_root: Path) -> str:
    path = repo_root / "VERSION"
    if not path.is_file():
        raise InstallError("missing source: VERSION")
    version = path.read_text(encoding="utf-8").strip()
    if not version:
        raise InstallError("VERSION is empty")
    return version


def source_metadata(
    options: InstallerOptions,
    previous: ManifestState | None,
) -> dict[str, str]:
    explicit_source = any(
        name in os.environ
        for name in (
            "ENGINEERING_BIBLE_SOURCE_KIND",
            "ENGINEERING_BIBLE_SOURCE_REF",
            "ENGINEERING_BIBLE_SOURCE_LOCATION",
            "ENGINEERING_BIBLE_SOURCE_DIGEST",
        )
    )
    installed_root = options.be_home / "current"
    if not explicit_source and options.repo_root.resolve() == installed_root.resolve() and previous:
        package = previous.payload.get("package")
        prior_source = package.get("source") if isinstance(package, dict) else None
        if isinstance(prior_source, dict) and all(
            isinstance(key, str) and isinstance(value, str) for key, value in prior_source.items()
        ):
            return {
                key: value
                for key, value in prior_source.items()
                if isinstance(key, str) and isinstance(value, str)
            }

    kind = os.environ.get("ENGINEERING_BIBLE_SOURCE_KIND", "checkout")
    reference = os.environ.get("ENGINEERING_BIBLE_SOURCE_REF", "working-tree")
    location = os.environ.get("ENGINEERING_BIBLE_SOURCE_LOCATION", str(options.repo_root))
    result = {"kind": kind, "reference": reference, "location": location}
    digest = os.environ.get("ENGINEERING_BIBLE_SOURCE_DIGEST")
    if digest:
        result["digest"] = digest
    return result


def build_manifest(
    options: InstallerOptions,
    desired_files: list[DesiredFile],
    actions: list[PlannedAction],
    registry: dict[str, object],
    skills: list[str],
    previous: ManifestState | None,
) -> dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA,
        "package": {
            "name": PACKAGE_NAME,
            "version": read_version(options.repo_root),
            "digest": package_digest(desired_files),
            "source": source_metadata(options, previous),
        },
        "roots": root_strings(options),
        "groups": {
            "default": default_group_names(registry),
            "requested": options.groups,
            "include_all": options.all_groups,
            "prompt_profile": options.prompt_profile,
            "selected_skills": skills,
        },
        "complete": not any(action.status == "SKIP" for action in actions),
        "files": [manifest_entry(item) for item in final_owned_files(actions)],
    }


def encode_json(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate_lock_identity(file_descriptor: int, lock_path: Path) -> os.stat_result:
    descriptor_state = os.fstat(file_descriptor)
    if not stat.S_ISREG(descriptor_state.st_mode):
        raise InstallError(f"installer lock is not a regular file: {lock_path}")
    if descriptor_state.st_uid != os.geteuid():
        raise InstallError(f"installer lock is not owned by the current user: {lock_path}")
    if descriptor_state.st_nlink != 1:
        raise InstallError(f"installer lock must have exactly one link: {lock_path}")

    try:
        path_state = os.stat(lock_path, follow_symlinks=False)
    except FileNotFoundError as exc:
        raise InstallError(f"installer lock path changed while opening: {lock_path}") from exc
    if not stat.S_ISREG(path_state.st_mode):
        raise InstallError(f"installer lock path is not a regular file: {lock_path}")
    if path_state.st_uid != os.geteuid():
        raise InstallError(f"installer lock path is not owned by the current user: {lock_path}")
    if path_state.st_nlink != 1:
        raise InstallError(f"installer lock path must have exactly one link: {lock_path}")
    if (path_state.st_dev, path_state.st_ino) != (
        descriptor_state.st_dev,
        descriptor_state.st_ino,
    ):
        raise InstallError(f"installer lock path changed while opening: {lock_path}")
    return descriptor_state


def open_install_lock(lock_path: Path) -> int:
    flags = os.O_RDWR | os.O_NONBLOCK | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        return os.open(lock_path, flags | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            existing = os.stat(lock_path, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise InstallError(f"installer lock path changed while opening: {lock_path}") from exc
        if not stat.S_ISREG(existing.st_mode):
            raise InstallError(f"installer lock path is not a regular file: {lock_path}")
        if existing.st_uid != os.geteuid():
            raise InstallError(f"installer lock path is not owned by the current user: {lock_path}")
        if existing.st_nlink != 1:
            raise InstallError(f"installer lock path must have exactly one link: {lock_path}")
        try:
            return os.open(lock_path, flags)
        except OSError as exc:
            raise InstallError(f"cannot safely open installer lock: {lock_path}: {exc}") from exc
    except OSError as exc:
        raise InstallError(f"cannot safely create installer lock: {lock_path}: {exc}") from exc


def has_managed_lock_content(file_descriptor: int) -> bool:
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    content = os.read(file_descriptor, 65)
    if content == b"":
        return True
    if len(content) > 64 or not content.startswith(b"pid=") or not content.endswith(b"\n"):
        return False
    pid = content[4:-1]
    return bool(pid) and len(pid) <= 20 and pid.isdigit() and int(pid) > 0


@contextmanager
def install_lock(options: InstallerOptions) -> Iterator[None]:
    options.be_home.mkdir(parents=True, exist_ok=True)
    lock_path = options.be_home / ".install.lock"
    file_descriptor = open_install_lock(lock_path)
    locked = False
    try:
        validate_lock_identity(file_descriptor, lock_path)
        try:
            fcntl.flock(file_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InstallError(f"another installer holds the lock: {lock_path}") from exc
        locked = True
        validate_lock_identity(file_descriptor, lock_path)
        if not has_managed_lock_content(file_descriptor):
            raise InstallError(f"refusing to replace unmanaged installer lock: {lock_path}")

        validate_lock_identity(file_descriptor, lock_path)
        os.fchmod(file_descriptor, 0o600)
        content = f"pid={os.getpid()}\n".encode()
        os.lseek(file_descriptor, 0, os.SEEK_SET)
        os.ftruncate(file_descriptor, 0)
        remaining = memoryview(content)
        while remaining:
            written = os.write(file_descriptor, remaining)
            if written == 0:
                raise InstallError(f"short write while updating installer lock: {lock_path}")
            remaining = remaining[written:]
        os.fsync(file_descriptor)
        validate_lock_identity(file_descriptor, lock_path)
        try:
            yield
        finally:
            fcntl.flock(file_descriptor, fcntl.LOCK_UN)
            locked = False
    finally:
        if locked:
            fcntl.flock(file_descriptor, fcntl.LOCK_UN)
        os.close(file_descriptor)


def backup_path(options: InstallerOptions, action: PlannedAction) -> Path:
    return options.backup_dir / "files" / action.root / PurePosixPath(action.path)


def prepare_backup(options: InstallerOptions, actions: Iterable[PlannedAction]) -> None:
    options.backup_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    for action in actions:
        if action.observed.kind != "file":
            continue
        destination = backup_path(options, action)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.target, destination, follow_symlinks=False)
    if options.manifest_path.is_file() and not options.manifest_path.is_symlink():
        shutil.copy2(options.manifest_path, options.backup_dir / "manifest.before.json")


def write_journal(
    options: InstallerOptions,
    transaction_id: str,
    state: str,
    actions: Iterable[PlannedAction],
    applied: int,
    error: str | None = None,
) -> None:
    payload: dict[str, object] = {
        "schema_version": 1,
        "transaction_id": transaction_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "applied": applied,
        "operations": [
            {"root": action.root, "path": action.path, "status": action.status}
            for action in actions
            if action.status in MUTATING_STATUSES
        ],
    }
    if error:
        payload["error"] = error
    atomic_write(options.backup_dir / "journal.json", encode_json(payload), 0o600)


def stage_file(stage_root: Path, action: PlannedAction) -> Path:
    if action.desired is None:
        raise InstallError(f"missing desired content for {action.relative}")
    destination = safe_target(stage_root, action.path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(action.desired.content)
        handle.flush()
        os.fsync(handle.fileno())
    destination.chmod(action.desired.mode)
    return destination


def remove_regular_file(path: Path) -> None:
    state = file_state(path)
    if state.kind == "missing":
        return
    if state.kind != "file":
        raise InstallError(f"refusing to remove non-file target: {path}")
    path.unlink()


def rollback_actions(
    options: InstallerOptions,
    applied: list[PlannedAction],
    stage_roots: dict[str, Path],
    *,
    manifest_touched: bool,
) -> list[str]:
    errors: list[str] = []
    for action in reversed(applied):
        try:
            backup = backup_path(options, action)
            if backup.is_file():
                restore = safe_target(stage_roots[action.root], f"rollback/{action.path}")
                restore.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, restore)
                action.target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(restore, action.target)
            else:
                remove_regular_file(action.target)
        except (InstallError, OSError) as exc:
            errors.append(f"{action.relative}: {exc}")

    if manifest_touched:
        manifest_backup = options.backup_dir / "manifest.before.json"
        try:
            if manifest_backup.is_file():
                restore = options.be_home / f".manifest-rollback-{uuid.uuid4().hex}"
                shutil.copy2(manifest_backup, restore)
                os.replace(restore, options.manifest_path)
            elif options.manifest_path.exists():
                remove_regular_file(options.manifest_path)
        except (InstallError, OSError) as exc:
            errors.append(f"manifest: {exc}")
    return errors


def parse_failure_injection() -> int | None:
    raw = os.environ.get("ENGINEERING_BIBLE_TEST_FAIL_AFTER")
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise InstallError("ENGINEERING_BIBLE_TEST_FAIL_AFTER must be an integer") from exc
    if value < 0:
        raise InstallError("ENGINEERING_BIBLE_TEST_FAIL_AFTER must not be negative")
    return value


def apply_transaction(
    actions: list[PlannedAction],
    manifest: dict[str, object],
    options: InstallerOptions,
) -> None:
    conflicts = [action for action in actions if action.status in CONFLICT_STATUSES]
    if conflicts:
        unmanaged = [action.relative for action in conflicts if action.status == "UNMANAGED"]
        changed = [action.relative for action in conflicts if action.status == "CONFLICT"]
        details: list[str] = []
        if unmanaged:
            details.append(
                "unmanaged target(s) preserved; remove them or use --migrate-legacy "
                "for byte-identical legacy files: " + ", ".join(unmanaged)
            )
        if changed:
            details.append("changed managed target(s) require --force: " + ", ".join(changed))
        raise InstallError("; ".join(details))

    manifest_bytes = encode_json(manifest)
    manifest_state = file_state(options.manifest_path)
    manifest_changed = not (
        manifest_state.kind == "file"
        and manifest_state.sha256 == sha256_bytes(manifest_bytes)
        and manifest_state.mode == 0o600
    )
    mutations = [action for action in actions if action.status in MUTATING_STATUSES]
    if not mutations and not manifest_changed:
        return

    transaction_id = uuid.uuid4().hex
    stage_roots: dict[str, Path] = {}
    applied: list[PlannedAction] = []
    manifest_touched = False
    failure_after = parse_failure_injection()
    try:
        for root_name, root in options.roots().items():
            root.mkdir(parents=True, exist_ok=True)
            stage = root / f".engineering-bible-staging-{transaction_id}-{root_name}"
            stage.mkdir(mode=0o700)
            stage_roots[root_name] = stage

        staged: dict[tuple[str, str], Path] = {}
        for action in mutations:
            if action.status in {"ADD", "UPDATE"}:
                staged[(action.root, action.path)] = stage_file(stage_roots[action.root], action)

        prepare_backup(options, mutations)
        write_journal(options, transaction_id, "prepared", mutations, 0)

        if failure_after == 0:
            raise InstallError("injected transaction failure before first operation")
        for action in mutations:
            if file_state(action.target) != action.observed:
                raise InstallError(f"target changed while install was running: {action.relative}")
            action.target.parent.mkdir(parents=True, exist_ok=True)
            if action.status in {"ADD", "UPDATE"}:
                os.replace(staged[(action.root, action.path)], action.target)
            elif action.status == "MODE":
                if action.desired is None:
                    raise InstallError(f"missing desired mode for {action.relative}")
                action.target.chmod(action.desired.mode)
            elif action.status == "REMOVE":
                remove_regular_file(action.target)
            applied.append(action)
            write_journal(options, transaction_id, "applying", mutations, len(applied))
            if failure_after is not None and len(applied) == failure_after:
                raise InstallError(
                    f"injected transaction failure after {failure_after} operation(s)"
                )

        atomic_write(options.manifest_path, manifest_bytes, 0o600)
        manifest_touched = True
        write_journal(options, transaction_id, "committed", mutations, len(applied))
    except (InstallError, OSError) as exc:
        rollback_errors = rollback_actions(
            options,
            applied,
            stage_roots,
            manifest_touched=manifest_touched,
        )
        try:
            write_journal(
                options,
                transaction_id,
                "rollback-failed" if rollback_errors else "rolled-back",
                mutations,
                len(applied),
                str(exc),
            )
        except OSError as journal_exc:
            rollback_errors.append(f"journal: {journal_exc}")
        if rollback_errors:
            raise InstallError(
                f"transaction failed; rollback incomplete: {exc}; " + "; ".join(rollback_errors)
            ) from exc
        raise InstallError(f"transaction failed and rolled back: {exc}") from exc
    finally:
        for stage in stage_roots.values():
            shutil.rmtree(stage, ignore_errors=True)


def apply_backup_only(actions: list[PlannedAction], options: InstallerOptions) -> None:
    conflicts = [action.relative for action in actions if action.status == "CONFLICT"]
    if conflicts:
        raise InstallError("refusing to back up non-file target(s): " + ", ".join(conflicts))
    present = [action for action in actions if action.status == "BACKUP"]
    if not present and not options.manifest_path.is_file():
        return
    prepare_backup(options, present)
    write_journal(options, uuid.uuid4().hex, "backup-only", [], 0)


def print_actions(actions: Iterable[PlannedAction]) -> None:
    for action in actions:
        print(f"{action.status:10} {action.relative} -> {action.target}")


def print_header(options: InstallerOptions, skills: list[str]) -> None:
    if options.backup_only:
        mode = "--backup-only"
    elif options.dry_run:
        mode = "--dry-run"
    else:
        mode = "--install"
    print(f"Repo: {options.repo_root}")
    print(f"Engineering Bible home: {options.be_home}")
    print(f"Codex home: {options.codex_home}")
    print(f"Agents home: {options.agents_home}")
    print(f"Bin dir: {options.bin_dir}")
    print(f"Mode: {mode}")
    print(f"Backup: {options.backup_dir}")
    groups = ", ".join(options.groups) if options.groups else "(default)"
    print(f"Skill groups: {groups}{' + all' if options.all_groups else ''}")
    print(f"Prompt profile: {options.prompt_profile}")
    print(f"Migrate legacy: {'yes' if options.migrate_legacy else 'no'}")
    print(f"Install tools: {'yes' if options.install_tools else 'no'}")
    print("Skills: " + ", ".join(skills))


def load_install_inputs(
    options: InstallerOptions,
    skills: list[str],
) -> tuple[dict[str, object], list[DesiredFile], ManifestState | None]:
    registry = load_registry(options.repo_root)
    desired = build_desired_files(options, skills)
    previous = load_manifest(options)
    return registry, desired, previous


def run_install(options: InstallerOptions, skills: list[str]) -> list[PlannedAction]:
    def prepare_and_maybe_apply() -> list[PlannedAction]:
        registry, desired, previous = load_install_inputs(options, skills)
        if options.backup_only:
            actions = backup_actions(desired, previous, options)
        else:
            actions = build_actions(desired, previous, options)
        print_header(options, skills)
        print_actions(actions)
        if options.dry_run:
            return actions
        if options.backup_only:
            apply_backup_only(actions, options)
        else:
            manifest = build_manifest(options, desired, actions, registry, skills, previous)
            apply_transaction(actions, manifest, options)
        return actions

    if options.dry_run:
        return prepare_and_maybe_apply()
    with install_lock(options):
        return prepare_and_maybe_apply()
