# Quality Control Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight quality-gates layer with evidence, lifecycle, review, regression, and drift-audit checks for Engineering Bible AI.

**Architecture:** Keep quality policy in neutral `engineering/` docs and a small `quality-gates` skill, then enforce repository drift with a Python standard-library audit script. Integrate the audit through `be audit`, `make audit`, and `make validate` without changing local worker/runtime configuration.

**Tech Stack:** Markdown, Python 3 standard library, Bash, Make, `unittest`, existing validation scripts.

---

## Scope

This plan implements the first slice from `docs/superpowers/specs/2026-06-28-quality-control-layer-design.md`.

Included:

- `skills/quality-gates/SKILL.md`
- `engineering/35_evidence_contract.md`
- `engineering/36_task_lifecycle_gates.md`
- `engineering/37_review_regression_gates.md`
- `engineering/38_library_drift_audit.md`
- `scripts/audit-quality-gates.py`
- `tests/test_quality_audit.py`
- static quality-gate corpus files under `tests/quality-gates/`
- `be audit`
- `make audit`
- `make validate` includes audit and audit tests
- docs, manifest, installer, and validation-tree updates

Deferred:

- `be audit --json`
- full LLM eval runner
- automatic agent execution against golden cases
- release automation
- severity policy engine

## File Structure

- Create `skills/quality-gates/SKILL.md`: routing skill for evidence, lifecycle, review, regression, and drift gates.
- Modify `skills/workflow-router/SKILL.md`: include `quality-gates` for non-trivial engineering work.
- Create `engineering/35_evidence_contract.md`: evidence requirements for claims.
- Create `engineering/36_task_lifecycle_gates.md`: proportional task lifecycle gates.
- Create `engineering/37_review_regression_gates.md`: review and regression expectations.
- Create `engineering/38_library_drift_audit.md`: library drift invariants and audit output contract.
- Modify `engineering/README.md`: list docs 35-38 and selection rules.
- Modify `skills/engineering-standards/SKILL.md`: reference docs 35-38.
- Create `scripts/audit-quality-gates.py`: repository audit engine.
- Modify `scripts/install-codex.sh`: include `quality-gates` skill and chmod audit script.
- Modify `scripts/validate-skill-tree.sh`: require quality-gates files.
- Modify `MANIFEST.md`: list new skill and command entry point.
- Create `tests/quality-gates/*.md`: static failure-mode corpus.
- Create `tests/test_quality_audit.py`: audit engine regression tests.
- Modify `scripts/be.py`: add `be audit`.
- Modify `tests/test_be_cli.py`: cover `be audit`.
- Modify `Makefile`: add `audit` and `quality-audit-tests`.
- Modify `README.md`, `README.ru.md`, `CONTRIBUTING.md`, and `docs/oss-release-checklist.md`: document audit commands and validation.

## Task 1: Add Quality-Gates Skill And Reference Docs

**Files:**

- Create: `skills/quality-gates/SKILL.md`
- Create: `engineering/35_evidence_contract.md`
- Create: `engineering/36_task_lifecycle_gates.md`
- Create: `engineering/37_review_regression_gates.md`
- Create: `engineering/38_library_drift_audit.md`
- Modify: `engineering/README.md`
- Modify: `skills/engineering-standards/SKILL.md`
- Modify: `skills/workflow-router/SKILL.md`

- [x] **Step 1: Create `skills/quality-gates/SKILL.md`**

Create `skills/quality-gates/SKILL.md` with this content:

```markdown
---
name: quality-gates
description: "Apply evidence, lifecycle, review, regression, and library-drift gates for non-trivial engineering work."
---

# Skill: quality-gates

## Purpose

Use this skill as a lightweight control layer for non-trivial engineering work.
It keeps agent output evidence-bound, task execution lifecycle-aware, reviewable,
and resistant to Engineering Bible drift.

This skill does not replace language, security, UI, documentation, or review
skills. It composes with them.

## Required References

Read only the references needed for the task:

- `engineering/35_evidence_contract.md` for claims, facts, validation, and uncertainty.
- `engineering/36_task_lifecycle_gates.md` for task scope, inspection, planning, validation, and reporting.
- `engineering/37_review_regression_gates.md` for diff-risk review and regression coverage.
- `engineering/38_library_drift_audit.md` for repository integrity and portable-tree drift.

## When To Use

Use this skill when a request is non-trivial and involves any of:

- code changes;
- repository structure changes;
- installer or CLI behavior;
- docs that define behavior or process;
- validation, CI, test, or review workflows;
- multi-step debugging or refactoring;
- claims about current code, runtime state, test results, or external behavior.

For trivial read-only answers, apply the evidence contract without loading every
reference document.

## Operating Rules

- Important factual claims need evidence: file path, command output, test result, or explicit uncertainty.
- Do not claim validation passed unless the exact command was run.
- Inspect relevant files before changing them.
- Keep task gates proportional to task risk.
- Review behavior changes before completion.
- Add or update regression coverage when a defect class is fixed.
- Treat library drift as a repository bug, not as documentation polish.

## Output

When this skill materially affects the work, report:

- evidence used;
- lifecycle gates completed;
- validation commands and results;
- review or regression reasoning;
- remaining risks.
```

- [x] **Step 2: Create `engineering/35_evidence_contract.md`**

Create `engineering/35_evidence_contract.md` with this content:

```markdown
# Evidence Contract

Engineering claims must be traceable to evidence.

## What Counts As Evidence

Use the strongest available evidence:

- repository files with paths;
- command output from the current environment;
- test, lint, type-check, build, or audit results;
- official documentation when external behavior matters;
- direct user-provided context;
- explicitly stated uncertainty when evidence is unavailable.

## Claims That Need Evidence

Evidence is required for claims about:

- files, symbols, APIs, imports, and schemas;
- framework or dependency behavior;
- test status, build status, lint status, or CI status;
- git state, branches, commits, and diffs;
- runtime configuration and environment behavior;
- security posture, secrets, auth, permissions, and network exposure;
- installer, CLI, worker, or automation behavior.

## Reporting Uncertainty

If a fact cannot be confirmed from available context, say:

```text
I cannot confirm this from the available context.
```

Do not replace missing evidence with confidence.

## Validation Claims

Never say validation passed unless the command was actually run.

Report validation as:

```markdown
Validation:
- Ran: <exact command>
- Result: <passed, failed, or not run with reason>
```

## External Information

If a claim may have changed recently, verify it from a current source before
using it as a basis for engineering work.

## Evidence Review Checklist

Before finalizing meaningful work, check:

- Are important claims backed by file paths, command output, or test results?
- Are assumptions labeled?
- Are unverified facts explicitly marked?
- Are validation commands exact?
- Are limitations and residual risks visible?
```

- [x] **Step 3: Create `engineering/36_task_lifecycle_gates.md`**

Create `engineering/36_task_lifecycle_gates.md` with this content:

```markdown
# Task Lifecycle Gates

Non-trivial engineering work must move through explicit gates. The amount of
ceremony scales with risk.

## Gate 1: Scope

Before acting, identify:

- requested outcome;
- affected behavior;
- constraints;
- unclear assumptions;
- expected artifact.

Ask only when ambiguity blocks correct work.

## Gate 2: Inspection

Before editing, inspect relevant files:

- project layout;
- dependency and validation files;
- existing implementation patterns;
- tests near the change;
- docs or installer behavior when public commands change.

Do not infer project shape when files can be read.

## Gate 3: Plan

For small changes, use a short inline plan.

For multi-step work, write or follow a task plan with:

- target files;
- behavior changes;
- validation;
- risks;
- commit slices.

## Gate 4: Implementation

Implement the smallest correct change.

Rules:

- preserve existing boundaries;
- avoid unrelated refactors;
- avoid hidden side effects;
- do not add dependencies without a reason;
- do not use task notes as fake implementation.

## Gate 5: Validation

Run the best available validation:

- focused tests;
- full validation when behavior or shared tooling changes;
- static checks;
- manual verification only when automated checks are unavailable.

Report exact commands.

## Gate 6: Review And Risk

Before completion, identify:

- changed behavior;
- failure modes covered;
- tests added or updated;
- docs updated or not needed;
- remaining risks.

## Proportionality

Small read-only answer:

- evidence check;
- direct answer.

Small code change:

- inspect file;
- edit;
- focused validation;
- concise report.

Multi-file or behavior change:

- plan;
- implementation slices;
- validation;
- review gate;
- risk report.
```

- [x] **Step 4: Create `engineering/37_review_regression_gates.md`**

Create `engineering/37_review_regression_gates.md` with this content:

```markdown
# Review And Regression Gates

Review is a correctness tool. It is not a decorative approval ritual.

## Diff-Risk Review

For meaningful changes, review the diff for:

- public behavior changes;
- changed command or API contracts;
- persistence, config, installer, or runtime effects;
- security and secret handling;
- error handling and failure modes;
- compatibility with existing users;
- documentation impact.

## Regression Coverage

When fixing a defect, add coverage for the defect class when practical.

Good regression tests:

- fail before the fix;
- pass after the fix;
- verify behavior instead of implementation trivia;
- include the risky boundary where the defect happened.

## Review Output

A useful review says:

- what was checked;
- what evidence was used;
- whether there are Critical, Important, Minor, or Suggestion findings;
- what remains risky.

## Completion Gate

Before finishing, confirm:

- relevant tests passed;
- changed commands or docs were exercised;
- installer or runtime boundary changes were checked;
- no known blocking review findings remain;
- residual risks are reported.
```

- [x] **Step 5: Create `engineering/38_library_drift_audit.md`**

Create `engineering/38_library_drift_audit.md` with this content:

```markdown
# Library Drift Audit

Engineering Bible is useful only if instructions, skills, scripts, manifests,
installer behavior, and validation agree.

## Drift Classes

Audit should catch:

- a document exists but is not indexed;
- a skill exists but is not installed or validated;
- a command exists but is missing from `MANIFEST.md`;
- an installer copies files but validation does not require them;
- routing references a missing skill;
- docs describe behavior not implemented by scripts;
- runtime or secret-like files enter the portable tree.

## Audit Behavior

Audit commands must:

- read repository files directly;
- report all detected drift issues in one run;
- exit `0` when clean;
- exit `1` when drift exists;
- print actionable messages.

## Required Output Shape

Passing audit:

```text
quality audit passed
- engineering index: ok
- skill references: ok
- validation tree: ok
- manifest: ok
- installer: ok
- golden cases: ok
- runtime boundary: ok
```

Failing audit:

```text
quality audit failed
missing engineering index entry: engineering/35_evidence_contract.md
missing validation required file: skills/quality-gates/SKILL.md
```

## Runtime Boundary

The portable tree must not contain:

- `.env` files;
- auth files;
- `config.toml`;
- private keys;
- certificates;
- provider credentials;
- local worker state.
```

- [x] **Step 6: Update `engineering/README.md`**

In `engineering/README.md`, add these items after `34_evolution_decision_tree.md` in the expansion list:

```markdown
- `35_evidence_contract.md` - evidence requirements, validation claims, uncertainty, and source-backed engineering statements.
- `36_task_lifecycle_gates.md` - proportional scope, inspection, planning, implementation, validation, and reporting gates.
- `37_review_regression_gates.md` - diff-risk review, regression coverage, and completion review contracts.
- `38_library_drift_audit.md` - repository drift classes, audit behavior, output shape, and runtime boundary checks.
```

In the selection rules section, add:

```markdown
- Claims about code, tests, git state, runtime behavior, or external facts: read `35_evidence_contract.md`.
- Multi-step engineering tasks, implementation plans, or validation flow: read `36_task_lifecycle_gates.md`.
- Reviews, bug fixes, regression tests, and completion checks: read `37_review_regression_gates.md`.
- Skill, manifest, installer, validation, or standards-library integrity: read `38_library_drift_audit.md`.
```

- [x] **Step 7: Update `skills/engineering-standards/SKILL.md`**

In `skills/engineering-standards/SKILL.md`, add these references after `engineering/34_evolution_decision_tree.md`:

```markdown
- `engineering/35_evidence_contract.md` — evidence requirements and uncertainty reporting.
- `engineering/36_task_lifecycle_gates.md` — proportional task gates.
- `engineering/37_review_regression_gates.md` — review and regression gates.
- `engineering/38_library_drift_audit.md` — library drift audit contract.
```

- [x] **Step 8: Update `skills/workflow-router/SKILL.md`**

In `skills/workflow-router/SKILL.md`, in the general implementation routing bullet, include `quality-gates` before `engineering-standards`:

```markdown
- General implementation, bug fixing, debugging, refactoring, documentation,
  performance work, or language/ecosystem-specific engineering -> select the
  smallest applicable engineering skills:
  `quality-gates`, `engineering-standards`, `core-engineering`, `debugging`,
  `testing-tdd`, `code-quality`, `architecture-principles`, `refactoring`,
  `documentation`, `performance`, and the relevant ecosystem skill (`python`,
  `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`, or `esp32`).
```

Add this bullet after the broad standards bullet:

```markdown
- Evidence, validation claims, task lifecycle, completion review, regression
  gates, or repository drift concerns -> `quality-gates`.
```

- [x] **Step 9: Run frontmatter validation**

Run:

```bash
python3 scripts/validate-skill-frontmatter.py skills
```

Expected output includes:

```text
skill frontmatter validation passed
```

- [x] **Step 10: Commit Task 1**

Run:

```bash
git add skills/quality-gates/SKILL.md engineering/35_evidence_contract.md engineering/36_task_lifecycle_gates.md engineering/37_review_regression_gates.md engineering/38_library_drift_audit.md engineering/README.md skills/engineering-standards/SKILL.md skills/workflow-router/SKILL.md
git commit -m "docs: add quality gate references"
```

## Task 2: Add Quality Audit Engine And Tests

**Files:**

- Create: `scripts/audit-quality-gates.py`
- Create: `tests/test_quality_audit.py`
- Create: `tests/quality-gates/hallucinated-test-result.md`
- Create: `tests/quality-gates/skipped-inspection.md`
- Create: `tests/quality-gates/skipped-validation.md`
- Create: `tests/quality-gates/weak-review.md`
- Create: `tests/quality-gates/stale-routing-reference.md`
- Create: `tests/quality-gates/missing-manifest-entry.md`
- Modify: `scripts/validate-skill-tree.sh`
- Modify: `scripts/install-codex.sh`
- Modify: `MANIFEST.md`

- [x] **Step 1: Create the golden quality-gate corpus**

Create `tests/quality-gates/hallucinated-test-result.md`:

```markdown
# Hallucinated Test Result

## Failure

The agent says tests passed without running a validation command.

## Expected gate

Evidence Contract requires the exact command and result. If the command was not
run, the agent must report validation as not run with a reason.
```

Create `tests/quality-gates/skipped-inspection.md`:

```markdown
# Skipped Inspection

## Failure

The agent edits repository files without first inspecting relevant existing
files, patterns, and validation setup.

## Expected gate

Task Lifecycle Gates require inspection before non-trivial edits.
```

Create `tests/quality-gates/skipped-validation.md`:

```markdown
# Skipped Validation

## Failure

The agent completes a behavior change without running tests, audit, or a clear
manual validation substitute.

## Expected gate

Task Lifecycle Gates require exact validation reporting before completion.
```

Create `tests/quality-gates/weak-review.md`:

```markdown
# Weak Review

## Failure

The agent says a diff looks good without checking behavior, regression class,
docs impact, installer impact, or runtime boundary.

## Expected gate

Review And Regression Gates require diff-risk review and residual risk
reporting for meaningful changes.
```

Create `tests/quality-gates/stale-routing-reference.md`:

```markdown
# Stale Routing Reference

## Failure

A router or skill references a downstream skill that does not exist in the
portable tree.

## Expected gate

Library Drift Audit requires routing references to stay aligned with available
skills.
```

Create `tests/quality-gates/missing-manifest-entry.md`:

```markdown
# Missing Manifest Entry

## Failure

A new command entry point is added but `MANIFEST.md` does not list it.

## Expected gate

Library Drift Audit requires command entry points and manifests to agree.
```

- [x] **Step 2: Create failing audit tests**

Create `tests/test_quality_audit.py` with this content:

```python
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit-quality-gates.py"


def copy_repo(target: Path) -> Path:
    repo = target / "repo"

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__"}
        return {name for name in names if name in ignored or name.endswith(".pyc")}

    shutil.copytree(ROOT, repo, ignore=ignore)
    return repo


def run_audit(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / "audit-quality-gates.py"), str(repo)],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class QualityAuditTests(unittest.TestCase):
    def test_audit_passes_current_repository(self) -> None:
        result = subprocess.run(
            [sys.executable, str(AUDIT), str(ROOT)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("quality audit passed", result.stdout)
        self.assertIn("- engineering index: ok", result.stdout)
        self.assertIn("- runtime boundary: ok", result.stdout)

    def test_missing_engineering_index_entry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            index = repo / "engineering" / "README.md"
            index.write_text(
                index.read_text().replace(
                    "- `35_evidence_contract.md` - evidence requirements, validation claims, uncertainty, and source-backed engineering statements.\n",
                    "",
                )
            )
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "missing engineering index entry: engineering/35_evidence_contract.md",
            result.stdout,
        )

    def test_missing_quality_skill_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            (repo / "skills" / "quality-gates" / "SKILL.md").unlink()
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing required file: skills/quality-gates/SKILL.md", result.stdout)

    def test_missing_validation_tree_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            validation = repo / "scripts" / "validate-skill-tree.sh"
            validation.write_text(
                validation.read_text().replace('  "skills/quality-gates/SKILL.md"\n', "")
            )
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "missing validation required file: skills/quality-gates/SKILL.md",
            result.stdout,
        )

    def test_manifest_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            manifest = repo / "MANIFEST.md"
            manifest.write_text(
                manifest.read_text().replace("- `scripts/audit-quality-gates.py`\n", "")
            )
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "missing manifest entry: scripts/audit-quality-gates.py",
            result.stdout,
        )

    def test_forbidden_runtime_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            (repo / ".env").write_text("TOKEN=secret\n")
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn("forbidden runtime file: .env", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 3: Run audit tests and verify expected failure**

Run:

```bash
python3 -m unittest tests/test_quality_audit.py -v
```

Expected: failure because `scripts/audit-quality-gates.py` does not exist yet.

- [x] **Step 4: Create `scripts/audit-quality-gates.py`**

Create `scripts/audit-quality-gates.py` with this content:

```python
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
            if path.name not in index:
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
```

- [x] **Step 5: Make the audit script executable**

Run:

```bash
chmod +x scripts/audit-quality-gates.py
```

- [x] **Step 6: Update `scripts/validate-skill-tree.sh`**

In `scripts/validate-skill-tree.sh`, add these required files in the existing `required_files` array:

```bash
  "scripts/audit-quality-gates.py"
  "skills/quality-gates/SKILL.md"
  "engineering/35_evidence_contract.md"
  "engineering/36_task_lifecycle_gates.md"
  "engineering/37_review_regression_gates.md"
  "engineering/38_library_drift_audit.md"
  "tests/test_quality_audit.py"
  "tests/quality-gates/hallucinated-test-result.md"
  "tests/quality-gates/skipped-inspection.md"
  "tests/quality-gates/skipped-validation.md"
  "tests/quality-gates/weak-review.md"
  "tests/quality-gates/stale-routing-reference.md"
  "tests/quality-gates/missing-manifest-entry.md"
```

- [x] **Step 7: Update `scripts/install-codex.sh`**

In the `skills=(` array in `scripts/install-codex.sh`, add:

```bash
  quality-gates
```

After:

```bash
run chmod +x "$codex_home/scripts/be.py"
```

add:

```bash
run chmod +x "$codex_home/scripts/audit-quality-gates.py"
```

- [x] **Step 8: Update `MANIFEST.md`**

In `MANIFEST.md`, under `## Command Entry Points`, add:

```markdown
- `scripts/audit-quality-gates.py`
```

Under `## Primary Skills`, add:

```markdown
- `quality-gates`
```

- [x] **Step 9: Run audit tests**

Run:

```bash
python3 -m unittest tests/test_quality_audit.py -v
```

Expected output includes:

```text
Ran 6 tests
OK
```

- [x] **Step 10: Run the audit script directly**

Run:

```bash
python3 scripts/audit-quality-gates.py .
```

Expected output:

```text
quality audit passed
- engineering index: ok
- skill references: ok
- validation tree: ok
- manifest: ok
- installer: ok
- golden cases: ok
- runtime boundary: ok
```

- [x] **Step 11: Run shell and tree validation**

Run:

```bash
bash -n scripts/install-codex.sh scripts/validate-skill-tree.sh
bash scripts/validate-skill-tree.sh .
```

Expected output includes:

```text
skill tree validation passed
```

- [x] **Step 12: Commit Task 2**

Run:

```bash
git add scripts/audit-quality-gates.py tests/test_quality_audit.py tests/quality-gates scripts/validate-skill-tree.sh scripts/install-codex.sh MANIFEST.md
git commit -m "test: add quality gate audit"
```

## Task 3: Add `be audit`

**Files:**

- Modify: `scripts/be.py`
- Modify: `tests/test_be_cli.py`

- [x] **Step 1: Add failing CLI test for `be audit`**

In `tests/test_be_cli.py`, add this test before the final `if __name__ == "__main__":` block:

```python
    def test_audit_runs_quality_gate_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("audit", tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("quality audit passed", result.stdout)
        self.assertIn("- runtime boundary: ok", result.stdout)
```

- [x] **Step 2: Run the new CLI test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_be_cli.BeCliTests.test_audit_runs_quality_gate_checks -v
```

Expected: failure because `be` does not yet define the `audit` subcommand.

- [x] **Step 3: Add audit command implementation**

In `scripts/be.py`, after `command_install`, add:

```python
def command_audit(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    require_repo_file(paths, "scripts/audit-quality-gates.py")
    return run_command(
        ["python3", "scripts/audit-quality-gates.py", str(paths.repo_root)],
        cwd=paths.repo_root,
    )
```

In `build_parser()`, after the install subparser block, add:

```python
    audit = subparsers.add_parser("audit", help="Audit Engineering Bible quality gates")
    audit.set_defaults(func=command_audit)
```

- [x] **Step 4: Run the targeted CLI test**

Run:

```bash
python3 -m unittest tests.test_be_cli.BeCliTests.test_audit_runs_quality_gate_checks -v
```

Expected output includes:

```text
OK
```

- [x] **Step 5: Run all CLI tests**

Run:

```bash
python3 -m unittest tests/test_be_cli.py -v
```

Expected output includes:

```text
OK
```

- [x] **Step 6: Commit Task 3**

Run:

```bash
git add scripts/be.py tests/test_be_cli.py
git commit -m "feat: add be audit"
```

## Task 4: Add Make And Documentation Integration

**Files:**

- Modify: `Makefile`
- Modify: `README.md`
- Modify: `README.ru.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/oss-release-checklist.md`

- [x] **Step 1: Update Makefile `.PHONY`**

Replace the `.PHONY` line in `Makefile` with:

```make
.PHONY: help validate validate-tree validate-skills size secrets shell-syntax py-compile audit be-smoke quality-audit-tests dry-run install install-command
```

- [x] **Step 2: Update Makefile help**

In the `help` target, add this line after the `make validate` line:

```make
		'  make audit             Run quality gate repository audit' \
```

Add this line after the `make be-smoke` line:

```make
		'  make quality-audit-tests Run quality audit regression tests' \
```

- [x] **Step 3: Include audit in validation**

Replace:

```make
validate: validate-tree validate-skills size secrets shell-syntax py-compile be-smoke
```

with:

```make
validate: validate-tree validate-skills size secrets shell-syntax py-compile audit be-smoke quality-audit-tests
```

- [x] **Step 4: Add audit targets**

After the `py-compile` target, add:

```make
audit:
	$(PYTHON) scripts/audit-quality-gates.py .

quality-audit-tests:
	$(PYTHON) -m unittest tests/test_quality_audit.py -v
```

- [x] **Step 5: Update README commands**

In `README.md`, in the initial `be` commands block, add:

```bash
be audit
```

In the validate section, after the `make validate` block, add:

````markdown
Run only the quality gate audit:

```bash
make audit
```
````

- [x] **Step 6: Update Russian README commands**

In `README.ru.md`, in the initial `be` commands block, add:

```bash
be audit
```

In the validate section, after the `make validate` block, add:

````markdown
Запустить только quality gate audit:

```bash
make audit
```
````

- [x] **Step 7: Update expanded validation docs**

In `CONTRIBUTING.md` and `docs/oss-release-checklist.md`, add these commands after Python compilation:

```bash
python3 scripts/audit-quality-gates.py .
python3 -m unittest tests/test_quality_audit.py -v
```

Keep the existing `python3 -m unittest tests/test_be_cli.py -v` line.

- [x] **Step 8: Run Make targets**

Run:

```bash
make audit
make quality-audit-tests
make validate
```

Expected outputs include:

```text
quality audit passed
OK
```

- [x] **Step 9: Run docs diff check**

Run:

```bash
git diff --check -- Makefile README.md README.ru.md CONTRIBUTING.md docs/oss-release-checklist.md
```

Expected: no output and exit code `0`.

- [x] **Step 10: Commit Task 4**

Run:

```bash
git add Makefile README.md README.ru.md CONTRIBUTING.md docs/oss-release-checklist.md
git commit -m "docs: document quality gate audit"
```

## Task 5: Final Verification

**Files:**

- Verify: full repository

- [x] **Step 1: Run full validation**

Run:

```bash
make validate
```

Expected output includes:

```text
quality audit passed
OK
```

- [x] **Step 2: Run direct commands**

Run:

```bash
python3 scripts/audit-quality-gates.py .
python3 scripts/be.py audit
python3 scripts/be.py validate --checkout .
```

Expected:

- `audit-quality-gates.py` exits `0` and prints `quality audit passed`.
- `be audit` exits `0` and prints `quality audit passed`.
- `be validate --checkout .` exits `0`.

- [x] **Step 3: Run focused failure-mode check**

Run:

```bash
python3 -m unittest tests.test_quality_audit.QualityAuditTests.test_missing_engineering_index_entry_fails -v
```

Expected output includes:

```text
OK
```

- [x] **Step 4: Check repository status**

Run:

```bash
git status --short --branch
```

Expected: no unstaged changes remain.

- [x] **Step 5: Request final code review**

Dispatch a final reviewer over the implementation range. The reviewer should check:

- spec alignment;
- audit correctness;
- test coverage;
- installer and manifest integration;
- runtime boundary;
- no deferred scope added.

Fix Critical and Important findings before finishing.

## Plan Self-Review Notes

- Spec coverage: tasks cover the quality-gates skill, docs 35-38, audit script, golden cases, `be audit`, `make audit`, validation integration, docs, manifest, installer, and tests.
- Deferred scope remains deferred: no JSON audit output, LLM eval runner, release automation, or severity policy engine.
- Runtime boundary is preserved: no local config, auth, secret, or worker state files are created.
- File boundaries are focused: docs define the contract, `quality-gates` routes behavior, `audit-quality-gates.py` enforces repository drift checks, CLI/Make only delegate to the audit engine.
