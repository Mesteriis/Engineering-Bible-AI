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


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

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
    env["ENGINEERING_BIBLE_HOME"] = str(paths.be_home)
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


def read_tool_version(repo_root: Path) -> str:
    version_file = repo_root / "VERSION"
    if not version_file.is_file():
        raise BeError(f"missing VERSION under {repo_root}")
    version = version_file.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        raise BeError(f"invalid VERSION under {repo_root}: expected strict SemVer")
    return version


def resolve_paths(args: argparse.Namespace) -> Paths:
    repo_root = expand_path(args.repo_root) if args.repo_root else default_repo_root()
    codex_home = expand_path(args.codex_home or os.environ.get("CODEX_HOME", "~/.codex"))
    agents_home = expand_path(args.agents_home or os.environ.get("AGENTS_HOME", "~/.agents"))
    be_home = expand_path(
        args.home or os.environ.get("ENGINEERING_BIBLE_HOME", str(codex_home / "engineering-bible"))
    )
    bin_dir = expand_path(
        args.bin_dir or os.environ.get("ENGINEERING_BIBLE_BIN_DIR", "~/.local/bin")
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


def read_install_manifest(paths: Paths, *, required: bool = False) -> dict[str, object] | None:
    path = paths.be_home / "install-manifest.json"
    if not path.is_file():
        if required:
            raise BeError(f"installation manifest is missing: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BeError(f"installation manifest is invalid: {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise BeError(f"unsupported installation manifest: {path}")
    return {str(key): value for key, value in payload.items()}


def manifest_package(manifest: dict[str, object]) -> dict[str, object]:
    package = manifest.get("package")
    if not isinstance(package, dict):
        raise BeError("installation manifest has no package metadata")
    return {str(key): value for key, value in package.items()}


def manifest_source(manifest: dict[str, object]) -> dict[str, str]:
    source = manifest_package(manifest).get("source")
    if not isinstance(source, dict):
        raise BeError("installation manifest has no source metadata")
    normalized = {
        str(key): value
        for key, value in source.items()
        if isinstance(key, str) and isinstance(value, str)
    }
    for required_key in ("kind", "location", "reference"):
        if not normalized.get(required_key):
            raise BeError(f"installation manifest source is missing {required_key}")
    return normalized


def manifest_install_selection(manifest: dict[str, object]) -> tuple[list[str], bool, str]:
    groups = manifest.get("groups")
    if not isinstance(groups, dict):
        raise BeError("installation manifest has no group metadata")

    requested = groups.get("requested")
    if not isinstance(requested, list):
        raise BeError("installation manifest requested groups are invalid")
    requested_groups: list[str] = []
    for group in requested:
        if not isinstance(group, str) or not group.strip():
            raise BeError("installation manifest requested groups are invalid")
        requested_groups.append(group)
    include_all = groups.get("include_all")
    if not isinstance(include_all, bool):
        raise BeError("installation manifest include_all flag is invalid")
    prompt_profile = groups.get("prompt_profile")
    if prompt_profile not in {"full", "minimal", "fast"}:
        raise BeError("installation manifest prompt profile is invalid")
    return requested_groups, include_all, str(prompt_profile)


def preserve_manifest_source(paths: Paths, env: dict[str, str]) -> None:
    manifest = read_install_manifest(paths)
    if manifest is None:
        return
    source = manifest_source(manifest)
    env["ENGINEERING_BIBLE_SOURCE_KIND"] = source["kind"]
    env["ENGINEERING_BIBLE_SOURCE_LOCATION"] = source["location"]
    env["ENGINEERING_BIBLE_SOURCE_REF"] = source["reference"]
    if source.get("digest"):
        env["ENGINEERING_BIBLE_SOURCE_DIGEST"] = source["digest"]


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
    version = read_tool_version(default_repo_root())
    print(f"Engineering Bible AI be {version}")
    return 0


def doctor_checks(paths: Paths) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    python_supported = sys.version_info >= (3, 11)
    python_detail = f"{sys.executable} ({sys.version_info.major}.{sys.version_info.minor})"
    add("python3", "ok" if python_supported else "fail", python_detail)

    rg_path = shutil.which("rg")
    add("ripgrep", "ok" if rg_path else "warn", rg_path or "rg not found; secret scan is limited")

    required_files = [
        "AGENTS.md",
        "scripts/install-codex.sh",
        "scripts/install-tools.sh",
        "scripts/install_codex.py",
        "scripts/installer_core.py",
        "scripts/mcp_catalog.py",
        "scripts/mcp_catalog_cli.py",
        "scripts/mcp_catalog_storage.py",
        "scripts/registry.py",
        "scripts/tool_catalog.py",
        "scripts/validate.py",
        "scripts/validate-acceptance.py",
        "scripts/validate-installed-tree.sh",
        "scripts/validate-repo-tree.sh",
        "scripts/validate-skill-tree.sh",
        "scripts/validate-skill-frontmatter.py",
        "scripts/secret-sanity.sh",
        "skills/registry.yml",
        "skills/workflow-router/SKILL.md",
        "skills/mcp-tool-router/SKILL.md",
        "config/tools.json",
        "VERSION",
        ".secret-sanity-allowlist",
    ]
    missing = [
        relative for relative in required_files if not (paths.repo_root / relative).is_file()
    ]
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
        "version": read_tool_version(paths.repo_root),
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
    checkout = (
        paths.be_home / "current"
        if args.installed
        else (expand_path(args.checkout) if args.checkout else paths.repo_root)
    )
    profile = args.profile or ("bootstrap" if args.installed else "full")
    validator = checkout / "scripts" / "validate.py"
    if not validator.is_file():
        raise BeError(f"validation runner is missing: {validator}")
    result = run_command(
        [sys.executable, str(validator), "--root", str(checkout), "--profile", profile],
        cwd=checkout,
        env=make_env(paths),
    )
    if result != 0 or not args.installed:
        return result
    installed_validator = checkout / "scripts" / "validate-installed-tree.sh"
    return run_command(
        [
            "bash",
            str(installed_validator),
            str(checkout),
            str(paths.codex_home),
            str(paths.agents_home),
        ],
        cwd=checkout,
        env=make_env(paths),
    )


def command_audit(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    command = [sys.executable, "scripts/audit-quality-gates.py", str(paths.repo_root)]
    if getattr(args, "json", False):
        command.append("--json")
    return run_command(command, cwd=paths.repo_root, env=make_env(paths))


def command_acceptance(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    validator = paths.repo_root / "scripts" / "validate-acceptance.py"
    if not validator.is_file():
        raise BeError(f"acceptance validator is missing: {validator}")
    command = [sys.executable, str(validator), str(expand_path(args.file))]
    if args.json:
        command.append("--json")
    return run_command(command, cwd=paths.repo_root, env=make_env(paths))


def command_install(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    require_repo_file(paths, "scripts/install-codex.sh")
    if args.install_tools:
        raise BeError(
            "--install-tools is deprecated and disabled; run `be tools install` with an explicit selector"
        )

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
    if args.migrate_legacy:
        installer_args.append("--migrate-legacy")
    if args.all:
        installer_args.append("--all")
    if args.install_tools:
        installer_args.append("--install-tools")
    installer_args.extend(["--prompt-profile", args.prompt_profile])
    for group in args.group:
        installer_args.extend(["--group", group])

    env = make_env(paths)
    preserve_manifest_source(paths, env)

    return run_command(
        ["bash", "scripts/install-codex.sh", *installer_args], cwd=paths.repo_root, env=env
    )


def command_update(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    env = make_env(paths)
    mode = "--dry-run" if args.dry_run else "--install"
    installer_args: list[str] = [mode]
    requested_profile = args.prompt_profile if isinstance(args.prompt_profile, str) else None
    requested_ref = args.ref if isinstance(args.ref, str) else None
    if args.force:
        installer_args.append("--force")
    if args.migrate_legacy:
        installer_args.append("--migrate-legacy")

    manifest = read_install_manifest(paths)
    source: dict[str, str] | None = None
    if manifest is not None:
        package = manifest_package(manifest)
        source = manifest_source(manifest)
        requested_groups, include_all, prompt_profile = manifest_install_selection(manifest)
        print(f"Current version: {package.get('version', 'unknown')}")
        print(f"Current digest: {package.get('digest', 'unknown')}")
        for group in requested_groups:
            installer_args.extend(["--group", group])
        if include_all:
            installer_args.append("--all")
        installer_args.extend(["--prompt-profile", requested_profile or prompt_profile])
    else:
        print(f"Current version: {read_tool_version(paths.repo_root)} (unmanaged checkout)")
        print("Current digest: unmanaged")
        installer_args.extend(["--prompt-profile", requested_profile or "full"])

    if requested_ref is None and (source is None or source["kind"] == "checkout"):
        source_root = paths.repo_root if source is None else expand_path(source["location"])
        installer = source_root / "scripts" / "install.sh"
        if not installer.is_file():
            raise BeError(f"recorded source checkout is unavailable: {source_root}")
        print(f"Target source: checkout {source_root}")
        if source is not None:
            preserve_manifest_source(paths, env)
        return run_command(["bash", str(installer), *installer_args], cwd=source_root, env=env)

    if source is not None and source["kind"] == "checkout":
        raise BeError(
            "--ref is unavailable for a local checkout source; reinstall from a release to change channels"
        )

    require_repo_file(paths, "scripts/install.sh")
    reference = requested_ref or (source["reference"] if source is not None else None)
    if not reference:
        raise BeError("remote update requires a recorded or explicit --ref")
    installer_args.extend(["--ref", reference])
    if args.allow_unstable:
        installer_args.append("--allow-unstable")
    if source is not None:
        env["ENGINEERING_BIBLE_REPO"] = source["location"]
    env["ENGINEERING_BIBLE_FORCE_REMOTE"] = "1"
    print(f"Target source: remote {reference}")
    return run_command(
        ["bash", str(paths.repo_root / "scripts" / "install.sh"), *installer_args],
        cwd=paths.repo_root,
        env=env,
    )


def command_self_update(args: argparse.Namespace) -> int:
    print(
        "DEPRECATED: use `be update`; self-update now updates the complete package", file=sys.stderr
    )
    return command_update(args)


def command_mcp(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    script = paths.repo_root / "scripts" / "mcp_catalog.py"
    if not script.is_file():
        raise BeError(f"MCP catalog command is missing: {script}")
    command = [
        sys.executable,
        str(script),
        "--engineering-home",
        str(paths.be_home),
        args.mcp_command,
    ]
    if args.mcp_command in {"refresh", "status", "candidates"}:
        command.extend(["--repo", str(expand_path(args.repo))])
    if args.mcp_command == "candidates":
        command.append("--task-stdin")
        command.extend(["--limit", str(args.limit)])
    elif args.mcp_command == "show":
        command.append(args.tool_id)
    if getattr(args, "json", False):
        command.append("--json")
    return run_command(command, cwd=paths.repo_root, env=make_env(paths))


def command_tools(args: argparse.Namespace) -> int:
    paths = resolve_paths(args)
    script = paths.repo_root / "scripts" / "tool_catalog.py"
    catalog = paths.repo_root / "config" / "tools.json"
    if not script.is_file() or not catalog.is_file():
        raise BeError("optional tool catalog is unavailable in this installation")
    command = [sys.executable, str(script), "--catalog", str(catalog), args.tools_command]
    if args.tools_command in {"plan", "install", "doctor"}:
        for group in args.group:
            command.extend(["--group", group])
        for tool_id in args.tool:
            command.extend(["--tool", tool_id])
        if args.all:
            command.append("--all")
    if args.tools_command == "list" and args.capability:
        for capability in args.capability:
            command.extend(["--capability", capability])
    if args.tools_command == "install":
        if args.allow_unpinned:
            command.append("--allow-unpinned")
        if args.upgrade:
            command.append("--upgrade")
    if args.tools_command == "configure":
        command.extend(["--tool", args.tool_id, "--step", args.step])
        if args.repo:
            command.extend(["--repo", str(expand_path(args.repo))])
        for flag, option in (
            (args.allow_network, "--allow-network"),
            (args.allow_repo_write, "--allow-repo-write"),
            (args.allow_user_config, "--allow-user-config"),
            (args.allow_browser, "--allow-browser"),
            (args.interactive, "--interactive"),
            (args.dry_run, "--dry-run"),
        ):
            if flag:
                command.append(option)
    if getattr(args, "json", False):
        command.append("--json")
    return run_command(command, cwd=paths.repo_root, env=make_env(paths))


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
    validate_source = validate.add_mutually_exclusive_group()
    validate_source.add_argument("--checkout", help="Checkout path to validate")
    validate_source.add_argument(
        "--installed",
        action="store_true",
        help="Validate the installed namespaced package and active files",
    )
    validate.add_argument(
        "--profile",
        choices=("quick", "bootstrap", "full", "release"),
        help="Validation profile (default: full, or bootstrap with --installed)",
    )
    validate.set_defaults(func=command_validate)

    audit = subparsers.add_parser("audit", help="Run quality gates audit")
    audit.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    audit.set_defaults(func=command_audit)

    acceptance = subparsers.add_parser("acceptance", help="Validate acceptance evidence")
    acceptance_commands = acceptance.add_subparsers(dest="acceptance_command", required=True)
    for name in ("validate", "summary"):
        acceptance_command = acceptance_commands.add_parser(name)
        acceptance_command.add_argument("file")
        acceptance_command.add_argument("--json", action="store_true")
        acceptance_command.set_defaults(func=command_acceptance)

    install = subparsers.add_parser("install", help="Install Engineering Bible")
    install.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    install.add_argument(
        "--diff", action="store_true", help="Show ADD/UPDATE/CONFLICT/UNCHANGED status"
    )
    install.add_argument(
        "--backup-only", action="store_true", help="Back up existing managed targets only"
    )
    install.add_argument("--no-overwrite", action="store_true", help="Install only missing targets")
    install.add_argument("--force", action="store_true", help="Overwrite changed managed targets")
    install.add_argument(
        "--migrate-legacy",
        action="store_true",
        help="Adopt only identical files from a legacy installation",
    )
    install.add_argument(
        "--prompt-profile",
        choices=("full", "minimal", "fast"),
        default="full",
        help="Global instruction profile to activate",
    )
    install.add_argument(
        "--group", action="append", default=[], help="Additional skill group to install"
    )
    install.add_argument(
        "--all", action="store_true", help="Install every skill group, including optional"
    )
    install.add_argument(
        "--install-tools",
        action="store_true",
        help="Install optional companion CLI tools",
    )
    install.set_defaults(func=command_install)

    def add_update_options(command: argparse.ArgumentParser) -> None:
        command.add_argument("--dry-run", action="store_true", help="Print install actions only")
        command.add_argument(
            "--force", action="store_true", help="Replace modified manifest-owned files"
        )
        command.add_argument("--migrate-legacy", action="store_true")
        command.add_argument("--prompt-profile", choices=("full", "minimal", "fast"))
        command.add_argument("--ref", help="Explicit release tag or unstable ref")
        command.add_argument(
            "--allow-unstable",
            action="store_true",
            help="Permit a mutable/non-release ref",
        )

    update = subparsers.add_parser("update", help="Update Engineering Bible installation")
    add_update_options(update)
    update.set_defaults(func=command_update)

    self_command = subparsers.add_parser("self", help="Manage be wrapper")
    self_subcommands = self_command.add_subparsers(dest="self_command", required=True)
    self_update = self_subcommands.add_parser("update", help="Deprecated alias for complete update")
    add_update_options(self_update)
    self_update.set_defaults(func=command_self_update)

    self_update_alias = subparsers.add_parser("self-update", help="Deprecated alias for be update")
    add_update_options(self_update_alias)
    self_update_alias.set_defaults(func=command_self_update)

    mcp = subparsers.add_parser("mcp", help="Build and query runtime-derived tool capabilities")
    mcp_commands = mcp.add_subparsers(dest="mcp_command", required=True)
    mcp_refresh = mcp_commands.add_parser(
        "refresh", help="Refresh catalog from runtime JSON on stdin"
    )
    mcp_refresh.add_argument("--repo", required=True)
    mcp_refresh.add_argument("--json", action="store_true")
    mcp_refresh.set_defaults(func=command_mcp)
    mcp_status = mcp_commands.add_parser(
        "status", help="Show catalog and repository projection status"
    )
    mcp_status.add_argument("--repo", required=True)
    mcp_status.add_argument("--json", action="store_true")
    mcp_status.set_defaults(func=command_mcp)
    mcp_candidates = mcp_commands.add_parser(
        "candidates", help="Rank capabilities for a task on stdin"
    )
    mcp_candidates.add_argument("--repo", required=True)
    mcp_candidates.add_argument("--task-stdin", action="store_true", required=True)
    mcp_candidates.add_argument("--limit", type=int, default=8)
    mcp_candidates.add_argument("--json", action="store_true")
    mcp_candidates.set_defaults(func=command_mcp)
    mcp_show = mcp_commands.add_parser("show", help="Show one capability by opaque runtime id")
    mcp_show.add_argument("tool_id")
    mcp_show.add_argument("--json", action="store_true")
    mcp_show.set_defaults(func=command_mcp)

    tools_command = subparsers.add_parser("tools", help="Manage optional companion CLI tools")
    tools_commands = tools_command.add_subparsers(dest="tools_command", required=True)
    tools_list = tools_commands.add_parser("list", help="List catalog and installed versions")
    tools_list.add_argument("--json", action="store_true")
    tools_list.add_argument("--capability", action="append", default=[])
    tools_list.set_defaults(func=command_tools)

    def add_tool_selectors(command: argparse.ArgumentParser, *, include_json: bool = True) -> None:
        command.add_argument("--group", action="append", default=[])
        command.add_argument("--tool", action="append", default=[])
        command.add_argument("--all", action="store_true")
        if include_json:
            command.add_argument("--json", action="store_true")

    tools_plan = tools_commands.add_parser("plan", help="Plan explicit optional tool selection")
    add_tool_selectors(tools_plan)
    tools_plan.set_defaults(func=command_tools)
    tools_install = tools_commands.add_parser(
        "install", help="Install explicit optional tool selection"
    )
    add_tool_selectors(tools_install, include_json=False)
    tools_install.add_argument("--allow-unpinned", action="store_true")
    tools_install.add_argument("--upgrade", action="store_true")
    tools_install.set_defaults(func=command_tools)
    tools_configure = tools_commands.add_parser(
        "configure", help="Run one explicit setup step for one tool"
    )
    tools_configure.add_argument("--tool", dest="tool_id", required=True)
    tools_configure.add_argument("--step", required=True)
    tools_configure.add_argument("--repo")
    tools_configure.add_argument("--allow-network", action="store_true")
    tools_configure.add_argument("--allow-repo-write", action="store_true")
    tools_configure.add_argument("--allow-user-config", action="store_true")
    tools_configure.add_argument("--allow-browser", action="store_true")
    tools_configure.add_argument("--interactive", action="store_true")
    tools_configure.add_argument("--dry-run", action="store_true")
    tools_configure.set_defaults(func=command_tools)
    tools_doctor = tools_commands.add_parser("doctor", help="Run explicit tool healthchecks")
    add_tool_selectors(tools_doctor, include_json=False)
    tools_doctor.set_defaults(func=command_tools)

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
