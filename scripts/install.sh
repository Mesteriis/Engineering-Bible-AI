#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh | bash -s
  curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh | bash -s -- --dry-run

Options:
  --install    Install portable Codex skills and standards. This is the default.
  --dry-run    Download and validate the package, then print install actions.
  --help       Show this help.

Environment:
  ENGINEERING_BIBLE_REPO  default: Mesteriis/Engineering-Bible-AI
  ENGINEERING_BIBLE_REF   default: main
  CODEX_HOME              passed to scripts/install-codex.sh
  AGENTS_HOME             passed to scripts/install-codex.sh
  ENGINEERING_BIBLE_BIN_DIR  passed to scripts/install-codex.sh

This bootstrapper installs portable standards and skills only. It does not
write Codex config.toml, auth files, .env files, MCP credentials, or local
worker runtime state.
USAGE
}

mode="${1:---install}"
case "$mode" in
  --install | --dry-run)
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

repo_slug="${ENGINEERING_BIBLE_REPO:-Mesteriis/Engineering-Bible-AI}"
ref="${ENGINEERING_BIBLE_REF:-main}"

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
  curl -fsSL "https://github.com/${repo_slug}/archive/refs/heads/${ref}.tar.gz" -o "$archive"
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
  bash "$repo_root/scripts/validate-skill-tree.sh" "$repo_root"
  python3 "$repo_root/scripts/validate-skill-frontmatter.py" "$repo_root/skills"

  if command -v rg >/dev/null 2>&1; then
    bash "$repo_root/scripts/secret-sanity.sh" "$repo_root"
  else
    printf 'WARN: ripgrep not found; skipping secret-sanity scan in bootstrap validation.\n' >&2
  fi
}

require_cmd bash
require_cmd python3
require_cmd rsync

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
printf 'Mode: %s\n' "$mode"

run_validation "$repo_root"
bash "$repo_root/scripts/install-codex.sh" "$mode"
