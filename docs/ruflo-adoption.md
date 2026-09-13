# Ruflo Adoption Decision

Decision date: 2026-09-13. Adopt optional query simplification and reciprocal
rank fusion as a small Python helper alongside the existing search capability.
Retain the current worker runtime. Add local evidence validation and bounded
continuation decisions to the existing worker contract.

The evaluated Ruflo revision is
[`b02c0cacec225deea01f586b66a9694393369432`](https://github.com/ruvnet/ruflo/tree/b02c0cacec225deea01f586b66a9694393369432).
This is a scoped evaluation of that revision, not a certification of the full
framework or later releases. No Ruflo package, global hook, model dependency,
or additional memory service is added to this distribution.

## Worker Comparison

Six frozen synthetic code-review tasks were each run once through the installed
native Codex CLI and once through the unchanged Ruflo
[`DualModeOrchestrator.spawnWorker`](https://github.com/ruvnet/ruflo/blob/b02c0cacec225deea01f586b66a9694393369432/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts).
They cover an omitted final element, mutable default state, safe parameterized
SQL, binary-search termination, safe subprocess argument passing, and hidden
command failure. Checks require the expected bug classification and a valid
source location where applicable. Prompts and acceptance criteria were fixed
before execution; pair order alternated and there were no task retries.

Both arms used the same configured model and effort through Codex CLI 0.153.4,
with tools disabled and only the self-contained fixture in the prompt. At most
two workers ran concurrently. The upstream TypeScript ran unchanged under
Node 24.20.0 with its TOML parser installed only in the temporary pilot directory.

| Observed measure | Native worker | Ruflo worker |
| --- | ---: | ---: |
| Passed task checks | 6/6 | 6/6 |
| Sum of request duration, milliseconds | 168,743 | 181,572 |
| Input tokens | 75,001 | 75,865 |
| Cached input tokens | 0 | 20,736 |
| Output tokens | 380 | 669 |

Durations are summed per-request measurements, not total elapsed experiment
time. Usage comes from actual CLI completion events. This small run shows no
quality gain and is insufficient for a general speed claim. Different cache
usage and unverified prices preclude a cost conclusion. The requested route was
identical, but completion metadata did not independently identify the executed
provider/model; observed route therefore remains `unknown`. Passing task checks
does not satisfy the worker contract's separate route-verification gate.

This exercised real worker dispatch and responses. It did not exercise full
repository editing, shared-memory collaboration, swarms, or other Ruflo services.

A separate synthetic timeout probe started a worker with a sleeping descendant.
After a three-second timeout, the native adapter's process-group cancellation
stopped both. Ruflo's timeout stopped its worker parent while the descendant
remained running. The probe then explicitly cleaned it up and verified it had
stopped. This fails the existing process-tree cancellation requirement and is
an additional reason to retain the current launcher. The first probe attempt
used an insufficient startup deadline and produced no usable child fixture;
only the corrected, successfully completed probe supports this finding.

Evidence fingerprints:

- Worker fixture SHA-256:
  `0634104760368ec0d2c1c5f76ee9f623e42fe409e8dc70a0c29ca454bbf008fc`.
- Evaluated orchestrator SHA-256:
  `c764274e7be692e8f00bb7da621c9d49610b60d41750c8a78bb941e8a9902220`.

## Retrieval Comparison

The retrieval pilot used 57 frozen public repository documents and 15 labeled
English/Russian queries, including five held-out query variations. Every arm
searched the same isolated QMD 2.8.3 full-text index; no LLM or embedding model
was used. The unchanged upstream
[`smart-retrieval.ts`](https://github.com/ruvnet/ruflo/blob/b02c0cacec225deea01f586b66a9694393369432/v3/%40claude-flow/memory/src/smart-retrieval.ts)
was run against that index, followed by the new portable helper using the same
queries and labels. Labels were fixed before the runs.

| Method | Recall@5, all 15 | MRR, all 15 | Recall@5, held-out 5 | MRR, held-out 5 |
| --- | ---: | ---: | ---: | ---: |
| Original QMD search | 0.8000 | 0.8667 | 0.8000 | 0.8000 |
| Ruflo default retrieval | 0.8667 | 0.9333 | 1.0000 | 1.0000 |
| Ruflo with MMR disabled | 0.9000 | 0.9333 | 1.0000 | 1.0000 |
| Portable query variant + RRF | 0.8667 | 0.9333 | 1.0000 | 1.0000 |

Recall@5 is the mean fraction of labeled relevant documents in the top five;
MRR is the mean reciprocal rank of the first relevant document within the top
five. The new helper
did not regress on any labeled query. Most benefit came from removing
grammatical words from a natural-language query that otherwise missed a relevant
document. Ruflo's ASCII tokenization also broadened one mixed Russian query by
discarding its Cyrillic terms; the new helper preserves Unicode content words
and intentionally does not reproduce that behavior.

MMR did not improve this benchmark. Recency weighting also lacks an adoption
case here: modification time does not prove relevance or factual freshness.
The selected helper therefore retains only the original query, one optional
content-word variant, and rank fusion, with original scores and source hashes.
This is a separately implemented optional facility, not copied runtime code.

These results support use on this corpus, not a universal quality guarantee.
Repeat the comparison when changing the corpus or search service. Index/model
initialization and full application latency are outside the ranking experiment;
additional queries and source verification still have a measurable cost.

Across 21 rotated warm repetitions, with the same bridge and complete source
verification included for each arm, median/p95 milliseconds were 19.244/20.854
for baseline, 20.714/47.038 for Ruflo default, and 19.949/21.878 for the new helper.
These are local benchmark observations, not application latency guarantees.

Evidence fingerprints:

- Retrieval fixture SHA-256:
  `f3ab51fe2cc21e3883a812288e42fccfa73d8adae2d2a9c04327289cdb132079`.
- Frozen corpus manifest SHA-256:
  `28db92299ef4dd7d0cf780f01549857fae2377ce34fa0eff2b36d61a73c98f41`.
- Evaluated upstream retrieval SHA-256:
  `21548f9338f9fb260d2186bc07f0634671658b4377a222da6db5bf57ed9bb574`.

## Adopted Interfaces And Boundaries

- [Worker evidence](worker-evidence.md): capture allowlisted source hashes,
  validate the existing result contract, and compare matched historical runs
  without turning unknown routes or skipped checks into success.
- [Bounded continuation](worker-evidence.md#bounded-run-decisions): evaluate
  fixed budgets, repeated failures, unchanged verified progress, and checkpoint
  acknowledgment. Tests include a real subprocess loop with saved/reloaded state
  that stops when its output does not change. The host must retain authoritative
  state, enforce decisions, and cancel in-flight work independently.
- [Memory retrieval](memory-retrieval.md): plan optional queries and fuse existing
  search results with source verification. The host still owns search execution
  and the original index. Missing source verification is `SKIP`; stale source is
  `FAIL`, with fused results suppressed.

The commands, modules, and tests are included in installer validation. They do
not silently activate an autonomous loop or replace an installed runtime.
Sanitized aggregate decisions belong in this document. Original pilot scripts,
raw responses, fixture copies, runtime metadata, and machine configuration stay
in private untracked evidence storage under the runtime-boundary policy.
