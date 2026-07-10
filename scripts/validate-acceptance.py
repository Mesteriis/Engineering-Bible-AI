#!/usr/bin/env python3
"""Validate structured acceptance criteria evidence and print a verdict."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


STATUSES = {"pass", "fail", "blocked", "not_verified"}
EVIDENCE_TYPES = {"test", "runtime", "browser", "artifact", "command"}


def validate(payload: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if payload.get("schema_version") != 1:
        issues.append("schema_version must be 1")
    revision = payload.get("revision")
    if not isinstance(revision, str) or not revision.strip():
        issues.append("revision must be a non-empty string")
    criteria = payload.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        return issues + ["criteria must be a non-empty list"]
    seen: set[str] = set()
    for index, criterion in enumerate(criteria):
        prefix = f"criteria[{index}]"
        if not isinstance(criterion, dict):
            issues.append(f"{prefix} must be an object")
            continue
        criterion_id = criterion.get("id")
        if not isinstance(criterion_id, str) or not criterion_id.strip():
            issues.append(f"{prefix}.id must be non-empty")
        elif criterion_id in seen:
            issues.append(f"duplicate criterion id: {criterion_id}")
        else:
            seen.add(criterion_id)
        status = criterion.get("status")
        if status not in STATUSES:
            issues.append(f"{prefix}.status is invalid")
        evidence = criterion.get("evidence")
        if not isinstance(evidence, list):
            issues.append(f"{prefix}.evidence must be a list")
            evidence = []
        for evidence_index, item in enumerate(evidence):
            if not isinstance(item, dict) or item.get("type") not in EVIDENCE_TYPES:
                issues.append(f"{prefix}.evidence[{evidence_index}] has an invalid type")
        if status == "pass" and not evidence:
            issues.append(f"{prefix} cannot be pass without evidence")
        if (
            status in {"blocked", "fail", "not_verified"}
            and not str(criterion.get("reason", "")).strip()
        ):
            issues.append(f"{prefix} requires a reason for {status}")
        criterion_class = criterion.get("class", "general")
        evidence_types = {item.get("type") for item in evidence if isinstance(item, dict)}
        if status == "pass" and criterion_class == "security" and "runtime" not in evidence_types:
            issues.append(f"{prefix} security pass requires runtime evidence")
        if status == "pass" and criterion_class == "ui" and "browser" not in evidence_types:
            issues.append(f"{prefix} UI pass requires browser evidence")
        if status == "pass" and criterion_class == "migration":
            scenarios = {
                str(item.get("scenario", "")) for item in evidence if isinstance(item, dict)
            }
            if not {"upgrade", "rollback"}.issubset(scenarios):
                issues.append(f"{prefix} migration pass requires upgrade and rollback scenarios")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"acceptance validation failed: {exc}", file=sys.stderr)
        return 1
    issues = validate(payload)
    criteria = payload.get("criteria", []) if isinstance(payload, dict) else []
    summary = {
        "status": "fail" if issues else "pass",
        "total": len(criteria) if isinstance(criteria, list) else 0,
        "passed": sum(item.get("status") == "pass" for item in criteria if isinstance(item, dict)),
        "issues": issues,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif issues:
        print("acceptance validation failed", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
    else:
        print(f"acceptance validation passed: {summary['passed']}/{summary['total']} criteria")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
