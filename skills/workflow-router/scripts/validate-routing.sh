#!/usr/bin/env bash
set -euo pipefail

required_skills=(
  workflow-router
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

skill_roots=(
  "$HOME/.agents/skills"
  "$HOME/.codex/skills"
  "$HOME/.claude/skills"
  "$HOME/.config/opencode/skills"
  "$HOME/.gemini/skills"
)

instruction_files=(
  "$HOME/.codex/AGENTS.md"
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.config/opencode/AGENTS.md"
  "$HOME/.gemini/GEMINI.md"
)

quick_validate="$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

for instruction_file in "${instruction_files[@]}"; do
  test -f "$instruction_file" || fail "missing instruction file: $instruction_file"
  grep -q 'WORKFLOW:ROUTER:BEGIN' "$instruction_file" || fail "missing WORKFLOW router block in $instruction_file"
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
  managed_skill_files+=("$HOME/.agents/skills/$skill/SKILL.md")
done

if grep -n -E 'TODO:|Structuring This Skill|\[TODO' "${managed_skill_files[@]}"; then
  fail "template TODO text found in managed workflow skills"
fi

test -f "$quick_validate" || fail "missing quick_validate.py"
for skill in "${required_skills[@]}"; do
  python3 "$quick_validate" "$HOME/.codex/skills/$skill" >/dev/null
done

prompt_input="$(codex debug prompt-input '$workflow-router smoke' 2>/dev/null || true)"
test -n "$prompt_input" || fail "codex prompt-input smoke returned no output"
for skill in workflow-router security-router review-router security-diff-review ui-concept-first playwright-visual-qa; do
  printf '%s' "$prompt_input" | grep -q "$skill" || fail "Codex prompt-input missing $skill"
done

printf 'OK: workflow routing healthcheck passed\n'
