from __future__ import annotations

from dataclasses import replace
import hashlib
import io
from pathlib import Path
import stat
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from scripts.upstream_catalog import NoticeSpec, SourceSpec, UpstreamError
from scripts.upstream_sources import fingerprint_tree, stage_source


REVISION = "a" * 40
PREFIX = "skills-" + REVISION
LICENSE = b"MIT fixture license\n"


def source() -> SourceSpec:
    return SourceSpec(
        "author",
        "https://github.com/author/skills",
        REVISION,
        "main",
        "MIT",
        hashlib.sha256(LICENSE).hexdigest(),
    )


def archive(entries: list[tuple[str, bytes | None, int, bytes]]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as bundle:
        for name, data, mode, kind in entries:
            member = tarfile.TarInfo(name)
            member.mode = mode
            member.type = kind
            if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                member.linkname = "../../outside"
            if data is not None:
                member.size = len(data)
            bundle.addfile(member, io.BytesIO(data) if data is not None else None)
    return output.getvalue()


def valid_entries() -> list[tuple[str, bytes | None, int, bytes]]:
    return [
        (PREFIX + "/LICENSE", LICENSE, 0o644, tarfile.REGTYPE),
        (
            PREFIX + "/skills/general/sample/SKILL.md",
            b"---\nname: sample\n---\n",
            0o644,
            tarfile.REGTYPE,
        ),
        (
            PREFIX + "/skills/general/sample/scripts/check.sh",
            b"#!/bin/sh\nexit 0\n",
            0o755,
            tarfile.REGTYPE,
        ),
    ]


class UpstreamSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def stage(self, entries: list, reviewed_source: SourceSpec | None = None) -> Path:
        response = io.BytesIO(archive(entries))
        with patch("scripts.upstream_sources.urlopen", return_value=response):
            return stage_source(reviewed_source or source(), self.root / "staged")

    def test_declared_provider_root_preserves_complete_leaf_and_excludes_config(self) -> None:
        reviewed = replace(source(), skill_roots=(".claude/skills",))
        entries = [
            (
                name.replace("/skills/", "/.claude/skills/"),
                data,
                mode,
                kind,
            )
            for name, data, mode, kind in valid_entries()
        ] + [
            (PREFIX + "/.claude/auth.json", b"excluded config", 0o644, tarfile.REGTYPE),
            (PREFIX + "/.claude/settings.json", b"excluded config", 0o644, tarfile.REGTYPE),
            (PREFIX + "/.claude/skills-extra/unsafe", None, 0o644, tarfile.SYMTYPE),
            (PREFIX + "/skills/other/SKILL.md", b"unselected build", 0o644, tarfile.REGTYPE),
            (
                PREFIX + "/.claude/skills/general/sample/data/styles.csv",
                b"name,value\noriginal,dense\n",
                0o644,
                tarfile.REGTYPE,
            ),
        ]
        root = self.stage(entries, reviewed)
        tree = root / ".claude/skills/general/sample"
        self.assertEqual((tree / "scripts/check.sh").read_bytes(), b"#!/bin/sh\nexit 0\n")
        self.assertEqual(stat.S_IMODE((tree / "scripts/check.sh").stat().st_mode), 0o755)
        self.assertEqual((tree / "data/styles.csv").read_bytes(), b"name,value\noriginal,dense\n")
        self.assertFalse((root / ".claude/auth.json").exists())
        self.assertFalse((root / ".claude/settings.json").exists())
        self.assertFalse((root / ".claude/skills-extra").exists())
        self.assertFalse((root / "skills").exists())

    def test_reviewed_notices_are_preserved_at_original_paths(self) -> None:
        notice = b"Original third-party attribution\n"
        reviewed = replace(
            source(),
            notices=(NoticeSpec("legal/NOTICE.md", hashlib.sha256(notice).hexdigest()),),
        )
        root = self.stage(
            valid_entries()
            + [(PREFIX + "/legal/NOTICE.md", notice, 0o644, tarfile.REGTYPE)]
            + [(PREFIX + "/legal/unreviewed.md", b"excluded", 0o644, tarfile.REGTYPE)],
            reviewed,
        )
        self.assertEqual((root / "legal/NOTICE.md").read_bytes(), notice)
        self.assertFalse((root / "legal/unreviewed.md").exists())

    def test_notice_mismatch_missing_link_or_runtime_file_never_activates(self) -> None:
        reviewed = replace(source(), notices=(NoticeSpec("NOTICE.md", "b" * 64),))
        for entries in (
            valid_entries(),
            valid_entries() + [(PREFIX + "/NOTICE.md", b"wrong", 0o644, tarfile.REGTYPE)],
            valid_entries() + [(PREFIX + "/NOTICE.md", None, 0o644, tarfile.SYMTYPE)],
        ):
            with self.subTest(entries=entries), self.assertRaises(UpstreamError):
                self.stage(entries, reviewed)
            self.assertFalse((self.root / "staged").exists())
        reviewed = replace(source(), skill_roots=(".agents/skills",))
        for name, kind in (("auth.json", tarfile.REGTYPE), ("unsafe", tarfile.SYMTYPE)):
            with self.subTest(name=name), self.assertRaises(UpstreamError):
                self.stage(
                    valid_entries()
                    + [(PREFIX + "/.agents/skills/sample/" + name, b"unsafe", 0o644, kind)],
                    reviewed,
                )
            self.assertFalse((self.root / "staged").exists())

    def test_file_fidelity_modes_and_selective_extraction(self) -> None:
        entries = valid_entries() + [
            (PREFIX + "/AGENTS.md", None, 0o777, tarfile.SYMTYPE),
            (PREFIX + "/CLAUDE.md", b"repo instructions", 0o644, tarfile.REGTYPE),
        ]
        root = self.stage(entries)
        self.assertEqual((root / "LICENSE").read_bytes(), LICENSE)
        self.assertEqual(
            (root / "skills/general/sample/scripts/check.sh").read_bytes(), b"#!/bin/sh\nexit 0\n"
        )
        self.assertEqual(
            stat.S_IMODE((root / "skills/general/sample/scripts/check.sh").stat().st_mode), 0o755
        )
        self.assertFalse((root / "AGENTS.md").exists())
        self.assertFalse((root / "CLAUDE.md").exists())

    def test_links_and_special_files_within_extracted_scope_are_rejected(self) -> None:
        for kind in [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE]:
            with self.subTest(kind=kind), self.assertRaises(UpstreamError):
                self.stage(
                    valid_entries()
                    + [(PREFIX + "/skills/general/sample/unsafe", None, 0o644, kind)]
                )
            self.assertFalse((self.root / "staged").exists())

    def test_traversal_is_rejected_even_outside_extracted_scope(self) -> None:
        for name in [
            "../outside",
            "/outside",
            PREFIX + "/../../outside",
            PREFIX + "/skills\\outside",
            PREFIX + "/skills//outside",
        ]:
            with self.subTest(name=name), self.assertRaises(UpstreamError):
                self.stage(valid_entries() + [(name, b"x", 0o644, tarfile.REGTYPE)])
            self.assertFalse((self.root / "staged").exists())

    def test_wrong_revision_prefix_duplicate_and_license_mismatch_rejected(self) -> None:
        bad_cases = [
            [
                (name.replace(REVISION, "b" * 40), data, mode, kind)
                for name, data, mode, kind in valid_entries()
            ],
            valid_entries() + [valid_entries()[0]],
            [
                (name, b"wrong" if name.endswith("/LICENSE") else data, mode, kind)
                for name, data, mode, kind in valid_entries()
            ],
        ]
        for entries in bad_cases:
            with self.assertRaises(UpstreamError):
                self.stage(entries)
            self.assertFalse((self.root / "staged").exists())

    def test_existing_destination_is_not_overwritten(self) -> None:
        destination = self.root / "staged"
        destination.mkdir()
        (destination / "custom").write_text("preserve")
        with self.assertRaises(UpstreamError):
            self.stage(valid_entries())
        self.assertEqual((destination / "custom").read_text(), "preserve")

    def test_archive_transport_permissions_use_canonical_git_modes(self) -> None:
        entries = [(name, data, mode | 0o020, kind) for name, data, mode, kind in valid_entries()]
        root = self.stage(entries)
        self.assertEqual(
            stat.S_IMODE((root / "skills/general/sample/SKILL.md").stat().st_mode), 0o644
        )
        self.assertEqual(
            stat.S_IMODE((root / "skills/general/sample/scripts/check.sh").stat().st_mode), 0o755
        )

    def test_fingerprint_uses_path_bytes_and_modes(self) -> None:
        tree = self.root / "tree"
        tree.mkdir()
        file = tree / "SKILL.md"
        file.write_bytes(b"skill")
        file.chmod(0o644)
        expected = hashlib.sha256(
            b"SKILL.md\0000o644\0" + hashlib.sha256(b"skill").hexdigest().encode() + b"\n"
        ).hexdigest()
        self.assertEqual(fingerprint_tree(tree), expected)
        file.chmod(0o755)
        self.assertNotEqual(fingerprint_tree(tree), expected)

    def test_fingerprint_rejects_links_and_runtime_files(self) -> None:
        for name in [".env", ".env.production", "auth.json", "id_rsa", "runtime/capabilities.json"]:
            tree = self.root / name.replace("/", "-")
            tree.mkdir()
            file = tree / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b"unsafe")
            with self.assertRaises(UpstreamError):
                fingerprint_tree(tree)
        tree = self.root / "linked"
        tree.mkdir()
        (tree / "link").symlink_to(self.root)
        with self.assertRaises(UpstreamError):
            fingerprint_tree(tree)

    def test_extraction_is_bounded(self) -> None:
        with (
            patch("scripts.upstream_sources.MAX_ARCHIVE_BYTES", 10),
            self.assertRaises(UpstreamError),
        ):
            self.stage(valid_entries())
        self.assertFalse((self.root / "staged").exists())

    def test_member_file_and_expanded_size_limits(self) -> None:
        for constant, maximum in [
            ("MAX_MEMBERS", 2),
            ("MAX_FILE_BYTES", 5),
            ("MAX_EXTRACTED_BYTES", 5),
        ]:
            with (
                patch("scripts.upstream_sources." + constant, maximum),
                self.assertRaises(UpstreamError),
            ):
                self.stage(valid_entries())
            self.assertFalse((self.root / "staged").exists())

    def test_privileged_mode_and_runtime_payload_fail_before_activation(self) -> None:
        for name, mode in [("helper.sh", 0o4755), (".env", 0o644), ("auth.json", 0o644)]:
            with self.assertRaises(UpstreamError):
                self.stage(
                    valid_entries()
                    + [
                        (
                            PREFIX + "/skills/general/sample/" + name,
                            b"unsafe",
                            mode,
                            tarfile.REGTYPE,
                        )
                    ]
                )
            self.assertFalse((self.root / "staged").exists())

    def test_failed_download_and_invalid_tar_have_clear_errors(self) -> None:
        with (
            patch("scripts.upstream_sources.urlopen", side_effect=OSError("transport unavailable")),
            self.assertRaises(UpstreamError),
        ):
            stage_source(source(), self.root / "staged")
        with (
            patch("scripts.upstream_sources.urlopen", return_value=io.BytesIO(b"invalid tar")),
            self.assertRaises(UpstreamError),
        ):
            stage_source(source(), self.root / "staged")
        self.assertFalse((self.root / "staged").exists())


if __name__ == "__main__":
    unittest.main()
