#!/usr/bin/env bash
set -euo pipefail

mode="--codex-only"
case "${1:---codex-only}" in
  --codex-only)
    mode="--codex-only"
    ;;
  --all-agents)
    mode="--all-agents"
    ;;
  --help | -h)
    cat <<'USAGE'
Usage:
  validate-routing.sh [--codex-only]
  validate-routing.sh --all-agents

Default --codex-only validates ~/.codex/AGENTS.md, ~/.codex/skills, and
~/.agents/skills. --all-agents additionally validates optional Claude,
OpenCode, and Gemini roots when their instruction files or skill roots exist.
USAGE
    exit 0
    ;;
  *)
    printf 'unknown option: %s\n' "$1" >&2
    exit 2
    ;;
esac

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

read_required_skills() {
  local registry_script="$HOME/.codex/scripts/registry.py"
  if [[ -f "$registry_script" && -f "$HOME/.codex/skills/registry.yml" ]]; then
    python3 "$registry_script" --root "$HOME/.codex" skills
    return
  fi

  printf '%s\n' \
    workflow-router \
    engineering-standards \
    review-router \
    security-router \
    ui-router \
    ui-research \
    ui-build \
    ui-figma \
    ui-qa
}

required_skills=()
while IFS= read -r skill; do
  required_skills+=("$skill")
done < <(read_required_skills)

skill_roots=(
  "$HOME/.codex/skills"
  "$HOME/.agents/skills"
)

instruction_files=(
  "$HOME/.codex/AGENTS.md"
)

if [[ "$mode" == "--all-agents" ]]; then
  optional_skill_roots=(
    "$HOME/.claude/skills"
    "$HOME/.config/opencode/skills"
    "$HOME/.gemini/skills"
  )
  optional_instruction_files=(
    "$HOME/.claude/CLAUDE.md"
    "$HOME/.config/opencode/AGENTS.md"
    "$HOME/.gemini/GEMINI.md"
  )
  for root in "${optional_skill_roots[@]}"; do
    [[ -d "$root" ]] && skill_roots+=("$root")
  done
  for instruction_file in "${optional_instruction_files[@]}"; do
    [[ -f "$instruction_file" ]] && instruction_files+=("$instruction_file")
  done
fi

for instruction_file in "${instruction_files[@]}"; do
  test -f "$instruction_file" || fail "missing instruction file: $instruction_file"
  grep -Eq 'WORKFLOW:ROUTER:BEGIN|## Mandatory Routing' "$instruction_file" || fail "missing workflow router block in $instruction_file"
  grep -q 'workflow-router' "$instruction_file" || fail "missing workflow-router mention in $instruction_file"
done

for root in "${skill_roots[@]}"; do
  test -d "$root" || fail "missing skill root: $root"
  for skill in "${required_skills[@]}"; do
    test -f "$root/$skill/SKILL.md" || fail "missing $root/$skill/SKILL.md"
  done
done

managed_skill_files=()
for skill in "${required_skills[@]}"; do
  managed_skill_files+=("$HOME/.codex/skills/$skill/SKILL.md")
done

if grep -n -E 'TODO:|Structuring This Skill|\[TODO' "${managed_skill_files[@]}"; then
  fail "template TODO text found in managed workflow skills"
fi

quick_validate="$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$quick_validate" ]]; then
  for skill in "${required_skills[@]}"; do
    python3 "$quick_validate" "$HOME/.codex/skills/$skill" >/dev/null
  done
else
  warn "quick_validate.py not found; skipped skill structure smoke"
fi

if command -v codex >/dev/null 2>&1; then
  prompt_input="$(codex debug prompt-input '$workflow-router smoke' 2>/dev/null || true)"
  if [[ -n "$prompt_input" ]]; then
    for skill in workflow-router security-router review-router ui-router; do
      printf '%s' "$prompt_input" | grep -q "$skill" || fail "Codex prompt-input missing $skill"
    done
  else
    warn "codex prompt-input smoke returned no output; skipped prompt visibility check"
  fi
else
  warn "codex CLI not found; skipped prompt visibility check"
fi

printf 'OK: workflow routing healthcheck passed\n'
