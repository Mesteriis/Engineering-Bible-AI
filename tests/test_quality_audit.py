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
        ignored = {".git", ".engineering-bible", ".worktrees", "node_modules", "__pycache__"}
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

    def test_dotenv_variant_runtime_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            (repo / ".env.local").write_text("local fixture only\n")
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn("forbidden runtime file: .env.local", result.stdout)

    def test_root_local_worktree_runtime_is_pruned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            worktree = repo / ".worktrees" / "local"
            worktree.mkdir(parents=True)
            for name in (".env", ".env.local", "auth.json", "config.toml", "deploy.pem"):
                (worktree / name).write_text("local fixture only\n")
            result = run_audit(repo)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("- runtime boundary: ok", result.stdout)
        self.assertNotIn(".worktrees/local/", result.stdout)

    def test_nested_public_worktree_runtime_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            nested = repo / "public" / ".worktrees"
            nested.mkdir(parents=True)
            (nested / "auth.json").write_text("local fixture only\n")
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn("forbidden runtime file: public/.worktrees/auth.json", result.stdout)

    def test_tracked_root_worktree_runtime_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            private = repo / ".worktrees" / "local" / "runtime.json"
            private.parent.mkdir(parents=True)
            private.write_text("{}\n")
            subprocess.run(
                ["git", "-C", str(repo), "add", "-f", ".worktrees/local/runtime.json"],
                check=True,
            )
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn("private runtime path is tracked: .worktrees", result.stdout)

    def test_only_designated_private_runtime_is_pruned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            private = repo / ".engineering-bible" / "implementation" / "upstream" / "node_modules"
            private.mkdir(parents=True)
            (private / ".env").write_text("local fixture only\n")
            dependency = repo / "node_modules"
            dependency.mkdir()
            (dependency / "auth.json").write_text("local fixture only\n")
            dependency_result = run_audit(repo)
            (dependency / "auth.json").unlink()
            nested_private = repo / "public" / ".engineering-bible"
            nested_private.mkdir(parents=True)
            (nested_private / "auth.json").write_text("local fixture only\n")
            nested_result = run_audit(repo)
            (nested_private / "auth.json").unlink()
            result = run_audit(repo)

        self.assertEqual(dependency_result.returncode, 1)
        self.assertIn("forbidden runtime file: node_modules/auth.json", dependency_result.stdout)
        self.assertEqual(nested_result.returncode, 1)
        self.assertIn(
            "forbidden runtime file: public/.engineering-bible/auth.json", nested_result.stdout
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("quality audit passed", result.stdout)

    def test_tracked_private_runtime_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            private = repo / ".engineering-bible" / "runtime.json"
            private.parent.mkdir()
            private.write_text("{}\n")
            subprocess.run(
                ["git", "-C", str(repo), "add", "-f", ".engineering-bible/runtime.json"],
                check=True,
            )
            result = run_audit(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn("private runtime path is tracked: .engineering-bible", result.stdout)

    def test_repo_tree_gate_rejects_tracked_private_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = copy_repo(Path(raw))
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            private = repo / ".engineering-bible"
            private.mkdir(exist_ok=True)
            for index in range(512):
                (private / f"runtime-{index:04d}.json").write_text("{}\n")
            subprocess.run(
                ["git", "-C", str(repo), "add", "-f", ".engineering-bible"],
                check=True,
            )
            result = subprocess.run(
                ["bash", str(repo / "scripts" / "validate-repo-tree.sh"), str(repo)],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("private runtime files are tracked under .engineering-bible", result.stderr)

    def test_secret_sanity_prunes_private_runtime_but_checks_public_tree(self) -> None:
        script = ROOT / "scripts" / "secret-sanity.sh"
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            private = repo / ".engineering-bible" / "upstream"
            private.mkdir(parents=True)
            (private / ".env").write_text("local fixture only\n")
            private_only = subprocess.run(
                [str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            nested_private = repo / "public" / ".engineering-bible"
            nested_private.mkdir(parents=True)
            (nested_private / "auth.json").write_text("local fixture only\n")
            nested_result = subprocess.run(
                [str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            (nested_private / "auth.json").unlink()
            dependency = repo / "node_modules"
            dependency.mkdir()
            suspicious_source = dependency / "package.js"
            synthetic_secret = "sk-" + "Z" * 40
            suspicious_source.write_text(f"const token = '{synthetic_secret}';\n")
            content_result = subprocess.run(
                [str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            suspicious_source.unlink()
            (dependency / "token.json").write_text("local fixture only\n")
            dependency_result = subprocess.run(
                [str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            (dependency / "token.json").unlink()
            (repo / ".env").write_text("local fixture only\n")
            public = subprocess.run(
                [str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(private_only.returncode, 0, private_only.stdout + private_only.stderr)
        self.assertEqual(nested_result.returncode, 1)
        self.assertIn("public/.engineering-bible/auth.json", nested_result.stderr)
        self.assertEqual(content_result.returncode, 1)
        self.assertIn("Secret-looking value found", content_result.stderr)
        self.assertEqual(dependency_result.returncode, 1)
        self.assertIn("node_modules/token.json", dependency_result.stderr)
        self.assertEqual(public.returncode, 1)
        self.assertIn("Secret-like file name found", public.stderr)

    def test_secret_sanity_fails_when_rg_reports_a_scan_error(self) -> None:
        script = ROOT / "scripts" / "secret-sanity.sh"
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            fake_bin = base / "fake-bin"
            fake_bin.mkdir()
            fake_rg = fake_bin / "rg"
            fake_rg.write_text("#!/bin/sh\nexit 2\n")
            fake_rg.chmod(0o755)
            result = subprocess.run(
                [str(script), str(base)],
                env={"PATH": f"{fake_bin}:/usr/bin:/bin:/usr/local/bin"},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Secret content scan failed", result.stderr)

    def test_markdown_style_prunes_private_runtime_and_checks_public_files(self) -> None:
        script = ROOT / "scripts" / "validate-markdown-style.py"
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            private = repo / ".engineering-bible" / "implementation"
            private.mkdir(parents=True)
            (private / "local.md").write_text("# private\tbad\n")
            clean = subprocess.run(
                [sys.executable, str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            nested = repo / "public" / ".engineering-bible"
            nested.mkdir(parents=True)
            (nested / "invalid.md").write_text("# nested\tbad\n")
            nested_result = subprocess.run(
                [sys.executable, str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            (nested / "invalid.md").unlink()
            (repo / "public.md").write_text("# public\tbad\n")
            public = subprocess.run(
                [sys.executable, str(script), str(repo)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        self.assertEqual(nested_result.returncode, 1)
        self.assertIn("public/.engineering-bible/invalid.md", nested_result.stdout)
        self.assertEqual(public.returncode, 1)
        self.assertIn("public.md", public.stdout)


if __name__ == "__main__":
    unittest.main()
