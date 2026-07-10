#!/usr/bin/env python3
"""Install Engineering Bible AI into namespaced and active agent roots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import uuid

from installer_core import InstallError, InstallerOptions, run_install
from registry import RegistryError, load_registry, selected_skills


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install portable Engineering Bible AI files into local agent homes.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show planned changes without writing")
    mode.add_argument("--install", action="store_true", help="Apply the planned install")
    mode.add_argument(
        "--backup-only", action="store_true", help="Back up existing managed targets only"
    )
    parser.add_argument("--diff", action="store_true", help="Show planned status for each file")
    parser.add_argument("--no-overwrite", action="store_true", help="Install only missing targets")
    parser.add_argument(
        "--force", action="store_true", help="Replace changed manifest-owned targets"
    )
    parser.add_argument(
        "--group", action="append", default=[], help="Additional skill group to install"
    )
    parser.add_argument(
        "--all", action="store_true", help="Install every registry group, including optional"
    )
    parser.add_argument(
        "--migrate-legacy",
        action="store_true",
        help="Adopt byte- and mode-identical legacy files into the ownership manifest",
    )
    parser.add_argument(
        "--prompt-profile",
        choices=("full", "minimal"),
        default="full",
        help="Global instruction profile to activate (default: full)",
    )
    parser.add_argument(
        "--install-tools",
        action="store_true",
        help="Install optional companion CLI tools after the portable files",
    )
    args = parser.parse_args(argv)

    if args.force and args.no_overwrite:
        parser.error("--force and --no-overwrite are mutually exclusive")
    if args.install_tools:
        parser.error(
            "--install-tools is deprecated; use be tools install with an explicit selector"
        )
    if args.migrate_legacy and args.backup_only:
        parser.error("--migrate-legacy cannot be combined with --backup-only")
    if not args.install and not args.backup_only:
        args.dry_run = True
    if args.diff and not args.install and not args.backup_only:
        args.dry_run = True
    return args


def expand_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_options(args: argparse.Namespace) -> InstallerOptions:
    repo_root = Path(__file__).resolve().parents[1]
    codex_home = expand_path(os.environ.get("CODEX_HOME", "~/.codex"))
    agents_home = expand_path(os.environ.get("AGENTS_HOME", "~/.agents"))
    be_home = expand_path(
        os.environ.get("ENGINEERING_BIBLE_HOME", str(codex_home / "engineering-bible"))
    )
    bin_dir = expand_path(os.environ.get("ENGINEERING_BIBLE_BIN_DIR", "~/.local/bin"))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = be_home / "backups" / f"{timestamp}-{uuid.uuid4().hex[:12]}"
    return InstallerOptions(
        repo_root=repo_root,
        codex_home=codex_home,
        agents_home=agents_home,
        be_home=be_home,
        bin_dir=bin_dir,
        dry_run=bool(args.dry_run),
        backup_only=bool(args.backup_only),
        no_overwrite=bool(args.no_overwrite),
        force=bool(args.force),
        diff=bool(args.diff),
        groups=list(args.group),
        all_groups=bool(args.all),
        install_tools=bool(args.install_tools),
        migrate_legacy=bool(args.migrate_legacy),
        prompt_profile=str(args.prompt_profile),
        backup_dir=backup_dir,
    )


def selected_skill_names(options: InstallerOptions) -> list[str]:
    registry = load_registry(options.repo_root)
    return selected_skills(registry, groups=options.groups, include_all=options.all_groups)


def run_tool_installer(options: InstallerOptions) -> None:
    if not options.install_tools:
        return
    script = options.repo_root / "scripts" / "install-tools.sh"
    if not script.is_file():
        raise InstallError("core install committed; missing optional tool installer")
    mode = "--dry-run" if options.dry_run else "--install"
    sys.stdout.flush()
    sys.stderr.flush()
    result = subprocess.run(["bash", str(script), mode], cwd=options.repo_root, check=False)
    if result.returncode != 0:
        prefix = "core install committed; " if not options.dry_run else ""
        raise InstallError(
            f"{prefix}optional tool installer failed with exit code {result.returncode}"
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        options = build_options(args)
        skills = selected_skill_names(options)
        run_install(options, skills)
        run_tool_installer(options)
        print("Done. Restart or open a new agent session to refresh prompt-visible skills.")
        return 0
    except (InstallError, RegistryError) as exc:
        print(f"install-codex: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
