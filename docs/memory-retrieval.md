# Optional Memory Retrieval

`scripts/memory-retrieval.py` plans bounded search variants and combines ranked
document results with reciprocal rank fusion (RRF). It works offline using the
Python standard library. It performs no search or inference and installs no
store, model, service, hook, or runtime. Use it only when a measured comparison
shows that the additional query helps the selected corpus.

The isolated query-expansion/RRF idea was evaluated against Ruflo's
[`smart-retrieval.ts` at commit b02c0cacec225deea01f586b66a9694393369432](https://github.com/ruvnet/ruflo/blob/b02c0cacec225deea01f586b66a9694393369432/v3/@claude-flow/memory/src/smart-retrieval.ts).
This helper is a separate Python implementation of those general techniques;
it does not vendor Ruflo code. Recency boosts, session rotation and MMR reranking
are not included. Document age alone does not establish relevance or freshness.

## Workflow

1. Capture the explicitly authorized search corpus with the existing
   [source snapshot helper](worker-evidence.md). Keep index data and real search
   records in private, untracked storage. Bind index construction to that exact
   corpus; a snapshot taken only after search does not prove what was searched.
2. Run `plan` and send each returned variant to the same authorized search
   capability, with the same corpus and result limit. Pass queries as data,
   never interpolate them into shell commands. Do not add private collections.
3. Save the ranked lists, their original scores, document IDs, source-relative
   paths and source hashes. Include empty lists for searches returning nothing;
   a failed or unexecuted search is not an empty successful search.
4. Run `fuse --source-root` against that corpus. Check the status before using
   results. Read the cited source files before making claims about their content.

```bash
python3 scripts/memory-retrieval.py plan "How can I compare recorded worker workloads?"
python3 scripts/memory-retrieval.py fuse /path/to/private/rankings.json \
  --source-root /path/to/authorized/corpus --limit 5
```

`plan` preserves the trimmed original query and may add one lower-case variant
with common English/Russian grammatical words and punctuation removed. Unicode
content words remain intact. The original query handles cases where grammar,
punctuation or short symbols matter. This is lexical simplification, not
translation, stemming or semantic expansion. Queries are nonempty, single-line
UTF-8 strings of at most 1,024 bytes. No alternative is added when it would be
empty, equivalent to the original ignoring case, or above the query byte limit
after Unicode case conversion.

## Ranked Input

The JSON object has exactly three keys:

- `query`: the original query supplied to `plan`.
- `source`: the complete `{base_commit, snapshot}` object emitted by
  `worker-evidence.py snapshot`. Its file manifest must cover the authorized
  corpus, including local changes; all paths and hashes are checked for internal
  consistency. This is the existing snapshot format, not a second index format.
- `rankings`: one object for every planned variant, with exactly `query`,
  `snapshot_sha256`, and `results`. `snapshot_sha256` must match `source`.

Every `results` entry has exactly these fields:

| Field | Meaning |
| --- | --- |
| `id` | Stable document ID, a nonempty UTF-8 string of at most 512 bytes |
| `path` | Canonical relative POSIX file path from the source manifest |
| `sha256` | The corresponding file's SHA-256 from the indexed snapshot |
| `score` | Original finite numeric score returned by the search capability |

Lists arrive in best-first rank order. Raw scores are retained as provenance;
they are not assumed to have comparable scales between queries. There are at
most 100 results per variant. Each document occurs once per list, one ID always
names the same path/hash, and one path always has the same ID. This interface
accepts whole-document rankings; aggregate chunk results per file in the caller
before using it. Duplicate JSON keys, unknown fields, invalid hashes, aliases,
unplanned/missing variants and mixed snapshots are rejected.

The helper cannot detect a caller inventing source labels, omitting indexed
files or misreporting search execution. Preserve the search tool's raw outputs
and actual failures separately. Hash consistency is not authentication.

## Output And Status

The output retains the original `baseline` ranked list in full. `results` holds
the fused top results, with `rrf_score` and per-variant `provenance` containing
the query, one-based rank, raw score and snapshot hash. Each fused document also
retains its ID, source path and hash. RRF sums `1 / (60 + rank)` across lists.
Equal scores prefer the first occurrence in planned query order, starting with
the baseline, so input JSON list order cannot change ties. `--limit` accepts an
integer from 1 to 50; the default is 5. Results do not replace the stored baseline.

`contract_status` describes ranked-input consistency. `source_status` and
`outcome` distinguish:

- `PASS` (exit 0): every declared source file matches a fresh recapture of the
  manifest, including the base commit when known. Outside Git, `base_commit`
  remains `unknown`; file hashes can still be checked.
- `SKIP` (exit 2): `--source-root` was omitted. Fusion is available, but source
  freshness remains unknown. Do not present these results as freshly verified.
- `FAIL` (exit 1): malformed evidence, unavailable source, a changed manifest
  or unsafe source traversal. When source verification fails, both ranked output
  and baseline output are suppressed; the caller's original record is untouched.

The source checker reads only declared paths, rejects symlink traversal and
uses the snapshot helper's bounds and private-path filtering. Two matching
passes detect observed changes; they do not make an atomic index snapshot or
guarantee freshness after the command returns. The input JSON must be a regular
file, at most 8 MiB; symlink JSON files and duplicate keys are rejected.

## Validation

```bash
python3 -m unittest discover -s tests -p 'test_memory_retrieval.py' -v
```

For an adoption decision, compare the original search and fused search using the
same frozen corpus, independently labeled queries, held-out variations and
source checks. Record Recall@5, reciprocal rank and latency separately from
index/model initialization. Synthetic ranked-list tests establish helper
behavior only; they are not evidence of a working external search integration.
