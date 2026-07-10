from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_acceptance", ROOT / "scripts" / "validate-acceptance.py"
)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class AcceptanceTests(unittest.TestCase):
    def test_pass_requires_evidence(self) -> None:
        payload = {
            "schema_version": 1,
            "revision": "abc123",
            "criteria": [{"id": "AC-1", "requirement": "works", "status": "pass", "evidence": []}],
        }
        self.assertTrue(
            any("cannot be pass without evidence" in issue for issue in module.validate(payload))
        )

    def test_ui_and_migration_require_specialized_evidence(self) -> None:
        payload = {
            "schema_version": 1,
            "revision": "abc123",
            "criteria": [
                {
                    "id": "UI-1",
                    "requirement": "visible",
                    "class": "ui",
                    "status": "pass",
                    "evidence": [{"type": "test", "result": "ok"}],
                },
                {
                    "id": "M-1",
                    "requirement": "upgrade and rollback",
                    "class": "migration",
                    "status": "pass",
                    "evidence": [{"type": "runtime", "scenario": "upgrade", "result": "ok"}],
                },
            ],
        }
        issues = module.validate(payload)
        self.assertTrue(any("UI pass" in issue for issue in issues))
        self.assertTrue(any("upgrade and rollback" in issue for issue in issues))

    def test_blocked_requires_reason(self) -> None:
        payload = {
            "schema_version": 1,
            "revision": "abc123",
            "criteria": [
                {"id": "AC-1", "requirement": "blocked", "status": "blocked", "evidence": []}
            ],
        }
        self.assertTrue(any("requires a reason" in issue for issue in module.validate(payload)))
