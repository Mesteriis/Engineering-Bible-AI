#!/usr/bin/env python3
"""Build a private capability catalog from host-provided runtime metadata.

This module is intentionally transport-agnostic. It accepts normalized metadata,
never connects to a provider, and never invokes a discovered capability.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import TypeAlias


JsonObject: TypeAlias = dict[str, object]

CATALOG_SCHEMA_VERSION = 1
MAX_TOOLS = 4096
MAX_PARAMETERS = 512
MAX_TEXT_LENGTH = 2048
MAX_IDENTIFIER_LENGTH = 512
MAX_SCHEMA_DEPTH = 20
MAX_SCHEMA_NODES = 20_000
MAX_CANDIDATES = 8
MAX_EXPANDED_SCHEMAS = 3
VALID_RUNTIME_STATUSES = {"online", "partial", "offline"}
VALID_SCOPES = {"local", "remote", "unknown"}
VALID_RISKS = {"R0", "R1", "R2", "R3", "UNKNOWN"}

_URL_RE = re.compile(r"\b(?:https?|wss?|sse)://[^\s<>'\"]+", re.IGNORECASE)
_IPV4_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"\b(api[_-]?key|authorization|cookie|credential|password|secret|token)"
    r"\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
    re.IGNORECASE,
)
_PRIVATE_PATH_RE = re.compile(
    r"(?:/(?:Users|home)/[^\s/]+|[A-Za-z]:\\Users\\[^\s\\]+|~/[^\s]+)",
    re.IGNORECASE,
)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TOKEN_RE = re.compile(r"[\w-]{2,}", re.UNICODE)

_DESTRUCTIVE_SIGNAL_RE = re.compile(
    r"\b(delete|destroy|drop|erase|format|purge|remove|truncate|wipe)\b",
    re.IGNORECASE,
)
_EXECUTION_SIGNAL_RE = re.compile(
    r"\b(arbitrary\s+code|eval|execute|execution|privileged|root\s+access|run\s+(?:a\s+)?command|script\s+execution|shell\s+command|sudo|terminal\s+command)\b",
    re.IGNORECASE,
)
_MUTATION_SIGNAL_RE = re.compile(
    r"\b(apply|commit|configure|create|deploy|edit|grant|install|merge|message|modify|notify|post|publish|push|restart|revoke|rotate|send|set|start|stop|switch|sync|update|upload|write)\b",
    re.IGNORECASE,
)
_SENSITIVE_OR_REMOTE_SIGNAL_RE = re.compile(
    r"\b(account|configuration|credential|database|external|key|log|metrics|network|private|remote|repository|secret|token|user)\b",
    re.IGNORECASE,
)

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "tool",
    "using",
    "with",
}
_ACTION_WORDS = {
    "apply",
    "create",
    "delete",
    "destroy",
    "execute",
    "read",
    "remove",
    "send",
    "update",
    "write",
}
_VALUE_BEARING_SCHEMA_KEYS = {"const", "default", "enum", "example", "examples"}
_EXECUTION_PARAMETER_NAMES = {
    "argv",
    "cmd",
    "command",
    "command_line",
    "executable",
    "script",
    "shell",
    "shell_command",
}


class CatalogError(RuntimeError):
    """Raised when runtime metadata or persisted catalog state is invalid."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _expect_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CatalogError(f"{field} must be an object")
    result: JsonObject = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise CatalogError(f"{field} keys must be strings")
        result[key] = item
    return result


def _expect_text(
    value: object,
    field: str,
    *,
    required: bool = False,
    limit: int = MAX_TEXT_LENGTH,
) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise CatalogError(f"{field} must be a string")
    if required and not value.strip():
        raise CatalogError(f"{field} must not be empty")
    if len(value) > limit * 4:
        raise CatalogError(f"{field} exceeds the accepted size")
    return value


def sanitize_text(value: str, *, limit: int = MAX_TEXT_LENGTH) -> str:
    """Redact common endpoint, credential, identity, and private-path patterns."""

    text = _CONTROL_RE.sub(" ", value)
    text = _BEARER_RE.sub("[REDACTED_SECRET]", text)
    text = _SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[REDACTED_SECRET]", text)
    text = _URL_RE.sub("[REDACTED_URL]", text)
    text = _IPV4_RE.sub("[REDACTED_ADDRESS]", text)
    text = _EMAIL_RE.sub("[REDACTED_IDENTITY]", text)
    text = _PRIVATE_PATH_RE.sub("[REDACTED_PATH]", text)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _safe_identifier(value: object, field: str, *, required: bool = True) -> str:
    raw = _expect_text(value, field, required=required, limit=MAX_IDENTIFIER_LENGTH)
    sanitized = sanitize_text(raw, limit=MAX_IDENTIFIER_LENGTH)
    if required and not sanitized:
        raise CatalogError(f"{field} must not be empty after sanitization")
    return sanitized


def _safe_timestamp(captured_at: str | None) -> str:
    if captured_at is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    value = _safe_identifier(captured_at, "captured_at")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CatalogError("captured_at must be an ISO-8601 timestamp") from exc
    return value


def _redacted_value_shape(value: object) -> object:
    if isinstance(value, Mapping):
        return {"kind": "object", "size": len(value)}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return {"kind": "array", "size": len(value)}
    if value is None:
        return {"kind": "null"}
    return {"kind": type(value).__name__}


def _safe_schema_shape(
    value: object,
    *,
    field: str,
    depth: int = 0,
    nodes: list[int] | None = None,
    parent_key: str = "",
) -> object:
    """Return a secret-safe schema projection used only for change detection."""

    if nodes is None:
        nodes = [0]
    nodes[0] += 1
    if nodes[0] > MAX_SCHEMA_NODES:
        raise CatalogError(f"{field} is too large")
    if depth > MAX_SCHEMA_DEPTH:
        raise CatalogError(f"{field} exceeds maximum nesting depth")

    if parent_key.lower() in _VALUE_BEARING_SCHEMA_KEYS:
        return _redacted_value_shape(value)
    if isinstance(value, Mapping):
        result: JsonObject = {}
        raw_keys = list(value)
        if any(not isinstance(raw_key, str) for raw_key in raw_keys):
            raise CatalogError(f"{field} keys must be strings")
        for raw_key in sorted(raw_keys):
            safe_key = sanitize_text(raw_key, limit=MAX_IDENTIFIER_LENGTH)
            result[safe_key] = _safe_schema_shape(
                value[raw_key],
                field=field,
                depth=depth + 1,
                nodes=nodes,
                parent_key=raw_key,
            )
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > MAX_PARAMETERS:
            raise CatalogError(f"{field} contains too many entries")
        return [
            _safe_schema_shape(
                item,
                field=field,
                depth=depth + 1,
                nodes=nodes,
                parent_key=parent_key,
            )
            for item in value
        ]
    if isinstance(value, str):
        if parent_key.lower() in {"description", "format", "pattern", "title", "type", "$ref"}:
            return sanitize_text(value)
        return {"kind": "string"}
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise CatalogError(f"{field} contains unsupported value type: {type(value).__name__}")


def _parameter_type(schema: Mapping[str, object]) -> str:
    value = schema.get("type")
    if isinstance(value, str):
        return sanitize_text(value, limit=64) or "unknown"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        types = [sanitize_text(item, limit=64) for item in value if isinstance(item, str)]
        return " | ".join(types[:8]) or "unknown"
    for combinator in ("oneOf", "anyOf", "allOf"):
        options = schema.get(combinator)
        if isinstance(options, Sequence) and not isinstance(options, (str, bytes, bytearray)):
            return combinator
    return "unknown"


def _extract_parameters(schema: Mapping[str, object], field: str) -> list[JsonObject]:
    properties_value = schema.get("properties", {})
    properties = _expect_mapping(properties_value, f"{field}.properties")
    if len(properties) > MAX_PARAMETERS:
        raise CatalogError(f"{field}.properties contains too many parameters")

    required_value = schema.get("required", [])
    if not isinstance(required_value, Sequence) or isinstance(
        required_value, (str, bytes, bytearray)
    ):
        raise CatalogError(f"{field}.required must be an array")
    required: set[str] = set()
    for index, item in enumerate(required_value):
        if not isinstance(item, str):
            raise CatalogError(f"{field}.required[{index}] must be a string")
        required.add(item)

    parameters: list[JsonObject] = []
    for raw_name in sorted(properties):
        definition = _expect_mapping(properties[raw_name], f"{field}.properties.{raw_name}")
        name = sanitize_text(raw_name, limit=MAX_IDENTIFIER_LENGTH)
        description_value = definition.get("description", "")
        description = sanitize_text(
            _expect_text(description_value, f"{field}.properties.{raw_name}.description")
        )
        parameter: JsonObject = {
            "name": name,
            "type": _parameter_type(definition),
            "required": raw_name in required,
        }
        if description:
            parameter["description"] = description
        parameters.append(parameter)
    return parameters


def _annotation_bool(annotations: Mapping[str, object], key: str, field: str) -> bool | None:
    value = annotations.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise CatalogError(f"{field}.{key} must be a boolean")
    return value


def _metadata_tokens(value: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(value)
        if token.lower() not in _STOP_WORDS and not token.lower().startswith("redacted")
    }


def _capability_tags(
    tool: Mapping[str, object],
    *,
    searchable_text: str,
    field: str,
) -> list[str]:
    explicit_value = tool.get("capability_tags", [])
    if not isinstance(explicit_value, Sequence) or isinstance(
        explicit_value, (str, bytes, bytearray)
    ):
        raise CatalogError(f"{field}.capability_tags must be an array")
    if len(explicit_value) > 32:
        raise CatalogError(f"{field}.capability_tags contains too many entries")

    tags: set[str] = set()
    for index, value in enumerate(explicit_value):
        tag = _safe_identifier(value, f"{field}.capability_tags[{index}]")
        tags.update(_metadata_tokens(tag))
    inferred = _metadata_tokens(searchable_text) - _ACTION_WORDS
    tags.update(inferred)
    return sorted(tags)[:24]


def _classify_risk(
    *,
    searchable_text: str,
    parameter_names: Sequence[str],
    annotations: Mapping[str, object],
    field: str,
) -> tuple[str, list[str]]:
    read_only = _annotation_bool(annotations, "read_only", field)
    destructive = _annotation_bool(annotations, "destructive", field)
    open_world = _annotation_bool(annotations, "open_world", field)
    scope_value = annotations.get("scope", "unknown")
    if not isinstance(scope_value, str) or scope_value not in VALID_SCOPES:
        raise CatalogError(f"{field}.scope must be one of: {', '.join(sorted(VALID_SCOPES))}")

    evidence: list[str] = []
    if destructive is True:
        evidence.append("annotation.destructive=true")
    destructive_signal = _DESTRUCTIVE_SIGNAL_RE.search(searchable_text) is not None
    schema_execution_signal = any(
        name.strip().lower().replace("-", "_") in _EXECUTION_PARAMETER_NAMES
        for name in parameter_names
    )
    execution_signal = (
        _EXECUTION_SIGNAL_RE.search(searchable_text) is not None or schema_execution_signal
    )
    mutation_signal = _MUTATION_SIGNAL_RE.search(searchable_text) is not None
    sensitive_or_remote_signal = _SENSITIVE_OR_REMOTE_SIGNAL_RE.search(searchable_text) is not None

    if destructive_signal:
        evidence.append("metadata.signal=destructive")
    if execution_signal:
        evidence.append(
            "schema.parameter=execution" if schema_execution_signal else "metadata.signal=execution"
        )
    if mutation_signal:
        evidence.append("metadata.signal=mutation")
    if sensitive_or_remote_signal:
        evidence.append("metadata.signal=sensitive-or-remote")

    if destructive is True or destructive_signal or execution_signal:
        return "R3", evidence
    if read_only is False or mutation_signal:
        if read_only is False:
            evidence.append("annotation.read_only=false")
        return "R2", evidence
    if read_only is not True:
        evidence.append("annotation.read_only=unknown")
        return "UNKNOWN", evidence

    evidence.append("annotation.read_only=true")
    if destructive is not False:
        evidence.append("annotation.destructive=unknown")
        return "UNKNOWN", evidence
    evidence.append("annotation.destructive=false")
    if open_world is None:
        evidence.append("annotation.open_world=unknown")
        return "UNKNOWN", evidence

    if scope_value == "local" and open_world is False and not sensitive_or_remote_signal:
        evidence.append("annotation.scope=local")
        evidence.append("annotation.open_world=false")
        return "R0", evidence

    if open_world is True:
        evidence.append("annotation.open_world=true")
    if scope_value == "remote" or open_world is True or sensitive_or_remote_signal:
        evidence.append(f"annotation.scope={scope_value}")
        return "R1", evidence
    evidence.append("annotation.scope=unknown")
    return "UNKNOWN", evidence


def _normalize_tool(
    tool_value: object,
    *,
    index: int,
    source_ref: str,
    runtime_status: str,
) -> JsonObject:
    field = f"tools[{index}]"
    tool = _expect_mapping(tool_value, field)
    raw_selector = _expect_text(
        tool.get("selector"),
        f"{field}.selector",
        required=True,
        limit=MAX_IDENTIFIER_LENGTH,
    )
    selector = sanitize_text(raw_selector, limit=MAX_IDENTIFIER_LENGTH)
    if "[REDACTED_" in selector:
        raise CatalogError(f"{field}.selector contains sensitive or endpoint metadata")
    display_name_value = tool.get("display_name", selector)
    display_name = _safe_identifier(display_name_value, f"{field}.display_name")
    description = sanitize_text(_expect_text(tool.get("description", ""), f"{field}.description"))

    available_value = tool.get("available", runtime_status == "online")
    if not isinstance(available_value, bool):
        raise CatalogError(f"{field}.available must be a boolean")
    available = available_value and runtime_status != "offline"

    annotations = _expect_mapping(tool.get("annotations", {}), f"{field}.annotations")
    _annotation_bool(annotations, "idempotent", f"{field}.annotations")
    schema = _expect_mapping(tool.get("input_schema", {}), f"{field}.input_schema")
    safe_schema = _safe_schema_shape(schema, field=f"{field}.input_schema")
    parameters = _extract_parameters(schema, f"{field}.input_schema")

    parameter_text = " ".join(
        f"{parameter['name']} {parameter.get('description', '')}" for parameter in parameters
    )
    searchable_text = " ".join((selector, display_name, description, parameter_text))
    tags = _capability_tags(tool, searchable_text=searchable_text, field=field)
    searchable_text = f"{searchable_text} {' '.join(tags)}"
    risk, evidence = _classify_risk(
        searchable_text=searchable_text,
        parameter_names=[str(parameter["name"]) for parameter in parameters],
        annotations=annotations,
        field=f"{field}.annotations",
    )
    opaque_id = (
        "cap_" + hashlib.sha256(f"{source_ref}\0{selector}".encode("utf-8")).hexdigest()[:20]
    )

    normalized_annotations = {
        key: annotations[key]
        for key in ("read_only", "destructive", "open_world", "idempotent", "scope")
        if key in annotations
    }
    return {
        "runtime_id": opaque_id,
        "selector": selector,
        "display_name": display_name,
        "description": description,
        "available": available,
        "schema_hash": _sha256(safe_schema),
        "annotations": normalized_annotations,
        "parameters": parameters,
        "capability_tags": tags,
        "risk": risk,
        "requires_confirmation": risk in {"R2", "R3", "UNKNOWN"},
        "evidence": evidence,
    }


def build_catalog(
    runtime_metadata: Mapping[str, object],
    *,
    captured_at: str | None = None,
) -> JsonObject:
    """Normalize an already available runtime registry without invoking tools."""

    payload = _expect_mapping(runtime_metadata, "runtime_metadata")
    if payload.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise CatalogError(f"runtime_metadata.schema_version must be {CATALOG_SCHEMA_VERSION}")

    status = _safe_identifier(payload.get("status"), "runtime_metadata.status")
    if status not in VALID_RUNTIME_STATUSES:
        raise CatalogError(
            "runtime_metadata.status must be one of: " + ", ".join(sorted(VALID_RUNTIME_STATUSES))
        )
    source_id = _expect_text(
        payload.get("source_id", "runtime"),
        "runtime_metadata.source_id",
        required=True,
        limit=MAX_IDENTIFIER_LENGTH,
    )
    safe_source_id = sanitize_text(source_id, limit=MAX_IDENTIFIER_LENGTH)
    source_ref = "source_" + hashlib.sha256(safe_source_id.encode("utf-8")).hexdigest()[:16]

    tools_value = payload.get("tools", [])
    if not isinstance(tools_value, Sequence) or isinstance(tools_value, (str, bytes, bytearray)):
        raise CatalogError("runtime_metadata.tools must be an array")
    if len(tools_value) > MAX_TOOLS:
        raise CatalogError(f"runtime_metadata.tools exceeds the limit of {MAX_TOOLS}")

    raw_selectors: set[str] = set()
    tools: list[JsonObject] = []
    for index, tool_value in enumerate(tools_value):
        tool = _expect_mapping(tool_value, f"tools[{index}]")
        raw_selector = _expect_text(
            tool.get("selector"),
            f"tools[{index}].selector",
            required=True,
            limit=MAX_IDENTIFIER_LENGTH,
        )
        if raw_selector in raw_selectors:
            raise CatalogError(f"duplicate runtime selector at tools[{index}]")
        raw_selectors.add(raw_selector)
        tools.append(
            _normalize_tool(
                tool,
                index=index,
                source_ref=source_ref,
                runtime_status=status,
            )
        )

    tools.sort(key=lambda tool: str(tool["runtime_id"]))
    fingerprint_input = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "source_ref": source_ref,
        "status": status,
        "tools": tools,
    }
    return {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "captured_at": _safe_timestamp(captured_at),
        "source_ref": source_ref,
        "status": status,
        "fingerprint": _sha256(fingerprint_input),
        "tool_count": len(tools),
        "available_count": sum(bool(tool["available"]) for tool in tools),
        "tools": tools,
    }


def _catalog_tools(catalog: Mapping[str, object]) -> list[Mapping[str, object]]:
    if catalog.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise CatalogError(f"catalog schema_version must be {CATALOG_SCHEMA_VERSION}")
    tools_value = catalog.get("tools")
    if not isinstance(tools_value, list):
        raise CatalogError("catalog.tools must be an array")
    return [
        _expect_mapping(tool, f"catalog.tools[{index}]") for index, tool in enumerate(tools_value)
    ]


def validate_catalog_integrity(catalog: Mapping[str, object]) -> None:
    tools = _catalog_tools(catalog)
    status = catalog.get("status")
    if status not in VALID_RUNTIME_STATUSES:
        raise CatalogError("catalog.status is invalid")
    source_ref = catalog.get("source_ref")
    if not isinstance(source_ref, str) or re.fullmatch(r"source_[0-9a-f]{16}", source_ref) is None:
        raise CatalogError("catalog.source_ref is invalid")
    for index, tool in enumerate(tools):
        for key in ("runtime_id", "selector", "display_name", "description", "schema_hash", "risk"):
            if not isinstance(tool.get(key), str):
                raise CatalogError(f"catalog.tools[{index}].{key} must be a string")
        if re.fullmatch(r"cap_[0-9a-f]{20}", str(tool["runtime_id"])) is None:
            raise CatalogError(f"catalog.tools[{index}].runtime_id is invalid")
        if re.fullmatch(r"[0-9a-f]{64}", str(tool["schema_hash"])) is None:
            raise CatalogError(f"catalog.tools[{index}].schema_hash is invalid")
        if tool["risk"] not in VALID_RISKS:
            raise CatalogError(f"catalog.tools[{index}].risk is invalid")
        if not isinstance(tool.get("available"), bool):
            raise CatalogError(f"catalog.tools[{index}].available must be a boolean")
        for key in ("parameters", "capability_tags", "evidence"):
            if not isinstance(tool.get(key), list):
                raise CatalogError(f"catalog.tools[{index}].{key} must be an array")
        annotations = _expect_mapping(
            tool.get("annotations"), f"catalog.tools[{index}].annotations"
        )
        allowed_annotations = {
            "read_only",
            "destructive",
            "open_world",
            "idempotent",
            "scope",
        }
        unexpected = set(annotations) - allowed_annotations
        if unexpected:
            raise CatalogError(f"catalog.tools[{index}].annotations contains unsupported fields")
        for key in ("read_only", "destructive", "open_world", "idempotent"):
            if key in annotations and not isinstance(annotations[key], bool):
                raise CatalogError(f"catalog.tools[{index}].annotations.{key} must be a boolean")
        if "scope" in annotations and annotations["scope"] not in VALID_SCOPES:
            raise CatalogError(f"catalog.tools[{index}].annotations.scope is invalid")

    expected = _sha256(
        {
            "schema_version": CATALOG_SCHEMA_VERSION,
            "source_ref": source_ref,
            "status": status,
            "tools": [dict(tool) for tool in tools],
        }
    )
    if catalog.get("fingerprint") != expected:
        raise CatalogError("catalog fingerprint does not match catalog content")


def catalog_status(catalog: Mapping[str, object]) -> JsonObject:
    tools = _catalog_tools(catalog)
    return {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "captured_at": catalog.get("captured_at"),
        "status": catalog.get("status"),
        "fingerprint": catalog.get("fingerprint"),
        "tool_count": len(tools),
        "available_count": sum(tool.get("available") is True for tool in tools),
    }


def candidate_capabilities(
    catalog: Mapping[str, object],
    task: str,
    *,
    limit: int = MAX_CANDIDATES,
) -> list[JsonObject]:
    """Rank available capabilities using metadata overlap; never invoke them."""

    if not isinstance(task, str) or not task.strip():
        raise CatalogError("task must not be empty")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise CatalogError("limit must be a positive integer")
    limit = min(limit, MAX_CANDIDATES)
    if catalog.get("status") == "offline":
        return []

    task_tokens = _metadata_tokens(sanitize_text(task, limit=MAX_TEXT_LENGTH))
    ranked: list[tuple[int, int, str, Mapping[str, object]]] = []
    risk_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "UNKNOWN": 4}
    for tool in _catalog_tools(catalog):
        if tool.get("available") is not True:
            continue
        tags_value = tool.get("capability_tags", [])
        tags = {str(tag).lower() for tag in tags_value} if isinstance(tags_value, list) else set()
        searchable = " ".join(
            str(tool.get(key, "")) for key in ("selector", "display_name", "description")
        )
        metadata_tokens = _metadata_tokens(searchable) | tags
        overlap = task_tokens & metadata_tokens
        if not overlap:
            continue
        tag_overlap = task_tokens & tags
        score = len(overlap) * 10 + len(tag_overlap) * 4
        risk = str(tool.get("risk", "UNKNOWN"))
        score += max(0, 3 - risk_order.get(risk, 4))
        ranked.append(
            (
                score,
                risk_order.get(risk, 4),
                str(tool.get("runtime_id", "")),
                tool,
            )
        )

    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    result: list[JsonObject] = []
    for position, (score, _, _, tool) in enumerate(ranked[:limit]):
        candidate: JsonObject = {
            key: tool.get(key)
            for key in (
                "runtime_id",
                "selector",
                "display_name",
                "description",
                "schema_hash",
                "capability_tags",
                "risk",
                "requires_confirmation",
                "evidence",
            )
        }
        candidate["score"] = score
        if position < MAX_EXPANDED_SCHEMAS:
            candidate["parameters"] = tool.get("parameters", [])
        result.append(candidate)
    return result


def show_capability(catalog: Mapping[str, object], runtime_id: str) -> JsonObject:
    if not isinstance(runtime_id, str) or not runtime_id:
        raise CatalogError("runtime_id must not be empty")
    for tool in _catalog_tools(catalog):
        if tool.get("runtime_id") == runtime_id:
            return dict(tool)
    raise CatalogError(f"capability not found: {sanitize_text(runtime_id, limit=128)}")


def persist_catalog(
    catalog: Mapping[str, object],
    *,
    engineering_home: Path,
    repo: Path,
) -> dict[str, Path]:
    from mcp_catalog_storage import persist_catalog as persist

    return persist(catalog, engineering_home=engineering_home, repo=repo)


def load_catalog(engineering_home: Path) -> JsonObject:
    from mcp_catalog_storage import load_catalog as load

    return load(engineering_home)


def repository_projection_status(
    catalog: Mapping[str, object],
    repo: Path,
) -> JsonObject:
    from mcp_catalog_storage import repository_projection_status as projection_status

    return projection_status(catalog, repo)


def require_current_projection(catalog: Mapping[str, object], repo: Path) -> None:
    from mcp_catalog_storage import require_current_projection as require_current

    require_current(catalog, repo)


def refresh_catalog(
    runtime_metadata: Mapping[str, object],
    *,
    engineering_home: Path,
    repo: Path,
    captured_at: str | None = None,
) -> tuple[JsonObject, dict[str, Path]]:
    catalog = build_catalog(runtime_metadata, captured_at=captured_at)
    paths = persist_catalog(catalog, engineering_home=engineering_home, repo=repo)
    return catalog, paths


if __name__ == "__main__":
    from mcp_catalog_cli import main

    raise SystemExit(main())
