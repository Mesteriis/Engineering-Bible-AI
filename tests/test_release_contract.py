from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


release_contract = load_script("release_contract", "validate-release-contract.py")
actions_pins = load_script("actions_pins", "validate-actions-pins.py")


class ReleaseContractTests(unittest.TestCase):
    def make_tree(self, root: Path, *, version: str = "1.2.3") -> None:
        (root / "VERSION").write_text(version + "\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text(
            f"# Changelog\n\n## [{version}] - 2026-07-10\n\n- Change.\n",
            encoding="utf-8",
        )
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "example"\nversion = "{version}"\n',
            encoding="utf-8",
        )
        scripts = root / "scripts"
        scripts.mkdir()
        (scripts / "install.sh").write_text(
            f'#!/usr/bin/env bash\nBOOTSTRAP_VERSION="{version}"\n', encoding="utf-8"
        )

    def test_release_contract_accepts_matching_semver(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_tree(root)

            self.assertEqual(release_contract.validate(root), [])

    def test_release_contract_rejects_version_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_tree(root)
            (root / "pyproject.toml").write_text(
                '[project]\nname = "example"\nversion = "9.9.9"\n',
                encoding="utf-8",
            )

            issues = release_contract.validate(root)

        self.assertTrue(any("pyproject" in issue for issue in issues), issues)

    def test_release_contract_rejects_non_semver(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_tree(root, version="main")

            issues = release_contract.validate(root)

        self.assertTrue(any("SemVer" in issue for issue in issues), issues)

    def test_release_contract_rejects_mismatched_trigger_tag(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_tree(root)

            issues = release_contract.validate(root, trigger_tag="v9.9.9")

        self.assertTrue(any("trigger tag" in issue for issue in issues), issues)

    def test_release_contract_rejects_bootstrap_version_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.make_tree(root)
            (root / "scripts" / "install.sh").write_text(
                '#!/usr/bin/env bash\nBOOTSTRAP_VERSION="9.9.9"\n', encoding="utf-8"
            )

            issues = release_contract.validate(root)

        self.assertTrue(any("bootstrap version" in issue for issue in issues), issues)

    def test_actions_must_use_full_sha(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "bad.yml").write_text(
                "steps:\n  - uses: actions/checkout@v4\n",
                encoding="utf-8",
            )

            issues = actions_pins.validate(root)

        self.assertEqual(len(issues), 1)
        self.assertIn("full 40-character commit SHA", issues[0])

    def test_actions_allow_full_sha_and_local_action(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "good.yml").write_text(
                "steps:\n"
                "  - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5\n"
                "  - uses: ./local-action\n",
                encoding="utf-8",
            )

            self.assertEqual(actions_pins.validate(root), [])


if __name__ == "__main__":
    unittest.main()
