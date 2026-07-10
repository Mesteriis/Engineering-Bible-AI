#!/usr/bin/env python3
"""Plan and install optional CLI tools from a validated provenance catalog."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable
from urllib.parse import urlparse


SUPPORTED_MANAGERS = {"brew", "npm", "uv"}
SUPPORTED_EFFECTS = {"network", "repo-write", "user-config", "browser-runtime"}


class CatalogError(RuntimeError):
    """Raised when the catalog or requested operation is invalid."""


@dataclass(frozen=True)
class ToolSpec:
    id: str
    manager: str
    package: str
    executable: str
    groups: tuple[str, ...]
    version: str | None
    unpinned: bool
    python: str | None
    source: str = "https://example.invalid/unspecified"
    platforms: tuple[str, ...] = ("linux", "macos")
    license: str = ""
    capabilities: tuple[str, ...] = ()
    integrity: str | None = None
    setup: tuple[dict[str, object], ...] = ()
    healthcheck: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolState:
    id: str
    status: str
    expected_version: str | None
    installed_version: str | None
    manager: str
    package: str
    source: str
    platforms: tuple[str, ...]
    capabilities: tuple[str, ...]
    setup_required: bool = False
    executable_path: str | None = None


@dataclass(frozen=True)
class ToolSelection:
    """Catalog-order selection partitioned for one normalized runtime platform."""

    platform: str
    tools: tuple[ToolSpec, ...]
    supported: tuple[ToolSpec, ...]
    unsupported: tuple[ToolSpec, ...]


def _required_text(entry: dict[str, object], key: str, tool_id: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"tool {tool_id!r} requires non-empty {key}")
    return value.strip()


def load_catalog(path: Path) -> list[ToolSpec]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot read tool catalog {path}: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("schema_version") not in {1, 2}:
        raise CatalogError("tool catalog schema_version must be 1 or 2")
    schema_version = int(payload["schema_version"])
    raw_tools = payload.get("tools")
    if not isinstance(raw_tools, list):
        raise CatalogError("tool catalog tools must be a list")

    result: list[ToolSpec] = []
    seen: set[str] = set()
    for index, raw_entry in enumerate(raw_tools):
        if not isinstance(raw_entry, dict):
            raise CatalogError(f"tool entry {index} must be an object")
        entry: dict[str, object] = {str(key): value for key, value in raw_entry.items()}
        provisional_id = str(entry.get("id", f"entry-{index}"))
        tool_id = _required_text(entry, "id", provisional_id)
        if tool_id in seen:
            raise CatalogError(f"duplicate tool id: {tool_id}")
        seen.add(tool_id)

        manager = _required_text(entry, "manager", tool_id)
        if manager not in SUPPORTED_MANAGERS:
            raise CatalogError(f"tool {tool_id!r} has unknown manager: {manager}")
        package = _required_text(entry, "package", tool_id)
        executable = _required_text(entry, "executable", tool_id)

        raw_groups = entry.get("groups")
        if not isinstance(raw_groups, list) or not raw_groups:
            raise CatalogError(f"tool {tool_id!r} requires at least one group")
        groups = tuple(str(group).strip() for group in raw_groups)
        if any(not group for group in groups):
            raise CatalogError(f"tool {tool_id!r} contains an empty group")

        version_value = entry.get("version")
        version = version_value.strip() if isinstance(version_value, str) else None
        unpinned = entry.get("unpinned") is True
        python_value = entry.get("python")
        python = python_value.strip() if isinstance(python_value, str) else None
        source = _required_text(entry, "source", tool_id)
        parsed_source = urlparse(source)
        if (
            parsed_source.scheme != "https"
            or not parsed_source.netloc
            or parsed_source.username is not None
            or parsed_source.password is not None
        ):
            raise CatalogError(f"tool {tool_id!r} requires a credential-free HTTPS source")
        raw_platforms = entry.get("platforms")
        if not isinstance(raw_platforms, list) or not raw_platforms:
            raise CatalogError(f"tool {tool_id!r} requires supported platforms")
        platforms = tuple(str(platform).strip() for platform in raw_platforms)
        unknown_platforms = sorted(set(platforms) - {"linux", "macos"})
        if any(not platform for platform in platforms) or unknown_platforms:
            raise CatalogError(f"tool {tool_id!r} has invalid platforms")

        if manager in {"uv", "npm"} and not version:
            raise CatalogError(f"tool {tool_id!r} requires an exact version")
        if manager in {"uv", "npm"} and unpinned:
            raise CatalogError(f"tool {tool_id!r} cannot be unpinned")
        if manager == "brew" and not unpinned:
            raise CatalogError(f"brew tool {tool_id!r} must declare unpinned: true")
        if manager == "brew" and version:
            raise CatalogError(f"brew tool {tool_id!r} cannot declare an exact version")
        if python and manager != "uv":
            raise CatalogError(f"tool {tool_id!r} may set python only for uv")

        license_name = entry.get("license")
        if schema_version >= 2 and (not isinstance(license_name, str) or not license_name.strip()):
            raise CatalogError(f"tool {tool_id!r} requires a license in schema v2")
        normalized_license = license_name.strip() if isinstance(license_name, str) else ""

        raw_capabilities = entry.get("capabilities", [])
        if not isinstance(raw_capabilities, list) or any(
            not isinstance(item, str) or not item.strip() for item in raw_capabilities
        ):
            raise CatalogError(f"tool {tool_id!r} capabilities must be non-empty strings")
        capabilities = tuple(str(item).strip() for item in raw_capabilities)

        integrity_value = entry.get("integrity")
        integrity = integrity_value.strip() if isinstance(integrity_value, str) else None
        if schema_version >= 2 and manager == "npm":
            if integrity is None or not integrity.startswith("sha512-"):
                raise CatalogError(f"npm tool {tool_id!r} requires sha512 integrity")

        raw_setup = entry.get("setup", [])
        if not isinstance(raw_setup, list):
            raise CatalogError(f"tool {tool_id!r} setup must be a list")
        setup: list[dict[str, object]] = []
        for step in raw_setup:
            if not isinstance(step, dict):
                raise CatalogError(f"tool {tool_id!r} setup steps must be objects")
            step_id = step.get("id")
            args = step.get("args")
            effects = step.get("effects", [])
            if not isinstance(step_id, str) or not step_id.strip():
                raise CatalogError(f"tool {tool_id!r} setup step requires id")
            if not isinstance(args, list) or any(not isinstance(arg, str) for arg in args):
                raise CatalogError(f"tool {tool_id!r} setup args must be literal strings")
            literal_args = [arg for arg in args if isinstance(arg, str)]
            if any("$" in arg or "`" in arg or "\n" in arg for arg in literal_args):
                raise CatalogError(
                    f"tool {tool_id!r} setup args cannot interpolate or contain newlines"
                )
            if not isinstance(effects, list) or any(
                effect not in SUPPORTED_EFFECTS for effect in effects
            ):
                raise CatalogError(f"tool {tool_id!r} has unsupported setup effect")
            setup.append({"id": step_id.strip(), "args": literal_args, "effects": list(effects)})

        raw_healthcheck = entry.get("healthcheck", [])
        if not isinstance(raw_healthcheck, list) or any(
            not isinstance(arg, str) for arg in raw_healthcheck
        ):
            raise CatalogError(f"tool {tool_id!r} healthcheck must be a string list")
        healthcheck = tuple(arg for arg in raw_healthcheck if isinstance(arg, str))

        result.append(
            ToolSpec(
                id=tool_id,
                manager=manager,
                package=package,
                executable=executable,
                groups=groups,
                version=version,
                unpinned=unpinned,
                python=python,
                source=source,
                platforms=platforms,
                license=normalized_license,
                capabilities=capabilities,
                integrity=integrity,
                setup=tuple(setup),
                healthcheck=healthcheck,
            )
        )
    return result


def normalize_platform(platform: str | None = None) -> str:
    """Map runtime platform identifiers to the catalog's portable vocabulary."""

    raw_platform = (platform if platform is not None else sys.platform).strip().lower()
    if raw_platform == "macos" or raw_platform.startswith("darwin"):
        return "macos"
    if raw_platform.startswith("linux"):
        return "linux"
    raise CatalogError(f"unsupported runtime platform: {raw_platform or '<empty>'}")


def select_tools(
    tools: Iterable[ToolSpec],
    *,
    groups: list[str],
    tool_ids: list[str],
    select_all: bool,
    platform: str | None = None,
) -> ToolSelection:
    tool_list = list(tools)
    if not select_all and not groups and not tool_ids:
        raise CatalogError("plan/install requires an explicit --group, --tool, or --all selector")

    known_groups = {group for tool in tool_list for group in tool.groups}
    unknown_groups = sorted(set(groups) - known_groups)
    if unknown_groups:
        raise CatalogError("unknown tool group(s): " + ", ".join(unknown_groups))
    known_ids = {tool.id for tool in tool_list}
    unknown_ids = sorted(set(tool_ids) - known_ids)
    if unknown_ids:
        raise CatalogError("unknown tool id(s): " + ", ".join(unknown_ids))

    selected_ids = set(tool_ids)
    if select_all:
        selected_ids.update(tool.id for tool in tool_list)
    for tool in tool_list:
        if selected_ids.intersection({tool.id}) or set(tool.groups).intersection(groups):
            selected_ids.add(tool.id)
    selected = tuple(tool for tool in tool_list if tool.id in selected_ids)
    runtime_platform = normalize_platform(platform)
    supported = tuple(tool for tool in selected if runtime_platform in tool.platforms)
    unsupported = tuple(tool for tool in selected if runtime_platform not in tool.platforms)
    return ToolSelection(
        platform=runtime_platform,
        tools=selected,
        supported=supported,
        unsupported=unsupported,
    )


def build_install_command(tool: ToolSpec, *, upgrade: bool = False) -> list[str]:
    if tool.manager == "brew":
        return ["brew", "install", tool.package]
    if tool.manager == "uv":
        command = ["uv", "tool", "install"]
        if upgrade:
            command.append("--force")
        if tool.python:
            command.extend(["-p", tool.python])
        command.append(f"{tool.package}=={tool.version}")
        return command
    if tool.manager == "npm":
        return ["npm", "install", "-g", f"{tool.package}@{tool.version}"]
    raise CatalogError(f"unsupported manager: {tool.manager}")


def verify_npm_integrity(tool: ToolSpec) -> None:
    if tool.manager != "npm" or not tool.integrity:
        return
    result = _run_capture(
        ["npm", "view", f"{tool.package}@{tool.version}", "dist.integrity", "--json"]
    )
    if result.returncode != 0:
        raise CatalogError(f"cannot verify npm integrity for {tool.id}: {result.stderr.strip()}")
    try:
        observed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"npm integrity response is invalid for {tool.id}") from exc
    if observed != tool.integrity:
        raise CatalogError(
            f"npm integrity mismatch for {tool.id}: expected {tool.integrity}, observed {observed}"
        )


def classify_tool(
    tool: ToolSpec,
    installed_version: str | None,
    *,
    platform: str | None = None,
    executable_path: str | None = None,
) -> ToolState:
    runtime_platform = normalize_platform(platform)
    if runtime_platform not in tool.platforms:
        status = "UNSUPPORTED"
    elif installed_version is None:
        status = "MISSING"
    elif tool.unpinned:
        status = "UNPINNED"
    elif installed_version == tool.version:
        status = "OK"
    else:
        status = "MISMATCH"
    setup_required = bool(tool.setup) and status in {"OK", "UNPINNED"}
    return ToolState(
        id=tool.id,
        status=status,
        expected_version=tool.version,
        installed_version=installed_version,
        manager=tool.manager,
        package=tool.package,
        source=tool.source,
        platforms=tool.platforms,
        capabilities=tool.capabilities,
        setup_required=setup_required,
        executable_path=executable_path,
    )


def _run_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def installed_versions(tools: Iterable[ToolSpec]) -> dict[str, str | None]:
    tool_list = list(tools)
    versions: dict[str, str | None] = {tool.id: None for tool in tool_list}

    brew_tools = [tool for tool in tool_list if tool.manager == "brew"]
    if brew_tools and shutil.which("brew"):
        result = _run_capture(["brew", "list", "--versions"])
        if result.returncode == 0:
            discovered = {}
            for line in result.stdout.splitlines():
                fields = line.split()
                if len(fields) >= 2:
                    discovered[fields[0]] = fields[-1]
            for tool in brew_tools:
                versions[tool.id] = discovered.get(tool.package)

    uv_tools = [tool for tool in tool_list if tool.manager == "uv"]
    if uv_tools and shutil.which("uv"):
        result = _run_capture(["uv", "tool", "list"])
        if result.returncode == 0:
            discovered: dict[str, str] = {}
            for line in result.stdout.splitlines():
                match = re.match(r"^(\S+)\s+v([^\s]+)$", line.strip())
                if match:
                    discovered[match.group(1)] = match.group(2)
            for tool in uv_tools:
                versions[tool.id] = discovered.get(tool.package)

    npm_tools = [tool for tool in tool_list if tool.manager == "npm"]
    if npm_tools and shutil.which("npm"):
        result = _run_capture(["npm", "list", "-g", "--depth=0", "--json"])
        if result.returncode in {0, 1} and result.stdout.strip():
            try:
                dependencies = json.loads(result.stdout).get("dependencies", {})
            except (AttributeError, json.JSONDecodeError):
                dependencies = {}
            if isinstance(dependencies, dict):
                for tool in npm_tools:
                    package = dependencies.get(tool.package)
                    if isinstance(package, dict) and isinstance(package.get("version"), str):
                        versions[tool.id] = package["version"]

    return versions


def tool_states(
    tools: Iterable[ToolSpec],
    *,
    platform: str | None = None,
) -> list[ToolState]:
    tool_list = list(tools)
    runtime_platform = normalize_platform(platform)
    supported = [tool for tool in tool_list if runtime_platform in tool.platforms]
    versions = installed_versions(supported)
    return [
        classify_tool(
            tool,
            versions.get(tool.id),
            platform=runtime_platform,
        )
        for tool in tool_list
    ]


def _print_states(states: Iterable[ToolState], json_output: bool) -> None:
    state_list = list(states)
    if json_output:
        print(json.dumps([asdict(state) for state in state_list], indent=2, sort_keys=True))
        return
    for state in state_list:
        version = state.installed_version or "-"
        expected = state.expected_version or "rolling"
        print(f"{state.status:<9} {state.id:<24} installed={version} expected={expected}")


def selected_tools_by_capability(
    tools: Iterable[ToolSpec], capabilities: list[str]
) -> list[ToolSpec]:
    wanted = {item.strip() for item in capabilities if item.strip()}
    if not wanted:
        return list(tools)
    return [tool for tool in tools if wanted.intersection(tool.capabilities)]


def _setup_step(tool: ToolSpec, step_id: str) -> dict[str, object]:
    for step in tool.setup:
        if step.get("id") == step_id:
            return step
    raise CatalogError(f"tool {tool.id!r} has no setup step {step_id!r}")


def run_setup(
    tool: ToolSpec,
    step_id: str,
    *,
    allow_effects: set[str],
    repo: Path | None = None,
    dry_run: bool = False,
) -> int:
    step = _setup_step(tool, step_id)
    raw_effects = step.get("effects", [])
    effects = (
        {effect for effect in raw_effects if isinstance(effect, str)}
        if isinstance(raw_effects, list)
        else set()
    )
    missing = sorted(effects - allow_effects)
    if missing:
        raise CatalogError(
            f"setup step {tool.id}/{step_id} requires explicit permissions: {', '.join(missing)}"
        )
    executable = shutil.which(tool.executable)
    if executable is None:
        raise CatalogError(f"tool {tool.id!r} executable is not on PATH: {tool.executable}")
    raw_args = step.get("args", [])
    command = (
        [executable, *[arg for arg in raw_args if isinstance(arg, str)]]
        if isinstance(raw_args, list)
        else [executable]
    )
    cwd = repo if "repo-write" in effects else None
    if cwd is not None and not cwd.is_dir():
        raise CatalogError(f"setup repository does not exist: {cwd}")
    print("TOOL-SETUP", tool.id, step_id, json.dumps(command))
    if dry_run:
        return 0
    result = subprocess.run(command, cwd=cwd, check=False)
    return result.returncode


def run_healthcheck(tool: ToolSpec) -> tuple[str, int]:
    executable = shutil.which(tool.executable)
    if executable is None:
        return "PATH_MISSING", 1
    command = [executable, *tool.healthcheck]
    result = subprocess.run(
        command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if result.returncode != 0:
        return "BROKEN", result.returncode
    return "OK", 0


def _add_selectors(parser: argparse.ArgumentParser, *, include_json: bool = True) -> None:
    parser.add_argument("--group", action="append", default=[], help="Select a catalog group")
    parser.add_argument("--tool", action="append", default=[], help="Select one tool id")
    parser.add_argument("--all", action="store_true", help="Select every catalog entry")
    if include_json:
        parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")


def build_parser() -> argparse.ArgumentParser:
    default_catalog = Path(__file__).resolve().parents[1] / "config" / "tools.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=default_catalog)
    commands = parser.add_subparsers(dest="command", required=True)

    list_command = commands.add_parser("list", help="List catalog entries and installed state")
    list_command.add_argument("--json", action="store_true")
    list_command.add_argument("--capability", action="append", default=[])

    plan = commands.add_parser("plan", help="Show selected tool install actions")
    _add_selectors(plan)

    install = commands.add_parser("install", help="Install selected tools")
    _add_selectors(install, include_json=False)
    install.add_argument("--allow-unpinned", action="store_true")
    install.add_argument("--upgrade", action="store_true")
    configure = commands.add_parser("configure", help="Run one explicit catalog setup step")
    configure.add_argument("--tool", required=True)
    configure.add_argument("--step", required=True)
    configure.add_argument("--repo", type=Path)
    configure.add_argument("--allow-network", action="store_true")
    configure.add_argument("--allow-repo-write", action="store_true")
    configure.add_argument("--allow-user-config", action="store_true")
    configure.add_argument("--allow-browser", action="store_true")
    configure.add_argument("--interactive", action="store_true")
    configure.add_argument("--dry-run", action="store_true")
    doctor = commands.add_parser("doctor", help="Run tool healthchecks")
    _add_selectors(doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        tools = load_catalog(args.catalog)
        if args.command == "list":
            filtered = selected_tools_by_capability(tools, args.capability)
            _print_states(tool_states(filtered), args.json)
            return 0

        if args.command == "configure":
            selected = [tool for tool in tools if tool.id == args.tool]
            if not selected:
                raise CatalogError(f"unknown tool id(s): {args.tool}")
            effects: set[str] = set()
            if args.allow_network:
                effects.add("network")
            if args.allow_repo_write:
                effects.add("repo-write")
            if args.allow_user_config:
                effects.add("user-config")
            if args.allow_browser:
                effects.add("browser-runtime")
            if args.interactive:
                effects.add("user-config")
            if not args.interactive and "user-config" in effects:
                raise CatalogError("user-config setup requires --interactive")
            result = run_setup(
                selected[0],
                args.step,
                allow_effects=effects,
                repo=args.repo,
                dry_run=args.dry_run,
            )
            return result

        if args.command == "doctor":
            selection = select_tools(
                tools,
                groups=args.group,
                tool_ids=args.tool,
                select_all=args.all,
            )
            failures = 0
            for tool in selection.tools:
                status, code = run_healthcheck(tool)
                print(f"{status:<12} {tool.id:<24} executable={tool.executable}")
                failures |= code != 0
            return int(failures)

        selection = select_tools(
            tools,
            groups=args.group,
            tool_ids=args.tool,
            select_all=args.all,
        )
        selected = list(selection.tools)
        states = tool_states(selected, platform=selection.platform)
        if args.command == "plan":
            _print_states(states, args.json)
            if not args.json:
                for tool, state in zip(selected, states):
                    if state.status in {"MISSING", "MISMATCH"}:
                        print("INSTALL", json.dumps(build_install_command(tool)))
            return 0

        failures: list[str] = []
        for tool, state in zip(selected, states):
            if state.status == "UNSUPPORTED":
                if tool.id in args.tool:
                    failures.append(f"{tool.id}: unsupported on {selection.platform}")
                else:
                    print(f"TOOL-SKIP {tool.id} (UNSUPPORTED on {selection.platform})")
                continue
            if state.status in {"OK", "UNPINNED"}:
                print(f"TOOL-SKIP {tool.id} ({state.status})")
                continue
            if tool.unpinned and not args.allow_unpinned:
                if tool.id in args.tool:
                    failures.append(f"{tool.id}: requires --allow-unpinned")
                else:
                    print(f"TOOL-SKIP {tool.id} (requires --allow-unpinned)")
                continue
            if shutil.which(tool.manager) is None:
                failures.append(f"{tool.id}: manager {tool.manager} is unavailable")
                continue
            if state.status == "MISMATCH" and not args.upgrade:
                failures.append(f"{tool.id}: installed version mismatch; use --upgrade")
                continue
            command = build_install_command(tool, upgrade=args.upgrade)
            verify_npm_integrity(tool)
            print("TOOL-INSTALL", json.dumps(command))
            result = subprocess.run(command, check=False)
            if result.returncode != 0:
                failures.append(f"{tool.id}: installer exited {result.returncode}")
        if failures:
            for failure in failures:
                print(f"TOOL-ERROR {failure}", file=sys.stderr)
            return 1
        return 0
    except CatalogError as exc:
        print(f"tool catalog: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
