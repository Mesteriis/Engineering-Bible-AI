#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
AGENTS_ROOT="${2:-${AGENTS_HOME:-$HOME/.agents}}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

required_files=(
    "AGENTS.md"
    "README.md"
    "README.ru.md"
    "MANIFEST.md"
    "Makefile"
    "LICENSE"
    "scripts/be.py"
    "scripts/install-codex.sh"
    "scripts/install_codex.py"
    "scripts/registry.py"
    "scripts/validate-installed-tree.sh"
    "scripts/validate-repo-tree.sh"
    "scripts/validate-router-cases.py"
    "scripts/validate-skill-frontmatter.py"
    "scripts/validate-skill-tree.sh"
    "scripts/secret-sanity.sh"
    "scripts/check-file-size.py"
    "skills/registry.yml"
    "scripts/validate-markdown-style.py"
    "skills/quality-gates/SKILL.md"
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
    "scripts/audit-quality-gates.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$ROOT/$file" ]]; then
        echo "missing: $file" >&2
        exit 1
    fi
done

if [[ -f "$ROOT/README.md" && -f "$ROOT/MANIFEST.md" ]]; then
    exec bash "$script_dir/validate-repo-tree.sh" "$ROOT"
fi

exec bash "$script_dir/validate-installed-tree.sh" "$ROOT" "$AGENTS_ROOT"
