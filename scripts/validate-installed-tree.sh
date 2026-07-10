#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="${1:-${ENGINEERING_BIBLE_HOME:-${CODEX_HOME:-$HOME/.codex}/engineering-bible}/current}"
CODEX_ROOT="${2:-${CODEX_HOME:-$HOME/.codex}}"
AGENTS_ROOT="${3:-${AGENTS_HOME:-$HOME/.agents}}"
shift $(($# > 0 ? 1 : 0)) || true
shift $(($# > 0 ? 1 : 0)) || true
shift $(($# > 0 ? 1 : 0)) || true

PACKAGE_ROOT="$(cd "$PACKAGE_ROOT" && pwd)"
CODEX_ROOT="$(cd "$CODEX_ROOT" && pwd)"
AGENTS_ROOT="$(cd "$AGENTS_ROOT" && pwd)"
MANIFEST_PATH="$(dirname "$PACKAGE_ROOT")/install-manifest.json"

python_bin="${ENGINEERING_BIBLE_PYTHON:-}"
if [[ -z "$python_bin" ]]; then
    if command -v python3.11 >/dev/null 2>&1; then
        python_bin=python3.11
    else
        python_bin=python3
    fi
fi
if ! command -v "$python_bin" >/dev/null 2>&1; then
    echo "Python interpreter not found: $python_bin" >&2
    exit 1
fi
"$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else "Python 3.11+ is required")'

package_required_files=(
    "AGENTS.md"
    "engineering/README.md"
    "instructions/global/full.md"
    "instructions/global/minimal.md"
    "reference/design-principles.md"
    "templates/agent-implementation-prompt.md"
    "tests/router-cases.yml"
    "scripts/be.py"
    "scripts/build-release.py"
    "scripts/install-codex.sh"
    "scripts/install-tools.sh"
    "scripts/install_codex.py"
    "scripts/installer_core.py"
    "scripts/mcp_catalog.py"
    "scripts/mcp_catalog_cli.py"
    "scripts/mcp_catalog_storage.py"
    "scripts/registry.py"
    "scripts/tool_catalog.py"
    "scripts/validate-actions-pins.py"
    "scripts/validate.py"
    "scripts/validate-release-contract.py"
    "scripts/validate-installed-tree.sh"
    "scripts/validate-markdown-style.py"
    "scripts/validate-repo-tree.sh"
    "scripts/validate-router-cases.py"
    "scripts/validate-skill-frontmatter.py"
    "scripts/validate-skill-tree.sh"
    "skills/registry.yml"
    "skills/mcp-tool-router/SKILL.md"
    "config/tools.json"
    "schemas/runtime-capabilities.schema.json"
    "examples/runtime-capabilities.synthetic.json"
    "pyproject.toml"
    ".python-version"
    "VERSION"
    ".secret-sanity-allowlist"
)

missing=0
if [[ ! -f "$MANIFEST_PATH" || -L "$MANIFEST_PATH" ]]; then
    echo "missing or unsafe install manifest: $MANIFEST_PATH" >&2
    missing=1
fi
for file in "${package_required_files[@]}"; do
    if [[ ! -f "$PACKAGE_ROOT/$file" ]]; then
        echo "missing installed package file: $file" >&2
        missing=1
    fi
done

if [[ ! -f "$CODEX_ROOT/AGENTS.md" ]]; then
    echo "missing active Codex instructions: AGENTS.md" >&2
    missing=1
fi
if [[ ! -f "$CODEX_ROOT/skills/registry.yml" ]]; then
    echo "missing active Codex registry: skills/registry.yml" >&2
    missing=1
fi
if [[ ! -f "$AGENTS_ROOT/skills/registry.yml" ]]; then
    echo "missing installed Agents registry: skills/registry.yml" >&2
    missing=1
fi
if [[ ! -f "$AGENTS_ROOT/engineering/README.md" ]]; then
    echo "missing installed Agents reference docs: engineering/README.md" >&2
    missing=1
fi

if [[ "$missing" -ne 0 ]]; then
    echo "installed tree validation failed" >&2
    exit 1
fi

manifest_selection="$(
    "$python_bin" - "$MANIFEST_PATH" "$PACKAGE_ROOT" "$CODEX_ROOT" "$AGENTS_ROOT" <<'PY'
import json
import hashlib
from pathlib import Path
from pathlib import PurePosixPath
import re
import stat
import sys

manifest_path = Path(sys.argv[1])
package_root = Path(sys.argv[2]).resolve()
codex_root = Path(sys.argv[3]).resolve()
agents_root = Path(sys.argv[4]).resolve()
sys.path.insert(0, str(package_root / "scripts"))
import installer_core  # noqa: E402
import registry  # noqa: E402

try:
    if stat.S_IMODE(manifest_path.stat().st_mode) != 0o600:
        raise ValueError("install manifest mode must be 0600")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("unsupported schema")
    if payload.get("complete") is not True:
        raise ValueError("installation is incomplete")

    roots = payload.get("roots")
    if not isinstance(roots, dict):
        raise ValueError("missing roots")
    expected_roots = {
        "be_home": package_root.parent,
        "codex_home": codex_root,
        "agents_home": agents_root,
    }
    for name, expected in expected_roots.items():
        value = roots.get(name)
        if not isinstance(value, str) or Path(value).expanduser().resolve() != expected:
            raise ValueError(f"root mismatch: {name}")

    root_paths = {}
    for name in ("be_home", "codex_home", "agents_home", "bin_dir"):
        value = roots.get(name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"missing root: {name}")
        root_paths[name] = Path(value).expanduser().resolve()

    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("missing file inventory")
    seen = set()
    normalized_inventory = []
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise ValueError(f"invalid file entry: {index}")
        root_name = entry.get("root")
        relative = entry.get("path")
        digest = entry.get("sha256")
        mode = entry.get("mode")
        if not isinstance(root_name, str) or root_name not in root_paths:
            raise ValueError(f"invalid file root: {index}")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"invalid file path: {index}")
        relative_path = PurePosixPath(relative)
        if (
            relative_path.is_absolute()
            or relative_path.as_posix() != relative
            or any(part in {"", ".", ".."} for part in relative_path.parts)
            or "\\" in relative
        ):
            raise ValueError(f"unsafe file path: {index}")
        key = (root_name, relative)
        if key in seen:
            raise ValueError(f"duplicate file entry: {root_name}:{relative}")
        seen.add(key)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(f"invalid file digest: {index}")
        if not isinstance(mode, str) or re.fullmatch(r"0[0-7]{3}", mode) is None:
            raise ValueError(f"invalid file mode: {index}")
        normalized_inventory.append(
            {"root": root_name, "path": relative, "sha256": digest, "mode": mode}
        )

        target = root_paths[root_name].joinpath(*relative_path.parts)
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"missing or unsafe managed file: {root_name}:{relative}")
        resolved_target = target.resolve(strict=True)
        try:
            resolved_target.relative_to(root_paths[root_name])
        except ValueError as exc:
            raise ValueError(f"managed file escapes root: {root_name}:{relative}") from exc
        hasher = hashlib.sha256()
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        observed_digest = hasher.hexdigest()
        if observed_digest != digest:
            raise ValueError(f"managed file digest mismatch: {root_name}:{relative}")
        observed_mode = stat.S_IMODE(target.stat().st_mode)
        if observed_mode != int(mode, 8):
            raise ValueError(f"managed file mode mismatch: {root_name}:{relative}")

    package = payload.get("package")
    if not isinstance(package, dict):
        raise ValueError("missing package metadata")
    version = package.get("version")
    digest = package.get("digest")
    source = package.get("source")
    if not isinstance(version, str) or re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version) is None:
        raise ValueError("invalid package version")
    expected_digest = "sha256:" + hashlib.sha256(
        json.dumps(normalized_inventory, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if digest != expected_digest:
        raise ValueError("package digest does not match file inventory")
    if not isinstance(source, dict) or any(
        not isinstance(source.get(key), str) or not source.get(key)
        for key in ("kind", "location", "reference")
    ):
        raise ValueError("invalid package source metadata")

    groups = payload.get("groups")
    if not isinstance(groups, dict):
        raise ValueError("missing groups")
    requested = groups.get("requested")
    include_all = groups.get("include_all")
    profile = groups.get("prompt_profile")
    selected = groups.get("selected_skills")
    if not isinstance(requested, list) or any(
        not isinstance(group, str) or not group.strip() for group in requested
    ):
        raise ValueError("invalid requested groups")
    if not isinstance(include_all, bool):
        raise ValueError("invalid include_all flag")
    if profile not in {"full", "minimal"}:
        raise ValueError("invalid prompt profile")
    if not isinstance(selected, list) or any(
        not isinstance(skill, str) or not skill.strip() for skill in selected
    ):
        raise ValueError("invalid selected skills")

    expected_skills = registry.selected_skills(
        registry.load_registry(package_root),
        groups=list(requested),
        include_all=include_all,
    )
    if selected != expected_skills:
        raise ValueError("selected skills do not match registry and group metadata")
    options = installer_core.InstallerOptions(
        repo_root=package_root,
        codex_home=root_paths["codex_home"],
        agents_home=root_paths["agents_home"],
        be_home=root_paths["be_home"],
        bin_dir=root_paths["bin_dir"],
        dry_run=True,
        backup_only=False,
        no_overwrite=False,
        force=False,
        diff=False,
        groups=list(requested),
        all_groups=include_all,
        install_tools=False,
        migrate_legacy=False,
        prompt_profile=profile,
        backup_dir=root_paths["be_home"] / "backups" / "validation-unused",
    )
    expected_files = installer_core.build_desired_files(options, expected_skills)
    expected_keys = {(item.root, item.path) for item in expected_files}
    if seen != expected_keys:
        missing_entries = sorted(expected_keys - seen)
        unexpected_entries = sorted(seen - expected_keys)
        details = []
        if missing_entries:
            details.append(f"missing expected manifest entries: {missing_entries[:3]}")
        if unexpected_entries:
            details.append(f"unexpected manifest entries: {unexpected_entries[:3]}")
        raise ValueError("; ".join(details))
except (
    OSError,
    UnicodeError,
    json.JSONDecodeError,
    ValueError,
    installer_core.InstallError,
    registry.RegistryError,
) as exc:
    raise SystemExit(f"invalid install manifest: {exc}") from exc

print(profile)
for skill in selected:
    print(skill)
PY
)" || {
    echo "installed tree validation failed" >&2
    exit 1
}

prompt_profile="${manifest_selection%%$'\n'*}"
skill_lines="${manifest_selection#*$'\n'}"
if [[ "$manifest_selection" != *$'\n'* ]]; then
    skill_lines=""
fi

if ! cmp -s "$CODEX_ROOT/AGENTS.md" "$PACKAGE_ROOT/instructions/global/$prompt_profile.md"; then
    echo "active Codex AGENTS.md does not match manifest prompt profile: $prompt_profile" >&2
    exit 1
fi

skills=()
while IFS= read -r skill; do
    if [[ -n "$skill" ]]; then
        skills+=("$skill")
    fi
done <<<"$skill_lines"

managed_paths=(
    "$PACKAGE_ROOT"
    "$CODEX_ROOT/AGENTS.md"
    "$CODEX_ROOT/skills/registry.yml"
    "$AGENTS_ROOT/skills/registry.yml"
    "$AGENTS_ROOT/engineering"
)

for skill in "${skills[@]}"; do
    skill_path="$CODEX_ROOT/skills/$skill"
    managed_paths+=("$skill_path")
    if [[ ! -f "$skill_path/SKILL.md" ]]; then
        echo "missing active Codex skill: $skill" >&2
        missing=1
    fi
    if [[ -f "$AGENTS_ROOT/skills/$skill/SKILL.md" ]]; then
        echo "duplicate installed Agents skill: skills/$skill" >&2
        missing=1
    fi
done

if [[ "$missing" -ne 0 ]]; then
    echo "installed tree validation failed" >&2
    exit 1
fi

if find "${managed_paths[@]}" -type f \( \
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
