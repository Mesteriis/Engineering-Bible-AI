#!/usr/bin/env bash
set -euo pipefail

CODEX_ROOT="${1:-${CODEX_HOME:-$HOME/.codex}}"
AGENTS_ROOT="${2:-${AGENTS_HOME:-$HOME/.agents}}"
shift $(($# > 0 ? 1 : 0)) || true
shift $(($# > 0 ? 1 : 0)) || true

CODEX_ROOT="$(cd "$CODEX_ROOT" && pwd)"
AGENTS_ROOT="$(cd "$AGENTS_ROOT" && pwd)"

required_files=(
    "AGENTS.md"
    "engineering/README.md"
    "reference/design-principles.md"
    "templates/agent-implementation-prompt.md"
    "tests/router-cases.yml"
    "scripts/be.py"
    "scripts/install-codex.sh"
    "scripts/install_codex.py"
    "scripts/registry.py"
    "scripts/validate-markdown-style.py"
    "scripts/validate-installed-tree.sh"
    "scripts/validate-repo-tree.sh"
    "scripts/validate-router-cases.py"
    "scripts/validate-skill-frontmatter.py"
    "scripts/validate-skill-tree.sh"
    "skills/registry.yml"
    "VERSION"
    ".secret-sanity-allowlist"
)

missing=0
for file in "${required_files[@]}"; do
    if [[ ! -f "$CODEX_ROOT/$file" ]]; then
        echo "missing installed Codex file: $file" >&2
        missing=1
    fi
done

if [[ ! -f "$AGENTS_ROOT/skills/registry.yml" ]]; then
    echo "missing installed Agents registry: skills/registry.yml" >&2
    missing=1
fi

if [[ "$missing" -ne 0 ]]; then
    echo "installed tree validation failed" >&2
    exit 1
fi

if ! grep -q "workflow-router" "$CODEX_ROOT/AGENTS.md"; then
    echo "installed AGENTS.md does not mention workflow-router" >&2
    exit 1
fi

if ! grep -Eq "WORKFLOW:ROUTER:BEGIN|## Mandatory Routing" "$CODEX_ROOT/AGENTS.md"; then
    echo "installed AGENTS.md does not contain a routing instruction block" >&2
    exit 1
fi

skills=()
while IFS= read -r skill; do
    skills+=("$skill")
done < <(python3 "$CODEX_ROOT/scripts/registry.py" --root "$CODEX_ROOT" skills "$@")
for skill in "${skills[@]}"; do
    if [[ ! -f "$CODEX_ROOT/skills/$skill/SKILL.md" ]]; then
        echo "missing installed Codex skill: $skill" >&2
        missing=1
    fi
    if [[ ! -f "$AGENTS_ROOT/skills/$skill/SKILL.md" ]]; then
        echo "missing installed Agents skill: $skill" >&2
        missing=1
    fi
done

if [[ "$missing" -ne 0 ]]; then
    echo "installed tree validation failed" >&2
    exit 1
fi

if find "$CODEX_ROOT" "$AGENTS_ROOT" -type f \( \
    -name ".env" -o \
    -name ".env.*" -o \
    -name "auth.json" -o \
    -name "config.toml" -o \
    -name "*.pem" -o \
    -name "*.key" \
    \) -print | grep -q .; then
    echo "runtime or secret-like file found in installed portable tree" >&2
    exit 1
fi

echo "installed tree validation passed"
