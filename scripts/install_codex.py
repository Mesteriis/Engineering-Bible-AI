#!/usr/bin/env python3
"""Install Engineering Bible AI into Codex and agent skill roots."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
import filecmp
import os
from pathlib import Path
import shutil
import shlex
import stat
import sys

from registry import RegistryError, load_registry, selected_skills


IGNORE_DIRS = {".git", ".worktrees", "__pycache__"}
IGNORE_SUFFIXES = {".pyc", ".pyo"}
EXECUTABLES = {
    "scripts/be.py",
    "scripts/check-file-size.py",
    "scripts/install-codex.sh",
    "scripts/audit-quality-gates.py",
    "scripts/install.sh",
    "scripts/install_codex.py",
    "scripts/registry.py",
    "scripts/secret-sanity.sh",
    "scripts/validate-installed-tree.sh",
    "scripts/validate-repo-tree.sh",
    "scripts/validate-router-cases.py",
    "scripts/validate-skill-frontmatter.py",
    "scripts/validate-skill-tree.sh",
}


class InstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class CopyPlan:
    source: Path | None
    target: Path
    relative: str
    kind: str
    content: bytes | None = None
    executable: bool = False


@dataclass(frozen=True)
class PlannedAction:
    plan: CopyPlan
    status: str


@dataclass(frozen=True)
class InstallerOptions:
    repo_root: Path
    codex_home: Path
    agents_home: Path
    bin_dir: Path
    dry_run: bool
    backup_only: bool
    no_overwrite: bool
    force: bool
    diff: bool
    groups: list[str]
    all_groups: bool
    backup_dir: Path


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install portable Engineering Bible AI files into local agent homes.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show planned changes without writing")
    mode.add_argument("--install", action="store_true", help="Apply the planned install")
    mode.add_argument("--backup-only", action="store_true", help="Back up existing managed targets only")
    parser.add_argument("--diff", action="store_true", help="Show ADD/UPDATE/CONFLICT/UNCHANGED status")
    parser.add_argument("--no-overwrite", action="store_true", help="Install only missing targets")
    parser.add_argument("--force", action="store_true", help="Overwrite changed managed targets")
    parser.add_argument("--group", action="append", default=[], help="Additional skill group to install")
    parser.add_argument("--all", action="store_true", help="Install every registry group, including optional")
    args = parser.parse_args(argv)

    if args.force and args.no_overwrite:
        parser.error("--force and --no-overwrite are mutually exclusive")
    if not args.install and not args.backup_only:
        args.dry_run = True
    if args.diff:
        args.dry_run = True if not args.install and not args.backup_only else args.dry_run
    return args


def expand_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_options(args: argparse.Namespace) -> InstallerOptions:
    repo_root = Path(__file__).resolve().parents[1]
    codex_home = expand_path(os.environ.get("CODEX_HOME", "~/.codex"))
    agents_home = expand_path(os.environ.get("AGENTS_HOME", "~/.agents"))
    bin_dir = expand_path(os.environ.get("ENGINEERING_BIBLE_BIN_DIR", "~/.local/bin"))
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = codex_home / "backups" / f"engineering-bible-ai-{timestamp}"
    return InstallerOptions(
        repo_root=repo_root,
        codex_home=codex_home,
        agents_home=agents_home,
        bin_dir=bin_dir,
        dry_run=bool(args.dry_run),
        backup_only=bool(args.backup_only),
        no_overwrite=bool(args.no_overwrite),
        force=bool(args.force),
        diff=bool(args.diff),
        groups=list(args.group),
        all_groups=bool(args.all),
        backup_dir=backup_dir,
    )


def mode_label(options: InstallerOptions) -> str:
    if options.backup_only:
        return "--backup-only"
    if options.dry_run:
        return "--dry-run"
    return "--install"


def selected_skill_names(options: InstallerOptions) -> list[str]:
    registry = load_registry(options.repo_root)
    return selected_skills(registry, groups=options.groups, include_all=options.all_groups)


def wrapper_content(codex_home: Path) -> bytes:
    target_script = codex_home / "scripts" / "be.py"
    quoted_target = shlex.quote(str(target_script))
    return f"#!/usr/bin/env bash\nexec python3 {quoted_target} \"$@\"\n".encode()


def build_plan(options: InstallerOptions, skills: list[str]) -> list[CopyPlan]:
    plans: list[CopyPlan] = []

    def add_path(source_relative: str, target: Path, backup_relative: str | None = None) -> None:
        source = options.repo_root / source_relative
        if not source.exists():
            raise InstallError(f"missing source: {source_relative}")
        plans.append(
            CopyPlan(
                source=source,
                target=target,
                relative=backup_relative or source_relative,
                kind="dir" if source.is_dir() else "file",
                executable=source_relative in EXECUTABLES,
            )
        )

    add_path("AGENTS.md", options.codex_home / "AGENTS.md")
    for directory in ("engineering", "reference", "templates", "scripts", "tests"):
        add_path(directory, options.codex_home / directory)

    add_path("skills/registry.yml", options.codex_home / "skills" / "registry.yml")
    add_path("skills/registry.yml", options.agents_home / "skills" / "registry.yml", "agents-skills/registry.yml")

    for skill in skills:
        add_path(f"skills/{skill}", options.codex_home / "skills" / skill)
        add_path(f"skills/{skill}", options.agents_home / "skills" / skill, f"agents-skills/{skill}")

    plans.append(
        CopyPlan(
            source=None,
            target=options.bin_dir / "be",
            relative="bin/be",
            kind="generated-file",
            content=wrapper_content(options.codex_home),
            executable=True,
        )
    )
    return plans


def ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts) or path.suffix in IGNORE_SUFFIXES


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ignored(relative):
            continue
        if path.is_file():
            files.append(relative)
    return sorted(files)


def same_file(source: Path, target: Path) -> bool:
    if source.resolve() == target.resolve():
        return True
    if not target.is_file():
        return False
    return filecmp.cmp(source, target, shallow=False)


def same_dir(source: Path, target: Path) -> bool:
    if source.resolve() == target.resolve():
        return True
    if not target.is_dir():
        return False
    source_files = iter_files(source)
    target_files = iter_files(target)
    if source_files != target_files:
        return False
    return all(
        filecmp.cmp(source / relative, target / relative, shallow=False)
        for relative in source_files
    )


def same_generated(content: bytes, target: Path) -> bool:
    return target.is_file() and target.read_bytes() == content


def plan_status(plan: CopyPlan, options: InstallerOptions) -> str:
    if options.backup_only:
        return "BACKUP" if plan.target.exists() else "MISSING"
    if not plan.target.exists():
        return "ADD"
    if plan.kind == "dir":
        if plan.source is None:
            raise InstallError(f"directory plan has no source: {plan.relative}")
        unchanged = same_dir(plan.source, plan.target)
    elif plan.kind == "generated-file":
        if plan.content is None:
            raise InstallError(f"generated plan has no content: {plan.relative}")
        unchanged = same_generated(plan.content, plan.target)
    else:
        if plan.source is None:
            raise InstallError(f"file plan has no source: {plan.relative}")
        unchanged = same_file(plan.source, plan.target)

    if unchanged:
        return "UNCHANGED"
    if options.no_overwrite:
        return "SKIP"
    return "UPDATE" if options.force else "CONFLICT"


def planned_actions(plans: Iterable[CopyPlan], options: InstallerOptions) -> list[PlannedAction]:
    return [PlannedAction(plan=plan, status=plan_status(plan, options)) for plan in plans]


def backup_target(plan: CopyPlan, options: InstallerOptions) -> None:
    if not plan.target.exists():
        return
    backup_path = options.backup_dir / plan.relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        if backup_path.is_dir():
            shutil.rmtree(backup_path)
        else:
            backup_path.unlink()
    if plan.target.is_dir():
        shutil.copytree(plan.target, backup_path, ignore=copy_ignore)
    else:
        shutil.copy2(plan.target, backup_path)


def copy_ignore(directory: str, names: list[str]) -> set[str]:
    ignored_names: set[str] = set()
    for name in names:
        path = Path(directory, name)
        if name in IGNORE_DIRS or path.suffix in IGNORE_SUFFIXES:
            ignored_names.add(name)
    return ignored_names


def copy_plan(plan: CopyPlan) -> None:
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    if plan.kind == "dir":
        if plan.source is None:
            raise InstallError(f"directory plan has no source: {plan.relative}")
        if plan.target.exists():
            remove_target(plan.target)
        shutil.copytree(plan.source, plan.target, ignore=copy_ignore)
        return

    if plan.kind == "generated-file":
        if plan.content is None:
            raise InstallError(f"generated plan has no content: {plan.relative}")
        if plan.target.exists() and plan.target.is_dir():
            remove_target(plan.target)
        plan.target.write_bytes(plan.content)
    else:
        if plan.source is None:
            raise InstallError(f"file plan has no source: {plan.relative}")
        if plan.target.exists() and plan.target.is_dir():
            remove_target(plan.target)
        shutil.copy2(plan.source, plan.target)

    if plan.executable:
        current_mode = plan.target.stat().st_mode
        plan.target.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def remove_target(target: Path) -> None:
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def print_header(options: InstallerOptions, skills: list[str]) -> None:
    print(f"Repo: {options.repo_root}")
    print(f"Codex home: {options.codex_home}")
    print(f"Agents home: {options.agents_home}")
    print(f"Bin dir: {options.bin_dir}")
    print(f"Mode: {mode_label(options)}")
    print(f"Backup: {options.backup_dir}")
    groups = ", ".join(options.groups) if options.groups else "(default)"
    print(f"Skill groups: {groups}{' + all' if options.all_groups else ''}")
    print("Skills: " + ", ".join(skills))


def print_actions(actions: list[PlannedAction]) -> None:
    for action in actions:
        print(f"{action.status:9} {action.plan.relative} -> {action.plan.target}")


def apply_actions(actions: list[PlannedAction], options: InstallerOptions) -> None:
    if options.dry_run:
        return
    if any(action.status == "CONFLICT" for action in actions):
        conflicts = [action.plan.relative for action in actions if action.status == "CONFLICT"]
        raise InstallError(
            "changed managed target(s) would be overwritten; rerun with --force: "
            + ", ".join(conflicts)
        )

    if options.backup_only:
        for action in actions:
            if action.status == "BACKUP":
                backup_target(action.plan, options)
        return

    for action in actions:
        if action.status == "UPDATE":
            backup_target(action.plan, options)
            copy_plan(action.plan)
        elif action.status == "ADD":
            copy_plan(action.plan)
        elif action.status in {"UNCHANGED", "SKIP"}:
            continue
        elif action.status == "CONFLICT":
            raise InstallError(f"unexpected unresolved conflict: {action.plan.relative}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        options = build_options(args)
        skills = selected_skill_names(options)
        plans = build_plan(options, skills)
        actions = planned_actions(plans, options)
        print_header(options, skills)
        print_actions(actions)
        apply_actions(actions, options)
        print("Done. Restart or open a new agent session to refresh prompt-visible skills.")
        return 0
    except (InstallError, RegistryError) as exc:
        print(f"install-codex: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
