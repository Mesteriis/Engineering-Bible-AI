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

Default --codex-only validates ~/.codex/AGENTS.md and ~/.codex/skills. It also
checks that managed Engineering Bible skills are not duplicated in
~/.agents/skills. --all-agents additionally validates optional Claude, OpenCode,
and Gemini roots when their instruction files or skill roots exist.
CODEX_HOME, AGENTS_HOME and ENGINEERING_BIBLE_HOME may select another installation.
Author files are checked against the installed profile; host exposure is SKIP.
USAGE
    exit 0
    ;;
*)
    printf 'unknown option: %s\n' "$1" >&2
    exit 2
    ;;
esac

routing_codex_home="${CODEX_HOME:-$HOME/.codex}"
routing_agents_home="${AGENTS_HOME:-$HOME/.agents}"
routing_be_home="${ENGINEERING_BIBLE_HOME:-$routing_codex_home/engineering-bible}"
routing_package_root="$routing_be_home/current"
routing_python="${ENGINEERING_BIBLE_PYTHON:-python3}"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

warn() {
    printf 'WARN: %s\n' "$*" >&2
}

read_required_skills() {
    local registry_script="$routing_package_root/scripts/registry.py"
    if [[ -f "$registry_script" && -f "$routing_package_root/skills/registry.yml" ]]; then
        "$routing_python" "$registry_script" --root "$routing_package_root" skills
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

read_registered_skills() {
    local registry_script="$routing_package_root/scripts/registry.py"
    if [[ -f "$registry_script" && -f "$routing_package_root/skills/registry.yml" ]]; then
        "$routing_python" "$registry_script" --root "$routing_package_root" skills --all
        return
    fi

    read_required_skills
}

required_skills=()
while IFS= read -r skill; do
    required_skills+=("$skill")
done < <(read_required_skills)

registered_skills=()
while IFS= read -r skill; do
    registered_skills+=("$skill")
done < <(read_registered_skills)

skill_roots=(
    "$routing_codex_home/skills"
)

instruction_files=(
    "$routing_codex_home/AGENTS.md"
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
    grep -Eq \
        'WORKFLOW:ROUTER:BEGIN|## Mandatory Routing|## Initial Task Routing|## Routing Discipline|## Skill Selection' \
        "$instruction_file" || fail "missing workflow routing block in $instruction_file"
    grep -q 'workflow-router' "$instruction_file" || fail "missing workflow-router mention in $instruction_file"
done

for root in "${skill_roots[@]}"; do
    test -d "$root" || fail "missing skill root: $root"
    for skill in "${required_skills[@]}"; do
        test -f "$root/$skill/SKILL.md" || fail "missing $root/$skill/SKILL.md"
    done
done

if [[ ! -f "$routing_agents_home/engineering/README.md" ]]; then
    fail "missing $routing_agents_home/engineering/README.md"
fi

if [[ -d "$routing_agents_home/skills" ]]; then
    for skill in "${registered_skills[@]}"; do
        if [[ -f "$routing_agents_home/skills/$skill/SKILL.md" ]]; then
            fail "duplicate managed skill in ~/.agents: $skill"
        fi
    done
fi

managed_skill_files=()
for skill in "${required_skills[@]}"; do
    managed_skill_files+=("$routing_codex_home/skills/$skill/SKILL.md")
done

author_status=0
author_validator="$routing_package_root/scripts/validate-router-cases.py"
test -f "$author_validator" || fail "missing installed author routing validator"
if "$routing_python" "$author_validator" --root "$routing_package_root" \
    --installed-providers --codex-home "$routing_codex_home" \
    --agents-home "$routing_agents_home" --be-home "$routing_be_home"; then
    :
else
    author_status=$?
    if [[ "$author_status" != 2 ]]; then
        fail "required author provider readiness failed"
    fi
fi

if grep -n -E 'TODO:|Structuring This Skill|\[TODO' "${managed_skill_files[@]}"; then
    fail "template TODO text found in managed workflow skills"
fi

quick_validate="$routing_codex_home/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$quick_validate" ]]; then
    for skill in "${required_skills[@]}"; do
        if ! "$routing_python" "$quick_validate" "$routing_codex_home/skills/$skill" >/dev/null 2>/dev/null; then
            warn "quick_validate.py failed for $skill; skipped optional skill structure smoke"
            break
        fi
    done
else
    warn "quick_validate.py not found; skipped skill structure smoke"
fi

if command -v codex >/dev/null 2>&1; then
    for skill in workflow-router security-router review-router ui-router; do
        prompt_input="$(codex debug prompt-input "\$$skill smoke" 2>/dev/null || true)"
        if [[ -n "$prompt_input" ]]; then
            printf '%s' "$prompt_input" | grep -q "$skill" || fail "Codex prompt-input missing $skill"
        else
            warn "codex prompt-input smoke returned no output for $skill; skipped prompt visibility check"
        fi
    done
else
    warn "codex CLI not found; skipped prompt visibility check"
fi

if [[ "$author_status" == 2 ]]; then
    printf 'SKIP: author readiness; owner routing filesystem checks passed\n'
else
    printf 'OK: workflow routing filesystem healthcheck passed; session exposure SKIP\n'
fi
