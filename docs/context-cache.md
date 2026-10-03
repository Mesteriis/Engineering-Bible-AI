# Context Cache Preparation

`scripts/context-cache.py` prepares an offline Anthropic Messages API fragment
from an explicitly captured source snapshot. It makes no model call, adds no
provider authentication or endpoint, and does not claim a provider cache hit.
Preparation proves only that the selected local files still match the supplied
snapshot at the time of verification.

## Request contract

Capture the source with the existing snapshot command, then supply the complete
captured text for each manifest entry in manifest order:

```json
{
  "schema_version": 1,
  "cache_scope": "project-alpha-review",
  "requested": {"provider": "provider-selected-by-caller", "model": "model-selected-by-caller"},
  "base_commit": "full-lowercase-git-object-id",
  "snapshot": {"state": "captured", "sha256": "...", "files": []},
  "wire_format": "anthropic_messages",
  "ttl": "5m",
  "blocks": [{"path": "src/example.py", "text": "complete UTF-8 file text"}],
  "task_text": "The complete volatile task text"
}
```

The request has exact fields. Duplicate JSON keys, non-finite numbers, symlinks,
private or unsafe source paths, stale snapshots, incomplete manifests, altered
text, and inputs beyond the bounded size limits fail closed. A snapshot with an
unknown base commit is blocked. `cache_scope` is a caller-owned opaque namespace
and must not contain secrets, host paths, or authorization claims. Route values
are caller inputs and are represented in output only by a digest.

Prepare and verify locally:

```bash
python3 scripts/worker-evidence.py snapshot --root /path/to/source \
  --file src/example.py > /path/to/snapshot.json
# Build request.json by retaining base_commit and snapshot and adding the fields above.
python3 scripts/context-cache.py prepare /path/to/request.json --source-root /path/to/source
```

The default output contains metadata and hashes only. To include source context
and task text in local stdout, explicitly pass `--export-authorized`. This flag
authorizes local export only; it does not authorize a network request. The
fragment is an append operation: merge `system_append` onto the caller's
existing system content and `messages_append` onto its existing messages. This
preserves the caller's system prompt. The appended system policy carries the
scope separator and marks source text as untrusted data. Stable source blocks
stay in user content, preserving the original file text, and the selected
`5m` or `1h` TTL is attached to the final stable user block only. The complete
task text follows as a separate user text block. The scope, requested route,
base commit, source snapshot, stable content, TTL, and wire format bind the
local cache identity. Volatile task text is excluded so task changes can reuse
the same prefix identity.

The documented Anthropic adapter is based on the provider's
[prompt caching documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
The usage adapter recognizes the documented cache-creation breakdown fields;
this schema reference does not establish support or behavior for any live route.
Its fragment is request preparation only. Runtime activation remains `BLOCKED`
until the selected gateway route has strict route enforcement, verified cache
support and minimum-token behavior, and actual provider usage evidence.

## Usage evidence

Pass a saved provider usage object or complete provider response JSON to `usage`:

```bash
python3 scripts/context-cache.py usage /path/to/provider-usage.json
```

The adapter accepts either a usage object directly or a complete provider
response containing a `usage` object. It preserves `input_tokens`,
`output_tokens`, `cache_read_input_tokens`, and `cache_creation_input_tokens` as
supplied finite nonnegative integers; missing counts become `null`. It also
preserves the measured `cache_creation.ephemeral_5m_input_tokens` and
`cache_creation.ephemeral_1h_input_tokens` counts or `null`, and rejects a
mismatch when the total and both breakdown counts are present. Uninterpreted
usage metadata such as service tier, inference geography, and iteration details
is ignored and omitted from normalized output. Keep the original provider
response as the raw evidence artifact.

It reports `HIT` only when cache-read tokens are positive, `MISS` when read
tokens are zero and cache creation is measured, and `UNKNOWN` otherwise.
Unknown cache metrics return `usage_status: SKIP` and exit `2`; known `HIT` or
`MISS` classifications return `usage_status: PASS` to indicate measured cache
evidence, not a successful application decision. Cost and savings remain
unknown; token counts alone do not establish billed price or savings.

Exit codes are `0` for successful preparation or measured usage interpretation,
`1` for an invalid request/response, and `2` when source evidence is unavailable
or incomplete, preparation is blocked, or cache usage metrics are unknown.
