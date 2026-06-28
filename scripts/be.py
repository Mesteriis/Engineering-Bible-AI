#!/usr/bin/env python3
"""Engineering Bible AI command-line manager."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


TOOL_VERSION = "0.1.0"


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


def require_repo_file(paths: Paths, relative_path: str) -> None:
    candidate = paths.repo_root / relative_path
    if not candidate.is_file():
        raise BeError(
            f"missing required repository file: {relative_path} under {paths.repo_root}",
            exit_code=1,
        )


def command_version(args: argparse.Namespace) -> int:
    print(f"Engineering Bible AI be {TOOL_VERSION}")
    return 0


def doctor_checks(paths: Paths) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    python_path = shutil.which("python3")
    add("python3", "ok" if python_path else "fail", python_path or "python3 not found on PATH")

    rsync_path = shutil.which("rsync")
    add("rsync", "ok" if rsync_path else "fail", rsync_path or "rsync not found on PATH")

    rg_path = shutil.which("rg")
    add("ripgrep", "ok" if rg_path else "warn", rg_path or "rg not found; secret scan is limited")

    required_files = [
        "AGENTS.md",
        "scripts/install-codex.sh",
        "scripts/validate-skill-tree.sh",
        "scripts/validate-skill-frontmatter.py",
        "scripts/secret-sanity.sh",
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
        ["bash", "scripts/validate-skill-tree.sh", str(checkout)],
        ["python3", "scripts/validate-skill-frontmatter.py", str(checkout / "skills")],
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


def command_install(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    require_repo_file(paths, "scripts/install-codex.sh")

    mode = "--dry-run" if args.dry_run else "--install"
    env = os.environ.copy()
    env["CODEX_HOME"] = str(paths.codex_home)
    env["AGENTS_HOME"] = str(paths.agents_home)
    env["ENGINEERING_BIBLE_BIN_DIR"] = str(paths.bin_dir)

    return run_command(["bash", "scripts/install-codex.sh", mode], cwd=paths.repo_root, env=env)


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

    install = subparsers.add_parser("install", help="Install Engineering Bible")
    install.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    install.set_defaults(func=command_install)

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
