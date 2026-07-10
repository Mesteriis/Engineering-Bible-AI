#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP_VERSION="0.1.0"
DEFAULT_REF_FILE="${SCRIPT_DIR}/../VERSION"
if [[ -f "$DEFAULT_REF_FILE" ]]; then
    DEFAULT_VERSION="$(tr -d '[:space:]' <"$DEFAULT_REF_FILE" | head -n 1)"
else
    DEFAULT_VERSION="$BOOTSTRAP_VERSION"
fi
if [[ -z "$DEFAULT_VERSION" ]]; then
    printf 'VERSION is empty; refusing mutable-ref fallback\n' >&2
    exit 1
fi
if [[ "$DEFAULT_VERSION" != v* ]]; then
    DEFAULT_VERSION="v${DEFAULT_VERSION}"
fi

usage() {
    local ref="${1:-$DEFAULT_VERSION}"
    cat <<EOF
Usage:
  curl -fSLo engineering-bible-install.sh https://github.com/Mesteriis/Engineering-Bible-AI/releases/download/${ref}/install.sh
  bash engineering-bible-install.sh --dry-run --diff

Options:
  --install    Install portable Codex skills and standards. This is the default.
  --dry-run    Download and validate the package, then print install actions.
  --diff       Print planned ADD/UPDATE/CONFLICT/UNCHANGED status.
  --group NAME Install an additional skill group, for example: --group wiki.
  --all        Install every skill group, including optional groups.
  --ref REF    Download an explicit immutable tag or allowed unstable ref.
  --allow-unstable  Permit a mutable/non-SemVer ref such as a branch name.
  --migrate-legacy  Adopt only byte- and mode-identical legacy managed files.
  --prompt-profile NAME  Activate full or minimal global instructions.
  --force      Overwrite changed managed files after backing them up.
  --no-overwrite  Install only missing managed files.
  --backup-only   Back up existing managed targets without copying.
  --help       Show this help.

Environment:
  ENGINEERING_BIBLE_REPO  default: Mesteriis/Engineering-Bible-AI
  ENGINEERING_BIBLE_REF   default: ${ref}
  ENGINEERING_BIBLE_ARCHIVE_URL  optional HTTPS or file:// archive override
  ENGINEERING_BIBLE_ARCHIVE_SHA256  required with a stable HTTPS archive override
  ENGINEERING_BIBLE_RELEASE_MANIFEST_URL  optional release-manifest.json override
  CODEX_HOME              passed to scripts/install-codex.sh
  AGENTS_HOME             passed to scripts/install-codex.sh
  ENGINEERING_BIBLE_BIN_DIR  passed to scripts/install-codex.sh

By default this bootstrapper installs portable standards and skills only.
Install companion CLIs separately with `be tools install` and an explicit
selector; this bootstrapper never writes Codex config.toml, auth files, .env
files, MCP credentials, hooks, or local worker runtime state.
EOF
}

installer_args=()
mode_seen=0
requested_ref=""
allow_unstable=0
while [[ $# -gt 0 ]]; do
    case "$1" in
    --install | --dry-run | --backup-only)
        installer_args+=("$1")
        mode_seen=1
        shift
        ;;
    --install-tools)
        printf '%s\n' '--install-tools is deprecated; use be tools install with an explicit selector' >&2
        exit 2
        ;;
    --diff | --all | --force | --no-overwrite | --migrate-legacy)
        installer_args+=("$1")
        shift
        ;;
    --group | --prompt-profile)
        if [[ $# -lt 2 ]]; then
            usage >&2
            exit 2
        fi
        installer_args+=("$1" "$2")
        shift 2
        ;;
    --ref)
        if [[ $# -lt 2 ]]; then
            usage >&2
            exit 2
        fi
        requested_ref="$2"
        shift 2
        ;;
    --allow-unstable)
        allow_unstable=1
        shift
        ;;
    --help | -h)
        usage
        exit 0
        ;;
    *)
        usage >&2
        exit 2
        ;;
    esac
done

if [[ "$mode_seen" -eq 0 ]]; then
    installer_args=(--install "${installer_args[@]}")
fi

repo_slug="${ENGINEERING_BIBLE_REPO:-Mesteriis/Engineering-Bible-AI}"
ref="${requested_ref:-${ENGINEERING_BIBLE_REF:-$DEFAULT_VERSION}}"
if [[ ! "$repo_slug" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
    printf 'invalid ENGINEERING_BIBLE_REPO: %s\n' "$repo_slug" >&2
    exit 2
fi
if [[ ! "$ref" =~ ^[A-Za-z0-9._/-]+$ || "$ref" == *".."* || "$ref" == /* ]]; then
    printf 'invalid Engineering Bible ref: %s\n' "$ref" >&2
    exit 2
fi
stable_ref=0
if [[ "$ref" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?$ ]]; then
    stable_ref=1
elif [[ "$allow_unstable" -ne 1 ]]; then
    printf 'mutable ref requires --allow-unstable: %s\n' "$ref" >&2
    exit 2
fi

require_cmd() {
    local command_name="$1"
    if ! command -v "$command_name" >/dev/null 2>&1; then
        printf 'required command not found: %s\n' "$command_name" >&2
        exit 1
    fi
}

find_local_repo() {
    if [[ "${ENGINEERING_BIBLE_FORCE_REMOTE:-0}" == "1" ]]; then
        return 1
    fi
    local script_path="${BASH_SOURCE[0]:-}"
    if [[ -n "$script_path" && -f "$script_path" ]]; then
        local candidate
        candidate="$(cd "$(dirname "$script_path")/.." && pwd)"
        if [[ -f "$candidate/scripts/install-codex.sh" && -d "$candidate/skills" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    fi
    return 1
}

download_repo() {
    require_cmd mktemp

    local tmp_dir archive_url expected_sha release_manifest_url output
    tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/engineering-bible-ai.XXXXXX")"
    archive_url="${ENGINEERING_BIBLE_ARCHIVE_URL:-}"
    expected_sha="${ENGINEERING_BIBLE_ARCHIVE_SHA256:-}"
    release_manifest_url="${ENGINEERING_BIBLE_RELEASE_MANIFEST_URL:-}"
    if ! output="$(
        "$python_bin" - "$repo_slug" "$ref" "$tmp_dir" "$archive_url" "$expected_sha" "$stable_ref" "$release_manifest_url" <<'PY'
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
from urllib.parse import quote, urljoin, urlparse
from urllib.request import urlopen


MAX_DOWNLOAD = 64 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_MEMBERS = 20_000


def fail(message: str) -> "NoReturn":
    raise RuntimeError(message)


def main() -> str:
    (
        repo_slug,
        ref,
        raw_tmp,
        override_url,
        expected_sha,
        stable_raw,
        release_manifest_override,
    ) = sys.argv[1:]
    stable = stable_raw == "1"
    tmp = Path(raw_tmp).resolve()
    archive_path = tmp / "source.tar.gz"
    extract_root = tmp / "extracted"
    extract_root.mkdir(mode=0o700)

    release_artifact_size: int | None = None
    if override_url:
        url = override_url
    elif stable:
        manifest_url = release_manifest_override or (
            f"https://github.com/{repo_slug}/releases/download/"
            f"{quote(ref, safe='')}/release-manifest.json"
        )
        manifest_scheme = urlparse(manifest_url).scheme
        if manifest_scheme not in {"https", "file"}:
            fail("release manifest URL must use https or file")
        with urlopen(manifest_url, timeout=30) as response:
            raw_manifest = response.read(1024 * 1024 + 1)
        if len(raw_manifest) > 1024 * 1024:
            fail("release manifest exceeds size limit")
        try:
            release_manifest = json.loads(raw_manifest)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            fail(f"invalid release manifest: {exc}")
        if not isinstance(release_manifest, dict) or release_manifest.get("schema_version") != 1:
            fail("unsupported release manifest schema")
        version = release_manifest.get("version")
        if not isinstance(version, str) or release_manifest.get("tag") != ref or f"v{version}" != ref:
            fail("release manifest version/tag does not match requested ref")
        artifact_name = f"engineering-bible-ai-{version}.tar.gz"
        artifacts = release_manifest.get("artifacts")
        artifact = artifacts.get(artifact_name) if isinstance(artifacts, dict) else None
        if not isinstance(artifact, dict):
            fail(f"release manifest does not describe {artifact_name}")
        manifest_sha = artifact.get("sha256")
        release_artifact_size = artifact.get("size")
        if not isinstance(manifest_sha, str):
            fail("release manifest archive checksum is missing")
        if expected_sha and expected_sha.lower() != manifest_sha.lower():
            fail("explicit archive checksum disagrees with release manifest")
        expected_sha = manifest_sha
        if not isinstance(release_artifact_size, int) or release_artifact_size < 1:
            fail("release manifest archive size is invalid")
        url = urljoin(manifest_url, quote(artifact_name, safe=""))
    else:
        url = f"https://github.com/{repo_slug}/archive/{quote(ref, safe='/')}.tar.gz"
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "file"}:
        fail("archive URL must use https or file")
    if parsed.scheme == "https" and stable and override_url and not expected_sha:
        fail("ENGINEERING_BIBLE_ARCHIVE_SHA256 is required for a stable HTTPS archive override")
    normalized_sha = expected_sha.lower()
    if normalized_sha and (
        len(normalized_sha) != 64
        or any(character not in "0123456789abcdef" for character in normalized_sha)
    ):
        fail("ENGINEERING_BIBLE_ARCHIVE_SHA256 must be 64 hexadecimal characters")

    digest = hashlib.sha256()
    downloaded = 0
    with urlopen(url, timeout=30) as response, archive_path.open("xb") as destination:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            downloaded += len(chunk)
            if downloaded > MAX_DOWNLOAD:
                fail("archive exceeds compressed size limit")
            digest.update(chunk)
            destination.write(chunk)
    actual_sha = digest.hexdigest()
    if release_artifact_size is not None and downloaded != release_artifact_size:
        fail(
            f"archive size mismatch: expected {release_artifact_size}, got {downloaded}"
        )
    if normalized_sha and actual_sha != normalized_sha:
        fail(f"archive checksum mismatch: expected {normalized_sha}, got {actual_sha}")
    (tmp / "archive.sha256").write_text(actual_sha + "\n", encoding="ascii")

    expanded = 0
    seen_files: set[str] = set()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        if len(members) > MAX_MEMBERS:
            fail("archive contains too many entries")
        for member in members:
            pure = PurePosixPath(member.name)
            canonical = pure.as_posix()
            if (
                not member.name
                or pure.is_absolute()
                or ".." in pure.parts
                or member.name.rstrip("/") != canonical
            ):
                fail(f"unsafe archive path: {member.name!r}")
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                fail(f"unsupported archive entry type: {member.name!r}")
            if not member.isdir() and not member.isfile():
                fail(f"unsupported archive entry type: {member.name!r}")

            destination = (extract_root / canonical).resolve(strict=False)
            try:
                destination.relative_to(extract_root)
            except ValueError:
                fail(f"archive path escapes extraction root: {member.name!r}")
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                destination.chmod(0o755)
                continue

            expanded += member.size
            if expanded > MAX_EXPANDED:
                fail("archive exceeds expanded size limit")
            if canonical in seen_files or destination.exists():
                fail(f"duplicate archive file: {member.name!r}")
            seen_files.add(canonical)
            source = archive.extractfile(member)
            if source is None:
                fail(f"unable to read archive file: {member.name!r}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source, destination.open("xb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
            destination.chmod(0o755 if member.mode & 0o111 else 0o644)

    roots = [candidate for candidate in extract_root.iterdir() if candidate.is_dir()]
    if len(roots) != 1:
        fail("archive must contain exactly one top-level directory")
    root = roots[0]
    if not (root / "scripts" / "install-codex.sh").is_file() or not (root / "skills").is_dir():
        fail("downloaded archive does not contain the expected installer")
    version_path = root / "VERSION"
    if not version_path.is_file():
        fail("downloaded archive has no VERSION")
    version = version_path.read_text(encoding="utf-8").strip().lstrip("v")
    if stable and ref != f"v{version}":
        fail(f"archive VERSION {version!r} does not match requested ref {ref!r}")
    return str(root)


try:
    print(main())
except Exception as exc:
    raise SystemExit(f"bootstrap archive error: {exc}") from exc
PY
    )"; then
        "$python_bin" - "$tmp_dir" <<'PY'
import shutil
import sys

shutil.rmtree(sys.argv[1], ignore_errors=True)
PY
        return 1
    fi
    printf '%s\n' "$output"
}

run_validation() {
    local repo_root="$1"
    bash "$repo_root/scripts/validate-repo-tree.sh" "$repo_root"
    "$python_bin" "$repo_root/scripts/validate-skill-frontmatter.py" "$repo_root/skills"
    "$python_bin" "$repo_root/scripts/validate-router-cases.py" --root "$repo_root" --fixtures

    if command -v rg >/dev/null 2>&1; then
        bash "$repo_root/scripts/secret-sanity.sh" "$repo_root"
    else
        printf 'WARN: ripgrep not found; skipping secret-sanity scan in bootstrap validation.\n' >&2
    fi
}

python_bin="${ENGINEERING_BIBLE_PYTHON:-}"
if [[ -z "$python_bin" ]]; then
    if command -v python3.11 >/dev/null 2>&1; then
        python_bin=python3.11
    else
        python_bin=python3
    fi
fi

require_cmd bash
require_cmd "$python_bin"
"$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else "Python 3.11+ is required")'

cleanup_dir=""
if repo_root="$(find_local_repo)"; then
    :
else
    repo_root="$(download_repo)"
    cleanup_dir="$(dirname "$(dirname "$repo_root")")"
fi

cleanup() {
    if [[ -n "$cleanup_dir" && -d "$cleanup_dir" ]]; then
        "$python_bin" - "$cleanup_dir" <<'PY'
import shutil
import sys

shutil.rmtree(sys.argv[1], ignore_errors=True)
PY
    fi
}
trap cleanup EXIT

printf 'Engineering Bible AI source: %s\n' "$repo_root"
target_version="$(tr -d '[:space:]' <"$repo_root/VERSION")"
target_digest="working-tree"
if [[ -n "$cleanup_dir" && -f "$cleanup_dir/archive.sha256" ]]; then
    target_digest="sha256:$(tr -d '[:space:]' <"$cleanup_dir/archive.sha256")"
fi
printf 'Target version: %s\n' "$target_version"
printf 'Target digest: %s\n' "$target_digest"
printf 'Installer args:'
printf ' %q' "${installer_args[@]}"
printf '\n'

run_validation "$repo_root"
if [[ -n "$cleanup_dir" ]]; then
    export ENGINEERING_BIBLE_SOURCE_KIND="archive"
    export ENGINEERING_BIBLE_SOURCE_LOCATION="$repo_slug"
    export ENGINEERING_BIBLE_SOURCE_REF="$ref"
    if [[ "$target_digest" == sha256:* ]]; then
        export ENGINEERING_BIBLE_SOURCE_DIGEST="$target_digest"
    fi
fi
bash "$repo_root/scripts/install-codex.sh" "${installer_args[@]}"
