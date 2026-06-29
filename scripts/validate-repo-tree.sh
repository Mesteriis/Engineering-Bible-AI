#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

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
    "skills/registry.yml"
    "scripts/install.sh"
    "scripts/be.py"
    "scripts/install-codex.sh"
    "scripts/install_codex.py"
    "scripts/registry.py"
    "scripts/secret-sanity.sh"
    "scripts/validate-markdown-style.py"
    "scripts/validate-installed-tree.sh"
    "scripts/validate-repo-tree.sh"
    "scripts/validate-router-cases.py"
    "scripts/validate-skill-frontmatter.py"
    "scripts/validate-skill-tree.sh"
    "engineering/README.md"
    "engineering/00_manifesto.md"
    "engineering/01_constitution.md"
    "engineering/02_philosophy.md"
    "engineering/03_definition_of_done.md"
    "engineering/04_definition_of_beautiful_code.md"
    "engineering/05_design_principles.md"
    "engineering/06_responsibility_model.md"
    "engineering/07_complexity_budget.md"
    "engineering/08_engineering_smells.md"
    "engineering/09_architectural_smells.md"
    "engineering/10_antipattern_catalog.md"
    "engineering/11_refactoring_catalog.md"
    "engineering/12_naming_bible.md"
    "engineering/13_testing_philosophy.md"
    "engineering/14_debugging_philosophy.md"
    "engineering/15_error_philosophy.md"
    "engineering/16_security_philosophy.md"
    "engineering/17_observability_contract.md"
    "engineering/18_performance_philosophy.md"
    "engineering/19_documentation_style.md"
    "engineering/20_review_checklist.md"
    "engineering/21_commit_pr_adr_style.md"
    "engineering/22_evolution_rules.md"
    "engineering/23_agent_behavior.md"
    "engineering/24_task_todo_style.md"
    "engineering/25_api_philosophy.md"
    "engineering/26_domain_modeling.md"
    "engineering/27_state_machine_philosophy.md"
    "engineering/28_concurrency_philosophy.md"
    "engineering/29_configuration_philosophy.md"
    "engineering/30_dependency_philosophy.md"
    "engineering/31_data_philosophy.md"
    "engineering/32_ui_architecture_philosophy.md"
    "engineering/33_ai_engineering_philosophy.md"
    "engineering/34_evolution_decision_tree.md"
    "templates/agent-implementation-prompt.md"
    "tests/router-cases.yml"
    "VERSION"
    ".secret-sanity-allowlist"
)

missing=0
for file in "${required_files[@]}"; do
    if [[ ! -f "$ROOT/$file" ]]; then
        echo "missing: $file" >&2
        missing=1
    fi
done

if [[ "$missing" -ne 0 ]]; then
    echo "repo tree validation failed" >&2
    exit 1
fi

python3 "$ROOT/scripts/registry.py" --root "$ROOT" validate

if ! grep -q "workflow-router" "$ROOT/AGENTS.md"; then
    echo "AGENTS.md does not mention workflow-router" >&2
    exit 1
fi

if ! grep -Eq "WORKFLOW:ROUTER:BEGIN|## Mandatory Routing" "$ROOT/AGENTS.md"; then
    echo "AGENTS.md does not contain a routing instruction block" >&2
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

echo "repo tree validation passed"
