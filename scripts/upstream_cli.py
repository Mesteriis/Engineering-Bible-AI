#!/usr/bin/env python3
"""CLI adapter for reviewed author skills and their separate dependency state."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable


def add_skills_parser(subparsers: Any, handler: Callable[[argparse.Namespace], int]) -> None:
    parser = subparsers.add_parser("skills", help="Manage reviewed upstream skill dependencies")
    commands = parser.add_subparsers(dest="skills_command", required=True)
    descriptions = {
        "list": "List reviewed skills and provenance without installation",
        "plan": "Preview explicit skills and their required tools",
        "status": "Inspect local files; current-session exposure remains unverified",
        "ensure": "Install missing reviewed skills and required pinned tools",
        "check": "Check author tracking refs without applying updates",
        "update": "Apply the catalog's reviewed revision, never an unreviewed branch tip",
        "rollback": "Restore the previous Bible-owned skill transaction",
        "route": "Resolve an intent to a provider and pending runtime requirements",
    }
    for name, description in descriptions.items():
        command = commands.add_parser(name, help=description, description=description)
        command.add_argument("--catalog", help="Explicit reviewed upstream catalog path")
        command.add_argument("--registry", help="Explicit registry path for group selection")
        command.add_argument(
            "--skill-root",
            action="append",
            default=[],
            help="Additional existing provider root to inspect and reuse; never modified",
        )
        command.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
        if name not in {"rollback", "route"}:
            command.add_argument("--skill", action="append", default=[], help="Reviewed skill ID")
            command.add_argument(
                "--group", action="append", default=[], help="Opt-in upstream group"
            )
            command.add_argument("--all", action="store_true", help="Select every reviewed skill")
        if name in {"ensure", "update", "rollback"}:
            command.add_argument("--dry-run", action="store_true", help="Preview without writes")
        if name == "route":
            command.add_argument("intent", help="Catalog workflow intent")
        command.set_defaults(func=handler)


def _emit(payload: Any, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for entry in payload:
            print(
                f"{entry.get('status', 'CATALOG'):<18} {entry.get('id', '')} "
                f"{entry.get('name', '')}"
            )
            if entry.get("required_tools"):
                print("  required tools: " + ", ".join(entry["required_tools"]))
            if entry.get("optional_tools"):
                print("  optional tools: " + ", ".join(entry["optional_tools"]))
            if entry.get("tracking_status"):
                print("  author tracking: " + entry["tracking_status"])
                if entry.get("tracking_revision"):
                    print(f"  {entry['reviewed_revision']} -> {entry['tracking_revision']}")
                if entry.get("compare_url"):
                    print("  changes: " + entry["compare_url"])
            if entry.get("reason"):
                print("  reason: " + entry["reason"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


def _tools_plan(paths: Any, skills: list[Any]) -> dict[str, Any]:
    from tool_catalog import build_install_command, load_catalog, select_tools, tool_states

    required_ids = sorted({tool_id for skill in skills for tool_id in skill.required_tools})
    optional_ids = sorted({tool_id for skill in skills for tool_id in skill.optional_tools})
    if not required_ids:
        return {"required": [], "optional": optional_ids, "exposure": "unverified"}
    catalog = load_catalog(paths.repo_root / "config" / "tools.json")
    selection = select_tools(catalog, groups=[], tool_ids=required_ids, select_all=False)
    required = []
    for tool, state in zip(selection.tools, tool_states(selection.tools)):
        item = asdict(state)
        item["install_command"] = build_install_command(tool)
        item["setup_steps"] = [step["id"] for step in tool.setup]
        item["exposure"] = "unverified"
        required.append(item)
    return {"required": required, "optional": optional_ids, "exposure": "unverified"}


def _preflight_tools(plan: dict[str, Any]) -> None:
    from upstream_catalog import UpstreamError

    for tool in plan["required"]:
        status = tool["status"]
        if status == "UNSUPPORTED":
            raise UpstreamError(f"required tool {tool['id']} is unsupported on this platform")
        if status == "MISMATCH":
            raise UpstreamError(
                f"required tool {tool['id']} has a version mismatch; "
                "review and use `be tools install --tool ID --upgrade` separately"
            )
        if status == "MISSING" and tool["expected_version"] is None:
            raise UpstreamError(
                f"required tool {tool['id']} is unpinned; "
                "review and use `be tools install --tool ID --allow-unpinned` separately"
            )


def _install_required_tools(paths: Any, plan: dict[str, Any]) -> dict[str, Any]:
    missing = [entry["id"] for entry in plan["required"] if entry["status"] == "MISSING"]
    if not missing:
        return {"status": "unchanged", "selected": [], "exposure": "unverified"}
    command = [
        sys.executable,
        str(paths.repo_root / "scripts" / "tool_catalog.py"),
        "--catalog",
        str(paths.repo_root / "config" / "tools.json"),
        "install",
    ]
    for tool_id in missing:
        command.extend(["--tool", tool_id])
    try:
        process = subprocess.run(command, text=True, capture_output=True, check=False)
    except OSError as exc:
        return {
            "status": "partial",
            "selected": missing,
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "exposure": "unverified",
            "recovery": "Skills were installed; tool installer could not start. Inspect before retrying.",
        }
    return {
        "status": "ok" if process.returncode == 0 else "partial",
        "selected": missing,
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "recovery": "Tool package changes are separate from skill rollback; inspect `be tools list`.",
        "exposure": "unverified",
    }


def command_skills(args: argparse.Namespace, paths: Any) -> int:
    command = args.skills_command
    if command in {"plan", "ensure", "check", "update"} and not (
        args.skill or args.group or args.all
    ):
        print("be skills: explicit selection required: --skill, --group, or --all", file=sys.stderr)
        return 2

    from tool_catalog import CatalogError
    from upstream_catalog import UpstreamError, load_catalog, select_skills
    from upstream_skills import SkillManager

    try:
        catalog_path = (
            Path(args.catalog).expanduser().resolve()
            if args.catalog
            else (paths.repo_root / "config" / "upstream-skills.json")
        )
        registry_path = (
            Path(args.registry).expanduser().resolve()
            if args.registry
            else (paths.repo_root / "skills" / "registry.yml")
        )
        catalog = load_catalog(catalog_path, registry_path=registry_path)
        manager = SkillManager(
            catalog,
            paths.be_home,
            paths.codex_home / "skills",
            existing_roots=tuple(Path(value).expanduser().resolve() for value in args.skill_root),
        )
        if command == "rollback":
            _emit(manager.rollback(dry_run=args.dry_run), args.json)
            return 0
        if command == "route":
            route = manager.route(args.intent)
            route["filesystem_status"] = route["status"]
            skill_id = route.get("skill_id")
            if isinstance(skill_id, str):
                selected = select_skills(catalog, [skill_id], [], False)
                tools = _tools_plan(paths, list(selected))
                route["tools"] = tools
                pending = [
                    entry["id"]
                    for entry in tools["required"]
                    if entry["status"] not in {"OK", "UNPINNED"} or entry["setup_steps"]
                ]
                route["pending_tools_or_setup"] = pending
                if pending:
                    route["status"] = "unavailable"
                elif route["filesystem_status"] == "available":
                    route["status"] = "pending-exposure"
            route["exposure"] = "unverified"
            _emit(route, args.json)
            return 0

        include_all = args.all or (command in {"list", "status"} and not (args.skill or args.group))
        selected = list(select_skills(catalog, args.skill, args.group, include_all))
        if command == "list":
            entries = []
            for skill in selected:
                entry = asdict(skill)
                entry["source_metadata"] = asdict(catalog.sources[skill.source])
                entry["groups"] = [
                    group for group, members in catalog.groups.items() if skill.id in members
                ]
                entry["exposure"] = "unverified"
                entries.append(entry)
            _emit(entries, args.json)
            return 0
        if command == "check":
            report = manager.check(selected)
            _emit(report, args.json)
            return 1 if any(entry.get("tracking_status") == "ERROR" for entry in report) else 0
        if command == "status":
            _emit(manager.plan(selected), args.json)
            return 0

        skill_plan = manager.plan(selected)
        tools = _tools_plan(paths, selected)
        preview = {"skills": skill_plan, "tools": tools, "exposure": "unverified"}
        if command == "plan":
            _emit(preview, args.json)
            return 0
        _preflight_tools(tools)
        if not args.dry_run:
            print("Required tool plan: " + json.dumps(tools, sort_keys=True), file=sys.stderr)
        result = manager.ensure(selected, dry_run=args.dry_run, upgrade=command == "update")
        result["tool_plan"] = tools
        if not args.dry_run:
            result["tools"] = _install_required_tools(paths, tools)
            if result["tools"]["status"] == "partial":
                result["status"] = "partial"
        result["exposure"] = "unverified"
        _emit(result, args.json)
        return 1 if result.get("status") == "partial" else 0
    except (UpstreamError, CatalogError, OSError) as exc:
        print(f"be skills: {exc}", file=sys.stderr)
        return 2
