#!/usr/bin/env python3
"""Audit Engineering Bible quality-gate invariants."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
import json
from pathlib import Path
import re
import sys


QUALITY_DOCS = [
    "engineering/35_evidence_contract.md",
    "engineering/36_task_lifecycle_gates.md",
    "engineering/37_review_regression_gates.md",
    "engineering/38_library_drift_audit.md",
]

GOLDEN_CASES = [
    "tests/quality-gates/hallucinated-test-result.md",
    "tests/quality-gates/skipped-inspection.md",
    "tests/quality-gates/skipped-validation.md",
    "tests/quality-gates/weak-review.md",
    "tests/quality-gates/stale-routing-reference.md",
    "tests/quality-gates/missing-manifest-entry.md",
]

REQUIRED_FILES = [
    "skills/quality-gates/SKILL.md",
    "scripts/audit-quality-gates.py",
    "tests/test_quality_audit.py",
    "scripts/validate-markdown-style.py",
    "scripts/validate.py",
    "scripts/installer_core.py",
    "scripts/mcp_catalog.py",
    "scripts/mcp_catalog_cli.py",
    "scripts/mcp_catalog_storage.py",
    "scripts/tool_catalog.py",
    "scripts/build-release.py",
    "scripts/validate-actions-pins.py",
    "scripts/validate-release-contract.py",
    "config/tools.json",
    "schemas/runtime-capabilities.schema.json",
    "skills/mcp-tool-router/SKILL.md",
    "instructions/global/full.md",
    "instructions/global/minimal.md",
    "VERSION",
    ".secret-sanity-allowlist",
    *QUALITY_DOCS,
    *GOLDEN_CASES,
]

MANIFEST_ENTRIES = [
    "scripts/audit-quality-gates.py",
    "scripts/install-tools.sh",
    "quality-gates",
    "scripts/validate-markdown-style.py",
    "scripts/validate.py",
    "scripts/installer_core.py",
    "scripts/mcp_catalog.py",
    "scripts/tool_catalog.py",
    "scripts/build-release.py",
    "scripts/validate-actions-pins.py",
    "scripts/validate-release-contract.py",
    "VERSION",
    ".secret-sanity-allowlist",
]

INSTALLER_SKILLS = [
    "quality-gates",
]

KNOWN_REGISTRY_SECTIONS = {"default_groups", "groups", "optional"}

FORBIDDEN_NAMES = {
    ".env",
    "auth.json",
    "config.toml",
}

FORBIDDEN_SUFFIXES = {
    ".pem",
    ".key",
}

SKIP_DIRS = {
    ".git",
    "__pycache__",
}


class Audit:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.issues: list[str] = []
        self.passed: list[str] = []

    def path(self, relative: str) -> Path:
        return self.root / relative

    def read_text(self, relative: str) -> str:
        path = self.path(relative)
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            self.issues.append(f"unreadable file: {relative}: {exc}")
            return ""

    def collect_engineering_index_entries(self, index: str) -> set[str]:
        entries: set[str] = set()
        for line in index.splitlines():
            match = re.search(r"`(engineering/[A-Za-z0-9_\\-]+\.md)`", line)
            if match:
                entries.add(match.group(1))
        return entries

    def require_file(self, relative: str) -> None:
        if not self.path(relative).is_file():
            self.issues.append(f"missing required file: {relative}")

    def check_required_files(self) -> None:
        before = len(self.issues)
        for relative in REQUIRED_FILES:
            self.require_file(relative)
        if len(self.issues) == before:
            self.passed.append("required files")

    def check_engineering_index(self) -> None:
        index = self.read_text("engineering/README.md")
        before = len(self.issues)
        index_entries = self.collect_engineering_index_entries(index)
        for path in sorted((self.root / "engineering").glob("*.md")):
            if path.name == "README.md":
                continue
            relative = f"engineering/{path.name}"
            if relative not in index_entries:
                self.issues.append(f"missing engineering index entry: {relative}")
        if len(self.issues) == before:
            self.passed.append("engineering index")

    def parse_yaml_array(self, text: str, *, section_name: str) -> Iterable[str]:
        in_section = False
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()

            if indent == 0 and stripped.endswith(":"):
                section = stripped[:-1]
                in_section = section == section_name
                continue

            if not in_section:
                continue

            if section_name in {"groups", "optional"} and indent == 2 and stripped.endswith(":"):
                continue

            if section_name == "default_groups" and indent == 2 and stripped.startswith("- "):
                yield stripped[2:].strip()
                continue

            if section_name in {"groups", "optional"} and indent == 4 and stripped.startswith("- "):
                yield stripped[2:].strip()

    def parse_registry_groups(self, text: str) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        section = ""
        current_group = ""
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()

            if indent == 0 and stripped.endswith(":"):
                section = stripped[:-1]
                current_group = ""
                continue

            if section not in {"groups", "optional"}:
                continue

            if indent == 2 and stripped.endswith(":"):
                current_group = stripped[:-1]
                groups[current_group] = []
                continue

            if indent == 4 and stripped.startswith("- ") and current_group:
                groups[current_group].append(stripped[2:].strip())
        return groups

    def collect_registered_skills(self) -> set[str]:
        registry = self.read_text("skills/registry.yml")
        if not registry:
            return set()

        group_map = self.parse_registry_groups(registry)
        skills: set[str] = set()
        for items in group_map.values():
            skills.update(items)
        return skills

    def collect_default_installed_skills(self) -> set[str]:
        registry = self.read_text("skills/registry.yml")
        if not registry:
            return set()

        default_groups = self.parse_yaml_array(registry, section_name="default_groups")
        group_map = self.parse_registry_groups(registry)
        skills: set[str] = set()
        for group in default_groups:
            skills.update(group_map.get(group, []))
        return skills

    def check_skill_references(self) -> None:
        standards = self.read_text("skills/engineering-standards/SKILL.md")
        quality = self.read_text("skills/quality-gates/SKILL.md")
        workflow = self.read_text("skills/workflow-router/SKILL.md")
        before = len(self.issues)

        for relative in QUALITY_DOCS:
            if relative not in standards:
                self.issues.append(f"missing engineering-standards reference: {relative}")
            if relative not in quality:
                self.issues.append(f"missing quality-gates reference: {relative}")

        if "quality-gates" not in workflow:
            self.issues.append("missing workflow-router reference: quality-gates")

        if not quality.startswith("---"):
            self.issues.append("invalid skill frontmatter: skills/quality-gates/SKILL.md")
        if "name: quality-gates" not in quality and "name: [be] quality-gates" not in quality:
            self.issues.append("missing skill name: skills/quality-gates/SKILL.md")
        if "description:" not in quality:
            self.issues.append("missing skill description: skills/quality-gates/SKILL.md")

        if len(self.issues) == before:
            self.passed.append("skill references")

    def check_validation_tree(self) -> None:
        validation = self.read_text("scripts/validate-skill-tree.sh")
        before = len(self.issues)
        for relative in REQUIRED_FILES:
            if relative not in validation:
                self.issues.append(f"missing validation required file: {relative}")
        if len(self.issues) == before:
            self.passed.append("validation tree")

    def check_manifest(self) -> None:
        manifest = self.read_text("MANIFEST.md")
        before = len(self.issues)
        for entry in MANIFEST_ENTRIES:
            if entry not in manifest:
                self.issues.append(f"missing manifest entry: {entry}")
        if len(self.issues) == before:
            self.passed.append("manifest")

    def check_installer(self) -> None:
        installer_py = self.read_text("scripts/install_codex.py") + self.read_text(
            "scripts/installer_core.py"
        )
        before = len(self.issues)
        registered_skills = self.collect_registered_skills()
        default_skills = self.collect_default_installed_skills()

        for skill in INSTALLER_SKILLS:
            if skill not in registered_skills:
                self.issues.append(f"missing installer skill: {skill}")
            if skill not in default_skills:
                self.issues.append(f"missing installer default-group skill: {skill}")
        if "audit-quality-gates.py" not in installer_py:
            self.issues.append("missing installer chmod: scripts/audit-quality-gates.py")
        if len(self.issues) == before:
            self.passed.append("installer")

    def check_golden_cases(self) -> None:
        before = len(self.issues)
        for relative in GOLDEN_CASES:
            text = self.read_text(relative)
            if "## Expected gate" not in text:
                self.issues.append(f"missing expected gate section: {relative}")
        if len(self.issues) == before:
            self.passed.append("golden cases")

    def check_runtime_boundary(self) -> None:
        before = len(self.issues)
        for path in self.root.rglob("*"):
            relative_parts = set(path.relative_to(self.root).parts)
            if path.is_dir():
                if relative_parts.intersection(SKIP_DIRS):
                    continue
                continue
            if any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            if not path.is_file():
                continue
            relative = path.relative_to(self.root).as_posix()
            if path.name in FORBIDDEN_NAMES or any(
                path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES
            ):
                self.issues.append(f"forbidden runtime file: {relative}")
        if len(self.issues) == before:
            self.passed.append("runtime boundary")

    def run(self, *, emit_report: bool = True) -> int:
        self.check_required_files()
        self.check_engineering_index()
        self.check_skill_references()
        self.check_validation_tree()
        self.check_manifest()
        self.check_installer()
        self.check_golden_cases()
        self.check_runtime_boundary()

        if self.issues:
            if emit_report:
                print("quality audit failed")
                for issue in self.issues:
                    print(issue)
            return 1

        if emit_report:
            print("quality audit passed")
            for check in [
                "engineering index",
                "skill references",
                "validation tree",
                "manifest",
                "installer",
                "golden cases",
                "runtime boundary",
            ]:
                print(f"- {check}: ok")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Engineering Bible quality gates.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to audit")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"quality audit failed\nmissing audit root: {root}", file=sys.stderr)
        return 1

    audit = Audit(root)
    emit_report = not args.json
    status = 0 if audit.run(emit_report=emit_report) == 0 else 1

    if args.json:
        payload = {
            "tool": "quality-audit",
            "status": "ok" if status == 0 else "fail",
            "root": str(root),
            "checks": {check: "ok" for check in audit.passed},
            "issues": audit.issues,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return status

    return status


if __name__ == "__main__":
    raise SystemExit(main())
