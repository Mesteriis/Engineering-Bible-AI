#!/usr/bin/env python3
"""Unified validation runner for repository, bootstrap, and release gates."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from enum import Enum
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


class Result:
    def __init__(self, status: Status, detail: str = "") -> None:
        self.status = status
        self.detail = detail


class Check:
    def __init__(self, name: str, run: Callable[[], Result]) -> None:
        self.name = name
        self.run = run


PROMPT_BUDGETS = {
    "instructions/global/full.md": (2600, 20 * 1024),
    "instructions/global/minimal.md": (700, 6 * 1024),
    "instructions/global/fast.md": (700, 6 * 1024),
    "AGENTS.md": (800, 8 * 1024),
}

RELEASE_REQUIRED_FILES = (
    ".github/workflows/release.yml",
    ".github/workflows/validate.yml",
    ".python-version",
    "AGENTS.md",
    "MANIFEST.md",
    "README.md",
    "README.ru.md",
    "instructions/global/full.md",
    "instructions/global/minimal.md",
    "instructions/global/fast.md",
    "config/tools.json",
    "config/legacy-install-signatures.json",
    "examples/runtime-capabilities.synthetic.json",
    "pyproject.toml",
    "schemas/runtime-capabilities.schema.json",
    "schemas/acceptance-verdict.schema.json",
    "scripts/build-release.py",
    "scripts/install-tools.sh",
    "scripts/installer_core.py",
    "scripts/mcp_catalog.py",
    "scripts/mcp_catalog_cli.py",
    "scripts/mcp_catalog_storage.py",
    "scripts/registry.py",
    "scripts/tool_catalog.py",
    "scripts/validate-actions-pins.py",
    "scripts/validate-release-contract.py",
    "scripts/validate.py",
    "scripts/validate-acceptance.py",
    "skills/mcp-tool-router/SKILL.md",
    "skills/registry.yml",
    "tests/test_be_extended_cli.py",
    "tests/test_acceptance.py",
    "tests/test_bootstrap.py",
    "tests/test_installer.py",
    "tests/test_mcp_catalog.py",
    "tests/test_registry.py",
    "tests/test_release_contract.py",
    "tests/test_tool_catalog.py",
    "tests/test_validation.py",
)


def completed_result(process: subprocess.CompletedProcess[str]) -> Result:
    detail = "\n".join(part.strip() for part in (process.stdout, process.stderr) if part.strip())
    return Result(Status.PASS if process.returncode == 0 else Status.FAIL, detail)


def run_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> Result:
    executable = argv[0]
    if os.sep not in executable and shutil.which(executable) is None:
        return Result(Status.SKIP, f"required executable is unavailable: {executable}")
    process = subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed_result(process)


def shell_files(root: Path) -> list[Path]:
    files = list((root / "scripts").glob("*.sh"))
    files.extend((root / "skills").glob("*/scripts/*.sh"))
    return sorted(path for path in files if path.is_file())


def python_files(root: Path) -> list[Path]:
    files = list((root / "scripts").glob("*.py"))
    files.extend((root / "skills").glob("*/scripts/*.py"))
    files.extend((root / "tests").glob("test_*.py"))
    return sorted(path for path in files if path.is_file())


def validate_shell_syntax(files: Sequence[Path]) -> Result:
    failures: list[str] = []
    checked = 0
    for path in files:
        checked += 1
        process = subprocess.run(
            ["bash", "-n", str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if process.returncode != 0:
            error = process.stderr.strip() or process.stdout.strip() or "syntax error"
            failures.append(f"{path}: {error}")
    if failures:
        return Result(Status.FAIL, "\n".join(failures))
    return Result(Status.PASS, f"checked {checked} shell file(s) separately")


def validate_python_compile(files: Sequence[Path]) -> Result:
    failures: list[str] = []
    for path in files:
        process = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if process.returncode != 0:
            error = process.stderr.strip() or process.stdout.strip() or "compile error"
            failures.append(f"{path}: {error}")
    if failures:
        return Result(Status.FAIL, "\n".join(failures))
    return Result(Status.PASS, f"compiled {len(files)} Python file(s)")


def validate_prompt_budgets(root: Path) -> Result:
    failures: list[str] = []
    summaries: list[str] = []
    for relative, (word_limit, byte_limit) in PROMPT_BUDGETS.items():
        path = root / relative
        if not path.is_file():
            failures.append(f"missing prompt file: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        words = len(content.split())
        size = len(content.encode("utf-8"))
        summaries.append(f"{relative}: {words} words, {size} bytes")
        if words > word_limit:
            failures.append(f"{relative}: {words} words exceeds {word_limit}")
        if size > byte_limit:
            failures.append(f"{relative}: {size} bytes exceeds {byte_limit}")
    if failures:
        return Result(Status.FAIL, "\n".join([*summaries, *failures]))
    return Result(Status.PASS, "\n".join(summaries))


def validate_python_version() -> Result:
    required = (3, 11)
    current = sys.version_info[:2]
    if current < required:
        return Result(
            Status.FAIL,
            f"Python {required[0]}.{required[1]}+ is required; current is {current[0]}.{current[1]}",
        )
    return Result(Status.PASS, f"Python {current[0]}.{current[1]}")


def _tracked_files(root: Path) -> tuple[set[str] | None, Result | None]:
    if shutil.which("git") is None:
        return None, Result(Status.SKIP, "required executable is unavailable: git")
    process = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        return None, Result(
            Status.FAIL,
            process.stderr.decode("utf-8", errors="replace").strip(),
        )
    tracked = {
        item.decode("utf-8", errors="strict") for item in process.stdout.split(b"\0") if item
    }
    return tracked, None


def validate_release_membership(root: Path, required_files: Sequence[str]) -> Result:
    tracked, error = _tracked_files(root)
    if error is not None:
        return error
    assert tracked is not None
    missing = [relative for relative in required_files if relative not in tracked]
    if missing:
        return Result(
            Status.FAIL,
            "required release file is not tracked by git:\n" + "\n".join(missing),
        )
    return Result(Status.PASS, f"{len(required_files)} required release file(s) are tracked")


def validate_release_snapshot(root: Path, required_files: Sequence[str]) -> Result:
    membership = validate_release_membership(root, required_files)
    if membership.status != Status.PASS:
        return membership
    tracked, error = _tracked_files(root)
    if error is not None:
        return error
    assert tracked is not None
    with tempfile.TemporaryDirectory(prefix="engineering-bible-release-") as raw:
        temporary = Path(raw)
        snapshot = temporary / "snapshot"
        for relative in sorted(tracked):
            source = root / relative
            if source.is_symlink():
                return Result(Status.FAIL, f"tracked symbolic link is not portable: {relative}")
            if not source.is_file():
                return Result(Status.FAIL, f"tracked file is missing from working tree: {relative}")
            destination = snapshot / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        bootstrap = run_command(
            [
                sys.executable,
                "scripts/validate.py",
                "--root",
                str(snapshot),
                "--profile",
                "bootstrap",
            ],
            cwd=snapshot,
        )
        if bootstrap.status != Status.PASS:
            return Result(Status.FAIL, "tracked snapshot bootstrap failed:\n" + bootstrap.detail)

        home = temporary / "home"
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "CODEX_HOME": str(home / ".codex"),
                "AGENTS_HOME": str(home / ".agents"),
                "ENGINEERING_BIBLE_HOME": str(home / ".codex" / "engineering-bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(home / ".local" / "bin"),
            }
        )
        install = run_command(
            ["bash", "scripts/install-codex.sh", "--install"],
            cwd=snapshot,
            env=env,
        )
        if install.status != Status.PASS:
            return Result(Status.FAIL, "tracked snapshot install failed:\n" + install.detail)
        installed = run_command(
            [
                "bash",
                str(
                    home
                    / ".codex"
                    / "engineering-bible"
                    / "current"
                    / "scripts"
                    / "validate-installed-tree.sh"
                ),
                str(home / ".codex" / "engineering-bible" / "current"),
                str(home / ".codex"),
                str(home / ".agents"),
            ],
            cwd=snapshot,
            env=env,
        )
        if installed.status != Status.PASS:
            return Result(
                Status.FAIL, "tracked snapshot installed validation failed:\n" + installed.detail
            )
    return Result(
        Status.PASS,
        f"{len(required_files)} required release files are tracked; snapshot bootstrap/install passed",
    )


def command_check(root: Path, *argv: str) -> Check:
    name = " ".join(argv)
    return Check(name, lambda: run_command(argv, cwd=root))


def secret_sanity_check(root: Path) -> Result:
    if shutil.which("rg") is None:
        return Result(Status.SKIP, "content secret scan requires rg")
    return run_command(["bash", "scripts/secret-sanity.sh", "."], cwd=root)


def bootstrap_checks(root: Path) -> list[Check]:
    return [
        Check("Python version", validate_python_version),
        command_check(root, "bash", "scripts/validate-repo-tree.sh", "."),
        command_check(root, sys.executable, "scripts/validate-skill-frontmatter.py", "skills"),
        command_check(root, sys.executable, "scripts/registry.py", "--root", ".", "validate"),
        command_check(root, sys.executable, "scripts/validate-router-cases.py", "--fixtures"),
        Check("secret sanity", lambda: secret_sanity_check(root)),
        Check("prompt budgets", lambda: validate_prompt_budgets(root)),
        Check("shell syntax", lambda: validate_shell_syntax(shell_files(root))),
        Check("Python compile", lambda: validate_python_compile(python_files(root))),
    ]


def quick_checks(root: Path) -> list[Check]:
    return [
        *bootstrap_checks(root),
        command_check(root, sys.executable, "scripts/validate-markdown-style.py", "."),
        command_check(root, sys.executable, "scripts/check-file-size.py", ".", "--hard", "10000"),
        command_check(root, sys.executable, "scripts/audit-quality-gates.py", "."),
        command_check(
            root,
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_*.py",
            "-v",
        ),
    ]


def full_checks(root: Path) -> list[Check]:
    return [
        *quick_checks(root),
        command_check(
            root, "shellcheck", *[str(path.relative_to(root)) for path in shell_files(root)]
        ),
        command_check(
            root,
            "shfmt",
            "-i",
            "4",
            "-d",
            *[str(path.relative_to(root)) for path in shell_files(root)],
        ),
        command_check(root, "ruff", "check", "scripts", "tests"),
        command_check(root, "ruff", "format", "--check", "scripts", "tests"),
        command_check(root, "ty", "check", "scripts", "tests"),
        command_check(root, "make", "validate-install"),
    ]


def checks_for_profile(root: Path, profile: str) -> list[Check]:
    if profile == "bootstrap":
        return bootstrap_checks(root)
    if profile == "quick":
        return quick_checks(root)
    checks = full_checks(root)
    if profile == "release":
        checks.extend(
            [
                command_check(root, sys.executable, "scripts/validate-actions-pins.py", "."),
                command_check(root, sys.executable, "scripts/validate-release-contract.py", "."),
            ]
        )
        checks.append(
            Check(
                "release git snapshot",
                lambda: validate_release_snapshot(root, RELEASE_REQUIRED_FILES),
            )
        )
    return checks


def run_profile(root: Path, profile: str) -> int:
    results: list[tuple[str, Result]] = []
    print(f"validation profile: {profile}")
    for check in checks_for_profile(root, profile):
        result = check.run()
        results.append((check.name, result))
        print(f"[{result.status.value}] {check.name}")
        if result.detail and result.status != Status.PASS:
            print(result.detail)

    failed = [name for name, result in results if result.status == Status.FAIL]
    skipped = [name for name, result in results if result.status == Status.SKIP]
    if failed:
        print(f"validation failed: {len(failed)} check(s)", file=sys.stderr)
        return 1
    if profile in {"full", "release"} and skipped:
        print(
            f"{profile} validation failed: {len(skipped)} skipped required check(s)",
            file=sys.stderr,
        )
        return 1
    if skipped:
        print(f"validation passed with {len(skipped)} skipped optional check(s)")
    else:
        print("validation passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to validate",
    )
    parser.add_argument(
        "--profile",
        choices=("quick", "bootstrap", "full", "release"),
        default="full",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"validation root does not exist: {root}", file=sys.stderr)
        return 2
    return run_profile(root, args.profile)


if __name__ == "__main__":
    raise SystemExit(main())
