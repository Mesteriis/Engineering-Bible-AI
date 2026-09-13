"""Check worker result consistency and compare matched, recorded workloads.

Records are supplied by the launcher. This module does not certify a worker,
authenticate provider metadata, execute commands, or establish a sandbox.
"""

from __future__ import annotations

from collections import Counter
import math
from pathlib import PurePosixPath
from typing import cast

from worker_snapshot import validate_snapshot_manifest


REQUIRED_FIELDS = {
    "task_id",
    "goal",
    "base_commit",
    "snapshot",
    "requested",
    "observed",
    "status",
    "findings",
    "checks",
    "artifacts",
    "open_questions",
    "usage",
}
OUTCOMES = ("PASS", "FAIL", "SKIP", "BLOCKED")
METRICS = ("duration_ms", "tokens", "cost_usd")
MAX_METRIC = 2**53 - 1


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def artifact_path(value: object) -> bool:
    """Accept only canonical relative POSIX paths, never URLs or host paths."""
    return (
        isinstance(value, str)
        and bool(value)
        and not any(ord(char) < 32 for char in value)
        and not any(char in value for char in ("\\", ":", "#"))
        and not PurePosixPath(value).is_absolute()
        and all(part not in ("", ".", "..") for part in value.split("/"))
    )


def _object(value: object, name: str, issues: list[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        issues.append(f"{name} must be an object")
        return {}
    return cast(dict[str, object], value)


def _list(value: object, name: str, issues: list[str]) -> list[object]:
    if not isinstance(value, list):
        issues.append(f"{name} must be a list")
        return []
    return value


def _source(value: object, artifacts: list[object], name: str, issues: list[str]) -> None:
    path = value.split("#", 1)[0] if isinstance(value, str) else None
    if not artifact_path(path) or path not in artifacts:
        issues.append(f"{name} must reference a declared relative artifact")


def _check_records(raw: object, artifacts: list[object], issues: list[str]) -> list[str]:
    outcomes: list[str] = []
    commands: set[str] = set()
    for index, item in enumerate(_list(raw, "checks", issues)):
        name = f"checks[{index}]"
        check = _object(item, name, issues)
        command = check.get("command")
        if not isinstance(command, str) or not command.strip() or command in commands:
            issues.append(f"{name}.command must be nonempty and unique")
        else:
            commands.add(command)
        outcome = check.get("outcome")
        if not isinstance(outcome, str) or outcome not in OUTCOMES:
            issues.append(f"{name}.outcome is invalid")
            continue
        outcomes.append(outcome)
        code = check.get("exit_code")
        if outcome in ("PASS", "FAIL"):
            if type(code) is not int or (outcome == "PASS" and code != 0):
                issues.append(f"{name}: {outcome} requires its original integer exit code")
            raw_path = check.get("raw_artifact")
            if not artifact_path(raw_path) or raw_path not in artifacts:
                issues.append(f"{name}.raw_artifact must be a declared relative artifact")
        else:
            if "exit_code" not in check or code is not None or not _text(check.get("reason")):
                issues.append(f"{name}: {outcome} requires null exit_code and a reason")
            if check.get("raw_artifact") is not None:
                _source(check.get("raw_artifact"), artifacts, f"{name}.raw_artifact", issues)
    return outcomes


def _usage(raw: object, artifacts: list[object], issues: list[str]) -> None:
    if raw == "unknown":
        return
    usage = _object(raw, "usage", issues)
    for key in METRICS:
        value = usage.get(key)
        if key not in usage:
            issues.append(f"usage.{key} is required (null if unknown)")
        elif value is not None and (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value < 0
            or value > MAX_METRIC
            or not math.isfinite(value)
            or (key == "tokens" and type(value) is not int)
        ):
            issues.append(f"usage.{key} must be finite, nonnegative, or null; tokens are integers")
    if not _text(usage.get("method")):
        issues.append("usage.method must identify the measurement method")
    _source(usage.get("source"), artifacts, "usage.source", issues)


def inspect_record(payload: object) -> dict[str, object]:
    """Validate the existing result contract without turning completion into PASS."""
    issues: list[str] = []
    record = _object(payload, "record", issues)
    missing = REQUIRED_FIELDS - record.keys()
    if missing:
        issues.append("missing fields: " + ", ".join(sorted(missing)))
    for key in ("task_id", "goal", "base_commit"):
        if not _text(record.get(key)):
            issues.append(f"{key} must be nonempty")
    status = record.get("status")
    if not isinstance(status, str) or status not in ("completed", "failed", "blocked"):
        issues.append("status must be completed, failed, or blocked")
    questions = _list(record.get("open_questions"), "open_questions", issues)
    if any(not _text(question) for question in questions):
        issues.append("open_questions must contain nonempty strings")
    if status in ("failed", "blocked") and not questions and not _text(record.get("reason")):
        issues.append("failed/blocked result requires a reason or open question")

    snapshot = _object(record.get("snapshot"), "snapshot", issues)
    captured = snapshot.get("state") == "captured"
    if captured:
        issues.extend(validate_snapshot_manifest(snapshot, record.get("base_commit")))
    elif snapshot != {"state": "not_created", "sha256": "unknown", "files": []}:
        issues.append("snapshot must be captured or explicitly not_created with unknown hash")

    artifacts = _list(record.get("artifacts"), "artifacts", issues)
    paths: set[str] = set()
    for path in artifacts:
        if not isinstance(path, str) or not artifact_path(path) or path in paths:
            issues.append("artifacts must contain unique canonical relative paths")
        else:
            paths.add(path)
    requested = _object(record.get("requested"), "requested", issues)
    observed = _object(record.get("observed"), "observed", issues)
    for route_name, route in (("requested", requested), ("observed", observed)):
        for key in ("provider", "model"):
            if not _text(route.get(key)):
                issues.append(f"{route_name}.{key} must be nonempty (or unknown)")
    verification = observed.get("verification")
    route_known = isinstance(verification, str) and verification in (
        "runtime_metadata",
        "provider_response",
    )
    if route_known:
        _source(observed.get("source"), artifacts, "observed.source", issues)
        for key in ("provider", "model"):
            if observed.get(key) == "unknown" or observed.get(key) != requested.get(key):
                issues.append(f"observed.{key} must match the explicitly requested route")
    elif verification != "unknown" or any(
        observed.get(key) != "unknown" for key in ("provider", "model", "source")
    ):
        issues.append("unverified observed route must preserve unknown in all four fields")

    raw_files = snapshot.get("files")
    known_paths = {
        entry["path"]
        for entry in (raw_files if isinstance(raw_files, list) else [])
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    for index, raw in enumerate(_list(record.get("findings"), "findings", issues)):
        finding = _object(raw, f"findings[{index}]", issues)
        for key in ("file_line", "severity", "evidence", "limitations", "source_reviewer"):
            if not _text(finding.get(key)):
                issues.append(f"findings[{index}].{key} must be a nonempty string")
        location = finding.get("file_line")
        path, _, line = location.rpartition(":") if isinstance(location, str) else ("", "", "")
        if not (
            path in known_paths
            and line.isascii()
            and line.isdecimal()
            and len(line) <= 9
            and int(line) > 0
        ):
            issues.append(
                f"findings[{index}].file_line must name a snapshot file and positive line"
            )
    outcomes = _check_records(record.get("checks"), artifacts, issues)
    _usage(record.get("usage"), artifacts, issues)
    if issues or status == "failed" or "FAIL" in outcomes:
        outcome = "FAIL"
    elif status == "blocked" or "BLOCKED" in outcomes or not route_known:
        outcome = "BLOCKED"
    elif (
        not captured or record.get("base_commit") == "unknown" or not outcomes or "SKIP" in outcomes
    ):
        outcome = "SKIP"
    else:
        outcome = "PASS"
    return {
        "contract_status": "FAIL" if issues else "PASS",
        "outcome": outcome,
        "proof_scope": "record_consistency_only",
        "issues": issues,
        "checks": {key: outcomes.count(key) for key in OUTCOMES},
    }


def _series(raw: object, name: str, issues: list[str]) -> dict[str, dict[str, object]]:
    items = _list(raw, name, issues)
    if not items:
        issues.append(f"{name} must contain at least one run")
    records: dict[str, dict[str, object]] = {}
    routes: set[tuple[str, str]] = set()
    for index, item in enumerate(items):
        inspected = inspect_record(item)
        if inspected["contract_status"] != "PASS":
            issues.extend(
                f"{name}[{index}]: {issue}" for issue in cast(list[str], inspected["issues"])
            )
            continue
        record = cast(dict[str, object], item)
        task_id = cast(str, record["task_id"])
        if task_id in records:
            issues.append(f"{name}: duplicate task_id")
        records[task_id] = record
        requested = cast(dict[str, str], record["requested"])
        routes.add((requested["provider"], requested["model"]))
    if len(routes) > 1:
        issues.append(f"{name}: mixed routes within a series")
    return records


def _metric_summary(
    baseline: dict[str, dict[str, object]], candidate: dict[str, dict[str, object]], key: str
) -> dict[str, object]:
    pairs: list[tuple[float, float]] = []
    for task_id, before in baseline.items():
        old, new = before["usage"], candidate[task_id]["usage"]
        if not isinstance(old, dict) or not isinstance(new, dict) or old["method"] != new["method"]:
            continue
        if old[key] is not None and new[key] is not None:
            pairs.append((old[key], new[key]))
    complete = len(pairs) == len(baseline)
    before_total = sum(pair[0] for pair in pairs) if complete else None
    after_total = sum(pair[1] for pair in pairs) if complete else None
    delta = None
    reason = "missing or incompatible measurements" if not complete else "zero baseline"
    if before_total is not None and after_total is not None and before_total > 0:
        relative = (after_total - before_total) / before_total * 100
        if math.isfinite(relative):
            delta = round(relative, 6)
            reason = None
        else:
            reason = "percentage exceeds finite numeric range"
    return {
        "paired_cases": len(pairs),
        "total_cases": len(baseline),
        "baseline_total": before_total,
        "candidate_total": after_total,
        "delta_percent": delta,
        "reason": reason,
    }


def compare_runs(baseline: object, candidate: object) -> dict[str, object]:
    """Compare complete matched series; missing evidence never counts as zero."""
    issues: list[str] = []
    before = _series(baseline, "baseline", issues)
    after = _series(candidate, "candidate", issues)
    if before.keys() != after.keys():
        issues.append("baseline and candidate must contain exactly the same task ids")
    for task_id in before.keys() & after.keys():
        left, right = before[task_id], after[task_id]
        for field in ("goal", "base_commit", "snapshot"):
            if left[field] != right[field]:
                issues.append(f"{task_id}: different {field}")
        left_checks = cast(list[dict[str, object]], left["checks"])
        right_checks = cast(list[dict[str, object]], right["checks"])
        if {item["command"] for item in left_checks} != {item["command"] for item in right_checks}:
            issues.append(f"{task_id}: different check commands")
    if issues:
        return {"contract_status": "FAIL", "outcome": "FAIL", "issues": issues}
    old_outcomes = {key: inspect_record(value)["outcome"] for key, value in before.items()}
    new_outcomes = {key: inspect_record(value)["outcome"] for key, value in after.items()}
    regressions = sorted(
        key for key in before if old_outcomes[key] == "PASS" and new_outcomes[key] != "PASS"
    )
    counts = Counter(new_outcomes.values())
    all_outcomes = [*old_outcomes.values(), *new_outcomes.values()]
    outcome = (
        "FAIL"
        if counts["FAIL"]
        else next((key for key in ("BLOCKED", "SKIP") if key in all_outcomes), "PASS")
    )
    return {
        "contract_status": "PASS",
        "outcome": outcome,
        "proof_scope": "recorded_workloads_only",
        "issues": [],
        "cases": len(before),
        "baseline": {key: list(old_outcomes.values()).count(key) for key in OUTCOMES},
        "candidate": {key: counts[key] for key in OUTCOMES},
        "regressions": regressions,
        "metrics": {key: _metric_summary(before, after, key) for key in METRICS},
    }
