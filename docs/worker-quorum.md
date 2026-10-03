# Offline Cross-Provider Review Quorum

`worker-evidence.py quorum` evaluates a fixed review policy over the existing
[worker result contract](worker-evidence.md). It does not start a worker, contact
a provider, export source, execute checks, merge changes or authenticate metadata.
The parent launcher supplies the facts and must enforce the returned decision.

Live voting is off by default and requires the user's task-scoped `/quorum`
command. `/multimodel` alone does not enable voting. See
[Explicit Activation](cross-provider-review.md#explicit-activation).
Evaluating already-recorded offline fixtures does not activate live reviewers.

Use this after `/quorum` and two independent reviews of the same concrete change. An explicit
three-reviewer policy can request a third review when the first two materially
disagree, or run all three independently for a higher-risk task. The helper
recommends an adaptive third review only for an eligible APPROVE versus
REQUEST_CHANGES disagreement without an existing veto. Timeouts and abstentions
do not trigger a debate
loop or reduce the number of approvals required.

## Run

```bash
python3 scripts/worker-evidence.py quorum /path/to/envelope.json \
  --source-root /path/to/reviewed-source \
  --artifacts-root /path/to/local-evidence
```

The roots must contain the named source and artifact files. The helper checks
the source manifest against the current Git HEAD and file bytes, including
explicitly selected uncommitted files. It also hashes the pre-reviewed output
manifest and the post-review evidence manifest. Changed files, missing evidence,
symlinks and unsafe paths fail verification. Unselected files are outside this
proof; the launcher must select the complete relevant change and keep private
runtime data outside the package.

Omitting either root reports that verification as `SKIP`. A policy-only ACCEPT
then becomes CLI `decision=BLOCKED`, `policy_decision=ACCEPT`, `outcome=SKIP`,
exit 2. It cannot become a release or merge approval. A detected failure retains
`FAIL` even if another verification was skipped.

## Schema 1 Envelope

All fields below are required. Unknown fields in the envelope, target, policy,
ballots, concerns and resolutions are rejected. Embedded worker records retain
the existing contract. The JSON reader rejects duplicate keys, non-finite
numbers, non-regular files and inputs larger than 8 MiB.

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1` |
| `target` | The immutable reviewed task and artifact description below |
| `target_sha256` | Canonical SHA-256 of the entire `target` object |
| `policy` | Fixed mode, ordered reviewer roster and author identities |
| `policy_sha256` | Canonical SHA-256 of the entire `policy` object |
| `gate_record` | Non-voting launcher-owned worker record for actual checks |
| `ballots` | At most the two or three registered reviewers, without duplicates |
| `resolutions` | Explicit evidenced resolutions of noncritical concerns |
| `evidence_artifacts` | Post-review file manifest covering exactly every declared gate and ballot record artifact |

Canonical hashes use UTF-8 JSON with `ensure_ascii=False`, `sort_keys=True`,
`separators=(",", ":")`, and `allow_nan=False`. `worker_quorum.target_digest`
computes this digest for a JSON object. Repeat both hashes in every ballot;
changing the acceptance criteria, reviewed output, roster, authors or mode
invalidates earlier ballots. Recompute and collect new reviews after changing
the target. A caller can fabricate all these fields; hashing detects internal
inconsistency, not a dishonest launcher.

`target` contains exactly:

- `task_id`, `goal`, `base_commit`: the exact identity repeated by every worker
  record. An unknown base commit cannot pass.
- `snapshot`: the captured manifest from `worker-evidence.py snapshot`, including
  its aggregate digest and sorted path/SHA-256/byte entries. A commit name alone
  does not bind dirty files.
- `acceptance_criteria`: 1–64 unique, concrete nonempty strings.
- `required_checks`: 1–32 unique exact check command strings. A reviewer's
  confidence or prose is not a check execution.
- `artifacts`: a nonempty sorted manifest of the change being reviewed, such as
  a patch and specification. Each entry is exactly `path`, `sha256`, `bytes`.
  This manifest is created before dispatch and contains no future review logs.

The post-review `evidence_artifacts` uses the same entry format. It includes the
exact union of all gate and ballot `record.artifacts`, including raw check logs,
observed-model metadata, launcher independence attestations, counterexamples,
parent confirmations and resolution evidence. Those files are distinct from
the pre-reviewed target artifacts. The launcher seals this manifest after
collecting records and retains it with the envelope. Its bytes must match at
evaluation; a changed check log cannot silently retain PASS. Both manifests use
the existing snapshot limits: at most 256 files, 8 MiB per file, 32 MiB total,
canonical relative paths, no private metadata paths and no filesystem aliases.

`policy` contains exactly `mode`, `roster`, `author_ids`. Modes are:

| Mode | Fixed roster | Required approvals |
| --- | --- | --- |
| `consensus_2_of_2` | Exactly two reviewers | Both reviewers |
| `quorum_2_of_3` | Exactly three reviewers | Any two eligible reviewers |

Each ordered roster entry is exactly `reviewer_id` and `requested`, where
`requested` contains explicit `provider` and `model` strings. Reviewer identities
are unique and cannot appear in the unique `author_ids` list. The roster and
route are fixed before dispatch; replacing a reviewer or silently falling back
to another model invalidates the recorded review. `author_ids` must reflect all
implementers; the helper cannot discover real identities itself.

Two approvals must come from **two distinct observed providers**. Two models of
one provider cannot satisfy this cross-provider policy. Provider/model pairs
are compared after trimming and case-folding; duplicate observed pairs block
the quorum. The launcher must provide canonical actual identities and prevent
aliases for one backend from pretending to be independent providers. An alias
string, a worker's self-description or `runtime_metadata` in JSON does not
authenticate a provider. Unknown observations cannot vote.

## Ballots And Evidence

Each ballot contains exactly:

- `reviewer_id`, `target_sha256`, `policy_sha256`: registered identity and the
  two hashes given to that reviewer before dispatch.
- `vote`: `APPROVE`, `REQUEST_CHANGES` or `ABSTAIN`.
- `reason`: a concrete nonempty rationale; it is never counted as a PASS check.
- `record`: the existing worker result with the exact task, goal, commit and
  snapshot. Requested and known observed route must match its roster entry.
- `independence`: exactly `phase`, `peer_results_seen`, `source`. A voter needs
  `phase=independent`, an empty peer list and a declared launcher artifact as
  source. `phase=informed` records an ineligible later discussion participant.
  The launcher attests what was actually sent; a role prompt is insufficient.
- `concerns`: at most 32 explicit concerns. REQUEST_CHANGES requires at least
  one. A worker finding by itself does not establish a confirmed counterexample.

An eligible voter has a valid completed record, known matching route, PASS
recorded checks, no open questions and an independent first assessment. A
failed or blocked reviewer, skipped check, missing measurement, unknown route
or informed discussion cannot provide an approval. Unknown token/cost usage
remains unknown and does not itself invalidate a review.

Each concern contains exactly `id`, `severity` (`critical` or `noncritical`),
`evidence_artifact`, `parent_confirmed` (boolean), and `confirmation_artifact`.
IDs are unique across the envelope. Evidence references a declared artifact in
that ballot. For `parent_confirmed=true`, the confirmation also references a
declared parent/launcher evidence artifact; otherwise it is `null`. The parent
must actually vet the counterexample. The evaluator checks this declaration and
file integrity, and does not reproduce or prove the alleged bug.

Every unresolved concern prevents acceptance. Unconfirmed critical claims need
factual review; they are not automatically verified vetoes. A confirmed critical
counterexample vetoes the current target regardless of approval count. It cannot
be overridden with a resolution on the same artifact. Fix the change, capture
the new target and obtain new reviews. If investigation disproves a critical
claim, preserve that evidence and obtain an updated assessment.

A noncritical resolution contains exactly `concern_id`, `reviewed_by` and
`evidence`. At least two eligible reviewers from distinct providers must be
listed. Each has one evidence entry containing `reviewer_id` and `artifact`,
referencing their declared record artifacts. The evaluator cannot decide whether
the evidence actually resolves the concern; the parent remains responsible.
Resolution does not rewrite a REQUEST_CHANGES ballot into an approval.

Required checks may be recorded by the non-voting gate or reviewer records.
The non-voting gate can retain unknown model metadata for deterministic local
tests; it need not invent an LLM provider identity. Its record still needs to be
completed, with actual PASS checks and no open questions. A failed, blocked,
empty or skipped gate cannot be replaced by reviewer agreement.
Every required command needs an original PASS result and raw artifact. Any
required FAIL in a scoped valid record vetoes acceptance, even if another record
reports PASS or another ballot is malformed. SKIP, BLOCKED, prose summaries and
successful model completion cannot replace a required check.

## Decisions And Limits

| Decision | Meaning | CLI exit |
| --- | --- | --- |
| `ACCEPT` | Two eligible approvals from distinct providers, required checks PASS, resolved concerns, local verification PASS | `0` |
| `REQUEST_CHANGES` | Required check failure or a parent-confirmed critical counterexample | `1` |
| `NEEDS_REVIEW` | Unresolved factual or noncritical disagreement | `2` |
| `BLOCKED` | Fixed threshold, independent route evidence or required verification unavailable | `2` |
| `INVALID` | Malformed/replayed/substituted/mismatched records or failed local verification | `1` |

`evaluate_quorum` is the pure policy evaluator: its ACCEPT covers only recorded
consistency. Use the CLI with both roots to add local verification. Its
`proof_scope` remains `launcher_record_consistency_only` even after file checks;
file hashes do not prove execution, reviewer identity, test correctness, a
sandbox or independent reasoning. Veto facts already found are retained if an
unrelated invalid ballot changes the final decision to INVALID.

The helper neither persists an authoritative roster nor detects fabrication of
an entirely new envelope. The parent must retain the pre-dispatch policy,
enforce identity and capability checks from the
[runtime boundary](worker-runtime-boundary.md), preserve raw artifacts and
original exit codes, prevent peer leakage in first reviews, and keep export
authorization and budgets bounded. It must not interpret majority agreement as
permission to publish, merge, contact others or expose source externally.

## Verification

```bash
python3 -m unittest tests.test_worker_quorum -v
```

The tests use synthetic provider identities and temporary local Git repositories.
They exercise actual CLI exit codes, stale dirty source, changed patch/evidence
bytes, missing roots, majority vetoes, unresolved concerns, timeouts, authors,
roster changes, model fallbacks, replay, duplicate JSON keys and input limits.
They do not launch or certify any real provider.
