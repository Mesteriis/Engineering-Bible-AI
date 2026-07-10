"""Command-line adapter for the dynamic runtime capability catalog."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
import os
from pathlib import Path
import sys

from mcp_catalog import (
    MAX_CANDIDATES,
    CatalogError,
    _expect_mapping,
    candidate_capabilities,
    catalog_status,
    load_catalog,
    refresh_catalog,
    repository_projection_status,
    require_current_projection,
    show_capability,
)


def _default_home() -> Path:
    configured = os.environ.get("ENGINEERING_BIBLE_HOME")
    if configured:
        return Path(configured).expanduser()
    codex_home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    return codex_home / "engineering-bible"


def _read_json_stdin() -> Mapping[str, object]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"runtime metadata stdin is not valid JSON: {exc.msg}") from exc
    return _expect_mapping(payload, "runtime_metadata")


def _json_document(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _print_human(command: str, result: object) -> None:
    if command == "candidates" and isinstance(result, list):
        if not result:
            print("No relevant available capabilities.")
            return
        for item in result:
            capability = _expect_mapping(item, "candidate")
            print(
                f"{capability.get('risk', 'UNKNOWN'):<7} "
                f"{capability.get('runtime_id', '')} "
                f"{capability.get('display_name', '')}"
            )
        return
    if isinstance(result, Mapping):
        for key, value in result.items():
            if isinstance(value, Mapping):
                print(f"{key}: {_json_document(dict(value)).strip()}")
            else:
                print(f"{key}: {value}")
        return
    print(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and query a private dynamic runtime capability catalog",
    )
    parser.add_argument("--engineering-home", type=Path, default=_default_home())
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh = subparsers.add_parser("refresh", help="Read normalized runtime metadata from stdin")
    refresh.add_argument("--repo", type=Path, required=True)
    refresh.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status", help="Show persisted catalog status")
    status.add_argument("--repo", type=Path, required=True)
    status.add_argument("--json", action="store_true")

    candidates = subparsers.add_parser("candidates", help="Rank capabilities for a stdin task")
    candidates.add_argument("--repo", type=Path, required=True)
    candidates.add_argument("--task-stdin", action="store_true", required=True)
    candidates.add_argument("--limit", type=int, default=MAX_CANDIDATES)
    candidates.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show", help="Show one capability by opaque runtime id")
    show.add_argument("runtime_id")
    show.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "refresh":
            catalog, paths = refresh_catalog(
                _read_json_stdin(),
                engineering_home=args.engineering_home,
                repo=args.repo,
            )
            result: object = {
                **catalog_status(catalog),
                "paths": {name: str(path) for name, path in paths.items()},
            }
        elif args.command == "status":
            catalog = load_catalog(args.engineering_home)
            result = {
                **catalog_status(catalog),
                "repository_projection": repository_projection_status(catalog, args.repo),
            }
        elif args.command == "candidates":
            catalog = load_catalog(args.engineering_home)
            require_current_projection(catalog, args.repo)
            result = candidate_capabilities(
                catalog,
                sys.stdin.read(),
                limit=args.limit,
            )
        elif args.command == "show":
            result = show_capability(load_catalog(args.engineering_home), args.runtime_id)
        else:
            raise CatalogError(f"unsupported command: {args.command}")

        if args.json:
            print(_json_document(result), end="")
        else:
            _print_human(args.command, result)
        return 0
    except (CatalogError, OSError) as exc:
        print(f"mcp-catalog: {exc}", file=sys.stderr)
        return 1
