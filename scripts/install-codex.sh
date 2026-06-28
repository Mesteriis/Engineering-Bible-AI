#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/install-codex.sh --dry-run
  scripts/install-codex.sh --install

Environment:
  CODEX_HOME    default: $HOME/.codex
  AGENTS_HOME   default: $HOME/.agents

The installer copies portable standards and skills only. It does not edit
CODEX_HOME/config.toml, auth files, .env files, MCP credentials, or runtime
worker state.
USAGE
}

mode="${1:-}"
if [[ "$mode" != "--dry-run" && "$mode" != "--install" ]]; then
  usage
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
codex_home="${CODEX_HOME:-$HOME/.codex}"
agents_home="${AGENTS_HOME:-$HOME/.agents}"
agent_skill_root="$agents_home/skills"
timestamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$codex_home/backups/engineering-bible-ai-$timestamp"

skills=(
  workflow-router
  engineering-standards
  core-engineering
  code-quality
  architecture-principles
  testing-tdd
  debugging
  code-review
  security
  performance
  refactoring
  documentation
  python
  typescript
  rust
  go
  c-cpp
  homeassistant
  esphome
  esp32
  code-wiki-ru
  security-router
  review-router
  ui-router
  ui-research
  ui-build
  ui-figma
  ui-qa
  multi-agent-pr-review
  architecture-map
  migration-planner
  subagent-result-merge
  agent-retrospective
  agents-md-retrospective
  security-diff-review
  fix-security-finding
  threat-model
  dependency-advisory-audit
  secrets-and-config-review
  authz-boundary-review
  deserialization-parser-review
  supply-chain-review
  ui-concept-first
  design-system-extractor
  figma-to-code
  code-to-figma
  playwright-visual-qa
  responsive-breakpoint-check
  accessibility-ui-review
)

run() {
  if [[ "$mode" == "--dry-run" ]]; then
    printf '[dry-run] %q' "$1"
    shift
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
  else
    "$@"
  fi
}

backup_path() {
  local source_path="$1"
  local relative_path="$2"
  if [[ -e "$source_path" ]]; then
    run mkdir -p "$backup_dir/$(dirname "$relative_path")"
    run cp -a "$source_path" "$backup_dir/$relative_path"
  fi
}

copy_dir() {
  local source_dir="$1"
  local target_dir="$2"
  run mkdir -p "$target_dir"
  run rsync -a "$source_dir/" "$target_dir/"
}

copy_skill() {
  local skill="$1"
  local source_dir="$repo_root/skills/$skill"
  [[ -d "$source_dir" ]] || {
    printf 'missing skill: %s\n' "$skill" >&2
    exit 1
  }

  backup_path "$codex_home/skills/$skill" "skills/$skill"
  backup_path "$agent_skill_root/$skill" "agents-skills/$skill"
  copy_dir "$source_dir" "$codex_home/skills/$skill"
  copy_dir "$source_dir" "$agent_skill_root/$skill"
}

printf 'Repo: %s\n' "$repo_root"
printf 'Codex home: %s\n' "$codex_home"
printf 'Agents home: %s\n' "$agents_home"
printf 'Mode: %s\n' "$mode"
printf 'Backup: %s\n' "$backup_dir"

backup_path "$codex_home/AGENTS.md" "AGENTS.md"
run mkdir -p "$codex_home" "$agent_skill_root"
run cp -a "$repo_root/AGENTS.md" "$codex_home/AGENTS.md"

backup_path "$codex_home/engineering" "engineering"
backup_path "$codex_home/reference" "reference"
backup_path "$codex_home/templates" "templates"
backup_path "$codex_home/scripts" "scripts"
backup_path "$codex_home/tests" "tests"

copy_dir "$repo_root/engineering" "$codex_home/engineering"
copy_dir "$repo_root/reference" "$codex_home/reference"
copy_dir "$repo_root/templates" "$codex_home/templates"
copy_dir "$repo_root/scripts" "$codex_home/scripts"
copy_dir "$repo_root/tests" "$codex_home/tests"

for skill in "${skills[@]}"; do
  copy_skill "$skill"
done

run chmod +x "$codex_home/scripts/validate-skill-tree.sh"
run chmod +x "$codex_home/scripts/check-file-size.py"
run chmod +x "$codex_home/scripts/validate-skill-frontmatter.py"
run chmod +x "$codex_home/scripts/install.sh"
run chmod +x "$codex_home/scripts/install-codex.sh"
run chmod +x "$codex_home/scripts/secret-sanity.sh"

printf 'Done. Restart or open a new agent session to refresh prompt-visible skills.\n'
