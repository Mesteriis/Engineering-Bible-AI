#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
CODEX_ROOT="${2:-${CODEX_HOME:-$HOME/.codex}}"
AGENTS_ROOT="${3:-${AGENTS_HOME:-$HOME/.agents}}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

required_files=(
    "AGENTS.md"
    "instructions/global/steady.md"
    "instructions/global/full.md"
    "instructions/global/minimal.md"
    "instructions/global/fast.md"
    "README.md"
    "README.ru.md"
    "MANIFEST.md"
    "Makefile"
    "LICENSE"
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
    "scripts/build-release.py"
    "scripts/validate-actions-pins.py"
    "scripts/validate-release-contract.py"
    "scripts/validate-installed-tree.sh"
    "scripts/validate-repo-tree.sh"
    "scripts/validate-router-cases.py"
    "scripts/validate-skill-frontmatter.py"
    "scripts/validate-skill-tree.sh"
    "scripts/secret-sanity.sh"
    "scripts/check-file-size.py"
    "skills/registry.yml"
    "scripts/validate-markdown-style.py"
    "scripts/validate.py"
    "skills/quality-gates/SKILL.md"
    "skills/workflow-router/references/routes.md"
    "skills/mcp-tool-router/references/host-adapter.md"
    "VERSION"
    ".secret-sanity-allowlist"
    "engineering/README.md"
    "engineering/35_evidence_contract.md"
    "engineering/36_task_lifecycle_gates.md"
    "engineering/37_review_regression_gates.md"
    "engineering/38_library_drift_audit.md"
    "tests/quality-gates/hallucinated-test-result.md"
    "tests/quality-gates/skipped-inspection.md"
    "tests/quality-gates/skipped-validation.md"
    "tests/quality-gates/weak-review.md"
    "tests/quality-gates/stale-routing-reference.md"
    "tests/quality-gates/missing-manifest-entry.md"
    "tests/test_quality_audit.py"
    "tests/test_registry.py"
    "tests/test_bootstrap.py"
    "tests/test_be_extended_cli.py"
    "tests/test_installer.py"
    "tests/test_mcp_catalog.py"
    "tests/test_release_contract.py"
    "tests/test_tool_catalog.py"
    "tests/test_validation.py"
    "tests/test_prompt_profiles.py"
    "tests/test_skill_catalog.py"
    "tests/test_skill_frontmatter.py"
    "tests/test_steady_profile.py"
    "config/tools.json"
    "schemas/runtime-capabilities.schema.json"
    "examples/runtime-capabilities.synthetic.json"
    "skills/mcp-tool-router/SKILL.md"
    "pyproject.toml"
    ".python-version"
    "scripts/audit-quality-gates.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$ROOT/$file" ]]; then
        echo "missing: $file" >&2
        exit 1
    fi
done

if [[ -f "$ROOT/../install-manifest.json" ]]; then
    exec bash "$script_dir/validate-installed-tree.sh" "$ROOT" "$CODEX_ROOT" "$AGENTS_ROOT"
fi

if [[ -f "$ROOT/README.md" && -f "$ROOT/MANIFEST.md" ]]; then
    exec bash "$script_dir/validate-repo-tree.sh" "$ROOT"
fi

exec bash "$script_dir/validate-installed-tree.sh" "$ROOT" "$CODEX_ROOT" "$AGENTS_ROOT"
