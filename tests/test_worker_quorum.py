from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import shlex
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

quorum = importlib.import_module("worker_quorum")
snapshot = importlib.import_module("worker_snapshot")
evaluate_quorum = quorum.evaluate_quorum
target_digest = quorum.target_digest
capture_snapshot = snapshot.capture_snapshot
snapshot_digest = snapshot.snapshot_digest


def worker(reviewer: str, target: dict) -> dict:
    provider = f"synthetic-{reviewer}"
    artifacts = [f"{reviewer}/check.log", f"{reviewer}/launcher.json", f"{reviewer}/evidence.txt"]
    return {
        **{key: deepcopy(target[key]) for key in ("task_id", "goal", "base_commit", "snapshot")},
        "requested": {"provider": provider, "model": "synthetic-model"},
        "observed": {
            "provider": provider,
            "model": "synthetic-model",
            "source": artifacts[1],
            "verification": "runtime_metadata",
        },
        "status": "completed",
        "findings": [],
        "checks": [
            {
                "command": "fixture-check",
                "exit_code": 0,
                "outcome": "PASS",
                "raw_artifact": artifacts[0],
            }
        ],
        "artifacts": artifacts,
        "open_questions": [],
        "usage": "unknown",
    }


def envelope(mode: str = "quorum_2_of_3") -> dict:
    files = [{"path": "example.txt", "sha256": "a" * 64, "bytes": 1}]
    target = {
        "task_id": "synthetic-task",
        "goal": "Review the synthetic change",
        "base_commit": "b" * 40,
        "snapshot": {
            "state": "captured",
            "sha256": snapshot_digest("b" * 40, files),
            "files": files,
        },
        "acceptance_criteria": ["The synthetic change preserves its fixture contract"],
        "required_checks": ["fixture-check"],
        "artifacts": [
            {
                "path": "change.diff",
                "sha256": hashlib.sha256(b"synthetic patch").hexdigest(),
                "bytes": 15,
            }
        ],
    }
    voters = ["one", "two"] if mode == "consensus_2_of_2" else ["one", "two", "three"]
    ballots = []
    for reviewer in voters[:2]:
        record = worker(reviewer, target)
        ballots.append(
            {
                "reviewer_id": reviewer,
                "target_sha256": target_digest(target),
                "vote": "APPROVE",
                "reason": "Synthetic review completed",
                "record": record,
                "independence": {
                    "phase": "independent",
                    "peer_results_seen": [],
                    "source": record["artifacts"][1],
                },
                "concerns": [],
            }
        )
    payload = {
        "schema_version": 1,
        "target": target,
        "target_sha256": target_digest(target),
        "policy": {
            "mode": mode,
            "roster": [
                {"reviewer_id": reviewer, "requested": worker(reviewer, target)["requested"]}
                for reviewer in voters
            ],
            "author_ids": ["author"],
        },
        "gate_record": worker("gate", target),
        "ballots": ballots,
        "resolutions": [],
    }
    seal_policy(payload)
    seal_evidence(payload)
    return payload


def seal_policy(payload: dict) -> None:
    payload["policy_sha256"] = target_digest(payload["policy"])
    for ballot in payload["ballots"]:
        ballot["policy_sha256"] = payload["policy_sha256"]


def seal_evidence(payload: dict) -> None:
    paths = {
        path
        for record in [payload["gate_record"], *[ballot["record"] for ballot in payload["ballots"]]]
        for path in record["artifacts"]
    }
    content = b"Synthetic evidence only"
    payload["evidence_artifacts"] = [
        {"path": path, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        for path in sorted(paths)
    ]


def concern(ballot: dict, *, critical: bool = False, confirmed: bool = False) -> str:
    identifier = f"{ballot['reviewer_id']}:finding"
    ballot["vote"] = "REQUEST_CHANGES"
    ballot["concerns"] = [
        {
            "id": identifier,
            "severity": "critical" if critical else "noncritical",
            "evidence_artifact": ballot["record"]["artifacts"][2],
            "parent_confirmed": confirmed,
            "confirmation_artifact": ballot["record"]["artifacts"][1] if confirmed else None,
        }
    ]
    return identifier


class WorkerQuorumTests(unittest.TestCase):
    def test_fixed_two_approvals_from_distinct_providers_pass_policy(self) -> None:
        for mode in ("consensus_2_of_2", "quorum_2_of_3"):
            with self.subTest(mode=mode):
                result = evaluate_quorum(envelope(mode))
                self.assertEqual(
                    (result["decision"], result["outcome"]), ("ACCEPT", "PASS"), result
                )
                self.assertEqual(result["proof_scope"], "launcher_record_consistency_only")
                self.assertFalse(result["recommend_third_review"])

    def test_first_two_may_agree_and_still_include_an_independent_third(self) -> None:
        payload = envelope()
        third = deepcopy(payload["ballots"][0])
        third.update(reviewer_id="three", record=worker("three", payload["target"]))
        third["independence"]["source"] = third["record"]["artifacts"][1]
        payload["ballots"].append(third)
        seal_evidence(payload)
        self.assertEqual(evaluate_quorum(payload)["decision"], "ACCEPT")

    def test_required_failure_is_a_veto_despite_two_approvals(self) -> None:
        payload = envelope()
        payload["gate_record"]["checks"][0].update(outcome="FAIL", exit_code=7)
        result = evaluate_quorum(payload)
        self.assertEqual(result["decision"], "REQUEST_CHANGES")
        self.assertIn("required_check_failed:fixture-check", result["vetoes"])

    def test_deterministic_gate_needs_no_invented_model_route(self) -> None:
        payload = envelope()
        payload["gate_record"]["requested"] = {"provider": "unknown", "model": "unknown"}
        payload["gate_record"]["observed"] = dict.fromkeys(
            ("provider", "model", "source", "verification"), "unknown"
        )
        self.assertEqual(evaluate_quorum(payload)["decision"], "ACCEPT")
        payload["gate_record"]["checks"][0].update(
            outcome="SKIP", exit_code=None, reason="Gate not run", raw_artifact=None
        )
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")
        payload["gate_record"]["checks"] = []
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")

    def test_missing_or_skipped_required_gate_never_passes(self) -> None:
        payload = envelope()
        for record in [
            payload["gate_record"],
            *[ballot["record"] for ballot in payload["ballots"]],
        ]:
            record["checks"][0].update(command="scoped-review")
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")
        payload["gate_record"]["checks"][0].update(
            command="fixture-check",
            outcome="SKIP",
            exit_code=None,
            reason="Unavailable",
            raw_artifact=None,
        )
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")

    def test_confirmed_critical_counterexample_vetoes_majority(self) -> None:
        payload = envelope()
        third = deepcopy(payload["ballots"][0])
        third.update(reviewer_id="three", record=worker("three", payload["target"]))
        third["independence"]["source"] = third["record"]["artifacts"][1]
        identifier = concern(third, critical=True, confirmed=True)
        payload["ballots"].append(third)
        seal_evidence(payload)
        result = evaluate_quorum(payload)
        self.assertEqual(result["decision"], "REQUEST_CHANGES")
        self.assertIn(f"confirmed_critical:{identifier}", result["vetoes"])

    def test_unconfirmed_critical_claim_is_review_not_verified_veto(self) -> None:
        payload = envelope()
        concern(payload["ballots"][1], critical=True)
        result = evaluate_quorum(payload)
        self.assertEqual(result["decision"], "NEEDS_REVIEW")
        self.assertEqual(result["vetoes"], [])
        self.assertTrue(result["recommend_third_review"])

    def test_confirmed_veto_does_not_recommend_spending_on_third_vote(self) -> None:
        payload = envelope()
        concern(payload["ballots"][1], critical=True, confirmed=True)
        result = evaluate_quorum(payload)
        self.assertEqual(result["decision"], "REQUEST_CHANGES")
        self.assertFalse(result["recommend_third_review"])

    def test_noncritical_disagreement_needs_evidenced_cross_provider_resolution(self) -> None:
        payload = envelope()
        identifier = concern(payload["ballots"][1])
        result = evaluate_quorum(payload)
        self.assertEqual(result["decision"], "NEEDS_REVIEW")
        self.assertTrue(result["recommend_third_review"])
        third = deepcopy(payload["ballots"][0])
        third.update(reviewer_id="three", record=worker("three", payload["target"]))
        third["independence"]["source"] = third["record"]["artifacts"][1]
        payload["ballots"].append(third)
        seal_evidence(payload)
        self.assertEqual(evaluate_quorum(payload)["decision"], "NEEDS_REVIEW")
        payload["resolutions"] = [
            {
                "concern_id": identifier,
                "reviewed_by": ["one", "three"],
                "evidence": [
                    {"reviewer_id": reviewer, "artifact": f"{reviewer}/evidence.txt"}
                    for reviewer in ("one", "three")
                ],
            }
        ]
        self.assertEqual(evaluate_quorum(payload)["decision"], "ACCEPT")

    def test_abstention_timeout_or_failed_reviewer_does_not_lower_threshold(self) -> None:
        for mutation in ("abstain", "blocked", "failed"):
            with self.subTest(mutation=mutation):
                payload = envelope()
                ballot = payload["ballots"][1]
                if mutation == "abstain":
                    ballot["vote"] = "ABSTAIN"
                else:
                    ballot["record"].update(status=mutation, reason="Synthetic timeout")
                result = evaluate_quorum(payload)
                self.assertEqual(result["decision"], "BLOCKED", result)
                self.assertEqual(result["approvals"], 1)
                self.assertFalse(result["recommend_third_review"])

    def test_unknown_models_alias_collision_and_informed_reviews_do_not_vote(self) -> None:
        payload = envelope()
        payload["ballots"][1]["record"]["observed"] = dict.fromkeys(
            ("provider", "model", "source", "verification"), "unknown"
        )
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")
        payload = envelope()
        payload["policy"]["roster"][1]["requested"]["provider"] = "SYNTHETIC-ONE"
        payload["ballots"][1]["record"]["requested"]["provider"] = "SYNTHETIC-ONE"
        payload["ballots"][1]["record"]["observed"]["provider"] = "SYNTHETIC-ONE"
        seal_policy(payload)
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")
        payload = envelope()
        payload["ballots"][1]["independence"].update(phase="informed", peer_results_seen=["one"])
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")

    def test_two_models_of_same_provider_cannot_form_cross_provider_quorum(self) -> None:
        payload = envelope()
        route = {"provider": "synthetic-one", "model": "different-model"}
        payload["policy"]["roster"][1]["requested"] = route.copy()
        payload["ballots"][1]["record"]["requested"] = route.copy()
        payload["ballots"][1]["record"]["observed"].update(route)
        seal_policy(payload)
        self.assertEqual(evaluate_quorum(payload)["decision"], "BLOCKED")

    def test_roster_substitution_author_vote_and_replays_are_invalid(self) -> None:
        for mutation in ("substitute", "author", "replay", "extra"):
            with self.subTest(mutation=mutation):
                payload = envelope("consensus_2_of_2")
                if mutation == "substitute":
                    payload["ballots"][1]["reviewer_id"] = "replacement"
                elif mutation == "author":
                    payload["policy"]["author_ids"].append("one")
                elif mutation == "replay":
                    payload["ballots"][1] = deepcopy(payload["ballots"][0])
                else:
                    payload["ballots"].append(deepcopy(payload["ballots"][0]))
                self.assertEqual(evaluate_quorum(payload)["decision"], "INVALID")

    def test_changed_dirty_snapshot_goal_criteria_or_artifact_is_invalid(self) -> None:
        for mutation in ("snapshot", "goal", "criteria", "artifact", "route"):
            with self.subTest(mutation=mutation):
                payload = envelope()
                if mutation == "snapshot":
                    files = payload["ballots"][1]["record"]["snapshot"]["files"]
                    files[0]["sha256"] = "c" * 64
                    payload["ballots"][1]["record"]["snapshot"]["sha256"] = snapshot_digest(
                        "b" * 40, files
                    )
                elif mutation == "goal":
                    payload["ballots"][1]["record"]["goal"] = "Another goal"
                elif mutation == "criteria":
                    payload["target"]["acceptance_criteria"].append("Changed criteria")
                elif mutation == "artifact":
                    payload["target"]["artifacts"][0]["sha256"] = "c" * 64
                else:
                    payload["ballots"][1]["record"]["observed"]["model"] = "fallback-model"
                self.assertEqual(evaluate_quorum(payload)["decision"], "INVALID")

    def test_known_failure_is_retained_when_another_ballot_is_malformed(self) -> None:
        payload = envelope()
        payload["gate_record"]["checks"][0].update(outcome="FAIL", exit_code=9)
        payload["ballots"][1]["vote"] = "PASS"
        result = evaluate_quorum(payload)
        self.assertEqual(result["decision"], "INVALID")
        self.assertIn("required_check_failed:fixture-check", result["vetoes"])

    def test_ballot_failures_are_retained_even_before_an_invalid_vote(self) -> None:
        payload = envelope()
        payload["ballots"][0]["vote"] = "PASS"
        payload["ballots"][1]["record"]["checks"][0].update(outcome="FAIL", exit_code=7)
        result = evaluate_quorum(payload)
        self.assertEqual(result["decision"], "INVALID")
        self.assertIn("required_check_failed:fixture-check", result["vetoes"])

    def test_policy_changes_after_ballots_and_evidence_coverage_are_invalid(self) -> None:
        for mutation in ("roster", "authors", "evidence", "extra_evidence"):
            with self.subTest(mutation=mutation):
                payload = envelope()
                if mutation == "roster":
                    payload["policy"]["roster"][2]["reviewer_id"] = "replacement"
                    payload["policy_sha256"] = target_digest(payload["policy"])
                elif mutation == "authors":
                    payload["policy"]["author_ids"].append("another-author")
                elif mutation == "evidence":
                    payload["evidence_artifacts"].pop()
                else:
                    extra = deepcopy(payload["evidence_artifacts"][-1])
                    extra["path"] = "unreferenced.log"
                    payload["evidence_artifacts"].append(extra)
                self.assertEqual(evaluate_quorum(payload)["decision"], "INVALID")

    def test_malformed_and_unbounded_collections_fail_without_crashing(self) -> None:
        for value in (None, [], {"schema_version": True}, {"schema_version": 2}):
            self.assertEqual(evaluate_quorum(value)["decision"], "INVALID")
        payload = envelope()
        payload["target"]["acceptance_criteria"] *= 65
        self.assertEqual(evaluate_quorum(payload)["decision"], "INVALID")


class WorkerQuorumCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.artifacts = self.root / "artifacts"
        self.source.mkdir()
        self.artifacts.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.source)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.source),
                "-c",
                "user.name=Synthetic Test",
                "-c",
                "user.email=synthetic@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--allow-empty",
                "--quiet",
                "-m",
                "synthetic input",
            ],
            check=True,
        )
        (self.source / "example.txt").write_text("synthetic source")
        self.payload = envelope()
        self.payload["target"].update(capture_snapshot(self.source, ["example.txt"]))
        self.payload["target_sha256"] = target_digest(self.payload["target"])
        self.payload["gate_record"] = worker("gate", self.payload["target"])
        for ballot in self.payload["ballots"]:
            ballot["record"] = worker(ballot["reviewer_id"], self.payload["target"])
            ballot["target_sha256"] = self.payload["target_sha256"]
        for record in [
            self.payload["gate_record"],
            *[ballot["record"] for ballot in self.payload["ballots"]],
        ]:
            for name in record["artifacts"]:
                path = self.artifacts / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Synthetic evidence only")
        (self.artifacts / "change.diff").write_bytes(b"synthetic patch")
        self.request = self.root / "request.json"

    def run_cli(self, *extra: str) -> subprocess.CompletedProcess[str]:
        self.request.write_text(json.dumps(self.payload))
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/worker-evidence.py"),
                "quorum",
                str(self.request),
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def roots(self) -> tuple[str, ...]:
        return ("--source-root", str(self.source), "--artifacts-root", str(self.artifacts))

    def test_roots_are_required_for_a_cli_pass(self) -> None:
        result = self.run_cli()
        self.assertEqual(result.returncode, 2, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["outcome"], "SKIP")
        self.assertEqual((output["source_status"], output["artifact_status"]), ("SKIP", "SKIP"))
        result = self.run_cli(*self.roots())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "ACCEPT")

    def test_actual_failing_gate_exit_and_raw_bytes_veto_two_approvals(self) -> None:
        command = [sys.executable, "-c", "import sys; print('synthetic failure'); sys.exit(7)"]
        executed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)
        raw = executed.stdout + executed.stderr
        (self.artifacts / "gate/check.log").write_text(raw)
        command_text = shlex.join(command)
        self.payload["target"]["required_checks"] = [command_text]
        self.payload["target_sha256"] = target_digest(self.payload["target"])
        self.payload["gate_record"]["checks"][0].update(
            command=command_text, outcome="FAIL", exit_code=executed.returncode
        )
        for ballot in self.payload["ballots"]:
            ballot["target_sha256"] = self.payload["target_sha256"]
        self.payload["evidence_artifacts"] = capture_snapshot(
            self.artifacts, [item["path"] for item in self.payload["evidence_artifacts"]]
        )["snapshot"]["files"]
        result = self.run_cli(*self.roots())
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["decision"], "REQUEST_CHANGES")
        self.assertEqual(output["approvals"], 2)
        self.assertEqual((self.artifacts / "gate/check.log").read_text(), raw)
        self.assertEqual(executed.returncode, 7)

    def test_review_and_evidence_symlinks_fail_safe_verification(self) -> None:
        for relative in ("change.diff", "two/launcher.json"):
            with self.subTest(relative=relative):
                path = self.artifacts / relative
                original = path.read_bytes()
                replacement = self.artifacts / "synthetic-copy.txt"
                replacement.write_bytes(original)
                path.unlink()
                path.symlink_to(replacement)
                result = self.run_cli(*self.roots())
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                path.unlink()
                path.write_bytes(original)

    def test_stale_source_changed_review_artifact_or_missing_evidence_is_failure(self) -> None:
        for mutation in (
            "source",
            "target",
            "evidence",
            "raw_check",
            "route_and_independence",
            "finding_and_resolution",
        ):
            with self.subTest(mutation=mutation):
                changed = (
                    self.source / "example.txt"
                    if mutation == "source"
                    else self.artifacts
                    / (
                        "change.diff"
                        if mutation == "target"
                        else "two/launcher.json"
                        if mutation == "route_and_independence"
                        else "two/evidence.txt"
                        if mutation == "finding_and_resolution"
                        else "two/check.log"
                    )
                )
                original = changed.read_bytes()
                if mutation == "evidence":
                    changed.unlink()
                else:
                    changed.write_bytes(b"Changed bytes")
                result = self.run_cli(*self.roots())
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["outcome"], "FAIL")
                changed.write_bytes(original)

    def test_duplicate_keys_nonfinite_and_large_json_are_rejected(self) -> None:
        command = [
            sys.executable,
            str(ROOT / "scripts/worker-evidence.py"),
            "quorum",
            str(self.request),
        ]
        for text in (
            '{"schema_version":1,"schema_version":1}',
            '{"value":NaN}',
            " " * (8 * 1024 * 1024 + 1),
        ):
            self.request.write_text(text)
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, timeout=10
            )
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
