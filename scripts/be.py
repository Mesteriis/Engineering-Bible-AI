#!/usr/bin/env python3
"""Engineering Bible AI command-line manager."""

from __future__ import annotations

import argparse
import json
import re
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


TOOL_VERSION = "0.1.0"
BOOTSTRAP_INSTALL_URL = "https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh"

FORBIDDEN_FILENAMES = {".env", "auth.json", "config.toml"}
FORBIDDEN_PREFIXES = {".env."}
FORBIDDEN_SUFFIXES = {".pem", ".key"}
SKIP_CHECK_DIRS = {".git", ".worktrees", "__pycache__"}


def is_url(value: str) -> bool:
    return re.match(r"^[a-zA-Z][a-zA-Z0-9.+-]*://", value) is not None


def make_env(paths: Paths) -> dict[str, str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(paths.codex_home)
    env["AGENTS_HOME"] = str(paths.agents_home)
    env["ENGINEERING_BIBLE_BIN_DIR"] = str(paths.bin_dir)
    return env


def copytree_with_message(source: Path, destination: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"be add skill [dry-run] copy {source} -> {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


class BeError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class Paths:
    def __init__(
        self,
        repo_root: Path,
        codex_home: Path,
        agents_home: Path,
        be_home: Path,
        bin_dir: Path,
    ) -> None:
        self.repo_root = repo_root
        self.codex_home = codex_home
        self.agents_home = agents_home
        self.be_home = be_home
        self.bin_dir = bin_dir


def expand_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_paths(args: argparse.Namespace) -> Paths:
    repo_root = expand_path(args.repo_root) if args.repo_root else default_repo_root()
    codex_home = expand_path(args.codex_home or os.environ.get("CODEX_HOME", "~/.codex"))
    agents_home = expand_path(args.agents_home or os.environ.get("AGENTS_HOME", "~/.agents"))
    be_home = expand_path(
        args.home
        or os.environ.get("ENGINEERING_BIBLE_HOME", str(codex_home / "engineering-bible"))
    )
    bin_dir = expand_path(
        args.bin_dir
        or os.environ.get("ENGINEERING_BIBLE_BIN_DIR", "~/.local/bin")
    )
    return Paths(
        repo_root=repo_root,
        codex_home=codex_home,
        agents_home=agents_home,
        be_home=be_home,
        bin_dir=bin_dir,
    )


def run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> int:
    process = subprocess.run(command, cwd=cwd, env=env, text=True, check=False)
    return process.returncode


def run_command_capture(
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def require_repo_file(paths: Paths, relative_path: str) -> None:
    candidate = paths.repo_root / relative_path
    if not candidate.is_file():
        raise BeError(
            f"missing required repository file: {relative_path} under {paths.repo_root}",
            exit_code=1,
        )


def is_forbidden_runtime_name(name: str) -> bool:
    return (
        name in FORBIDDEN_FILENAMES
        or any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
        or any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)
    )


def check_runtime_boundary_for_path(
    root: Path,
    relative_to: Path | None = None,
) -> list[str]:
    violations: list[str] = []
    rel_base = relative_to or root
    for current, directories, filenames in os.walk(root):
        directories[:] = [entry for entry in directories if entry not in SKIP_CHECK_DIRS]
        for filename in filenames:
            if is_forbidden_runtime_name(filename):
                candidate = Path(current) / filename
                relative = candidate.relative_to(rel_base).as_posix()
                violations.append(relative)
    return violations


def read_skill_name_and_description(skill_root: Path) -> tuple[str, str]:
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        raise BeError(f"missing SKILL.md in {skill_root}")

    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise BeError(f"invalid skill frontmatter: {skill_md}")

    properties: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        properties[key.strip()] = value.strip()

    name = properties.get("name")
    description = properties.get("description")
    if not name:
        raise BeError(f"missing skill name: {skill_md}")
    if not description:
        raise BeError(f"missing skill description: {skill_md}")
    return name, description


def infer_skill_name(skill_root: Path, override: str | None) -> str:
    if override:
        if "/" in override or "\\" in override or not override.strip():
            raise BeError(f"invalid skill name: {override}")
        return override.strip()
    return skill_root.name


def discover_skill_root(source_root: Path) -> Path:
    matches = [match.parent for match in source_root.rglob("SKILL.md") if match.is_file()]
    matches = [
        match
        for match in matches
        if ".git" not in match.relative_to(source_root).parts
        and "tests" not in match.relative_to(source_root).parts
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise BeError(f"no SKILL.md found under {source_root}")
    raise BeError(
        "multiple SKILL.md files found; use --path to pick one:"
        + "".join(f"\n  - {match.relative_to(source_root)}" for match in matches)
    )


def resolve_local_skill_source(source_root: Path, path_arg: str | None) -> tuple[Path, Path]:
    if path_arg:
        target = (source_root / path_arg).resolve()
        if not target.is_dir():
            raise BeError(f"missing skill path in source: {path_arg}")
        return target, source_root

    target = discover_skill_root(source_root)
    return target, source_root


def resolve_skill_source(
    source: str,
    ref: str | None,
    path_arg: str | None,
) -> tuple[Path, Path | None]:
    source_path = Path(source).expanduser()
    if source_path.exists():
        source_root = source_path.resolve()
        target, _ = resolve_local_skill_source(source_root, path_arg)
        return target, None

    if not is_url(source):
        raise BeError(f"missing skill source: {source}")

    if not shutil.which("git"):
        raise BeError("git is required for URL-based skill source")
    if run_command(["git", "version"], Path.cwd()) != 0:
        raise BeError("git is required for URL-based skill source")

    temp_root = Path(tempfile.mkdtemp(prefix="be-add-skill-"))
    clone_target = temp_root / "skill-source"
    clone_command = ["git", "clone", "--depth", "1"]
    if ref:
        clone_command += ["--branch", ref]
    clone_command += ["--", source, str(clone_target)]
    result = run_command_capture(clone_command, cwd=temp_root)
    if result.returncode != 0:
        raise BeError(f"unable to clone skill source: {source}\n{result.stderr.strip()}")

    target, _ = resolve_local_skill_source(clone_target, path_arg)
    return target, temp_root


def command_version(args: argparse.Namespace) -> int:
    print(f"Engineering Bible AI be {TOOL_VERSION}")
    return 0


def doctor_checks(paths: Paths) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    python_path = shutil.which("python3")
    add("python3", "ok" if python_path else "fail", python_path or "python3 not found on PATH")

    rg_path = shutil.which("rg")
    add("ripgrep", "ok" if rg_path else "warn", rg_path or "rg not found; secret scan is limited")

    required_files = [
        "AGENTS.md",
        "scripts/install-codex.sh",
        "scripts/install_codex.py",
        "scripts/registry.py",
        "scripts/validate-installed-tree.sh",
        "scripts/validate-repo-tree.sh",
        "scripts/validate-skill-tree.sh",
        "scripts/validate-skill-frontmatter.py",
        "scripts/secret-sanity.sh",
        "skills/registry.yml",
        "skills/workflow-router/SKILL.md",
    ]
    missing = [relative for relative in required_files if not (paths.repo_root / relative).is_file()]
    if missing:
        add("repository", "fail", "missing: " + ", ".join(missing))
    else:
        add("repository", "ok", str(paths.repo_root))

    forbidden = [
        paths.repo_root / "config.toml",
        paths.repo_root / "auth.json",
        paths.repo_root / ".env",
    ]
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        add("runtime-boundary", "fail", "forbidden files present: " + ", ".join(present))
    else:
        add("runtime-boundary", "ok", "no root runtime config files found")

    add("codex-home", "ok" if paths.codex_home.exists() else "warn", str(paths.codex_home))
    add("agents-home", "ok" if paths.agents_home.exists() else "warn", str(paths.agents_home))
    add("be-home", "ok" if paths.be_home.exists() else "warn", str(paths.be_home))
    add("bin-dir", "ok" if paths.bin_dir.exists() else "warn", str(paths.bin_dir))

    return checks


def aggregate_status(checks: list[dict[str, str]]) -> str:
    statuses = {check["status"] for check in checks}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "ok"


def command_doctor(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    checks = doctor_checks(paths)
    status = aggregate_status(checks)
    payload = {
        "tool": "be",
        "version": TOOL_VERSION,
        "status": status,
        "paths": {
            "repo_root": str(paths.repo_root),
            "codex_home": str(paths.codex_home),
            "agents_home": str(paths.agents_home),
            "be_home": str(paths.be_home),
            "bin_dir": str(paths.bin_dir),
        },
        "checks": checks,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"be doctor: {status}")
        for check in checks:
            print(f"{check['status']:>4}  {check['name']}: {check['detail']}")

    return 1 if status == "fail" else 0


def command_validate(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    checkout = expand_path(args.checkout) if args.checkout else paths.repo_root
    commands = [
        ["bash", "scripts/validate-repo-tree.sh", str(checkout)],
        ["python3", "scripts/validate-skill-frontmatter.py", str(checkout / "skills")],
        ["python3", "scripts/validate-router-cases.py", "--root", str(checkout), "--static"],
        ["python3", "scripts/check-file-size.py", str(checkout), "--hard", "10000"],
    ]

    if shutil.which("rg"):
        commands.append(["bash", "scripts/secret-sanity.sh", str(checkout)])
    else:
        print("WARN: rg not found; skipping secret-sanity scan", file=sys.stderr)

    for command in commands:
        result = run_command(command, cwd=checkout)
        if result != 0:
            return result
    return 0


def command_audit(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    command = ["python3", "scripts/audit-quality-gates.py", str(paths.repo_root)]
    if args.json:
        command.append("--json")
    return run_command(command, cwd=paths.repo_root, env=make_env(paths))


def command_install(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    require_repo_file(paths, "scripts/install-codex.sh")

    mode = "--dry-run" if args.dry_run else "--install"
    installer_args = [mode]
    if args.diff:
        installer_args.append("--diff")
    if args.backup_only:
        installer_args = ["--backup-only"]
    if args.no_overwrite:
        installer_args.append("--no-overwrite")
    if args.force:
        installer_args.append("--force")
    if args.all:
        installer_args.append("--all")
    for group in args.group:
        installer_args.extend(["--group", group])

    env = os.environ.copy()
    env["CODEX_HOME"] = str(paths.codex_home)
    env["AGENTS_HOME"] = str(paths.agents_home)
    env["ENGINEERING_BIBLE_BIN_DIR"] = str(paths.bin_dir)

    return run_command(["bash", "scripts/install-codex.sh", *installer_args], cwd=paths.repo_root, env=env)


def command_update(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    env = make_env(paths)

    mode = "--dry-run" if args.dry_run else "--install"
    require_repo_file(paths, "scripts/install.sh")
    return run_command(["bash", "scripts/install.sh", mode], cwd=paths.repo_root, env=env)


def command_self_update(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    bootstrap_url = os.environ.get(
        "ENGINEERING_BIBLE_BOOTSTRAP_URL",
        BOOTSTRAP_INSTALL_URL,
    )
    mode = "--dry-run" if args.dry_run else "--install"
    env = make_env(paths)

    if bootstrap_url.startswith("file://"):
        script_path = bootstrap_url.removeprefix("file://")
        return run_command(["bash", script_path, mode], cwd=paths.repo_root, env=env)

    if not shutil.which("curl"):
        raise BeError("curl is required for remote be self-update")

    return run_command(
        ["bash", "-lc", f"curl -fsSL {bootstrap_url} | bash -s -- {mode}"],
        cwd=paths.repo_root,
        env=env,
    )


def command_add_skill(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    source = args.source.strip()
    ref = args.ref.strip() if args.ref else None
    path_arg = args.path.strip() if args.path else None

    source_dir, cleanup_root = resolve_skill_source(source, ref, path_arg)
    try:
        violations = check_runtime_boundary_for_path(source_dir, relative_to=source_dir)
        if violations:
            raise BeError("runtime-boundary violations in source: " + ", ".join(violations))

        read_skill_name_and_description(source_dir)
        skill_name = infer_skill_name(source_dir, args.name)

        destinations = [
            (paths.codex_home / "skills" / "external" / skill_name),
            (paths.agents_home / "skills" / "external" / skill_name),
            (paths.be_home / "skills" / "external" / skill_name),
        ]

        for destination in destinations:
            if destination.exists():
                raise BeError(f"external skill already exists: {destination}")

        if args.dry_run:
            print(
                f"be add skill --dry-run: "
                f"{args.source} -> "
                f"{paths.codex_home / 'skills' / 'external' / skill_name}"
            )
            return 0

        for destination in destinations:
            copytree_with_message(source_dir, destination, args.dry_run)
            print(f"installed external skill: {destination}")

        return 0
    finally:
        if cleanup_root is not None:
            shutil.rmtree(cleanup_root, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="be", description="Engineering Bible AI manager")
    parser.add_argument("--home", help="Engineering Bible state directory")
    parser.add_argument("--codex-home", help="Codex home directory")
    parser.add_argument("--agents-home", help="Agents home directory")
    parser.add_argument("--bin-dir", help="Directory for installed be wrapper")
    parser.add_argument("--repo-root", help="Engineering Bible checkout root")
    parser.add_argument("--debug", action="store_true", help="Show Python tracebacks")

    subparsers = parser.add_subparsers(dest="command", required=True)

    version = subparsers.add_parser("version", help="Print be version")
    version.set_defaults(func=command_version)

    doctor = subparsers.add_parser("doctor", help="Check local Engineering Bible setup")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    doctor.set_defaults(func=command_doctor)

    validate = subparsers.add_parser("validate", help="Run repository validation")
    validate.add_argument("--checkout", help="Checkout path to validate")
    validate.set_defaults(func=command_validate)

    audit = subparsers.add_parser("audit", help="Run quality gates audit")
    audit.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    audit.set_defaults(func=command_audit)

    install = subparsers.add_parser("install", help="Install Engineering Bible")
    install.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    install.add_argument("--diff", action="store_true", help="Show ADD/UPDATE/CONFLICT/UNCHANGED status")
    install.add_argument("--backup-only", action="store_true", help="Back up existing managed targets only")
    install.add_argument("--no-overwrite", action="store_true", help="Install only missing targets")
    install.add_argument("--force", action="store_true", help="Overwrite changed managed targets")
    install.add_argument("--group", action="append", default=[], help="Additional skill group to install")
    install.add_argument("--all", action="store_true", help="Install every skill group, including optional")
    install.set_defaults(func=command_install)

    update = subparsers.add_parser("update", help="Update Engineering Bible installation")
    update.add_argument("--dry-run", action="store_true", help="Print install actions only")
    update.set_defaults(func=command_update)

    self_command = subparsers.add_parser("self", help="Manage be wrapper")
    self_subcommands = self_command.add_subparsers(dest="self_command", required=True)
    self_update = self_subcommands.add_parser("update", help="Self-update be via bootstrap installer")
    self_update.add_argument("--dry-run", action="store_true", help="Print bootstrap update actions only")
    self_update.set_defaults(func=command_self_update)

    self_update_alias = subparsers.add_parser("self-update", help="Update be wrapper via bootstrap installer")
    self_update_alias.add_argument("--dry-run", action="store_true", help="Print bootstrap update actions only")
    self_update_alias.set_defaults(func=command_self_update)

    add = subparsers.add_parser("add", help="Add extra skill")
    add_commands = add.add_subparsers(dest="add_command", required=True)
    add_skill = add_commands.add_parser("skill", help="Add skill from local path or git URL")
    add_skill.add_argument("source", help="Skill source: local path or git URL")
    add_skill.add_argument("--ref", help="Git ref (branch/tag) for URL sources")
    add_skill.add_argument("--name", help="Install under this skill name")
    add_skill.add_argument("--path", help="Relative path to skill directory inside source")
    add_skill.add_argument("--dry-run", action="store_true", help="Validate without copying files")
    add_skill.set_defaults(func=command_add_skill)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except BeError as exc:
        print(f"be: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:
        if getattr(args, "debug", False):
            raise
        print(f"be: unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
