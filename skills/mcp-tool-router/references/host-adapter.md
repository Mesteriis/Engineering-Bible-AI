# Host Adapter Contract

The orchestration host must enumerate its current-session capability registry
directly. It must not filter by namespace prefix, provider name, remembered
inventory, or configuration-file presence.

For every exposed entry, map only metadata the host actually provides:

- unique host selector -> `selector`;
- host label, when present -> `display_name`;
- host description, when present -> `description`;
- current exposure state -> `available`;
- input schema and annotations -> normalized fields only when explicitly
  exposed by the host.

If a schema, annotation, scope, or availability signal is absent, omit it. Never
synthesize evidence to obtain a lower risk rating. Use `partial` when the
registry is known to be incomplete and `offline` when it cannot be read. The
adapter serializes this projection to `be mcp refresh` stdin. The catalog process
does not query the host and has no invocation callback.

The normalized input contract is
`schemas/runtime-capabilities.schema.json`.

## Public Commands

```text
be mcp refresh --repo PATH [--json]
be mcp status --repo PATH [--json]
be mcp candidates --repo PATH --task-stdin [--limit N] [--json]
be mcp show TOOL_ID [--json]
```

`refresh` consumes metadata supplied by the runtime adapter. If the host does
not expose metadata, report the limitation and use repository-native fallback
tools. Never claim that an external capability was used without invocation
evidence.

## Offline And Partial State

- `offline`: no catalog entry is executable, even if stale definitions remain.
- `partial`: consider only entries explicitly marked available.
- disappeared capability: remove it on refresh and use a local fallback.
- invocation failure: report it; never silently claim that it contributed
  evidence.

## Private State

The private full catalog lives under
`$ENGINEERING_BIBLE_HOME/runtime/mcp/catalog.json`. Repository projections live
under `.engineering-bible/mcp/`. Generated files use mode `0600`, and the
repository directory is added to local Git exclude rather than tracked
`.gitignore`.
