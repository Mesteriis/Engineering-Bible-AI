from __future__ import annotations

import io
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "install.sh"


class BootstrapTests(unittest.TestCase):
    def make_fixture_tree(self, base: Path) -> Path:
        fixture = base / "fixture"
        scripts = fixture / "scripts"
        skills = fixture / "skills"
        scripts.mkdir(parents=True)
        skills.mkdir()
        (fixture / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        (skills / "fixture.txt").write_text("fixture\n", encoding="utf-8")
        (scripts / "install-codex.sh").write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\nprintf 'fixture install:'\nprintf ' %s' \"$@\"\nprintf '\\n'\n",
            encoding="utf-8",
        )
        (scripts / "validate-repo-tree.sh").write_text(
            "#!/usr/bin/env bash\nexit 0\n",
            encoding="utf-8",
        )
        (scripts / "secret-sanity.sh").write_text(
            "#!/usr/bin/env bash\nexit 0\n",
            encoding="utf-8",
        )
        for name in ("validate-skill-frontmatter.py", "validate-router-cases.py"):
            (scripts / name).write_text("raise SystemExit(0)\n", encoding="utf-8")
        return fixture

    def make_archive(
        self,
        base: Path,
        *,
        extra: tarfile.TarInfo | None = None,
        extra_content: bytes = b"",
    ) -> Path:
        fixture = self.make_fixture_tree(base)
        archive = base / "fixture.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            bundle.add(fixture, arcname="fixture-v0.1.0")
            if extra is not None:
                bundle.addfile(extra, io.BytesIO(extra_content) if extra.isfile() else None)
        return archive

    def run_standalone(
        self,
        base: Path,
        *args: str,
        archive: Path | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        standalone_dir = base / "standalone"
        standalone_dir.mkdir()
        script = standalone_dir / "install.sh"
        shutil.copy2(BOOTSTRAP, script)
        downloads = base / "downloads"
        downloads.mkdir()
        env = os.environ.copy()
        env.update(
            {
                "TMPDIR": str(downloads),
                "ENGINEERING_BIBLE_REPO": "example/project",
                "CODEX_HOME": str(base / "codex"),
                "AGENTS_HOME": str(base / "agents"),
                "ENGINEERING_BIBLE_HOME": str(base / "engineering-bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(base / "bin"),
            }
        )
        env.pop("ENGINEERING_BIBLE_ARCHIVE_SHA256", None)
        env.pop("ENGINEERING_BIBLE_REF", None)
        if archive is not None:
            env["ENGINEERING_BIBLE_ARCHIVE_URL"] = archive.as_uri()
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(script), *args],
            cwd=standalone_dir,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_file_fixture_is_safely_extracted_without_network_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            archive = self.make_archive(base)
            result = self.run_standalone(base, "--dry-run", "--ref", "v0.1.0", archive=archive)

            remaining_downloads = list((base / "downloads").iterdir())

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fixture install: --dry-run", result.stdout)
        self.assertEqual(remaining_downloads, [])

    def test_stable_release_manifest_supplies_asset_checksum_and_size(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            archive = self.make_archive(base)
            release_manifest = base / "release-manifest.json"
            release_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version": "0.1.0",
                        "tag": "v0.1.0",
                        "commit": "0" * 40,
                        "artifacts": {
                            archive.name: {
                                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                                "size": archive.stat().st_size,
                            },
                            "engineering-bible-ai-0.1.0.tar.gz": {
                                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                                "size": archive.stat().st_size,
                            },
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            release_archive = base / "engineering-bible-ai-0.1.0.tar.gz"
            shutil.copy2(archive, release_archive)
            result = self.run_standalone(
                base,
                "--dry-run",
                "--ref",
                "v0.1.0",
                extra_env={"ENGINEERING_BIBLE_RELEASE_MANIFEST_URL": release_manifest.as_uri()},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fixture install: --dry-run", result.stdout)

    def test_mutable_ref_requires_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            result = self.run_standalone(base, "--dry-run", "--ref", "main")

        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --allow-unstable", result.stderr)

    def test_checksum_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            archive = self.make_archive(base)
            result = self.run_standalone(
                base,
                "--dry-run",
                "--ref",
                "v0.1.0",
                archive=archive,
                extra_env={"ENGINEERING_BIBLE_ARCHIVE_SHA256": "0" * 64},
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive checksum mismatch", result.stderr)

    def test_path_traversal_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            traversal = tarfile.TarInfo("../escape")
            traversal.size = 4
            archive = self.make_archive(base, extra=traversal, extra_content=b"nope")
            result = self.run_standalone(base, "--dry-run", "--ref", "v0.1.0", archive=archive)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe archive path", result.stderr)
        self.assertFalse((base / "escape").exists())

    def test_symbolic_link_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            link = tarfile.TarInfo("fixture-v0.1.0/link")
            link.type = tarfile.SYMTYPE
            link.linkname = "/tmp/outside"
            archive = self.make_archive(base, extra=link)
            result = self.run_standalone(base, "--dry-run", "--ref", "v0.1.0", archive=archive)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported archive entry type", result.stderr)


if __name__ == "__main__":
    unittest.main()
