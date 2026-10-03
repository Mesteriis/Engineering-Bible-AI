#!/usr/bin/env python3
"""Stdlib-only isolated child reporter for the targeted mutation runner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import sys
import unittest


MAX_REPORT_BYTES = 2 * 1024 * 1024


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("modules", nargs="+")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    # The isolated interpreter contributes only standard-library paths. Project
    # imports can resolve solely from this case's private source snapshot.
    sys.path[:0] = [str(root), str(root / "scripts")]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(args.modules)

    class Result(unittest.TestResult):
        def __init__(self) -> None:
            super().__init__()
            self.identities: list[str] = []

        def startTest(self, test: unittest.case.TestCase) -> None:
            self.identities.append(test.id())
            super().startTest(test)

    result = Result()
    suite.run(result)

    def entries(
        values: Sequence[tuple[unittest.case.TestCase, str]],
    ) -> list[dict[str, str]]:
        return [{"test_id": item.id(), "detail": detail[:8192]} for item, detail in values]

    payload = {
        "tests_run": result.testsRun,
        "test_ids": result.identities,
        "failures": entries(result.failures),
        "errors": entries(result.errors)
        + [{"test_id": "<loader>", "detail": str(error)[:8192]} for error in loader.errors],
        "skipped": entries(result.skipped),
        # Tracebacks embed the private per-case workspace path. Keep only the
        # stable outcome identity for cross-run comparisons.
        "expected_failures": [test.id() for test, _ in result.expectedFailures],
        "unexpected_successes": [test.id() for test in result.unexpectedSuccesses],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        raise RuntimeError("test report exceeded size limit")
    args.report.write_bytes(encoded)
    return (
        1 if result.failures or result.errors or loader.errors or result.unexpectedSuccesses else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
