#!/usr/bin/env python3
"""Require immutable commit pins for third-party GitHub Actions."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


USES = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def validate(root: Path) -> list[str]:
    workflow_root = root / ".github" / "workflows"
    issues: list[str] = []
    for path in sorted((*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml"))):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"{path.relative_to(root)}: cannot read: {exc}")
            continue
        for match in USES.finditer(text):
            value = match.group(1)
            if value.startswith("./") or value.startswith("docker://"):
                continue
            reference = value.rsplit("@", 1)[1] if "@" in value else ""
            if not FULL_SHA.fullmatch(reference):
                line = text.count("\n", 0, match.start()) + 1
                issues.append(
                    f"{path.relative_to(root)}:{line}: {value} must use a full 40-character commit SHA"
                )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    issues = validate(args.root.resolve())
    if issues:
        print("GitHub Actions pin validation failed", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("GitHub Actions pin validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
