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
                    "- `engineering/35_evidence_contract.md` - evidence requirements, validation claims, uncertainty, and source-backed engineering statements.\n",
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
