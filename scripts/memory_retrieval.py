"""Optional offline query planning and evidence-preserving rank fusion.

This module performs no search, inference, installation or index mutation.
Ranked lists come from the caller's authorized search capability. A matching
source manifest proves only the checked files, never search execution.
"""

from __future__ import annotations

import math
from pathlib import Path
import re
from typing import TypedDict, cast

from worker_snapshot import validate_snapshot_manifest, verify_snapshot


MAX_QUERY_BYTES = 1024
MAX_RESULTS_PER_VARIANT = 100
MAX_LIMIT = 50
RRF_K = 60
# Plain grammatical words, not domain-specific expansion dictionaries.
_STOPWORDS = frozenset(
    "a an the and or of to in on for with about is are was were be been being "
    "do does did have has had how what when where who why which can could should "
    "would will i me my we our you your it its this that these those "
    "и или в на к с из для по о об это как что где когда кто почему какой какие "
    "я мы вы мне нам мой наш ваш ли бы".split()
)


class RetrievalError(ValueError):
    """The query or ranked evidence is malformed, inconsistent or unbounded."""


class QueryPlan(TypedDict):
    query: str
    variants: list[str]


class Candidate(TypedDict):
    id: str
    path: str
    sha256: str
    score: float


class Ranking(TypedDict):
    query: str
    snapshot_sha256: str
    results: list[Candidate]


class FileEntry(TypedDict):
    path: str
    sha256: str
    bytes: int


class Manifest(TypedDict):
    state: str
    sha256: str
    files: list[FileEntry]


class Source(TypedDict):
    base_commit: str
    snapshot: Manifest


def _text(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise RetrievalError(f"{label} must be a nonempty string")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise RetrievalError(f"{label} must be valid UTF-8") from exc
    if size > maximum or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise RetrievalError(f"{label} exceeds its byte limit or contains control characters")
    return value


def query_plan(query: object) -> QueryPlan:
    """Keep the primary query and at most one Unicode content-word variant.

    Variants are ordinary query strings, never shell commands. Grammatical
    simplification is deliberately conservative; the original query remains
    available when punctuation or short symbols carry meaning.
    """
    primary = _text(query, "query", MAX_QUERY_BYTES).strip()
    if not primary:
        raise RetrievalError("query must not be blank")
    keywords = " ".join(
        word for word in re.findall(r"[^\W_]+", primary.casefold()) if word not in _STOPWORDS
    )
    variants = [primary]
    if (
        keywords
        and keywords != primary.casefold()
        and len(keywords.encode("utf-8")) <= MAX_QUERY_BYTES
    ):
        variants.append(keywords)
    return {"query": primary, "variants": variants}


def _object(value: object, fields: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise RetrievalError(f"{label} must contain exactly: {', '.join(sorted(fields))}")
    return value


def _validate_payload(payload: object) -> tuple[QueryPlan, Source, list[Ranking]]:
    body = _object(payload, {"query", "source", "rankings"}, "payload")
    plan = query_plan(body["query"])
    source = _object(body["source"], {"base_commit", "snapshot"}, "source")
    issues = validate_snapshot_manifest(source["snapshot"], source["base_commit"])
    if issues:
        raise RetrievalError("; ".join(issues))
    checked_source = cast(Source, source)
    manifest = checked_source["snapshot"]
    hashes = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
    rankings = body["rankings"]
    if not isinstance(rankings, list) or len(rankings) != len(plan["variants"]):
        raise RetrievalError("one ranking is required for every planned query variant")
    by_query: dict[str, Ranking] = {}
    identities: dict[str, tuple[str, str]] = {}
    path_ids: dict[str, str] = {}
    for item in rankings:
        ranking = _object(item, {"query", "snapshot_sha256", "results"}, "ranking")
        query = _text(ranking["query"], "ranking query", MAX_QUERY_BYTES)
        if query not in plan["variants"] or query in by_query:
            raise RetrievalError("ranking query must be planned and unique")
        if ranking["snapshot_sha256"] != manifest["sha256"]:
            raise RetrievalError("rankings must name the same captured source snapshot")
        results = ranking["results"]
        if not isinstance(results, list) or len(results) > MAX_RESULTS_PER_VARIANT:
            raise RetrievalError("ranking results must be a bounded list")
        seen: set[str] = set()
        for item in results:
            candidate = _object(item, {"id", "path", "sha256", "score"}, "candidate")
            identity = _text(candidate["id"], "candidate id", 512)
            path = _text(candidate["path"], "candidate path", 4096)
            digest = candidate["sha256"]
            # The already-validated manifest enforces canonical relative paths.
            if path not in hashes or digest != hashes[path]:
                raise RetrievalError("candidate path and hash must match the source manifest")
            if identity in seen:
                raise RetrievalError("duplicate candidate id within one ranking")
            seen.add(identity)
            if identity in identities and identities[identity] != (path, digest):
                raise RetrievalError("candidate id names conflicting source files")
            if path in path_ids and path_ids[path] != identity:
                raise RetrievalError("one source file cannot have multiple candidate ids")
            identities[identity] = (path, cast(str, digest))
            path_ids[path] = identity
            score = candidate["score"]
            try:
                finite = type(score) in (int, float) and math.isfinite(cast(float, score))
            except OverflowError:
                finite = False
            if not finite:
                raise RetrievalError("candidate score must be a finite real number")
        by_query[query] = cast(Ranking, ranking)
    # Fusion and equal-score ties do not depend on JSON ranking-array order.
    return plan, checked_source, [by_query[query] for query in plan["variants"]]


def fuse_rankings(
    payload: object, *, limit: int = 5, source_root: Path | None = None
) -> dict[str, object]:
    """Fuse ranked document lists with RRF, retaining baseline and provenance.

    An omitted root reports SKIP. A supplied root is checked against the full
    declared manifest; any mismatch reports FAIL and suppresses ranked output.
    Files outside Git can match their content hashes while base_commit remains
    unknown. This is not an atomic index snapshot or search authentication.
    """
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise RetrievalError(f"limit must be an integer between 1 and {MAX_LIMIT}")
    plan, source, rankings = _validate_payload(payload)
    source_status = "SKIP"
    issues = ["source root omitted; source freshness is unknown"]
    if source_root is not None:
        issues = verify_snapshot(source_root, source["snapshot"], source["base_commit"])
        source_status = "FAIL" if issues else "PASS"
    response: dict[str, object] = {
        "contract_status": "PASS",
        "source_status": source_status,
        "outcome": source_status,
        "query": plan["query"],
        "variants": plan["variants"],
        "source": source,
        "issues": issues,
        "baseline": [],
        "results": [],
    }
    if source_status == "FAIL":
        return response
    response["baseline"] = [dict(candidate) for candidate in rankings[0]["results"]]
    candidates: dict[str, dict[str, object]] = {}
    scores: dict[str, float] = {}
    traces: dict[str, list[dict[str, object]]] = {}
    for ranking in rankings:
        for rank, candidate in enumerate(ranking["results"], start=1):
            identity = candidate["id"]
            if identity not in candidates:
                candidates[identity] = {key: candidate[key] for key in ("id", "path", "sha256")}
                scores[identity] = 0.0
                traces[identity] = []
            scores[identity] += 1 / (RRF_K + rank)
            traces[identity].append(
                {
                    "query": ranking["query"],
                    "rank": rank,
                    "raw_score": candidate["score"],
                    "snapshot_sha256": ranking["snapshot_sha256"],
                }
            )
    ordered = sorted(candidates, key=lambda identity: -scores[identity])[:limit]
    response["results"] = [
        {**candidates[identity], "rrf_score": scores[identity], "provenance": traces[identity]}
        for identity in ordered
    ]
    return response
