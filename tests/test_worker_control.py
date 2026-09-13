from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("worker_control", ROOT / "scripts/worker_control.py")
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
evaluate_continuation = module.evaluate_continuation


def request() -> dict:
    return {
        "schema_version": 1,
        "limits": {
            "max_steps": 10,
            "max_no_progress": 3,
            "max_consecutive_failures": 2,
            "max_tokens": 1000,
            "max_tool_calls": 20,
            "max_duration_ms": 10000,
            "checkpoint_interval": 3,
        },
        "state": {
            "run_id": "run-1",
            "snapshot_sha256": "a" * 64,
            "step": 0,
            "tokens": 0,
            "tool_calls": 0,
            "duration_ms": 0,
            "no_progress_steps": 0,
            "consecutive_failures": 0,
            "last_checkpoint_step": 0,
            "last_progress_sha256": "b" * 64,
        },
        "observation": {
            "run_id": "run-1",
            "snapshot_sha256": "a" * 64,
            "step": 1,
            "tokens": 100,
            "tool_calls": 1,
            "duration_ms": 1000,
            "progress_sha256": "c" * 64,
            "check_outcome": "PASS",
            "checkpoint_ack": False,
        },
    }


def advance(payload: dict, result: dict) -> None:
    payload["state"] = result["next_state"]
    payload["observation"]["step"] += 1
    payload["observation"]["duration_ms"] += 100


class WorkerControlTests(unittest.TestCase):
    def test_cli_loop_stops_real_repeated_work_and_persists_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = request()
            payload["limits"].update(
                max_tokens=10000, max_tool_calls=50, max_duration_ms=60000, checkpoint_interval=1
            )
            launched = 0
            decisions = []
            started = time.monotonic()
            while launched < 10:
                process = subprocess.run(
                    [sys.executable, "-c", "print('unchanged result')"],
                    capture_output=True,
                    check=False,
                )
                launched += 1
                (root / f"raw-{launched}.txt").write_bytes(process.stdout + process.stderr)
                observation = payload["observation"]
                observation.update(
                    step=launched,
                    tool_calls=launched,
                    tokens=0,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    progress_sha256=hashlib.sha256(process.stdout).hexdigest(),
                    checkpoint_ack=False,
                )
                request_file = root / "request.json"
                request_file.write_text(json.dumps(payload))
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/worker-evidence.py"),
                        "continue",
                        str(request_file),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                decision = json.loads(result.stdout)
                decisions.append(decision["decision"])
                state_file = root / "state.json"
                state_file.write_text(json.dumps(decision["next_state"]))
                payload["state"] = json.loads(state_file.read_text())
                if decision["decision"] == "checkpoint":
                    self.assertEqual(result.returncode, 2)
                    observation["checkpoint_ack"] = True
                    request_file.write_text(json.dumps(payload))
                    ack = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "scripts/worker-evidence.py"),
                            "continue",
                            str(request_file),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(ack.returncode, 0, ack.stdout + ack.stderr)
                    payload["state"] = json.loads(ack.stdout)["next_state"]
                elif decision["decision"] == "stop":
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("max_no_progress", decision["reasons"])
                    break
            self.assertEqual(launched, 4)
            self.assertEqual(decisions, ["checkpoint", "checkpoint", "checkpoint", "stop"])
            self.assertEqual(payload["state"]["terminal_decision"], "stop")

    def test_accepts_progress_without_mutating_input(self) -> None:
        payload = request()
        original = deepcopy(payload)
        result = evaluate_continuation(payload)
        self.assertEqual(result["decision"], "continue")
        self.assertEqual(result["next_state"]["step"], 1)
        self.assertEqual(result["next_state"]["last_progress_sha256"], "c" * 64)
        self.assertEqual(result["next_state"]["tokens"], 100)
        self.assertEqual(payload, original)
        json.dumps(result, allow_nan=False)

    def test_each_budget_stops_at_exact_limit(self) -> None:
        for counter in ("step", "tokens", "tool_calls", "duration_ms"):
            with self.subTest(counter=counter):
                payload = request()
                limit = "max_steps" if counter == "step" else "max_" + counter
                payload["limits"][limit] = payload["observation"][counter]
                result = evaluate_continuation(payload)
                self.assertEqual(result["decision"], "stop", result)
                self.assertIn(limit, result["reasons"])
                self.assertEqual(result["next_state"][counter], payload["observation"][counter])

    def test_reports_all_exhausted_budgets(self) -> None:
        payload = request()
        payload["limits"].update(max_tokens=100, max_duration_ms=1000, max_tool_calls=1)
        result = evaluate_continuation(payload)
        self.assertEqual(result["decision"], "stop")
        self.assertEqual(
            set(result["reasons"]), {"max_tokens", "max_duration_ms", "max_tool_calls"}
        )

    def test_no_progress_stops_and_cannot_be_resumed_by_new_progress(self) -> None:
        payload = request()
        payload["limits"]["checkpoint_interval"] = 10
        payload["observation"]["progress_sha256"] = "b" * 64
        for step in range(1, 4):
            result = evaluate_continuation(payload)
            self.assertEqual(result["next_state"]["no_progress_steps"], step)
            self.assertEqual(result["decision"], "stop" if step == 3 else "continue")
            advance(payload, result)
        payload["observation"]["progress_sha256"] = "d" * 64
        self.assertEqual(evaluate_continuation(payload)["decision"], "stop")

    def test_verified_progress_resets_no_progress_counter(self) -> None:
        payload = request()
        payload["observation"]["progress_sha256"] = "b" * 64
        result = evaluate_continuation(payload)
        advance(payload, result)
        payload["observation"]["progress_sha256"] = "c" * 64
        result = evaluate_continuation(payload)
        self.assertEqual(result["decision"], "continue")
        self.assertEqual(result["next_state"]["no_progress_steps"], 0)

    def test_failed_and_skipped_checks_do_not_reset_no_progress(self) -> None:
        for outcome in ("FAIL", "SKIP"):
            with self.subTest(outcome=outcome):
                payload = request()
                payload["observation"]["check_outcome"] = outcome
                result = evaluate_continuation(payload)
                self.assertEqual(result["next_state"]["no_progress_steps"], 1)

    def test_unverified_digest_cannot_make_repeated_verified_output_new_progress(self) -> None:
        for outcome in ("FAIL", "SKIP"):
            with self.subTest(outcome=outcome):
                payload = request()
                payload["limits"].update(checkpoint_interval=10, max_no_progress=2)
                first = evaluate_continuation(payload)
                advance(payload, first)
                payload["observation"].update(check_outcome=outcome, progress_sha256="d" * 64)
                unverified = evaluate_continuation(payload)
                self.assertEqual(unverified["decision"], "continue")
                self.assertEqual(unverified["next_state"]["last_progress_sha256"], "c" * 64)
                self.assertEqual(unverified["next_state"]["last_observation_sha256"], "d" * 64)
                advance(payload, unverified)
                payload["observation"].update(check_outcome="PASS", progress_sha256="c" * 64)
                repeated = evaluate_continuation(payload)
                self.assertEqual(repeated["decision"], "stop")
                self.assertEqual(repeated["next_state"]["no_progress_steps"], 2)
                self.assertIn("max_no_progress", repeated["reasons"])

    def test_unverified_checkpoint_ack_replays_observation_without_changing_progress(self) -> None:
        for outcome in ("FAIL", "SKIP"):
            with self.subTest(outcome=outcome):
                payload = request()
                payload["limits"]["checkpoint_interval"] = 1
                payload["observation"]["check_outcome"] = outcome
                checkpoint = evaluate_continuation(payload)
                self.assertEqual(checkpoint["decision"], "checkpoint")
                self.assertEqual(checkpoint["next_state"]["last_progress_sha256"], "b" * 64)
                payload["state"] = checkpoint["next_state"]
                payload["observation"]["checkpoint_ack"] = True
                acknowledged = evaluate_continuation(payload)
                self.assertEqual(acknowledged["decision"], "continue")
                self.assertEqual(acknowledged["next_state"]["last_progress_sha256"], "b" * 64)
                self.assertEqual(acknowledged["next_state"]["no_progress_steps"], 1)
                advance(payload, acknowledged)
                payload["observation"].update(
                    check_outcome="PASS", progress_sha256="b" * 64, checkpoint_ack=False
                )
                repeated = evaluate_continuation(payload)
                self.assertEqual(repeated["decision"], "checkpoint")
                self.assertEqual(repeated["next_state"]["no_progress_steps"], 2)

    def test_resumed_state_requires_valid_last_observation_digest(self) -> None:
        for value in (None, "unknown", "", True):
            with self.subTest(value=value):
                payload = request()
                advance(payload, evaluate_continuation(payload))
                if value is None:
                    payload["state"].pop("last_observation_sha256", None)
                else:
                    payload["state"]["last_observation_sha256"] = value
                result = evaluate_continuation(payload)
                self.assertEqual(result["decision"], "blocked")
                self.assertIsNone(result["next_state"])

    def test_failure_streak_resets_only_on_pass(self) -> None:
        payload = request()
        payload["limits"].update(max_no_progress=10, checkpoint_interval=10)
        for outcome, expected in (("FAIL", 1), ("SKIP", 1), ("PASS", 0), ("FAIL", 1), ("FAIL", 2)):
            payload["observation"]["check_outcome"] = outcome
            result = evaluate_continuation(payload)
            self.assertEqual(result["next_state"]["consecutive_failures"], expected)
            self.assertEqual(result["decision"], "stop" if expected == 2 else "continue")
            advance(payload, result)

    def test_blocked_observation_preserves_real_consumption_and_stays_blocked(self) -> None:
        payload = request()
        payload["observation"]["check_outcome"] = "BLOCKED"
        result = evaluate_continuation(payload)
        self.assertEqual(result["decision"], "blocked")
        self.assertEqual(result["next_state"]["tokens"], 100)
        advance(payload, result)
        payload["observation"]["check_outcome"] = "PASS"
        self.assertEqual(evaluate_continuation(payload)["decision"], "blocked")

    def test_checkpoint_roundtrip_requires_same_step_ack_and_preserves_counters(self) -> None:
        payload = request()
        payload["limits"]["checkpoint_interval"] = 1
        result = evaluate_continuation(payload)
        self.assertEqual(result["decision"], "checkpoint")
        self.assertTrue(result["next_state"]["pending_checkpoint"])
        payload["state"] = json.loads(json.dumps(result["next_state"]))
        waiting = evaluate_continuation(payload)
        self.assertEqual(waiting["decision"], "checkpoint")
        self.assertEqual(waiting["next_state"], payload["state"])
        payload["observation"]["checkpoint_ack"] = True
        resumed = evaluate_continuation(payload)
        self.assertEqual(resumed["decision"], "continue")
        self.assertEqual(resumed["next_state"]["step"], 1)
        self.assertEqual(resumed["next_state"]["last_checkpoint_step"], 1)
        self.assertEqual(resumed["next_state"]["tokens"], 100)
        self.assertFalse(resumed["next_state"]["pending_checkpoint"])
        advance(payload, resumed)
        payload["observation"]["checkpoint_ack"] = False
        self.assertEqual(evaluate_continuation(payload)["decision"], "checkpoint")

    def test_checkpoint_cannot_acknowledge_future_work_or_new_counters(self) -> None:
        for change in ({"step": 2}, {"tokens": 101}, {"progress_sha256": "d" * 64}):
            with self.subTest(change=change):
                payload = request()
                payload["limits"]["checkpoint_interval"] = 1
                payload["state"] = evaluate_continuation(payload)["next_state"]
                payload["observation"].update(checkpoint_ack=True, **change)
                result = evaluate_continuation(payload)
                self.assertEqual(result["decision"], "blocked")
                self.assertIsNone(result["next_state"])

    def test_unrequested_or_replayed_ack_is_blocked(self) -> None:
        payload = request()
        payload["observation"]["checkpoint_ack"] = True
        self.assertEqual(evaluate_continuation(payload)["decision"], "blocked")
        payload["limits"]["checkpoint_interval"] = 1
        payload["observation"]["checkpoint_ack"] = False
        payload["state"] = evaluate_continuation(payload)["next_state"]
        payload["observation"]["checkpoint_ack"] = True
        payload["state"] = evaluate_continuation(payload)["next_state"]
        self.assertEqual(evaluate_continuation(payload)["decision"], "blocked")

    def test_checkpoint_wait_obeys_elapsed_time_budget(self) -> None:
        payload = request()
        payload["limits"]["checkpoint_interval"] = 1
        payload["state"] = evaluate_continuation(payload)["next_state"]
        payload["observation"]["duration_ms"] = payload["limits"]["max_duration_ms"]
        self.assertEqual(evaluate_continuation(payload)["decision"], "stop")

    def test_out_of_order_steps_and_rewound_counters_are_blocked(self) -> None:
        for change in (
            {"step": 0},
            {"step": 2},
            {"tokens": 49},
            {"duration_ms": 49},
            {"tool_calls": 0},
        ):
            with self.subTest(change=change):
                payload = request()
                payload["state"].update(tokens=50, duration_ms=50, tool_calls=1)
                payload["observation"].update(change)
                result = evaluate_continuation(payload)
                self.assertEqual(result["decision"], "blocked")
                self.assertIsNone(result["next_state"])

    def test_changed_run_snapshot_or_limits_cannot_resume(self) -> None:
        for key, value in (("run_id", "run-2"), ("snapshot_sha256", "f" * 64)):
            payload = request()
            payload["observation"][key] = value
            self.assertEqual(evaluate_continuation(payload)["decision"], "blocked")
        payload = request()
        advance(payload, evaluate_continuation(payload))
        payload["limits"]["max_tokens"] += 1
        self.assertEqual(evaluate_continuation(payload)["decision"], "blocked")

    def test_noninitial_state_cannot_drop_its_bound_limits(self) -> None:
        payload = request()
        advance(payload, evaluate_continuation(payload))
        del payload["state"]["limits_sha256"]
        payload["limits"]["max_tokens"] *= 2
        result = evaluate_continuation(payload)
        self.assertEqual(result["decision"], "blocked")
        self.assertEqual(result["reasons"], ["missing_limits_sha256"])
        self.assertIsNone(result["next_state"])

    def test_initial_exhausted_budget_never_accepts_another_step(self) -> None:
        payload = request()
        payload["state"]["tokens"] = payload["limits"]["max_tokens"]
        payload["observation"]["tokens"] = payload["state"]["tokens"] + 50
        result = evaluate_continuation(payload)
        self.assertEqual(result["decision"], "stop")
        self.assertEqual(result["next_state"]["step"], 0)
        self.assertEqual(result["next_state"]["tokens"], payload["state"]["tokens"])

    def test_terminal_state_still_rejects_invalid_step_or_ack(self) -> None:
        for change in ({"step": 3}, {"checkpoint_ack": True}):
            with self.subTest(change=change):
                payload = request()
                payload["observation"]["check_outcome"] = "BLOCKED"
                advance(payload, evaluate_continuation(payload))
                payload["observation"].update(change)
                result = evaluate_continuation(payload)
                self.assertEqual(result["decision"], "blocked")
                self.assertIsNone(result["next_state"])

    def test_missing_and_invalid_counters_are_never_zero(self) -> None:
        counter_keys = {
            "limits": list(request()["limits"]),
            "state": [
                "step",
                "tokens",
                "tool_calls",
                "duration_ms",
                "no_progress_steps",
                "consecutive_failures",
                "last_checkpoint_step",
            ],
            "observation": ["step", "tokens", "tool_calls", "duration_ms"],
        }
        for section, keys in counter_keys.items():
            for key in keys:
                for value in (None, True, -1, 1.5, float("nan"), float("inf"), 2**53):
                    with self.subTest(section=section, key=key, value=value):
                        payload = request()
                        payload[section][key] = value
                        result = evaluate_continuation(payload)
                        self.assertEqual(result["decision"], "blocked")
                        self.assertIsNone(result["next_state"])
                payload = request()
                del payload[section][key]
                self.assertEqual(evaluate_continuation(payload)["decision"], "blocked")

    def test_invalid_structure_hashes_outcomes_flags_and_state_are_blocked(self) -> None:
        cases = [None, [], {"schema_version": True}, {"schema_version": 2}]
        for section, key, value in (
            ("state", "last_checkpoint_step", 1),
            ("state", "no_progress_steps", 1),
            ("state", "consecutive_failures", 1),
            ("state", "pending_checkpoint", "false"),
            ("state", "terminal_decision", "continue"),
            ("state", "last_progress_sha256", "unknown"),
            ("state", "run_id", ""),
            ("observation", "snapshot_sha256", "unknown"),
            ("observation", "progress_sha256", "unknown"),
            ("observation", "checkpoint_ack", 1),
            ("observation", "check_outcome", "completed"),
            ("limits", "max_steps", 0),
        ):
            payload = request()
            payload[section][key] = value
            cases.append(payload)
        for payload in cases:
            with self.subTest(payload=payload):
                result = evaluate_continuation(payload)
                self.assertEqual(result["decision"], "blocked")
                self.assertIsNone(result["next_state"])


if __name__ == "__main__":
    unittest.main()
