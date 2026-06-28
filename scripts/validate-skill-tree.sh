#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

required_files=(
  "AGENTS.md"
  "README.md"
  "README.ru.md"
  "MANIFEST.md"
  "Makefile"
  "LICENSE"
  "CHANGELOG.md"
  "CODE_OF_CONDUCT.md"
  "CONTRIBUTING.md"
  "GOVERNANCE.md"
  "SECURITY.md"
  "SUPPORT.md"
  "THIRD_PARTY_NOTICES.md"
  ".github/CODEOWNERS"
  ".github/PULL_REQUEST_TEMPLATE.md"
  ".github/dependabot.yml"
  ".github/ISSUE_TEMPLATE/bug_report.yml"
  ".github/ISSUE_TEMPLATE/feature_request.yml"
  ".github/ISSUE_TEMPLATE/config.yml"
  ".github/workflows/validate.yml"
  "docs/worker-runtime-boundary.md"
  "docs/oss-release-checklist.md"
  "scripts/install.sh"
  "scripts/be.py"
  "scripts/install-codex.sh"
  "scripts/secret-sanity.sh"
  "scripts/validate-skill-frontmatter.py"
  "skills/workflow-router/SKILL.md"
  "skills/engineering-standards/SKILL.md"
  "skills/core-engineering/SKILL.md"
  "skills/code-quality/SKILL.md"
  "skills/architecture-principles/SKILL.md"
  "skills/testing-tdd/SKILL.md"
  "skills/debugging/SKILL.md"
  "skills/code-review/SKILL.md"
  "skills/security/SKILL.md"
  "skills/performance/SKILL.md"
  "skills/refactoring/SKILL.md"
  "skills/documentation/SKILL.md"
  "skills/python/SKILL.md"
  "skills/typescript/SKILL.md"
  "skills/rust/SKILL.md"
  "skills/go/SKILL.md"
  "skills/c-cpp/SKILL.md"
  "skills/homeassistant/SKILL.md"
  "skills/esphome/SKILL.md"
  "skills/esp32/SKILL.md"
  "skills/code-wiki-ru/SKILL.md"
  "skills/security-router/SKILL.md"
  "skills/review-router/SKILL.md"
  "skills/ui-router/SKILL.md"
  "skills/ui-research/SKILL.md"
  "skills/ui-build/SKILL.md"
  "skills/ui-figma/SKILL.md"
  "skills/ui-qa/SKILL.md"
  "skills/multi-agent-pr-review/SKILL.md"
  "skills/architecture-map/SKILL.md"
  "skills/migration-planner/SKILL.md"
  "skills/subagent-result-merge/SKILL.md"
  "skills/agent-retrospective/SKILL.md"
  "skills/agents-md-retrospective/SKILL.md"
  "skills/security-diff-review/SKILL.md"
  "skills/fix-security-finding/SKILL.md"
  "skills/threat-model/SKILL.md"
  "skills/dependency-advisory-audit/SKILL.md"
  "skills/secrets-and-config-review/SKILL.md"
  "skills/authz-boundary-review/SKILL.md"
  "skills/deserialization-parser-review/SKILL.md"
  "skills/supply-chain-review/SKILL.md"
  "skills/ui-concept-first/SKILL.md"
  "skills/design-system-extractor/SKILL.md"
  "skills/figma-to-code/SKILL.md"
  "skills/code-to-figma/SKILL.md"
  "skills/playwright-visual-qa/SKILL.md"
  "skills/responsive-breakpoint-check/SKILL.md"
  "skills/accessibility-ui-review/SKILL.md"
  "engineering/00_manifesto.md"
  "engineering/01_constitution.md"
  "engineering/05_design_principles.md"
  "engineering/06_responsibility_model.md"
  "engineering/07_complexity_budget.md"
  "engineering/08_engineering_smells.md"
  "engineering/09_architectural_smells.md"
  "engineering/10_antipattern_catalog.md"
  "engineering/11_refactoring_catalog.md"
  "engineering/12_naming_bible.md"
  "engineering/24_task_todo_style.md"
  "templates/agent-implementation-prompt.md"
)

missing=0
for file in "${required_files[@]}"; do
  if [[ ! -f "$ROOT/$file" ]]; then
    echo "missing: $file" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "skill tree validation failed" >&2
  exit 1
fi

if ! grep -q "workflow-router" "$ROOT/AGENTS.md"; then
  echo "AGENTS.md does not mention workflow-router" >&2
  exit 1
fi

if find "$ROOT" -path "$ROOT/.git" -prune -o -type f \( \
  -name ".env" -o \
  -name ".env.*" -o \
  -name "auth.json" -o \
  -name "config.toml" -o \
  -name "*.pem" -o \
  -name "*.key" \
\) -print | grep -q .; then
  echo "runtime or secret-like file found in portable tree" >&2
  exit 1
fi

echo "skill tree validation passed"
