---
name: [be] mcp-tool-router
description: "Динамически выбирает доступные runtime capabilities по metadata текущей сессии, не полагаясь на заранее известные MCP, namespaces или tool names."
---

# Dynamic Runtime Capability Router

Use this skill when a non-trivial task may benefit from capabilities exposed by
the current host runtime. Discovery is capability-based: never assume a server,
namespace, provider, or tool name exists because it appeared in an earlier
session or local configuration.

## Invariants

- The host-provided registry for the current session is the source of truth.
- Discovery reads definitions only. It never invokes a capability, starts an
  endpoint, probes a disabled provider, or reads provider launch configuration.
- Production instructions and policy never contain a preselected inventory.
- URLs, commands, arguments, headers, environment values, credentials, and
  invocation values must not enter generated catalogs.
- Runtime names may exist only in private generated state excluded from Git.
- Missing, stale, contradictory, or unknown metadata is deny-by-default.

## Discovery Workflow

1. Obtain the normalized definitions already visible to the model from the host
   runtime adapter. Do not reconstruct them from configuration or cache.
2. Refresh the repository catalog from this metadata before a non-trivial task.
   The normalized input contract is
   `schemas/runtime-capabilities.schema.json`.
3. Compare the current fingerprint with the local catalog. A changed tool set,
   description, annotation, or input-schema structure requires regeneration.
4. Read `.engineering-bible/mcp/MCP_CAPABILITIES.md` for the repository-level
   shortlist, then rank candidates for the concrete task.
5. Load at most eight candidate summaries and parameter details for at most the
   first three. Use the opaque runtime id with `be mcp show` when one capability
   needs focused inspection.
6. Before invocation, verify that the selected capability is still available
   in the current host registry. Catalog presence is not proof of availability.

### Host Adapter Contract

When the orchestration host exposes a current-session registry such as
`ALL_TOOLS`, the adapter must enumerate that registry directly and map every
entry to the normalized stdin document. It must not select entries by namespace
prefix, provider name, remembered inventory, or configuration-file presence.

For each exposed entry, map only metadata the host actually provides:

- unique host selector -> `selector`;
- host label, when present -> `display_name`;
- host description, when present -> `description`;
- current exposure state -> `available`;
- input schema and annotations -> their normalized fields only when explicitly
  exposed by the host.

If a schema, annotation, scope, or availability signal is not exposed, omit it;
never synthesize evidence to obtain a lower risk rating. Use `partial` when the
registry is known to be incomplete and `offline` when it cannot be read. The
adapter serializes this projection directly to `be mcp refresh` stdin. The
catalog process itself does not query the host and has no invocation callback.

The public workflow is:

```text
be mcp refresh --repo PATH [--json]
be mcp status --repo PATH [--json]
be mcp candidates --repo PATH --task-stdin [--limit N] [--json]
be mcp show TOOL_ID [--json]
```

`refresh` consumes metadata supplied by the runtime adapter. If the host does
not expose metadata, report that limitation and use repository-native fallback
tools. Do not claim that an external capability was used.

## Risk Policy

- `R0`: local read-only; may be used when relevant.
- `R1`: remote or sensitive read; may be used when relevant to the request.
- `R2`: reversible write or external communication; use only when the current
  request already authorizes that exact side effect.
- `R3`: destructive, privileged, or arbitrary execution; require separate
  confirmation immediately before use.
- `UNKNOWN`: require separate confirmation and treat as unsafe until metadata
  resolves the ambiguity.

Provider annotations are evidence, not authority. A read-only hint cannot lower
risk when the name, description, or schema indicates mutation, destruction, or
execution.

## Offline And Partial State

- `offline`: no catalog entry is executable, even if stale definitions remain.
- `partial`: consider only entries explicitly marked available.
- disappeared tool: remove it on refresh and use a local fallback.
- invocation failure: report the failure; never silently claim the capability
  contributed evidence.

## Local State

The private full catalog lives under
`$ENGINEERING_BIBLE_HOME/runtime/mcp/catalog.json`. Repository projections live
under `.engineering-bible/mcp/`. All generated files use mode `0600`, and the
repository directory is added to the local Git exclude rather than tracked
`.gitignore`.
