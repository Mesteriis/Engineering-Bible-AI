#!/usr/bin/env python3
"""Audit Engineering Bible quality-gate invariants."""

from __future__ import annotations

import argparse
from pathlib import Path
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
    *QUALITY_DOCS,
    *GOLDEN_CASES,
]

MANIFEST_ENTRIES = [
    "scripts/audit-quality-gates.py",
    "quality-gates",
]

INSTALLER_SKILLS = [
    "quality-gates",
]

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
        for path in sorted((self.root / "engineering").glob("*.md")):
            if path.name == "README.md":
                continue
            relative = f"engineering/{path.name}"
            if f"- `{path.name}`" not in index:
                self.issues.append(f"missing engineering index entry: {relative}")
        if len(self.issues) == before:
            self.passed.append("engineering index")

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
        if "name: quality-gates" not in quality:
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
        installer = self.read_text("scripts/install-codex.sh")
        before = len(self.issues)
        for skill in INSTALLER_SKILLS:
            if skill not in installer:
                self.issues.append(f"missing installer skill: {skill}")
        if "audit-quality-gates.py" not in installer:
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
            if any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            if not path.is_file():
                continue
            relative = path.relative_to(self.root).as_posix()
            if path.name in FORBIDDEN_NAMES or path.suffix in FORBIDDEN_SUFFIXES:
                self.issues.append(f"forbidden runtime file: {relative}")
        if len(self.issues) == before:
            self.passed.append("runtime boundary")

    def run(self) -> int:
        self.check_required_files()
        self.check_engineering_index()
        self.check_skill_references()
        self.check_validation_tree()
        self.check_manifest()
        self.check_installer()
        self.check_golden_cases()
        self.check_runtime_boundary()

        if self.issues:
            print("quality audit failed")
            for issue in self.issues:
                print(issue)
            return 1

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
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"quality audit failed\nmissing audit root: {root}", file=sys.stderr)
        return 1

    return Audit(root).run()


if __name__ == "__main__":
    raise SystemExit(main())
