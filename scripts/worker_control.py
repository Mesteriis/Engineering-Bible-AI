"""Evaluate a bounded worker run using launcher-supplied cumulative evidence.

Schema 1 requires ``limits``, ``state`` and ``observation`` objects. Limits are
positive integers: max_steps, max_no_progress, max_consecutive_failures,
max_tokens, max_tool_calls, max_duration_ms and checkpoint_interval. State has
run_id, snapshot_sha256, step, tokens, tool_calls, duration_ms, no_progress_steps,
consecutive_failures, last_checkpoint_step and last_progress_sha256. Initial
step/streaks/checkpoint are zero; resource counters must contain real readings.

An observation repeats run/snapshot identity and cumulative step/resource
counters, plus progress_sha256, check_outcome (PASS/FAIL/SKIP/BLOCKED), and boolean
checkpoint_ack. Work advances exactly one step. Only PASS with a changed progress
digest resets no-progress; SKIP does not erase the failure streak.

Persist the returned next_state verbatim, including limits_sha256,
last_observation_sha256, pending_checkpoint and any terminal_decision.
last_progress_sha256 retains the latest verified digest; failed/skipped
observations cannot replace it. A pending checkpoint accepts only a same-step
replay matching last_observation_sha256 and unchanged resource counts (duration
may rise). checkpoint_ack acknowledges that saved checkpoint; it never advances
work. Terminal states cannot resume. Invalid transitions return next_state=None.

This pure function authenticates neither measurements nor caller-owned state.
The launcher must retain authoritative state, enforce decisions, save checkpoint
artifacts before acknowledgment, and supply measured counters and content hashes.
It does not start workers, increase budgets, or infer progress from prose.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import cast


COUNTERS = ("step", "tokens", "tool_calls", "duration_ms")
STREAKS = ("no_progress_steps", "consecutive_failures", "last_checkpoint_step")
BUDGETS = {
    "max_steps": "step",
    "max_tokens": "tokens",
    "max_tool_calls": "tool_calls",
    "max_duration_ms": "duration_ms",
    "max_no_progress": "no_progress_steps",
    "max_consecutive_failures": "consecutive_failures",
}
MAX_COUNT = 2**53 - 1


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"invalid_{name}")
    return cast(dict[str, object], value)


def _counts(raw: dict[str, object], keys: tuple[str, ...], name: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for key in keys:
        value = raw.get(key)
        if type(value) is not int or not 0 <= value <= MAX_COUNT:
            raise ValueError(f"invalid_{name}.{key}")
        values[key] = value
    return values


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _reply(decision: str, reasons: list[str], state: dict[str, object] | None) -> dict[str, object]:
    return {
        "schema_version": 1,
        "decision": decision,
        "reasons": reasons,
        "next_state": state,
    }


def _exhausted(counts: dict[str, int], limits: dict[str, int]) -> list[str]:
    return [limit for limit, counter in BUDGETS.items() if counts[counter] >= limits[limit]]


def _evaluate(payload: object) -> dict[str, object]:
    request = _object(payload, "request")
    if type(request.get("schema_version")) is not int or request["schema_version"] != 1:
        raise ValueError("invalid_schema_version")
    raw_limits = _object(request.get("limits"), "limits")
    limit_keys = (*BUDGETS, "checkpoint_interval")
    limits = _counts(raw_limits, limit_keys, "limits")
    if set(raw_limits) != set(limit_keys) or not all(limits.values()):
        raise ValueError("invalid_limits")
    limits_digest = hashlib.sha256(
        json.dumps(limits, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    state = _object(request.get("state"), "state")
    observation = _object(request.get("observation"), "observation")
    before = _counts(state, COUNTERS + STREAKS, "state")
    after = _counts(observation, COUNTERS, "observation")

    for item in (state, observation):
        run_id = item.get("run_id")
        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or not _digest(item.get("snapshot_sha256"))
        ):
            raise ValueError("invalid_identity")
    if any(state[key] != observation[key] for key in ("run_id", "snapshot_sha256")):
        raise ValueError("identity_changed")
    if not _digest(state.get("last_progress_sha256")) or not _digest(
        observation.get("progress_sha256")
    ):
        raise ValueError("invalid_progress_sha256")
    if before["step"] > 0 and "last_observation_sha256" not in state:
        raise ValueError("missing_last_observation_sha256")
    last_observation = state.get("last_observation_sha256", state["last_progress_sha256"])
    if not _digest(last_observation):
        raise ValueError("invalid_last_observation_sha256")
    if observation.get("check_outcome") not in ("PASS", "FAIL", "SKIP", "BLOCKED"):
        raise ValueError("invalid_check_outcome")
    if type(observation.get("checkpoint_ack")) is not bool:
        raise ValueError("invalid_checkpoint_ack")
    pending = state.get("pending_checkpoint", False)
    if type(pending) is not bool:
        raise ValueError("invalid_pending_checkpoint")
    terminal = state.get("terminal_decision")
    if terminal not in (None, "stop", "blocked"):
        raise ValueError("invalid_terminal_decision")
    if any(before[key] > before["step"] for key in STREAKS):
        raise ValueError("invalid_state_counters")
    if pending and before["last_checkpoint_step"] >= before["step"]:
        raise ValueError("invalid_pending_checkpoint")
    if before["step"] > 0 and "limits_sha256" not in state:
        raise ValueError("missing_limits_sha256")
    if "limits_sha256" in state and state["limits_sha256"] != limits_digest:
        raise ValueError("limits_changed")
    if any(after[key] < before[key] for key in COUNTERS):
        raise ValueError("counters_rewound")
    if pending:
        if any(after[key] != before[key] for key in ("step", "tokens", "tool_calls")) or (
            observation["progress_sha256"] != last_observation
        ):
            raise ValueError("checkpoint_replay_mismatch")
    elif observation["checkpoint_ack"]:
        raise ValueError("unexpected_checkpoint_ack")
    elif after["step"] != before["step"] + 1:
        raise ValueError("step_out_of_order")

    next_state: dict[str, object] = {
        **before,
        "run_id": state["run_id"],
        "snapshot_sha256": state["snapshot_sha256"],
        "last_progress_sha256": state["last_progress_sha256"],
        "last_observation_sha256": last_observation,
        "limits_sha256": limits_digest,
        "pending_checkpoint": pending,
    }
    if terminal is not None:
        next_state["terminal_decision"] = terminal
        return _reply(cast(str, terminal), ["terminal_state"], next_state)
    exhausted = _exhausted(before, limits)
    if exhausted:
        next_state["terminal_decision"] = "stop"
        return _reply("stop", exhausted, next_state)

    if pending:
        next_state["duration_ms"] = after["duration_ms"]
        if observation["checkpoint_ack"]:
            next_state.update(last_checkpoint_step=before["step"], pending_checkpoint=False)
    else:
        outcome = observation["check_outcome"]
        progressed = (
            outcome == "PASS" and observation["progress_sha256"] != state["last_progress_sha256"]
        )
        next_state.update(after)
        next_state["no_progress_steps"] = 0 if progressed else before["no_progress_steps"] + 1
        next_state["consecutive_failures"] = (
            0 if outcome == "PASS" else before["consecutive_failures"] + (outcome == "FAIL")
        )
        next_state["last_observation_sha256"] = observation["progress_sha256"]
        if progressed:
            next_state["last_progress_sha256"] = observation["progress_sha256"]

    if observation["check_outcome"] == "BLOCKED":
        next_state["terminal_decision"] = "blocked"
        return _reply("blocked", ["observation_blocked"], next_state)
    exhausted = _exhausted(_counts(next_state, COUNTERS + STREAKS, "next_state"), limits)
    if exhausted:
        next_state["terminal_decision"] = "stop"
        return _reply("stop", exhausted, next_state)
    if pending:
        acknowledged = observation["checkpoint_ack"]
        return _reply(
            "continue" if acknowledged else "checkpoint",
            ["checkpoint_acknowledged" if acknowledged else "checkpoint_pending"],
            next_state,
        )
    if after["step"] - before["last_checkpoint_step"] >= limits["checkpoint_interval"]:
        next_state["pending_checkpoint"] = True
        return _reply("checkpoint", ["checkpoint_due"], next_state)
    return _reply("continue", ["within_limits"], next_state)


def evaluate_continuation(payload: object) -> dict[str, object]:
    """Return decision, stable reason codes and the next valid state (or None)."""
    try:
        return _evaluate(payload)
    except ValueError as error:
        return _reply("blocked", [str(error)], None)
