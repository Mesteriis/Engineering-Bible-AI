"""Download reviewed sources without executing their content or importing setup."""

from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tarfile
import tempfile
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener
from urllib.parse import urlsplit

try:
    from .upstream_catalog import (
        SourceSpec,
        UpstreamError,
        source_repository,
        unsafe_runtime_path,
        validate_source,
    )
except ImportError:
    from upstream_catalog import (
        SourceSpec,
        UpstreamError,
        source_repository,
        unsafe_runtime_path,
        validate_source,
    )


MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_EXTRACTED_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 20000
MAX_FILE_BYTES = 16 * 1024 * 1024


class RestrictedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "codeload.github.com"
            or parsed.query
            or parsed.fragment
        ):
            raise UpstreamError("upstream archive redirected outside the public source host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def urlopen(request: Request, *, timeout: int):
    """An explicit transport seam keeps fixtures credential-free and networkless."""
    return build_opener(HTTPSHandler(), RestrictedRedirect()).open(request, timeout=timeout)


def fingerprint_tree(root: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise UpstreamError("skill tree must be a regular directory")
    digest = hashlib.sha256()
    try:
        paths = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        for path in paths:
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or unsafe_runtime_path(PurePosixPath(relative)):
                raise UpstreamError("skill tree contains a symlink or unsafe runtime file")
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode) or mode & (stat.S_ISUID | stat.S_ISGID):
                raise UpstreamError("skill tree contains a special file or privileged mode")
            digest.update(relative.encode("utf-8") + b"\0")
            digest.update(oct(stat.S_IMODE(mode)).encode() + b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode() + b"\n")
    except OSError as exc:
        raise UpstreamError("cannot read skill tree") from exc
    return digest.hexdigest()


def archive_path(name: str, prefix: str) -> PurePosixPath:
    # Tar directory names can end in '/', but internal empty components are unsafe.
    clean = name[:-1] if name.endswith("/") else name
    parts = clean.split("/")
    if (
        "\\" in clean
        or any(ord(char) < 32 for char in clean)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise UpstreamError("unsafe path in upstream archive")
    path = PurePosixPath(clean)
    if path.is_absolute() or parts[0] != prefix:
        raise UpstreamError("upstream archive path or revision prefix mismatch")
    return PurePosixPath(*parts[1:])


def stage_source(source: SourceSpec, destination: Path) -> Path:
    """Return declared original skill trees and reviewed source attribution only.

    Repository instructions, packaging, setup and root aliases are not part of
    the skill payload. Validate paths and size limits globally; reject archive
    links and special files inside the extracted license/skills scope. Normalize
    regular files to Git's 0644/0755 modes, preserving author executable intent
    without retaining the archive transport's group-write permission bits.
    """
    validate_source(source)
    if destination.exists() or destination.is_symlink():
        raise UpstreamError("source staging destination already exists")
    owner, repository = source_repository(source.url)
    prefix = repository + "-" + source.revision
    request = Request(
        f"https://codeload.github.com/{owner}/{repository}/tar.gz/{source.revision}",
        headers={"User-Agent": "Engineering-Bible-AI", "Accept": "application/gzip"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read(MAX_ARCHIVE_BYTES + 1)
        if len(data) > MAX_ARCHIVE_BYTES:
            raise UpstreamError("upstream archive exceeds download limit")
    except UpstreamError:
        raise
    except OSError as exc:
        raise UpstreamError("cannot download reviewed public upstream archive") from exc

    staging: Path | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".upstream-stage-", dir=destination.parent))
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            seen: set[str] = set()
            members: list[tuple[tarfile.TarInfo, PurePosixPath]] = []
            total = 0
            for index, member in enumerate(archive, 1):
                if index > MAX_MEMBERS:
                    raise UpstreamError("upstream archive exceeds member limit")
                relative = archive_path(member.name, prefix)
                if member.name.rstrip("/") in seen:
                    raise UpstreamError("duplicate path in upstream archive")
                seen.add(member.name.rstrip("/"))
                if member.size < 0 or member.size > MAX_FILE_BYTES:
                    raise UpstreamError("upstream archive exceeds file limit")
                total += member.size
                if total > MAX_EXTRACTED_BYTES:
                    raise UpstreamError("upstream archive exceeds expanded size limit")
                relative_name = relative.as_posix()
                in_scope = relative_name in {
                    source.license_path,
                    *(notice.path for notice in source.notices),
                } or any(
                    relative_name == root or relative_name.startswith(root + "/")
                    for root in source.skill_roots
                )
                if not in_scope:
                    continue
                if not (member.isfile() or member.isdir()) or member.mode & (
                    stat.S_ISUID | stat.S_ISGID
                ):
                    raise UpstreamError(
                        "link, special file or privileged mode in upstream skill payload"
                    )
                if unsafe_runtime_path(relative):
                    raise UpstreamError("unsafe runtime file in upstream skill payload")
                members.append((member, relative))
            # All archive boundaries have passed before any payload is written.
            directories: list[tuple[Path, int]] = []
            for member, relative in members:
                path = staging / relative.as_posix()
                if member.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                    directories.append((path, member.mode))
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                extracted_file = archive.extractfile(member)
                if extracted_file is None:
                    raise UpstreamError("missing regular file body in upstream archive")
                with extracted_file as input_file:
                    with path.open("xb") as output_file:
                        shutil.copyfileobj(input_file, output_file)
                path.chmod(0o755 if member.mode & 0o111 else 0o644)
            license_file = staging / source.license_path
            if (
                not license_file.is_file()
                or hashlib.sha256(license_file.read_bytes()).hexdigest() != source.license_sha256
            ):
                raise UpstreamError("upstream license digest mismatch or missing license")
            for notice in source.notices:
                notice_file = staging / notice.path
                if (
                    not notice_file.is_file()
                    or hashlib.sha256(notice_file.read_bytes()).hexdigest() != notice.sha256
                ):
                    raise UpstreamError("upstream notice digest mismatch or missing notice")
            for path, mode in reversed(directories):
                path.chmod(mode)
        os.replace(staging, destination)
        staging = None
        return destination
    except UpstreamError:
        raise
    except (OSError, ValueError, tarfile.TarError) as exc:
        raise UpstreamError("invalid or unreadable reviewed upstream archive") from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
