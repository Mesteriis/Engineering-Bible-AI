"""Independent, ownership-safe lifecycle for unchanged upstream skill trees."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import AbstractSet, Iterator, cast
import urllib.request
from urllib.parse import urlparse
import uuid

try:
    from .upstream_catalog import Catalog, SkillSpec, SourceSpec, UpstreamError, fingerprint_tree
    from .upstream_sources import stage_source
except ImportError:
    from upstream_catalog import Catalog, SkillSpec, SourceSpec, UpstreamError, fingerprint_tree
    from upstream_sources import stage_source


NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA = re.compile(r"^[a-f0-9]{64}$")
REVISION = re.compile(r"^[a-f0-9]{40}$")
BACKUP = re.compile(r"^[a-f0-9]{32}$")


def tracking_revision(source: SourceSpec) -> str:
    """Read a GitHub tracking ref without changing the reviewed installation pin."""
    parsed = urlparse(source.url)
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if parsed.netloc != "github.com" or len(parts) != 2:
        raise UpstreamError("tracking checks currently support GitHub sources only")
    from urllib.parse import quote

    ref = quote(source.tracking, safe="")
    url = f"https://api.github.com/repos/{parts[0]}/{parts[1]}/commits/{ref}"
    request = urllib.request.Request(url, headers={"User-Agent": "Engineering-Bible-skill-check"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise UpstreamError("tracking response exceeds size limit")
        payload = json.loads(raw)
        revision = payload.get("sha") if isinstance(payload, dict) else None
        if not isinstance(revision, str) or not REVISION.fullmatch(revision):
            raise UpstreamError("tracking response does not contain a full commit")
        return revision
    except (OSError, ValueError) as exc:
        raise UpstreamError(
            f"cannot check upstream ref for {source.id}: {type(exc).__name__}"
        ) from exc


def _safe_directory(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise UpstreamError(f"unsafe dependency directory: {path}")


def _read_json(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise UpstreamError(f"unsafe or missing state file: {path}")
    try:
        if path.stat().st_size > 8 * 1024 * 1024:
            raise UpstreamError("dependency state exceeds size limit")
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UpstreamError(f"invalid dependency state: {path.name}") from exc
    if not isinstance(result, dict):
        raise UpstreamError("dependency state must be an object")
    return result


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    if path.is_symlink():
        raise UpstreamError(f"refusing symlink state file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_skill(tree: Path, skill: SkillSpec) -> None:
    path = tree / "SKILL.md"
    if path.is_symlink() or not path.is_file():
        raise UpstreamError(f"missing skill entry point: {skill.id}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise UpstreamError(f"missing skill frontmatter: {skill.id}")
    try:
        end = lines.index("---", 1, min(len(lines), 100))
    except ValueError as exc:
        raise UpstreamError(f"invalid skill frontmatter: {skill.id}") from exc
    names = [
        line[5:].strip().strip('"').strip("'") for line in lines[1:end] if line.startswith("name:")
    ]
    descriptions = [line[12:].strip() for line in lines[1:end] if line.startswith("description:")]
    if names != [skill.name] or len(descriptions) != 1 or not descriptions[0]:
        raise UpstreamError(f"skill name/description does not match reviewed catalog: {skill.id}")


class SkillManager:
    def __init__(
        self,
        catalog: Catalog,
        home: Path,
        skill_root: Path,
        existing_roots: tuple[Path, ...] = (),
    ) -> None:
        self.catalog = catalog
        self.home = Path(home).absolute()
        self.skill_root = Path(skill_root).absolute()
        self.existing_roots = tuple(Path(path).absolute() for path in existing_roots)
        self.store = self.home / "dependencies"
        self.state_path = self.store / "state.json"
        self.journal_path = self.store / "transaction.json"

    def _target(self, name: str) -> Path:
        if not NAME.fullmatch(name):
            raise UpstreamError("invalid active skill name")
        _safe_directory(self.skill_root)
        return self.skill_root / name

    def _validate_state(self, state: dict[str, object]) -> dict[str, object]:
        if state.get("schema_version") != 1 or not isinstance(state.get("skills"), dict):
            raise UpstreamError("unsupported dependency state schema")
        if state.get("last_backup") is not None:
            identity, digest = state.get("last_backup"), state.get("backup_sha256")
            if (
                not isinstance(identity, str)
                or not BACKUP.fullmatch(identity)
                or not isinstance(digest, str)
                or not SHA.fullmatch(digest)
            ):
                raise UpstreamError("invalid dependency backup binding")
        records = state["skills"]
        assert isinstance(records, dict)
        for identity, value in records.items():
            if not isinstance(identity, str) or not isinstance(value, dict):
                raise UpstreamError("invalid dependency ownership record")
            name, owner, raw_path = value.get("name"), value.get("owner"), value.get("path")
            if not isinstance(name, str) or not NAME.fullmatch(name):
                raise UpstreamError("invalid dependency record name")
            if owner not in {"bible", "external"} or not isinstance(raw_path, str):
                raise UpstreamError("invalid dependency ownership")
            path = Path(raw_path)
            if not path.is_absolute() or path.name != name:
                raise UpstreamError("invalid dependency record path")
            if owner == "bible" and path != self._target(name):
                raise UpstreamError("managed dependency points outside the active skill root")
            digest, revision = value.get("tree_sha256"), value.get("revision")
            if not isinstance(digest, str) or not SHA.fullmatch(digest):
                raise UpstreamError("invalid recorded skill digest")
            if not isinstance(revision, str) or not REVISION.fullmatch(revision):
                raise UpstreamError("invalid recorded source revision")
        return state

    def _state(self) -> dict[str, object]:
        _safe_directory(self.store)
        if not self.state_path.exists() and not self.state_path.is_symlink():
            return {"schema_version": 1, "skills": {}, "last_backup": None}
        return self._validate_state(_read_json(self.state_path))

    def _write_state(self, state: dict[str, object]) -> None:
        self._validate_state(state)
        _atomic_json(self.state_path, state)

    def _store_directory(self, path: Path) -> None:
        """Reject symlink ancestors inside the controlled dependency store."""
        path.relative_to(self.store)
        for parent in (path, *path.parents):
            _safe_directory(parent)
            if parent == self.store:
                break

    @contextmanager
    def _lock(self) -> Iterator[None]:
        _safe_directory(self.home)
        _safe_directory(self.store)
        self.store.mkdir(parents=True, exist_ok=True)
        lock_path = self.store / ".lock"
        if lock_path.is_symlink():
            raise UpstreamError("unsafe dependency lock file")
        with lock_path.open("a+b") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                self._recover()
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _providers(self, skill: SkillSpec, record: dict[str, object] | None) -> list[Path]:
        target = self._target(skill.name)
        found: list[Path] = []
        if target.exists() or target.is_symlink():
            found.append(target)
        for root in (self.skill_root, *self.existing_roots):
            _safe_directory(root)
            if not root.exists():
                continue
            for count, entry in enumerate(root.rglob("SKILL.md"), 1):
                if count > 2048:
                    raise UpstreamError("existing provider inventory exceeds size limit")
                if entry.parent.name == skill.name:
                    found.append(entry.parent)
        if record is not None:
            path = Path(str(record["path"]))
            if path.exists() or path.is_symlink():
                found.append(path)
        unique: dict[str, Path] = {}
        for path in found:
            # Do not resolve a symlink into another tree and falsely claim reuse.
            unique[str(path.absolute())] = path
        return list(unique.values())

    def plan(
        self, skills: list[SkillSpec], legacy_owned: dict[str, str] | None = None
    ) -> list[dict[str, object]]:
        legacy_owned = legacy_owned or {}
        names = {skill.name for skill in skills}
        if any(
            name not in names or not isinstance(digest, str) or not SHA.fullmatch(digest)
            for name, digest in legacy_owned.items()
        ):
            raise UpstreamError("invalid verified legacy ownership handoff")
        if self.journal_path.exists() or self.journal_path.is_symlink():
            return [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "status": "RECOVERY_REQUIRED",
                    "path": str(self._target(skill.name)),
                    "revision": self.catalog.sources[skill.source].revision,
                    "exposure": "unverified",
                    "reason": "interrupted dependency transaction requires recovery",
                }
                for skill in skills
            ]
        state = self._state()
        records = state["skills"]
        assert isinstance(records, dict)
        result: list[dict[str, object]] = []
        for skill in skills:
            value = records.get(skill.id)
            record = cast(dict[str, object], value) if isinstance(value, dict) else None
            candidates = self._providers(skill, record)
            source = self.catalog.sources[skill.source]
            item: dict[str, object] = {
                "id": skill.id,
                "name": skill.name,
                "status": "MISSING",
                "path": str(self._target(skill.name)),
                "owner": "bible",
                "revision": source.revision,
                "tree_sha256": skill.tree_sha256,
                "exposure": "unverified",
            }
            if len(candidates) > 1:
                target = self._target(skill.name)
                others = [path for path in candidates if path != target]
                reuse = None
                if record is None and skill.name in legacy_owned and len(others) == 1:
                    try:
                        if (
                            fingerprint_tree(target) == legacy_owned[skill.name]
                            and fingerprint_tree(others[0]) == skill.tree_sha256
                        ):
                            _validate_skill(others[0], skill)
                            reuse = others[0]
                    except (UpstreamError, OSError):
                        pass
                if reuse is not None:
                    item.update(status="MIGRATE_REUSE", owner="external", path=str(reuse))
                else:
                    item.update(status="CONFLICT", reason="multiple discovered providers")
            elif candidates:
                path = candidates[0]
                record_matches = record is not None and Path(str(record["path"])) == path
                item["path"] = str(path)
                try:
                    digest = fingerprint_tree(path)
                    if not (
                        record is None
                        and path == self._target(skill.name)
                        and digest == legacy_owned.get(skill.name)
                    ):
                        _validate_skill(path, skill)
                except (UpstreamError, OSError):
                    item.update(status="CONFLICT", reason="unsafe provider tree")
                else:
                    if (
                        record is None
                        and path == self._target(skill.name)
                        and digest == legacy_owned.get(skill.name)
                    ):
                        item.update(status="MIGRATE_OWNED", owner="bible")
                    elif record_matches and record and record["owner"] == "bible":
                        if digest != record["tree_sha256"]:
                            item.update(status="MODIFIED", reason="local changes in managed tree")
                        elif digest == skill.tree_sha256 and record["revision"] == source.revision:
                            item["status"] = "SATISFIED"
                        else:
                            item["status"] = "UPDATE_AVAILABLE"
                    elif digest == skill.tree_sha256:
                        item.update(
                            status="SATISFIED" if record_matches else "REUSE", owner="external"
                        )
                    else:
                        item.update(
                            status="CONFLICT", owner="external", reason="unowned provider differs"
                        )
            if item["owner"] == "bible" and item["status"] == "SATISFIED":
                try:
                    attribution = self._attribution_targets(source)
                except (UpstreamError, OSError):
                    item.update(status="MODIFIED", reason="unsafe or modified retained attribution")
                else:
                    if any(not target.exists() for _, target, _ in attribution):
                        item.update(
                            status="ATTRIBUTION_REQUIRED",
                            reason="reviewed source attribution is missing",
                        )
            result.append(item)
        # Original packs can reference payloads in adjacent skill directories.
        # Reusing only part of such a pack across roots would break those paths.
        for source in self.catalog.sources.values():
            if source.layout != "siblings":
                continue
            rows = [item for skill, item in zip(skills, result) if skill.source == source.id]
            if len({Path(str(item["path"])).parent for item in rows}) > 1:
                for item in rows:
                    if item["status"] not in {"CONFLICT", "MODIFIED"}:
                        item.update(
                            status="CONFLICT",
                            reason="original sibling payloads require a common provider root",
                        )
        return result

    def _record(self, skill: SkillSpec, item: dict[str, object]) -> dict[str, object]:
        source = self.catalog.sources[skill.source]
        return {
            "name": skill.name,
            "path": item["path"],
            "owner": item["owner"],
            "source_id": source.id,
            "source": source.url,
            "revision": source.revision,
            "tracking": source.tracking,
            "license": source.license,
            "license_sha256": source.license_sha256,
            "skill_roots": list(source.skill_roots),
            "notices": [
                {"path": notice.path, "sha256": notice.sha256} for notice in source.notices
            ],
            "tree_sha256": skill.tree_sha256,
        }

    def _attribution_targets(self, source: SourceSpec) -> list[tuple[str, Path, str]]:
        root = self.store / "licenses" / source.id / source.revision
        entries = [(source.license_path, "LICENSE", source.license_sha256)]
        entries.extend((notice.path, notice.path, notice.sha256) for notice in source.notices)
        result = []
        for source_path, retained_path, digest in entries:
            target = root / retained_path
            self._store_directory(target.parent)
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise UpstreamError("unsafe source attribution target")
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise UpstreamError("modified retained source attribution")
            result.append((source_path, target, digest))
        return result

    def _backup(self, names: list[str], after: dict[str, str | None]) -> tuple[str, Path]:
        identity = uuid.uuid4().hex
        root = self.store / "backups" / identity
        self._store_directory(root)
        root.mkdir(parents=True)
        state_exists = self.state_path.is_file()
        if state_exists:
            shutil.copyfile(self.state_path, root / "state.json")
        targets: dict[str, object] = {}
        for name in names:
            target = self._target(name)
            exists = target.exists()
            if after[name] is None and not exists:
                raise UpstreamError("legacy provider disappeared before retirement")
            before = fingerprint_tree(target) if exists else None
            if exists:
                shutil.copytree(target, root / name)
            targets[name] = {
                "existed": exists,
                "before_digest": before,
                "after_digest": after[name],
            }
        _atomic_json(root / "backup.json", {"state_existed": state_exists, "targets": targets})
        return identity, root

    def _backup_root(self, identity: object) -> Path:
        if not isinstance(identity, str) or not BACKUP.fullmatch(identity):
            raise UpstreamError("invalid backup identity")
        root = self.store / "backups" / identity
        self._store_directory(root)
        return root

    def _backup_digest(self, root: Path) -> str:
        metadata = _read_json(root / "backup.json")
        previous = b""
        if metadata.get("state_existed") is True:
            _read_json(root / "state.json")
            previous = (root / "state.json").read_bytes()
        return hashlib.sha256((root / "backup.json").read_bytes() + b"\0" + previous).hexdigest()

    def _displaced(self, identity: object, name: str, operation: str) -> Path:
        self._backup_root(identity)
        self._target(name)
        return self.skill_root / f".upstream-{operation}-{identity}-{name}"

    def _displace(self, target: Path, retained: Path, expected: AbstractSet[object]) -> None:
        if retained.exists() or retained.is_symlink():
            raise UpstreamError("interrupted active tree displacement requires recovery")
        os.rename(target, retained)
        try:
            if fingerprint_tree(retained) not in expected:
                raise UpstreamError("active tree changed during replacement")
        except Exception:
            if not target.exists() and not target.is_symlink():
                os.rename(retained, target)
            raise

    def _clear_displaced(self, identity: object, targets: dict[str, object]) -> None:
        # Retain displaced trees until state commit; validate again before disposal.
        for name, raw_info in targets.items():
            assert isinstance(raw_info, dict)
            info = cast(dict[str, object], raw_info)
            for operation in ("previous", "rollback"):
                retained = self._displaced(identity, name, operation)
                if retained.exists() or retained.is_symlink():
                    if fingerprint_tree(retained) not in {
                        info["before_digest"],
                        info["after_digest"],
                    }:
                        raise UpstreamError(
                            f"local changes preserved in displaced tree: {retained}"
                        )
                    shutil.rmtree(retained)

    def _restore(
        self, identity: object, expected_digest: object, validate_only: bool = False
    ) -> None:
        root = self._backup_root(identity)
        if (
            not isinstance(expected_digest, str)
            or not SHA.fullmatch(expected_digest)
            or self._backup_digest(root) != expected_digest
        ):
            raise UpstreamError("backup metadata digest mismatch")
        metadata = _read_json(root / "backup.json")
        targets = metadata.get("targets")
        if not isinstance(targets, dict) or not isinstance(metadata.get("state_existed"), bool):
            raise UpstreamError("invalid backup metadata")
        # Validate every tree before touching any active target.
        for name, info in targets.items():
            if not isinstance(name, str) or not isinstance(info, dict):
                raise UpstreamError("invalid backup target")
            target = self._target(name)
            existed, before, after = (
                info.get("existed"),
                info.get("before_digest"),
                info.get("after_digest"),
            )
            if not isinstance(existed, bool) or not (
                (isinstance(after, str) and SHA.fullmatch(after)) or (after is None and existed)
            ):
                raise UpstreamError("invalid backup digest")
            if existed:
                if not isinstance(before, str) or fingerprint_tree(root / name) != before:
                    raise UpstreamError("backup tree digest mismatch")
            if target.exists() or target.is_symlink():
                current = fingerprint_tree(target)
                if current not in {before, after}:
                    raise UpstreamError("rollback refused: active tree has local changes")
            for operation in ("previous", "rollback"):
                retained = self._displaced(identity, name, operation)
                if retained.exists() or retained.is_symlink():
                    if fingerprint_tree(retained) not in {before, after}:
                        raise UpstreamError(
                            f"local changes preserved in displaced tree: {retained}"
                        )
        previous = None
        if metadata["state_existed"]:
            previous = self._validate_state(_read_json(root / "state.json"))
        if validate_only:
            return
        targets = cast(dict[str, object], targets)
        for name, info in targets.items():
            info = cast(dict[str, object], info)
            target = self._target(name)
            expected = {info["before_digest"], info["after_digest"]}
            if target.exists() and info["existed"]:
                if fingerprint_tree(target) == info["before_digest"]:
                    continue
            if target.exists():
                self._displace(target, self._displaced(identity, name, "rollback"), expected)
            if info["existed"]:
                self.skill_root.mkdir(parents=True, exist_ok=True)
                temporary = self.skill_root / f".recover-{uuid.uuid4().hex}"
                shutil.copytree(root / name, temporary)
                try:
                    os.rename(temporary, target)
                finally:
                    if temporary.exists():
                        shutil.rmtree(temporary)
        # Recovery deliberately bypasses _write_state: that may be the failed step.
        if previous is not None:
            _atomic_json(self.state_path, previous)
        else:
            self.state_path.unlink(missing_ok=True)
        self._clear_displaced(identity, targets)

    def _recover(self) -> None:
        if self.journal_path.exists() or self.journal_path.is_symlink():
            journal = _read_json(self.journal_path)
            if journal.get("schema_version") != 1:
                raise UpstreamError("unsupported recovery journal")
            self._restore(journal.get("backup"), journal.get("backup_sha256"))
            self.journal_path.unlink()

    def recover(self) -> bool:
        """Recover a pending owned transaction before an authorized install."""
        if not self.journal_path.exists() and not self.journal_path.is_symlink():
            return False
        with self._lock():
            return True

    def ensure(
        self,
        skills: list[SkillSpec],
        dry_run: bool = False,
        upgrade: bool = False,
        legacy_owned: dict[str, str] | None = None,
    ) -> dict[str, object]:
        if not skills:
            raise UpstreamError("select at least one upstream skill")
        if dry_run:
            return {
                "status": "dry-run",
                "skills": self.plan(skills, legacy_owned=legacy_owned),
                "backup": None,
                "exposure": "unverified",
            }
        with self._lock():
            plan = self.plan(skills, legacy_owned=legacy_owned)
            refused = {"MODIFIED", "CONFLICT", "UNSUPPORTED"}
            if not upgrade:
                refused.add("UPDATE_AVAILABLE")
            conflicts = [item for item in plan if item["status"] in refused]
            if conflicts:
                names = ", ".join(f"{item['id']} ({item['status']})" for item in conflicts)
                raise UpstreamError(f"dependency installation refused: {names}")
            changes = [
                item
                for item in plan
                if item["status"] in {"MISSING", "UPDATE_AVAILABLE", "MIGRATE_OWNED"}
                or item["status"] == "MIGRATE_REUSE"
            ]
            state = self._state()
            records = state["skills"]
            assert isinstance(records, dict)
            desired = dict(records)
            for skill, item in zip(skills, plan):
                desired[skill.id] = self._record(skill, item)
            attribution_sources: dict[str, SourceSpec] = {}
            for skill, item in zip(skills, plan):
                if item["owner"] != "bible":
                    continue
                source = self.catalog.sources[skill.source]
                if any(not target.exists() for _, target, _ in self._attribution_targets(source)):
                    attribution_sources[source.id] = source
            if not changes and desired == records and not attribution_sources:
                return {"status": "ok", "skills": plan, "backup": None, "exposure": "unverified"}
            with tempfile.TemporaryDirectory(prefix=".stage-", dir=self.store) as raw:
                stage = Path(raw)
                sources = {
                    identity: stage_source(source, stage / identity)
                    for identity, source in attribution_sources.items()
                }
                staged: dict[str, Path] = {}
                for item in changes:
                    if item["status"] == "MIGRATE_REUSE":
                        continue
                    skill = self.catalog.skills[str(item["id"])]
                    source = self.catalog.sources[skill.source]
                    if source.id not in sources:
                        sources[source.id] = stage_source(source, stage / source.id)
                    tree = sources[source.id] / skill.path
                    if fingerprint_tree(tree) != skill.tree_sha256:
                        raise UpstreamError(f"staged tree digest mismatch: {skill.id}")
                    _validate_skill(tree, skill)
                    staged[skill.name] = tree
                # Recheck provider state after staging, before any active mutation.
                if self.plan(skills, legacy_owned=legacy_owned) != plan:
                    raise UpstreamError("provider state changed during staging")
                for source_id in sources:
                    source = self.catalog.sources[source_id]
                    for source_path, _, digest in self._attribution_targets(source):
                        leaf = sources[source_id] / source_path
                        if (
                            leaf.is_symlink()
                            or not leaf.is_file()
                            or hashlib.sha256(leaf.read_bytes()).hexdigest() != digest
                        ):
                            raise UpstreamError("staged source attribution digest mismatch")
                after = {
                    str(item["name"]): (
                        None if item["status"] == "MIGRATE_REUSE" else str(item["tree_sha256"])
                    )
                    for item in changes
                }
                identity, backup = self._backup(list(after), after)
                backup_digest = self._backup_digest(backup)
                if self.plan(skills, legacy_owned=legacy_owned) != plan:
                    raise UpstreamError("provider state changed during backup")
                raw_backup_targets = _read_json(backup / "backup.json")["targets"]
                assert isinstance(raw_backup_targets, dict)
                backup_targets = cast(dict[str, object], raw_backup_targets)
                new_state: dict[str, object] = {
                    "schema_version": 1,
                    "skills": desired,
                    "last_backup": identity,
                    "backup_sha256": backup_digest,
                }
                _atomic_json(
                    self.journal_path,
                    {"schema_version": 1, "backup": identity, "backup_sha256": backup_digest},
                )
                try:
                    self.skill_root.mkdir(parents=True, exist_ok=True)
                    for name, tree in staged.items():
                        target = self._target(name)
                        temporary = self.skill_root / f".upstream-{uuid.uuid4().hex}"
                        shutil.copytree(tree, temporary)
                        try:
                            raw_info = backup_targets[name]
                            assert isinstance(raw_info, dict)
                            info = cast(dict[str, object], raw_info)
                            if target.exists():
                                self._displace(
                                    target,
                                    self._displaced(identity, name, "previous"),
                                    {info["before_digest"]},
                                )
                            elif info["existed"]:
                                raise UpstreamError(
                                    "active provider disappeared during replacement"
                                )
                            os.rename(temporary, target)
                        finally:
                            if temporary.exists():
                                shutil.rmtree(temporary)
                    for item in changes:
                        if item["status"] != "MIGRATE_REUSE":
                            continue
                        name = str(item["name"])
                        raw_info = backup_targets[name]
                        assert isinstance(raw_info, dict)
                        info = cast(dict[str, object], raw_info)
                        self._displace(
                            self._target(name),
                            self._displaced(identity, name, "previous"),
                            {info["before_digest"]},
                        )
                    # Retain reviewed attribution outside unchanged active skill trees.
                    for source_id, source_root in sources.items():
                        source = self.catalog.sources[source_id]
                        for source_path, target, _ in self._attribution_targets(source):
                            target.parent.mkdir(parents=True, exist_ok=True)
                            descriptor, raw_license = tempfile.mkstemp(
                                prefix=".attribution-", dir=target.parent
                            )
                            os.close(descriptor)
                            temporary_license = Path(raw_license)
                            try:
                                shutil.copyfile(source_root / source_path, temporary_license)
                                temporary_license.chmod(0o644)
                                os.replace(temporary_license, target)
                            finally:
                                temporary_license.unlink(missing_ok=True)
                    self._write_state(new_state)
                    self._clear_displaced(identity, backup_targets)
                except Exception:
                    self._restore(identity, backup_digest)
                    self.journal_path.unlink(missing_ok=True)
                    raise
                self.journal_path.unlink()
                _atomic_json(backup / "result.json", {"skills": list(after)})
            return {
                "status": "ok",
                "skills": self.plan(skills),
                "backup": identity,
                "exposure": "unverified",
            }

    def rollback(
        self, dry_run: bool = False, *, expected_backup: str | None = None
    ) -> dict[str, object]:
        state = self._state()
        identity = state.get("last_backup")
        if expected_backup is not None and identity != expected_backup:
            raise UpstreamError("rollback refused: a different dependency transaction is current")
        digest = state.get("backup_sha256")
        if identity is None:
            raise UpstreamError("no dependency backup available")
        if dry_run:
            root = self._backup_root(identity)
            self._restore(identity, digest, validate_only=True)
            return {
                "status": "dry-run",
                "backup": identity,
                "targets": _read_json(root / "backup.json")["targets"],
            }
        with self._lock():
            state = self._state()
            identity, digest = state.get("last_backup"), state.get("backup_sha256")
            if expected_backup is not None and identity != expected_backup:
                raise UpstreamError(
                    "rollback refused: a different dependency transaction is current"
                )
            self._restore(identity, digest, validate_only=True)
            _atomic_json(
                self.journal_path,
                {"schema_version": 1, "backup": identity, "backup_sha256": digest},
            )
            self._restore(identity, digest)
            self.journal_path.unlink()
            return {"status": "ok", "backup": identity, "exposure": "unverified"}

    def check(self, skills: list[SkillSpec]) -> list[dict[str, object]]:
        plan = self.plan(skills)
        revisions: dict[str, str] = {}
        for skill, item in zip(skills, plan):
            source = self.catalog.sources[skill.source]
            item["reviewed_revision"] = source.revision
            try:
                if source.id not in revisions:
                    revisions[source.id] = tracking_revision(source)
                item["tracking_revision"] = revisions[source.id]
                item["compare_url"] = (
                    f"{source.url.removesuffix('.git')}/compare/"
                    f"{source.revision}...{revisions[source.id]}"
                )
                item["tracking_status"] = (
                    "UNCHANGED" if revisions[source.id] == source.revision else "CHANGED"
                )
            except UpstreamError as exc:
                item.update(tracking_status="ERROR", reason=str(exc))
        return plan

    def route(self, intent: str) -> dict[str, object]:
        matches = [
            skill
            for skill in self.catalog.skills.values()
            if intent in skill.intents or intent in {skill.id, skill.name}
        ]
        if len(matches) != 1:
            raise UpstreamError("route must resolve to exactly one upstream skill")
        skill = matches[0]
        # A route's dependencies must also be available, not merely its entry point.
        required: list[SkillSpec] = []
        visited: set[str] = set()

        def visit(item: SkillSpec) -> None:
            if item.id in visited:
                return
            visited.add(item.id)
            for identity in item.requires:
                visit(self.catalog.skills[identity])
            required.append(item)

        visit(skill)
        plan = self.plan(required)
        item = plan[-1]
        available = all(row["status"] in {"SATISFIED", "REUSE"} for row in plan)
        return {
            "intent": intent,
            "skill_id": skill.id,
            "skill_name": skill.name,
            "status": "available" if available else "unavailable",
            "path": item["path"],
            "revision": item["revision"],
            "exposure": "unverified",
            "dependencies": plan,
            "invocation": "explicit" if skill.user_invoked else "explicit-or-implicit",
            "required_tools": list(
                dict.fromkeys(tool for part in required for tool in part.required_tools)
            ),
        }
