#!/usr/bin/env python3
"""Run bounded, selected Python unittest mutation checks in copied workspaces.

This runner executes repository code. Its temporary workspace and child process
are not a security sandbox; use it only with trusted source and test files.
"""

from __future__ import annotations

import argparse
import base64
from collections.abc import Sequence
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import IO, cast

import worker_snapshot


MAX_PLAN_BYTES = 1024 * 1024
MAX_MUTANTS = 10
MAX_TIMEOUT_SECONDS = 300
MAX_LOG_BYTES = 256 * 1024
MAX_REPORT_BYTES = 2 * 1024 * 1024
MAX_EVIDENCE_BYTES = 72 * 1024 * 1024
MAX_FILE_BYTES = worker_snapshot.MAX_FILE_BYTES
_MODULE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\Z")
_SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}\Z")
_ALLOWED_SUFFIXES = {
    ".py",
    ".pyi",
    ".toml",
    ".ini",
    ".cfg",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".sql",
    ".csv",
    ".xml",
}


class MutationError(ValueError):
    """The plan or selected source cannot be safely run."""


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise MutationError(f"{name} must be a JSON object")
    return cast(dict[str, object], value)


def _relative_path(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise MutationError(f"{name} must be a normalized relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        raise MutationError(f"{name} must be a normalized relative POSIX path")
    return value


def _module_path(module: str) -> str:
    if not _MODULE.fullmatch(module):
        raise MutationError("test module names must be dotted Python identifiers")
    return module.replace(".", "/") + ".py"


def validate_plan(value: object) -> dict[str, object]:
    """Validate a schema 1 plan without reading its selected source tree."""
    plan = _object(value, "plan")
    expected_keys = {
        "schema_version",
        "base_commit",
        "snapshot",
        "test_modules",
        "max_mutants",
        "per_case_timeout_seconds",
        "total_timeout_seconds",
        "mutants",
    }
    if set(plan) != expected_keys:
        raise MutationError("plan must contain exactly the schema 1 fields")
    if type(plan["schema_version"]) is not int or plan["schema_version"] != 1:
        raise MutationError("schema_version must be 1")
    base_commit = plan["base_commit"]
    if not isinstance(base_commit, str) or (
        base_commit != "unknown" and not _SHA.fullmatch(base_commit)
    ):
        raise MutationError("base_commit must be a full Git object ID or unknown")
    snapshot = plan["snapshot"]
    errors = worker_snapshot.validate_snapshot_manifest(snapshot, base_commit)
    if errors:
        raise MutationError("invalid source snapshot: " + "; ".join(errors))
    assert isinstance(snapshot, dict)
    entries = snapshot.get("files")
    assert isinstance(entries, list)
    allowlist = {cast(str, cast(dict[str, object], entry)["path"]) for entry in entries}
    if any(PurePosixPath(path).suffix.lower() not in _ALLOWED_SUFFIXES for path in allowlist):
        raise MutationError(
            "snapshot may contain only selected source, test, and text config files"
        )
    modules = plan["test_modules"]
    if not isinstance(modules, list) or not modules or len(modules) > 64:
        raise MutationError("test_modules must be a nonempty bounded list")
    if any(not isinstance(module, str) for module in modules):
        raise MutationError("test_modules entries must be strings")
    module_names = cast(list[str], modules)
    if len(set(module_names)) != len(module_names):
        raise MutationError("test_modules must be unique")
    for module in module_names:
        test_path = _module_path(module)
        if test_path not in allowlist:
            raise MutationError(f"selected test module is not in the source snapshot: {module}")
    selected_test_paths = {_module_path(module) for module in module_names}
    max_mutants = plan["max_mutants"]
    if type(max_mutants) is not int or not 1 <= max_mutants <= MAX_MUTANTS:
        raise MutationError(f"max_mutants must be between 1 and {MAX_MUTANTS}")
    for key in ("per_case_timeout_seconds", "total_timeout_seconds"):
        limit = plan[key]
        if type(limit) is not int or not 1 <= limit <= MAX_TIMEOUT_SECONDS:
            raise MutationError(f"{key} must be between 1 and {MAX_TIMEOUT_SECONDS}")
    if cast(int, plan["per_case_timeout_seconds"]) > cast(int, plan["total_timeout_seconds"]):
        raise MutationError("per_case_timeout_seconds cannot exceed total_timeout_seconds")
    mutants = plan["mutants"]
    if not isinstance(mutants, list) or not mutants or len(mutants) > max_mutants:
        raise MutationError("mutants must be a nonempty list within max_mutants")
    ids: set[str] = set()
    for raw in mutants:
        mutant = _object(raw, "mutant")
        if set(mutant) != {"id", "path", "before", "after"}:
            raise MutationError("each mutant must contain exactly id, path, before and after")
        identifier = mutant["id"]
        if not isinstance(identifier, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", identifier
        ):
            raise MutationError("mutant id must be a short stable identifier")
        if identifier in ids:
            raise MutationError("mutant ids must be unique")
        ids.add(identifier)
        path = _relative_path(mutant["path"], "mutant path")
        if path not in allowlist or not path.endswith(".py"):
            raise MutationError("mutant path must select an allowlisted Python source file")
        if (
            path in selected_test_paths
            or path.startswith("tests/")
            or PurePosixPath(path).name.startswith("test_")
        ):
            raise MutationError("mutant path must be a production Python file")
        before, after = mutant["before"], mutant["after"]
        if not isinstance(before, str) or not isinstance(after, str) or not before:
            raise MutationError("mutant before and after must be nonempty strings")
        try:
            replacement_size = max(len(before.encode("utf-8")), len(after.encode("utf-8")))
        except UnicodeEncodeError as exc:
            raise MutationError("mutant replacements must be valid UTF-8 strings") from exc
        if before == after or replacement_size > 65536:
            raise MutationError("mutant replacements must differ and fit the replacement bound")
    return plan


def _source_bytes(root: Path, snapshot: dict[str, object]) -> dict[str, tuple[bytes, int]]:
    entries = cast(list[dict[str, object]], snapshot["files"])
    captured: dict[str, tuple[bytes, int]] = {}
    if not all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK")):
        raise MutationError("safe source file descriptors are unavailable")
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for entry in entries:
            relative = cast(str, entry["path"])
            parts = PurePosixPath(relative).parts
            parent_fd = os.dup(root_fd)
            try:
                for part in parts[:-1]:
                    child_fd = os.open(
                        part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
                    )
                    os.close(parent_fd)
                    parent_fd = child_fd
                initial = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
                if not stat.S_ISREG(initial.st_mode) or initial.st_size > MAX_FILE_BYTES:
                    raise MutationError("snapshot entries must be bounded regular files")
                descriptor = os.open(
                    parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd
                )
                try:
                    before = os.fstat(descriptor)
                    metadata = (
                        before.st_dev,
                        before.st_ino,
                        before.st_size,
                        before.st_mtime_ns,
                        before.st_ctime_ns,
                    )
                    initial_metadata = (
                        initial.st_dev,
                        initial.st_ino,
                        initial.st_size,
                        initial.st_mtime_ns,
                        initial.st_ctime_ns,
                    )
                    if not stat.S_ISREG(before.st_mode) or metadata != initial_metadata:
                        raise MutationError("snapshot file changed before reading")
                    chunks: list[bytes] = []
                    size = 0
                    while True:
                        chunk = os.read(descriptor, min(65536, MAX_FILE_BYTES - size + 1))
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_FILE_BYTES:
                            raise MutationError("snapshot file exceeded byte limit while reading")
                        chunks.append(chunk)
                    after = os.fstat(descriptor)
                    after_metadata = (
                        after.st_dev,
                        after.st_ino,
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                    )
                    data = b"".join(chunks)
                    if metadata != after_metadata or size != after.st_size:
                        raise MutationError("snapshot file changed while reading")
                    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                        raise MutationError("source snapshot changed while reading")
                    captured[relative] = (data, stat.S_IMODE(after.st_mode))
                finally:
                    os.close(descriptor)
            finally:
                os.close(parent_fd)
    finally:
        os.close(root_fd)
    return captured


def _validate_snapshot(root: Path, plan: dict[str, object]) -> dict[str, tuple[bytes, int]]:
    snapshot = cast(dict[str, object], plan["snapshot"])
    diagnostics = worker_snapshot.verify_snapshot(root, snapshot, plan["base_commit"])
    if diagnostics:
        raise MutationError("source snapshot is stale: " + "; ".join(diagnostics))
    return _source_bytes(root, snapshot)


def _artifact_directory(value: Path, source_root: Path, snapshot: dict[str, object]) -> Path:
    if ".." in value.parts:
        raise MutationError("artifacts-root must not contain parent traversal")
    if value.exists() or value.is_symlink():
        raise MutationError("artifacts-root must be a new directory")
    absolute = value if value.is_absolute() else Path.cwd() / value
    current = Path(absolute.anchor)
    missing: list[str] = []
    parts = absolute.parts[1:]
    for index, part in enumerate(parts):
        candidate = current / part
        if candidate.is_symlink():
            raise MutationError("artifacts-root parent path must not contain symlinks")
        if not candidate.exists():
            missing = list(parts[index:])
            break
        if index < len(parts) - 1 and not candidate.is_dir():
            raise MutationError("artifacts-root parent components must be directories")
        current = candidate
    target = current.joinpath(*missing)
    if source_root == target or target in source_root.parents:
        raise MutationError("artifacts-root must not equal or contain the source root")
    entries = cast(list[dict[str, object]], snapshot["files"])
    selected = [
        source_root.joinpath(*PurePosixPath(cast(str, row["path"])).parts) for row in entries
    ]
    if any(target == path or target in path.parents or path in target.parents for path in selected):
        raise MutationError("artifacts-root must not overlap a selected source file")
    if source_root in target.parents:
        relative = target.relative_to(source_root).as_posix()
        allowed = ".engineering-bible/implementation/cache-mutation"
        if relative != allowed and not relative.startswith(allowed + "/"):
            raise MutationError(
                "artifacts inside source-root must use the private cache-mutation subtree"
            )
        current = source_root
        for part in PurePosixPath(relative).parts[:-1]:
            current = current / part
            if not current.exists():
                current.mkdir(mode=0o700)
            elif current.is_symlink() or not current.is_dir():
                raise MutationError("artifacts-root parent path must be real directories")
        if current.is_symlink():
            raise MutationError("artifacts-root parent path must not contain symlinks")
    elif len(missing) != 1 or not target.parent.is_dir():
        raise MutationError("artifacts-root parent directory must already exist")
    target.mkdir(mode=0o700)
    os.chmod(target, 0o700)
    return target


def _write_workspace(
    root: Path, files: dict[str, tuple[bytes, int]], replacement: tuple[str, bytes] | None
) -> None:
    for relative, (data, mode) in files.items():
        if replacement is not None and replacement[0] == relative:
            data = replacement[1]
        destination = root.joinpath(*PurePosixPath(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
        os.chmod(destination, mode)


def _terminate_group(process: subprocess.Popen[bytes]) -> bool:
    if os.name != "posix":
        process.kill()
        return True
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    grace_deadline = time.monotonic() + 0.2
    while time.monotonic() < grace_deadline:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        time.sleep(0.01)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return True


def _run_tests(
    root: Path, modules: list[str], timeout: float, env: dict[str, str]
) -> dict[str, object]:
    import selectors

    with tempfile.TemporaryDirectory(prefix="mutation-report-") as report_dir:
        report = Path(report_dir) / "result.json"
        command = [
            sys.executable,
            "-I",
            "-S",
            str(Path(__file__).with_name("mutation_unittest.py").resolve()),
            "--root",
            str(root),
            "--report",
            str(report),
            *modules,
        ]
        process: subprocess.Popen[bytes] = subprocess.Popen(
            command,
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        assert process.stdout is not None and process.stderr is not None
        selector = selectors.DefaultSelector()
        output = {
            "stdout": bytearray(),
            "stderr": bytearray(),
        }
        truncated = {"stdout": False, "stderr": False}
        for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        timed_out = False
        cleanup_ok = True
        process_done = False
        cleanup_started = False
        run_deadline = time.monotonic() + timeout
        drain_deadline: float | None = None
        while selector.get_map() or not process_done:
            now = time.monotonic()
            if not process_done and process.poll() is not None:
                process_done = True
            if not process_done and not cleanup_started and now >= run_deadline:
                timed_out = True
                cleanup_started = True
                cleanup_ok = _terminate_group(process)
                try:
                    process.wait(timeout=0.25)
                    process_done = True
                except subprocess.TimeoutExpired:
                    cleanup_ok = False
                    process_done = process.poll() is not None
                drain_deadline = time.monotonic() + 0.5
            elif process_done and not cleanup_started:
                cleanup_started = True
                cleanup_ok = _terminate_group(process)
                drain_deadline = time.monotonic() + 0.5
            if cleanup_started and drain_deadline is not None and now >= drain_deadline:
                cleanup_ok = False
                break
            next_deadline = drain_deadline if cleanup_started and drain_deadline else run_deadline
            wait_for = min(0.05, max(0.0, next_deadline - now))
            for key, _ in selector.select(wait_for):
                stream = cast(IO[bytes], key.fileobj)
                name = cast(str, key.data)
                for _ in range(4):
                    try:
                        chunk = os.read(stream.fileno(), 8192)
                    except BlockingIOError:
                        break
                    if not chunk:
                        selector.unregister(stream)
                        break
                    saved = output[name]
                    remaining = MAX_LOG_BYTES - len(saved)
                    if remaining > 0:
                        saved.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated[name] = True
        for key in list(selector.get_map().values()):
            selector.unregister(key.fileobj)
        selector.close()
        process.stdout.close()
        process.stderr.close()
        if not process_done and process.poll() is None:
            cleanup_ok = False
        if process.returncode is None:
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                cleanup_ok = False
        report_data: dict[str, object] | None = None
        if report.is_file() and report.stat().st_size <= MAX_REPORT_BYTES:
            try:
                report_data = _object(
                    json.loads(report.read_text(encoding="utf-8")), "child report"
                )
            except (OSError, UnicodeError, json.JSONDecodeError, MutationError):
                report_data = None
        return {
            "exit_code": process.returncode,
            "timed_out": timed_out,
            "report": report_data,
            "stdout": bytes(output["stdout"]).decode("utf-8", errors="replace"),
            "stderr": bytes(output["stderr"]).decode("utf-8", errors="replace"),
            "stdout_base64": base64.b64encode(output["stdout"]).decode("ascii"),
            "stderr_base64": base64.b64encode(output["stderr"]).decode("ascii"),
            "stdout_truncated": truncated["stdout"],
            "stderr_truncated": truncated["stderr"],
            "cleanup_error": not cleanup_ok,
        }


def _run_one(
    root: Path,
    artifacts: Path,
    files: dict[str, tuple[bytes, int]],
    modules: list[str],
    replacement: tuple[str, bytes] | None,
    deadline: float,
    env: dict[str, str],
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=".workspace-", dir=artifacts) as directory:
        workspace = Path(directory)
        _write_workspace(workspace, files, replacement)
        home = workspace / ".home"
        temp = workspace / ".tmp"
        home.mkdir(mode=0o700)
        temp.mkdir(mode=0o700)
        case_env = {**env, "HOME": str(home), "TMPDIR": str(temp)}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            result: dict[str, object] = {
                "exit_code": None,
                "timed_out": True,
                "report": None,
                "stdout": "",
                "stderr": "",
                "stdout_base64": "",
                "stderr_base64": "",
                "stdout_truncated": False,
                "stderr_truncated": False,
                "cleanup_error": False,
            }
        else:
            result = _run_tests(workspace, modules, remaining, case_env)
        result["child_cleanup_marker"] = (temp / "child-stopped").is_file()
        return result


def _expected_identities(report: object) -> list[str] | None:
    if not isinstance(report, dict):
        return None
    ids = report.get("test_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        return None
    return cast(list[str], ids)


def run_plan(plan_value: object, source_root: Path, artifacts_root: Path) -> dict[str, object]:
    """Run baseline and each explicit mutant, returning a private evidence record."""
    plan = validate_plan(plan_value)
    if os.name != "posix" or not hasattr(os, "killpg"):
        return {"decision": "SKIP", "reason": "process-group cancellation is unsupported"}
    source = source_root.resolve(strict=True)
    if source_root.is_symlink() or not source.is_dir():
        raise MutationError("source-root must be a real directory")
    if plan["base_commit"] == "unknown":
        artifact_dir = _artifact_directory(
            artifacts_root, source, cast(dict[str, object], plan["snapshot"])
        )
        evidence = {
            "schema_version": 1,
            "decision": "SKIP",
            "reason": "snapshot has no pinned Git base commit",
            "mutants": [],
        }
        _save_evidence(artifact_dir, evidence)
        return evidence
    files = _validate_snapshot(source, plan)
    artifact_dir = _artifact_directory(
        artifacts_root, source, cast(dict[str, object], plan["snapshot"])
    )
    env = {
        "PATH": os.defpath,
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "LC_ALL": "C.UTF-8",
    }
    for name in ("per_case_timeout_seconds", "total_timeout_seconds"):
        assert type(plan[name]) is int
    deadline = time.monotonic() + cast(int, plan["total_timeout_seconds"])
    modules = cast(list[str], plan["test_modules"])
    baseline_case_deadline = min(
        deadline, time.monotonic() + cast(int, plan["per_case_timeout_seconds"])
    )
    baseline = _run_one(
        source,
        artifact_dir,
        files,
        modules,
        None,
        baseline_case_deadline,
        env,
    )
    results: list[dict[str, object]] = []
    baseline_report = baseline["report"]
    baseline_ids = _expected_identities(baseline_report)
    baseline_good = (
        not baseline["timed_out"]
        and not baseline["cleanup_error"]
        and not baseline["stdout_truncated"]
        and not baseline["stderr_truncated"]
        and baseline["exit_code"] == 0
        and isinstance(baseline_report, dict)
        and cast(int, baseline_report.get("tests_run", 0)) > 0
        and baseline_report.get("failures") == []
        and baseline_report.get("errors") == []
        and baseline_report.get("unexpected_successes") == []
        and len(cast(list[object], baseline_report.get("skipped", [])))
        + len(cast(list[object], baseline_report.get("expected_failures", [])))
        < cast(int, baseline_report.get("tests_run", 0))
        and baseline_ids is not None
    )
    if not baseline_good:
        empty_baseline = (
            not baseline["timed_out"]
            and not baseline["cleanup_error"]
            and isinstance(baseline_report, dict)
            and (
                baseline_report.get("tests_run") == 0
                or len(cast(list[object], baseline_report.get("skipped", [])))
                + len(cast(list[object], baseline_report.get("expected_failures", [])))
                >= cast(int, baseline_report.get("tests_run", 0))
            )
            and baseline_report.get("errors") == []
            and baseline_report.get("failures") == []
            and baseline_report.get("unexpected_successes") == []
        )
        decision = "SKIP" if empty_baseline or plan["base_commit"] == "unknown" else "FAIL"
        if plan["base_commit"] == "unknown":
            decision = "SKIP"
        evidence = {
            "schema_version": 1,
            "decision": decision,
            "reason": "baseline did not pass",
            "baseline": baseline,
            "mutants": results,
        }
        _save_evidence(artifact_dir, evidence)
        return evidence

    for raw in cast(list[object], plan["mutants"]):
        mutant = cast(dict[str, object], raw)
        identifier = cast(str, mutant["id"])
        path = cast(str, mutant["path"])
        original = files[path][0]
        try:
            before = cast(str, mutant["before"]).encode("utf-8")
            after = cast(str, mutant["after"]).encode("utf-8")
        except UnicodeEncodeError:
            results.append(
                {"id": identifier, "status": "INVALID", "reason": "replacement is not valid UTF-8"}
            )
            continue
        occurrences = original.count(before)
        if occurrences != 1:
            results.append(
                {
                    "id": identifier,
                    "status": "ERROR",
                    "reason": "before text occurrence count is not exactly one",
                }
            )
            continue
        mutated = original.replace(before, after, 1)
        try:
            import ast

            ast.parse(mutated.decode("utf-8"), filename=path)
        except (SyntaxError, UnicodeError) as exc:
            results.append(
                {
                    "id": identifier,
                    "status": "INVALID",
                    "reason": f"mutant is not valid Python: {type(exc).__name__}",
                }
            )
            continue
        case_deadline = min(
            deadline, time.monotonic() + cast(int, plan["per_case_timeout_seconds"])
        )
        execution = _run_one(
            source,
            artifact_dir,
            files,
            modules,
            (path, mutated),
            case_deadline,
            env,
        )
        report = execution["report"]
        ids = _expected_identities(report)
        details: dict[str, object] = {
            "id": identifier,
            "path": path,
            "execution": execution,
        }
        if execution["timed_out"]:
            details["status"] = "TIMEOUT"
        elif execution["cleanup_error"]:
            details["status"] = "ERROR"
            details["reason"] = "test process group did not stop cleanly"
        elif execution["stdout_truncated"] or execution["stderr_truncated"]:
            details["status"] = "ERROR"
            details["reason"] = "captured output exceeded its evidence bound"
        elif (
            execution["exit_code"] is None
            or not isinstance(report, dict)
            or ids != baseline_ids
            or report.get("tests_run") != baseline_report.get("tests_run")
            or report.get("errors") != []
            or report.get("skipped") != baseline_report.get("skipped")
            or report.get("expected_failures") != baseline_report.get("expected_failures")
            or report.get("unexpected_successes") != []
        ):
            details["status"] = "ERROR"
            details["reason"] = "runner error, test load error, or changed test identities"
        elif report.get("failures") and execution["exit_code"] == 1:
            details["status"] = "KILLED"
        elif execution["exit_code"] == 0 and report.get("skipped") == baseline_report.get(
            "skipped"
        ):
            details["status"] = "SURVIVED"
        else:
            details["status"] = "ERROR"
            details["reason"] = "test result did not match a classified outcome"
        results.append(details)

    # Ensure files and HEAD stayed identical to the captured evidence.
    try:
        _validate_snapshot(source, plan)
    except (OSError, MutationError) as exc:
        decision = "ERROR"
        reason = f"source snapshot drifted during run: {exc}"
    else:
        reason = "all selected valid mutants were killed"
        statuses = [result["status"] for result in results]
        executed = any(status in ("KILLED", "SURVIVED") for status in statuses)
        runtime_error = any(status in ("ERROR", "TIMEOUT") for status in statuses)
        if runtime_error or (executed and any(status == "INVALID" for status in statuses)):
            decision = "FAIL"
            reason = "one or more selected mutants survived or could not be classified"
        elif statuses and all(status == "KILLED" for status in statuses):
            decision = "PASS"
        elif not executed:
            decision = "SKIP"
            reason = "no valid mutant execution completed"
        else:
            decision = "FAIL"
            reason = "one or more selected mutants were not executed"
    evidence = {
        "schema_version": 1,
        "decision": decision,
        "reason": reason,
        "baseline": baseline,
        "mutants": results,
        "score": {
            "killed": sum(result.get("status") == "KILLED" for result in results),
            "executed": sum(result.get("status") in ("KILLED", "SURVIVED") for result in results),
        },
    }
    _save_evidence(artifact_dir, evidence)
    return evidence


def _save_evidence(directory: Path, evidence: dict[str, object]) -> None:
    encoded = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_EVIDENCE_BYTES:
        raise MutationError("result evidence exceeded size limit")
    path = directory / "result.json"
    with path.open("xb") as stream:
        stream.write(encoded)
    os.chmod(path, 0o600)


def _load_plan(path: Path) -> object:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_PLAN_BYTES:
        raise MutationError("plan must be a bounded regular file without symlinks")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MutationError("plan is not valid UTF-8 JSON") from exc


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--artifacts-root", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(args_list)
    try:
        plan = validate_plan(_load_plan(args.plan))
        if args.validate_only:
            print("PLAN_VALID (execution not run)")
            return 0
        if args.artifacts_root is None:
            raise MutationError("--artifacts-root is required unless --validate-only is used")
        result = run_plan(plan, args.source_root, args.artifacts_root)
        print(f"{result['decision']}: {result.get('reason', '')}")
        return {"PASS": 0, "FAIL": 1, "SKIP": 2, "ERROR": 2, "TIMEOUT": 2}.get(
            cast(str, result["decision"]), 2
        )
    except (MutationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
