#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

required_files=(
    "AGENTS.md"
    "README.md"
    "README.ru.md"
    "MANIFEST.md"
    "instructions/global/steady.md"
    "instructions/global/full.md"
    "instructions/global/minimal.md"
    "instructions/global/fast.md"
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
    ".github/workflows/release.yml"
    "docs/worker-runtime-boundary.md"
    "docs/worker-evidence.md"
    "docs/memory-retrieval.md"
    "docs/ruflo-adoption.md"
    "docs/oss-release-checklist.md"
    "docs/upstream-skills.md"
    "docs/absorbed-skills-migration.md"
    "docs/business-ui-profile.md"
    "docs/quality-context-authors.md"
    "docs/task-continuation.md"
    "docs/worker-quorum.md"
    "docs/cross-provider-review.md"
    "docs/context-cache.md"
    "docs/targeted-mutation-testing.md"
    "templates/business-ui-brief.md"
    "templates/task-resume-checkpoint.md"
    "skills/registry.yml"
    "skills/fast/SKILL.md"
    "skills/workflow-router/references/routes.md"
    "skills/mcp-tool-router/references/host-adapter.md"
    "scripts/install.sh"
    "scripts/be.py"
    "scripts/install-codex.sh"
    "scripts/install-tools.sh"
    "scripts/install_codex.py"
    "scripts/installer_core.py"
    "scripts/mcp_catalog.py"
    "scripts/mcp_catalog_cli.py"
    "scripts/mcp_catalog_storage.py"
    "scripts/registry.py"
    "scripts/tool_catalog.py"
    "scripts/upstream_catalog.py"
    "scripts/upstream_sources.py"
    "scripts/upstream_skills.py"
    "scripts/upstream_cli.py"
    "scripts/build-release.py"
    "scripts/validate-actions-pins.py"
    "scripts/validate-release-contract.py"
    "scripts/secret-sanity.sh"
    "scripts/validate-markdown-style.py"
    "scripts/validate.py"
    "scripts/validate-acceptance.py"
    "scripts/worker-evidence.py"
    "scripts/memory-retrieval.py"
    "scripts/memory_retrieval.py"
    "scripts/worker_control.py"
    "scripts/worker_results.py"
    "scripts/worker_quorum.py"
    "scripts/context-cache.py"
    "scripts/context_cache.py"
    "scripts/mutation-check.py"
    "scripts/mutation_check.py"
    "scripts/mutation_unittest.py"
    "scripts/worker_snapshot.py"
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
    "tests/test_registry.py"
    "tests/test_bootstrap.py"
    "tests/test_acceptance.py"
    "tests/test_be_extended_cli.py"
    "tests/test_installer.py"
    "tests/test_mcp_catalog.py"
    "tests/test_release_contract.py"
    "tests/test_tool_catalog.py"
    "tests/test_upstream_catalog.py"
    "tests/test_upstream_sources.py"
    "tests/test_upstream_skills.py"
    "tests/test_upstream_cli.py"
    "tests/test_upstream_installer.py"
    "tests/test_validation.py"
    "tests/test_worker_results.py"
    "tests/test_worker_quorum.py"
    "tests/test_worker_context_contract.py"
    "tests/test_context_cache.py"
    "tests/test_mutation_check.py"
    "tests/test_worker_control.py"
    "tests/test_memory_retrieval.py"
    "tests/test_worker_snapshot.py"
    "tests/test_prompt_profiles.py"
    "tests/test_skill_catalog.py"
    "tests/test_skill_frontmatter.py"
    "tests/test_steady_profile.py"
    "config/tools.json"
    "config/upstream-skills.json"
    "config/legacy-install-signatures.json"
    "schemas/runtime-capabilities.schema.json"
    "schemas/acceptance-verdict.schema.json"
    "examples/runtime-capabilities.synthetic.json"
    "pyproject.toml"
    ".python-version"
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

# Generated runtime/vendor state is allowed locally only while untracked. Keep
# it out of scans, but fail if anyone explicitly adds it to the public tree.
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if ! tracked_private="$(git -C "$ROOT" ls-files -- .engineering-bible | awk 'END { if (NR > 0) print "tracked" }')"; then
        echo "could not verify tracked private runtime paths" >&2
        exit 1
    fi
    if [[ -n "$tracked_private" ]]; then
        echo "private runtime files are tracked under .engineering-bible" >&2
        exit 1
    fi
fi

python3 "$ROOT/scripts/registry.py" --root "$ROOT" validate

if ! grep -q "workflow-router" "$ROOT/AGENTS.md"; then
    echo "AGENTS.md does not mention workflow-router" >&2
    exit 1
fi

if ! grep -Eq \
    "WORKFLOW:ROUTER:BEGIN|## Mandatory Routing|## Initial Task Routing|## Routing Discipline" \
    "$ROOT/AGENTS.md"; then
    echo "AGENTS.md does not contain a routing instruction block" >&2
    exit 1
fi

if ! forbidden_file="$(find "$ROOT" \( \
    -name .git -o \
    -path "$ROOT/.engineering-bible" \
    \) -prune -o -type f \( \
    -name ".env" -o \
    -name ".env.*" -o \
    -name "auth.json" -o \
    -name "config.toml" -o \
    -name "*.pem" -o \
    -name "*.key" \
    \) -print | awk 'NR == 1 { found = 1 } END { if (found) print "found" }')"; then
    echo "portable tree scan failed" >&2
    exit 1
fi
if [[ -n "$forbidden_file" ]]; then
    echo "runtime or secret-like file found in portable tree" >&2
    exit 1
fi

echo "repo tree validation passed"
