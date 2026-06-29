# `be` CLI Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working `be` console utility with version, doctor, validate, and install dry-run support, then install a `be` wrapper with the existing package installer.

**Architecture:** Add a Python standard-library CLI at `scripts/be.py` and keep `scripts/install-codex.sh` as the install engine. `be` is a management layer that resolves paths, runs repository validation, prints machine-readable doctor output, and delegates installation instead of duplicating file-copy behavior.

**Tech Stack:** Python 3 standard library, Bash installer scripts, `make`, `unittest`, existing validation scripts.

---

## Scope

This plan implements Phase 1 from `docs/superpowers/specs/2026-06-28-be-cli-design.md`.

Included:

- `be version`
- `be doctor [--json]`
- `be validate [--checkout PATH]`
- `be install --dry-run`
- installer-created `be` wrapper
- local smoke tests and CI integration through `make validate`

Deferred to later plans:

- `be update`
- `be self-update`
- profiles
- lockfile
- external skill add/remove
- rollback
- export/import

## File Structure

- Create `scripts/be.py`: Python CLI entrypoint and command implementations.
- Create `tests/test_be_cli.py`: `unittest` smoke tests for the Phase 1 commands.
- Modify `scripts/install-codex.sh`: copy `be.py` through the existing `scripts/` sync and write a `be` wrapper into `BIN_DIR`.
- Modify `scripts/validate-skill-tree.sh`: require `scripts/be.py`.
- Modify `Makefile`: add `be-smoke` and include it in `make validate`.
- Verify `.github/workflows/validate.yml`: no edit expected because it already runs `make validate`.
- Modify `README.md` and `README.ru.md`: document `be` commands.
- Modify `CONTRIBUTING.md` and `docs/oss-release-checklist.md`: include the CLI smoke test in expanded validation.
- Modify `MANIFEST.md`: list `scripts/be.py` and the installed `be` command.

## Task 1: Add CLI Smoke Tests

**Files:**

- Create: `tests/test_be_cli.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_be_cli.py` with this content:

```python
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "scripts" / "be.py"


class BeCliTests(unittest.TestCase):
    def run_be(self, *args: str, tmp: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CODEX_HOME": str(tmp / "codex"),
                "AGENTS_HOME": str(tmp / "agents"),
                "ENGINEERING_BIBLE_HOME": str(tmp / "engineering-bible"),
                "ENGINEERING_BIBLE_BIN_DIR": str(tmp / "bin"),
            }
        )
        return subprocess.run(
            [sys.executable, str(BE), *args],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_version_prints_tool_name(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("version", tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Engineering Bible AI", result.stdout)
        self.assertIn("be", result.stdout)

    def test_doctor_json_reports_required_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("doctor", "--json", tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tool"], "be")
        self.assertIn(payload["status"], {"ok", "warn"})
        check_names = {check["name"] for check in payload["checks"]}
        self.assertIn("python3", check_names)
        self.assertIn("rsync", check_names)
        self.assertIn("repository", check_names)
        self.assertIn("runtime-boundary", check_names)

    def test_validate_checkout_runs_repository_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_be("validate", "--checkout", str(ROOT), tmp=Path(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("skill tree validation passed", result.stdout)
        self.assertIn("skill frontmatter validation passed", result.stdout)

    def test_install_dry_run_delegates_to_installer_without_writing_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            result = self.run_be("install", "--dry-run", tmp=tmp)
            wrapper = tmp / "bin" / "be"

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Mode: --dry-run", result.stdout)
        self.assertIn("[dry-run] write be wrapper", result.stdout)
        self.assertFalse(wrapper.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify they fail because `scripts/be.py` does not exist**

Run:

```bash
python3 -m unittest tests/test_be_cli.py -v
```

Expected: `ERROR` or `FAIL` for all tests with output showing Python cannot open `scripts/be.py`.

## Task 2: Implement `scripts/be.py`

**Files:**

- Create: `scripts/be.py`
- Test: `tests/test_be_cli.py`

- [ ] **Step 1: Create the CLI implementation**

Create `scripts/be.py` with this content:

```python
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
```

- [ ] **Step 2: Make the script executable**

Run:

```bash
chmod +x scripts/be.py
```

- [ ] **Step 3: Run the CLI tests**

Run:

```bash
python3 -m unittest tests/test_be_cli.py -v
```

Expected: all tests pass except `test_install_dry_run_delegates_to_installer_without_writing_wrapper` if `scripts/install-codex.sh` does not yet print the wrapper dry-run lines. That test is completed in Task 3.

## Task 3: Install the `be` Wrapper

**Files:**

- Modify: `scripts/install-codex.sh`
- Modify: `scripts/validate-skill-tree.sh`
- Test: `tests/test_be_cli.py`

- [ ] **Step 1: Add `BIN_DIR` support to `scripts/install-codex.sh`**

In `scripts/install-codex.sh`, after this line:

```bash
agent_skill_root="$agents_home/skills"
```

add:

```bash
bin_dir="${ENGINEERING_BIBLE_BIN_DIR:-$HOME/.local/bin}"
```

After:

```bash
printf 'Agents home: %s\n' "$agents_home"
```

add:

```bash
printf 'Bin dir: %s\n' "$bin_dir"
```

- [ ] **Step 2: Add the wrapper writer function**

In `scripts/install-codex.sh`, after `copy_skill()`, add:

```bash
write_be_wrapper() {
  local wrapper_path="$bin_dir/be"
  local target_script="$codex_home/scripts/be.py"

  if [[ "$mode" == "--dry-run" ]]; then
    printf '[dry-run] mkdir -p %q\n' "$bin_dir"
    printf '[dry-run] write be wrapper %q -> %q\n' "$wrapper_path" "$target_script"
    return
  fi

  mkdir -p "$bin_dir"
  cat >"$wrapper_path" <<EOF
#!/usr/bin/env bash
exec python3 "$target_script" "\$@"
EOF
  chmod +x "$wrapper_path"
  printf 'Installed be wrapper: %s\n' "$wrapper_path"
}
```

- [ ] **Step 3: Call the wrapper writer**

In `scripts/install-codex.sh`, after:

```bash
run chmod +x "$codex_home/scripts/secret-sanity.sh"
```

add:

```bash
run chmod +x "$codex_home/scripts/be.py"
write_be_wrapper
```

- [ ] **Step 4: Require `scripts/be.py` in tree validation**

In `scripts/validate-skill-tree.sh`, add this item after `"scripts/install.sh"`:

```bash
  "scripts/be.py"
```

- [ ] **Step 5: Run the wrapper-focused test**

Run:

```bash
python3 -m unittest tests.test_be_cli.BeCliTests.test_install_dry_run_delegates_to_installer_without_writing_wrapper -v
```

Expected: `OK`.

- [ ] **Step 6: Run all CLI tests**

Run:

```bash
python3 -m unittest tests/test_be_cli.py -v
```

Expected: `OK`.

- [ ] **Step 7: Commit CLI foundation**

Run:

```bash
git add scripts/be.py scripts/install-codex.sh scripts/validate-skill-tree.sh tests/test_be_cli.py
git commit -m "feat: add be CLI foundation"
```

## Task 4: Add `make be-smoke`

**Files:**

- Modify: `Makefile`
- Test: `tests/test_be_cli.py`

- [ ] **Step 1: Update `.PHONY`**

Replace the `.PHONY` line in `Makefile` with:

```make
.PHONY: help validate validate-tree validate-skills size secrets shell-syntax py-compile be-smoke dry-run install install-command
```

- [ ] **Step 2: Include `be-smoke` in validation**

Replace:

```make
validate: validate-tree validate-skills size secrets shell-syntax py-compile
```

with:

```make
validate: validate-tree validate-skills size secrets shell-syntax py-compile be-smoke
```

- [ ] **Step 3: Keep shell syntax checks scoped to shell scripts**

Verify that `shell-syntax` remains scoped to shell scripts:

```make
shell-syntax:
    bash -n scripts/install.sh scripts/install-codex.sh scripts/secret-sanity.sh scripts/validate-skill-tree.sh
```

No shell syntax command is needed for `scripts/be.py`; it is covered by `py-compile` and `be-smoke`.

- [ ] **Step 4: Add the `be-smoke` target**

After the `py-compile` target, add:

```make
be-smoke:
    $(PYTHON) -m unittest tests/test_be_cli.py -v
```

- [ ] **Step 5: Run `make be-smoke`**

Run:

```bash
make be-smoke
```

Expected: `OK`.

- [ ] **Step 6: Run `make validate`**

Run:

```bash
make validate
```

Expected: all checks pass, including `be-smoke`.

- [ ] **Step 7: Commit Makefile integration**

Run:

```bash
git add Makefile
git commit -m "test: add be CLI smoke target"
```

## Task 5: Document the Phase 1 CLI

**Files:**

- Modify: `README.md`
- Modify: `README.ru.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/oss-release-checklist.md`
- Modify: `MANIFEST.md`

- [ ] **Step 1: Update `README.md` install section**

In `README.md`, after the install commands and before the backup note, add:

````markdown
After installation, the package also installs a small `be` manager command into
`~/.local/bin/be` by default. If `~/.local/bin` is not on your shell `PATH`,
run the command through `~/.local/bin/be` or add that directory to `PATH`.

Initial `be` commands:

```bash
be version
be doctor
be doctor --json
be validate --checkout .
be install --dry-run
```
````

- [ ] **Step 2: Update `README.ru.md` install section**

In `README.ru.md`, after the install commands and before the backup note, add:

````markdown
После установки пакет также ставит маленькую команду `be` в `~/.local/bin/be`
по умолчанию. Если `~/.local/bin` не входит в shell `PATH`, запускай команду
через `~/.local/bin/be` или добавь этот каталог в `PATH`.

Первые команды `be`:

```bash
be version
be doctor
be doctor --json
be validate --checkout .
be install --dry-run
```
````

- [ ] **Step 3: Update `CONTRIBUTING.md` validation commands**

In the expanded validation block, add this command after Python compilation:

```bash
python3 -m unittest tests/test_be_cli.py -v
```

- [ ] **Step 4: Update `docs/oss-release-checklist.md` validation commands**

In the expanded validation block, add this command after Python compilation:

```bash
python3 -m unittest tests/test_be_cli.py -v
```

- [ ] **Step 5: Update `MANIFEST.md` command entry points**

In `MANIFEST.md`, under `## Command Entry Points`, add:

```markdown
- `scripts/be.py`
- installed wrapper: `be`
```

- [ ] **Step 6: Run documentation checks**

Run:

```bash
git diff --check -- README.md README.ru.md CONTRIBUTING.md docs/oss-release-checklist.md MANIFEST.md
```

Expected: no output and exit code `0`.

- [ ] **Step 7: Run full validation**

Run:

```bash
make validate
```

Expected: all checks pass.

- [ ] **Step 8: Commit documentation**

Run:

```bash
git add README.md README.ru.md CONTRIBUTING.md docs/oss-release-checklist.md MANIFEST.md
git commit -m "docs: document be CLI foundation"
```

## Task 6: Final Verification

**Files:**

- Verify: full repository

- [ ] **Step 1: Run full validation**

Run:

```bash
make validate
```

Expected: all checks pass.

- [ ] **Step 2: Run direct CLI commands**

Run:

```bash
python3 scripts/be.py version
python3 scripts/be.py doctor --json
python3 scripts/be.py validate --checkout .
python3 scripts/be.py install --dry-run
```

Expected:

- `version` prints `Engineering Bible AI be 0.1.0`.
- `doctor --json` returns valid JSON with `tool` set to `be`.
- `validate --checkout .` exits `0`.
- `install --dry-run` exits `0` and prints `[dry-run] write be wrapper`.

- [ ] **Step 3: Verify repository status**

Run:

```bash
git status --short --branch
```

Expected: branch is ahead by the implementation commits and no unstaged changes remain.

## Plan Self-Review Notes

- Spec coverage: this plan implements Phase 1 CLI foundation and deliberately leaves update, self-update, profiles, lockfile, external skills, export/import, and rollback for later plans.
- File boundaries: `scripts/be.py` owns CLI behavior; `scripts/install-codex.sh` remains the file-copy installer; `tests/test_be_cli.py` owns CLI smoke coverage.
- Runtime boundary: the plan does not edit `~/.codex/config.toml`, auth files, `.env`, MCP credentials, or worker runtime state.
