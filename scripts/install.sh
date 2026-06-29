#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REF_FILE="${SCRIPT_DIR}/../VERSION"
if [[ -f "$DEFAULT_REF_FILE" ]]; then
    DEFAULT_VERSION="$(tr -d '[:space:]' <"$DEFAULT_REF_FILE" | head -n 1)"
else
    DEFAULT_VERSION="main"
fi
if [[ -z "$DEFAULT_VERSION" ]]; then
    DEFAULT_VERSION="main"
fi
if [[ "$DEFAULT_VERSION" =~ ^[0-9]+(\.[0-9]+)*$ ]]; then
    DEFAULT_VERSION="main"
fi
if [[ "$DEFAULT_VERSION" != v* && "$DEFAULT_VERSION" != "main" && "$DEFAULT_VERSION" != "master" ]]; then
    DEFAULT_VERSION="v${DEFAULT_VERSION}"
fi

usage() {
    local ref="${1:-$DEFAULT_VERSION}"
    cat <<EOF
Usage:
  curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/${ref}/scripts/install.sh | bash -s
  curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/${ref}/scripts/install.sh | bash -s -- --dry-run --diff

Options:
  --install    Install portable Codex skills and standards. This is the default.
  --dry-run    Download and validate the package, then print install actions.
  --diff       Print planned ADD/UPDATE/CONFLICT/UNCHANGED status.
  --group NAME Install an additional skill group, for example: --group wiki.
  --all        Install every skill group, including optional groups.
  --force      Overwrite changed managed files after backing them up.
  --no-overwrite  Install only missing managed files.
  --backup-only   Back up existing managed targets without copying.
  --help       Show this help.

Environment:
  ENGINEERING_BIBLE_REPO  default: Mesteriis/Engineering-Bible-AI
  ENGINEERING_BIBLE_REF   default: ${ref}
  CODEX_HOME              passed to scripts/install-codex.sh
  AGENTS_HOME             passed to scripts/install-codex.sh
  ENGINEERING_BIBLE_BIN_DIR  passed to scripts/install-codex.sh

This bootstrapper installs portable standards and skills only. It does not
write Codex config.toml, auth files, .env files, MCP credentials, or local
worker runtime state.
EOF
}

installer_args=()
mode_seen=0
while [[ $# -gt 0 ]]; do
    case "$1" in
    --install | --dry-run | --backup-only)
        installer_args+=("$1")
        mode_seen=1
        shift
        ;;
    --diff | --all | --force | --no-overwrite)
        installer_args+=("$1")
        shift
        ;;
    --group)
        if [[ $# -lt 2 ]]; then
            usage >&2
            exit 2
        fi
        installer_args+=("$1" "$2")
        shift 2
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
ref="${ENGINEERING_BIBLE_REF:-$DEFAULT_VERSION}"

require_cmd() {
    local command_name="$1"
    if ! command -v "$command_name" >/dev/null 2>&1; then
        printf 'required command not found: %s\n' "$command_name" >&2
        exit 1
    fi
}

find_local_repo() {
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
    require_cmd curl
    require_cmd tar
    require_cmd mktemp

    local tmp_dir archive repo_root
    tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/engineering-bible-ai.XXXXXX")"
    archive="$tmp_dir/source.tar.gz"
    curl -fsSL "https://github.com/${repo_slug}/archive/${ref}.tar.gz" -o "$archive"
    tar -xzf "$archive" -C "$tmp_dir"
    repo_root="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    if [[ -z "$repo_root" || ! -f "$repo_root/scripts/install-codex.sh" ]]; then
        printf 'downloaded archive does not contain expected installer\n' >&2
        exit 1
    fi

    printf '%s\n' "$repo_root"
}

run_validation() {
    local repo_root="$1"
    bash "$repo_root/scripts/validate-repo-tree.sh" "$repo_root"
    python3 "$repo_root/scripts/validate-skill-frontmatter.py" "$repo_root/skills"
    python3 "$repo_root/scripts/validate-router-cases.py" --root "$repo_root" --static

    if command -v rg >/dev/null 2>&1; then
        bash "$repo_root/scripts/secret-sanity.sh" "$repo_root"
    else
        printf 'WARN: ripgrep not found; skipping secret-sanity scan in bootstrap validation.\n' >&2
    fi
}

require_cmd bash
require_cmd python3

cleanup_dir=""
if repo_root="$(find_local_repo)"; then
    :
else
    repo_root="$(download_repo)"
    cleanup_dir="$(dirname "$repo_root")"
fi

cleanup() {
    if [[ -n "$cleanup_dir" && -d "$cleanup_dir" ]]; then
        python3 - "$cleanup_dir" <<'PY'
import shutil
import sys

shutil.rmtree(sys.argv[1], ignore_errors=True)
PY
    fi
}
trap cleanup EXIT

printf 'Engineering Bible AI source: %s\n' "$repo_root"
printf 'Installer args:'
printf ' %q' "${installer_args[@]}"
printf '\n'

run_validation "$repo_root"
bash "$repo_root/scripts/install-codex.sh" "${installer_args[@]}"
