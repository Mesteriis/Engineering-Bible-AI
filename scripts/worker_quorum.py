"""Evaluate a fixed, provider-neutral review quorum from launcher-owned records.

This offline helper checks consistency, not reviewer authenticity or the truth of
findings. It starts no model and executes no artifact. Local verification is an
additional CLI gate; a policy-only ACCEPT does not establish source freshness.
"""

from __future__ import annotations

import hashlib
import json
from typing import cast

from worker_results import artifact_path, inspect_record
from worker_snapshot import snapshot_digest, validate_snapshot_manifest


MODES = {"consensus_2_of_2": 2, "quorum_2_of_3": 3}
MAX_CONCERNS = 32
TARGET_FIELDS = {
    "task_id",
    "goal",
    "base_commit",
    "snapshot",
    "acceptance_criteria",
    "required_checks",
    "artifacts",
}


def target_digest(target: dict[str, object]) -> str:
    """Bind the exact target, criteria and required checks using canonical JSON."""
    return hashlib.sha256(
        json.dumps(
            target, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def _object(value: object, fields: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"invalid_{name}")
    return cast(dict[str, object], value)


def _list(value: object, maximum: int, name: str, minimum: int = 0) -> list[object]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"invalid_{name}")
    return cast(list[object], value)


def _text(value: object, name: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"invalid_{name}")
    return value


def _strings(value: object, maximum: int, name: str, minimum: int = 0) -> list[str]:
    items = [_text(item, name, 2048) for item in _list(value, maximum, name, minimum)]
    if len(set(items)) != len(items):
        raise ValueError(f"duplicate_{name}")
    return items


def _route(value: object) -> dict[str, str]:
    route = _object(value, {"provider", "model"}, "requested_route")
    result = {key: _text(route[key], f"requested_{key}", 128) for key in route}
    if any(value.strip().casefold() == "unknown" for value in result.values()):
        raise ValueError("unknown_requested_route")
    return result


def _evidence(value: object, record: dict[str, object], name: str) -> str:
    if not artifact_path(value) or value not in cast(list[object], record["artifacts"]):
        raise ValueError(f"invalid_{name}_artifact")
    return cast(str, value)


def _record(
    value: object, target: dict[str, object], name: str
) -> tuple[dict[str, object], dict[str, object]]:
    checked = inspect_record(value)
    if checked["contract_status"] != "PASS":
        raise ValueError(f"invalid_{name}_record")
    record = cast(dict[str, object], value)
    if any(record[key] != target[key] for key in ("task_id", "goal", "base_commit", "snapshot")):
        raise ValueError(f"{name}_scope_mismatch")
    return record, checked


def _failure_vetoes(record: dict[str, object], required: list[str], vetoes: list[str]) -> None:
    for check in cast(list[dict[str, object]], record["checks"]):
        if check["command"] in required and check["outcome"] == "FAIL":
            value = f"required_check_failed:{check['command']}"
            if value not in vetoes:
                vetoes.append(value)


def _manifest(value: object, base_commit: str, name: str) -> list[dict[str, object]]:
    entries = _list(value, 256, name, 1)
    if any(not isinstance(item, dict) or not artifact_path(item.get("path")) for item in entries):
        raise ValueError(f"invalid_{name}")
    entries = cast(list[dict[str, object]], entries)
    manifest = {
        "state": "captured",
        "sha256": snapshot_digest(base_commit, entries),
        "files": entries,
    }
    if validate_snapshot_manifest(manifest, base_commit):
        raise ValueError(f"invalid_{name}")
    return entries


def _retain_scoped_vetoes(
    request: dict[str, object],
    target: dict[str, object],
    required: list[str],
    digest: str,
    vetoes: list[str],
) -> None:
    """Keep valid failure facts when another ballot or its vote is malformed."""
    raw_ballots = request["ballots"]
    if not isinstance(raw_ballots, list) or len(raw_ballots) > 3:
        return
    for raw in raw_ballots:
        if not isinstance(raw, dict) or raw.get("target_sha256") != digest:
            continue
        try:
            record, _ = _record(raw.get("record"), target, "ballot")
        except (ValueError, TypeError, KeyError):
            continue
        _failure_vetoes(record, required, vetoes)
        raw_concerns = raw.get("concerns")
        if not isinstance(raw_concerns, list) or len(raw_concerns) > MAX_CONCERNS:
            continue
        for item in raw_concerns:
            if (
                not isinstance(item, dict)
                or item.get("severity") != "critical"
                or item.get("parent_confirmed") is not True
            ):
                continue
            try:
                identifier = _text(item.get("id"), "concern_id", 128)
                _evidence(item.get("evidence_artifact"), record, "concern")
                _evidence(item.get("confirmation_artifact"), record, "confirmation")
            except ValueError:
                continue
            value = f"confirmed_critical:{identifier}"
            if value not in vetoes:
                vetoes.append(value)


def _reply(
    decision: str, reasons: list[str], vetoes: list[str], **details: object
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_status": "FAIL" if decision == "INVALID" else "PASS",
        "decision": decision,
        "outcome": "PASS"
        if decision == "ACCEPT"
        else "FAIL"
        if decision in ("INVALID", "REQUEST_CHANGES")
        else "BLOCKED",
        "proof_scope": "launcher_record_consistency_only",
        "reasons": reasons,
        "vetoes": sorted(vetoes),
        "issues": reasons if decision == "INVALID" else [],
        "approvals": 0,
        "threshold": 2,
        "eligible_reviewers": [],
        "recommend_third_review": False,
        **details,
    }


def _evaluate(payload: object, vetoes: list[str]) -> dict[str, object]:
    request = _object(
        payload,
        {
            "schema_version",
            "target",
            "target_sha256",
            "policy_sha256",
            "policy",
            "gate_record",
            "ballots",
            "resolutions",
            "evidence_artifacts",
        },
        "envelope",
    )
    if type(request["schema_version"]) is not int or request["schema_version"] != 1:
        raise ValueError("invalid_schema_version")
    target = _object(request["target"], TARGET_FIELDS, "target")
    _text(target["task_id"], "task_id", 128)
    _text(target["goal"], "goal")
    errors = validate_snapshot_manifest(target["snapshot"], target["base_commit"])
    if errors:
        raise ValueError("invalid_target_snapshot")
    criteria = _strings(target["acceptance_criteria"], 64, "acceptance_criteria", 1)
    required = _strings(target["required_checks"], 32, "required_checks", 1)
    artifacts = _manifest(target["artifacts"], cast(str, target["base_commit"]), "target_artifacts")
    evidence_manifest = _manifest(
        request["evidence_artifacts"], cast(str, target["base_commit"]), "evidence_artifacts"
    )
    digest = target_digest(target)
    if request["target_sha256"] != digest:
        raise ValueError("target_digest_mismatch")
    policy = _object(request["policy"], {"mode", "roster", "author_ids"}, "policy")
    mode = policy["mode"]
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError("invalid_mode")
    roster: dict[str, dict[str, str]] = {}
    authors = _strings(policy["author_ids"], 16, "author_ids")
    for raw in _list(policy["roster"], MODES[mode], "roster", MODES[mode]):
        entry = _object(raw, {"reviewer_id", "requested"}, "roster_entry")
        reviewer = _text(entry["reviewer_id"], "reviewer_id", 128)
        if reviewer in roster or reviewer in authors:
            raise ValueError("duplicate_or_author_reviewer")
        roster[reviewer] = _route(entry["requested"])
    policy_hash = target_digest(policy)
    if request["policy_sha256"] != policy_hash:
        raise ValueError("policy_digest_mismatch")

    gate, _ = _record(request["gate_record"], target, "gate")
    _failure_vetoes(gate, required, vetoes)
    _retain_scoped_vetoes(request, target, required, digest, vetoes)
    ballots: dict[str, dict[str, object]] = {}
    records = [gate]
    eligible: dict[str, tuple[str, str]] = {}
    concerns: dict[str, dict[str, object]] = {}
    ineligible: list[str] = []
    record_hashes: set[str] = set()
    routes: set[tuple[str, str]] = set()
    collision = False
    for raw in _list(request["ballots"], MODES[mode], "ballots"):
        ballot = _object(
            raw,
            {
                "reviewer_id",
                "target_sha256",
                "policy_sha256",
                "vote",
                "reason",
                "record",
                "independence",
                "concerns",
            },
            "ballot",
        )
        reviewer = _text(ballot["reviewer_id"], "reviewer_id", 128)
        if reviewer not in roster or reviewer in ballots:
            raise ValueError("unknown_or_duplicate_reviewer")
        if ballot["target_sha256"] != digest:
            raise ValueError("ballot_target_mismatch")
        if ballot["policy_sha256"] != policy_hash:
            raise ValueError("ballot_policy_mismatch")
        vote = ballot["vote"]
        if vote not in ("APPROVE", "REQUEST_CHANGES", "ABSTAIN"):
            raise ValueError("invalid_vote")
        _text(ballot["reason"], "ballot_reason")
        record, checked = _record(ballot["record"], target, "ballot")
        if record["requested"] != roster[reviewer]:
            raise ValueError("roster_route_substitution")
        record_hash = target_digest(record)
        if record_hash in record_hashes:
            raise ValueError("replayed_worker_record")
        record_hashes.add(record_hash)
        _failure_vetoes(record, required, vetoes)
        records.append(record)
        independence = _object(
            ballot["independence"], {"phase", "peer_results_seen", "source"}, "independence"
        )
        peers = _strings(independence["peer_results_seen"], MODES[mode] - 1, "peer_results_seen")
        if any(peer not in roster or peer == reviewer for peer in peers):
            raise ValueError("invalid_seen_peer")
        phase = independence["phase"]
        if phase not in ("independent", "informed") or (phase == "independent" and peers):
            raise ValueError("invalid_independence_phase")
        _evidence(independence["source"], record, "independence")
        raw_concerns = _list(ballot["concerns"], MAX_CONCERNS, "concerns")
        if vote == "REQUEST_CHANGES" and not raw_concerns:
            raise ValueError("changes_vote_requires_concern")
        for raw_concern in raw_concerns:
            item = _object(
                raw_concern,
                {
                    "id",
                    "severity",
                    "evidence_artifact",
                    "parent_confirmed",
                    "confirmation_artifact",
                },
                "concern",
            )
            identifier = _text(item["id"], "concern_id", 128)
            if identifier in concerns:
                raise ValueError("duplicate_concern_id")
            if (
                item["severity"] not in ("critical", "noncritical")
                or type(item["parent_confirmed"]) is not bool
            ):
                raise ValueError("invalid_concern_classification")
            _evidence(item["evidence_artifact"], record, "concern")
            if item["parent_confirmed"]:
                _evidence(item["confirmation_artifact"], record, "confirmation")
            elif item["confirmation_artifact"] is not None:
                raise ValueError("unconfirmed_concern_has_confirmation")
            concerns[identifier] = item
            if item["severity"] == "critical" and item["parent_confirmed"]:
                value = f"confirmed_critical:{identifier}"
                if value not in vetoes:
                    vetoes.append(value)
        observed = cast(dict[str, object], record["observed"])
        known = observed["verification"] != "unknown"
        route = (
            cast(str, observed["provider"]).strip().casefold(),
            cast(str, observed["model"]).strip().casefold(),
        )
        if known:
            collision |= route in routes
            routes.add(route)
        if checked["outcome"] == "PASS" and not record["open_questions"] and phase == "independent":
            eligible[reviewer] = route
        else:
            ineligible.append(reviewer)
        ballots[reviewer] = ballot

    artifact_paths = {item["path"] for item in artifacts}
    evidence_paths = {item["path"] for item in evidence_manifest}
    referenced_paths = {path for record in records for path in cast(list[str], record["artifacts"])}
    if evidence_paths != referenced_paths or artifact_paths & evidence_paths:
        raise ValueError("evidence_manifest_coverage_mismatch")

    resolved: set[str] = set()
    for raw in _list(request["resolutions"], MODES[mode] * MAX_CONCERNS, "resolutions"):
        resolution = _object(raw, {"concern_id", "reviewed_by", "evidence"}, "resolution")
        identifier = _text(resolution["concern_id"], "resolution_concern", 128)
        if (
            identifier not in concerns
            or identifier in resolved
            or concerns[identifier]["severity"] == "critical"
        ):
            raise ValueError("invalid_resolution_concern")
        reviewers = _strings(resolution["reviewed_by"], MODES[mode], "resolution_reviewers", 2)
        if (
            any(reviewer not in eligible for reviewer in reviewers)
            or len({eligible[reviewer][0] for reviewer in reviewers}) < 2
        ):
            raise ValueError("invalid_resolution_reviewers")
        evidence_reviewers: set[str] = set()
        for raw_evidence in _list(resolution["evidence"], MODES[mode], "resolution_evidence", 2):
            evidence = _object(raw_evidence, {"reviewer_id", "artifact"}, "resolution_evidence")
            reviewer = _text(evidence["reviewer_id"], "resolution_reviewer", 128)
            if reviewer not in reviewers or reviewer in evidence_reviewers:
                raise ValueError("invalid_resolution_evidence_reviewer")
            _evidence(
                evidence["artifact"],
                cast(dict[str, object], ballots[reviewer]["record"]),
                "resolution",
            )
            evidence_reviewers.add(reviewer)
        if evidence_reviewers != set(reviewers):
            raise ValueError("missing_resolution_evidence")
        resolved.add(identifier)

    outcomes = {
        command: [
            check["outcome"]
            for record in records
            for check in cast(list[dict[str, object]], record["checks"])
            if check["command"] == command
        ]
        for command in required
    }
    approvals = [reviewer for reviewer in eligible if ballots[reviewer]["vote"] == "APPROVE"]
    approval_providers = {eligible[reviewer][0] for reviewer in approvals}
    first_two = list(roster)[:2]
    material_disagreement = all(reviewer in eligible for reviewer in first_two) and {
        ballots[reviewer]["vote"] for reviewer in first_two
    } == {"APPROVE", "REQUEST_CHANGES"}
    details: dict[str, object] = {
        "target_sha256": digest,
        "policy_sha256": policy_hash,
        "mode": mode,
        "approvals": len(approvals),
        "approval_providers": len(approval_providers),
        "eligible_reviewers": sorted(eligible),
        "ineligible_reviewers": sorted(ineligible),
        "required_checks": {
            command: "FAIL" if "FAIL" in statuses else "PASS" if "PASS" in statuses else "BLOCKED"
            for command, statuses in outcomes.items()
        },
        "unresolved_concerns": sorted(set(concerns) - resolved),
        "recommend_third_review": mode == "quorum_2_of_3"
        and material_disagreement
        and not vetoes
        and len(ballots) < 3,
        "acceptance_criteria_count": len(criteria),
    }
    if vetoes:
        return _reply("REQUEST_CHANGES", ["evidence_veto"], vetoes, **details)
    if collision:
        return _reply("BLOCKED", ["duplicate_observed_route"], vetoes, **details)
    if (
        target["base_commit"] == "unknown"
        or gate["status"] != "completed"
        or gate["open_questions"]
        or not gate["checks"]
        or any(
            check["outcome"] != "PASS" for check in cast(list[dict[str, object]], gate["checks"])
        )
        or any("PASS" not in statuses for statuses in outcomes.values())
    ):
        return _reply("BLOCKED", ["required_evidence_unavailable"], vetoes, **details)
    if set(concerns) - resolved:
        return _reply("NEEDS_REVIEW", ["unresolved_concerns"], vetoes, **details)
    if len(approvals) < 2 or len(approval_providers) < 2:
        return _reply("BLOCKED", ["fixed_cross_provider_threshold_not_met"], vetoes, **details)
    return _reply("ACCEPT", ["fixed_cross_provider_threshold_met"], vetoes, **details)


def evaluate_quorum(payload: object) -> dict[str, object]:
    """Evaluate recorded policy; CLI separately verifies local source and artifacts."""
    vetoes: list[str] = []
    try:
        return _evaluate(payload, vetoes)
    except ValueError as error:
        reason = str(error)
        if not reason.isascii() or not reason.replace("_", "").isalpha():
            reason = "invalid_or_inconsistent_envelope"
        return _reply("INVALID", [reason], vetoes)
    except (TypeError, KeyError, OverflowError, RecursionError):
        return _reply("INVALID", ["invalid_or_inconsistent_envelope"], vetoes)
