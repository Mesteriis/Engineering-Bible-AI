# Upstream Skill Lifecycle Implementation Plan

> **For agentic workers:** Execute the owner's approved design in this checkout,
> preserving existing changes. Use focused parallel implementation where file
> ownership is disjoint, and an independent review before completion.

**Goal:** Install missing author skills without rewriting them, retain provenance,
and provide independent check/update/rollback and task routing.

**Architecture:** Keep Bible package installation unchanged. Add a portable
upstream catalog, registry-owned opt-in groups, immutable source staging, and a
separate local ownership lock. CLI and routers consume that lifecycle.

**Tech Stack:** Python 3.11 standard library, JSON, existing registry YAML subset,
unittest, existing tool catalog.

**Spec:** `docs/superpowers/specs/2026-10-03-upstream-managed-skills-design.md`.

**Status:** Pilot implementation and review fixes delivered. Bootstrap and full
gates passed; release gates passed on an isolated source snapshot. The working
checkout's release membership gate still rejects its untracked new files.
Native host exposure and production installation are outside this execution.

## Constraints and Decisions

- Preserve dirty files and existing `be update` / `be add skill` behavior.
- No credentials, host inventory, downloaded skills, or runtime state tracked.
- Registry v2 adds opt-in `upstream` groups; local v1 selection stays compatible.
- Install exact author trees once under the Codex skill root, with license and
  provenance in a separate Bible dependency store. No rewriting author files.
- Reuse identical existing trees by content; conflict on unknown/different
  providers. The Codex skill root is inventoried recursively, including legacy
  `external/` imports. Other native roots require explicit additional skill roots,
  never private configuration. Installation is not session exposure.
- First curated pack: Pocock interview/domain/writing plus PR, retrospective,
  questionnaire. `implement-spec` remains deferred by the approved design.
- Updates apply the reviewed catalog revision. `check` reports tracking changes;
  it cannot automatically promote an unreviewed author commit.
- Required tool installation uses existing explicit tool selections and remains
  separate from authentication, setup, and actual runtime capability.

## Review Focus

- Interrupted multi-skill writes: recover previous active trees and lock.
- Local/unowned edits and symlink collisions: preserve files and stop.
- Source paths, archive links and revision/digest mismatch: reject before writes.
- Existing discovery roots and transitive dependencies: avoid duplicate installs.
- Repeated ensure, read-only status/check, and rollback: report actual state.

## Task 1: Catalog, registry, immutable sources

Files: `scripts/upstream_catalog.py`, `scripts/upstream_sources.py`,
`config/upstream-skills.json`, `scripts/registry.py`, `skills/registry.yml`,
`tests/test_upstream_catalog.py`, `tests/test_upstream_sources.py`.

Interfaces: `SourceSpec`, `SkillSpec`, `Catalog`, `UpstreamError`;
`load_catalog(path, registry_path=None)`,
`select_skills(catalog, skill_ids, groups, include_all)`,
`fingerprint_tree(path)`, `stage_source(source, destination)`.

- [x] Write and run failing tests for invalid provenance, unsafe paths,
  dependency cycles, group selection, file fidelity and archive boundaries.
- [x] Implement typed catalog and safe source staging; pin reviewed public source
  and compute the real per-tree and license digests.
- [x] Run focused catalog/source and existing registry tests.

## Task 2: Local lifecycle

Files: `scripts/upstream_skills.py`, `tests/test_upstream_skills.py`.

Interface: `SkillManager(catalog, home, skill_root, existing_roots=())` with
`plan(skills)`, `ensure(skills, dry_run=False, upgrade=False)`,
`check(skills)`, `rollback(dry_run=False)`, `route(intent)`.
All results are JSON-serializable dict/list values.

- [x] Write and observe failing filesystem regression tests for missing-only
  installation, reuse, conflicts, author fidelity, update and rollback.
- [x] Implement locked staging, tree ownership, provenance, atomic lock writes,
  backups and recovery; verify revisions/digests before active writes.
- [x] Cover interruptions, extra-file edits, changed modes, alias collisions,
  dependency closure and unchanged repeated synchronization.
- [x] Finish review regressions for rollback backup integrity and local edits
  arriving during a transaction, then rerun the final lifecycle checks.

## Task 3: CLI, routing and tools

Files: `scripts/be.py`, `scripts/upstream_cli.py`,
`tests/test_upstream_cli.py`, router policy and documentation.

Interfaces: CLI adapter uses the catalog and manager interfaces above. Commands
`be skills list|plan|status|ensure|check|update|rollback|route`;
selectors `--skill`, `--group`, `--all`; output `--json`; extra existing-provider
roots `--skill-root`; optional catalog override for explicit synthetic fixtures.

- [x] Write and run failing subprocess tests in isolated temporary homes.
- [x] Implement CLI without changing existing package update semantics.
- [x] Connect required tools through existing catalog; show unresolved setup and
  exposure separately. Add thin route references and update adoption defaults.
- [x] Update README, operating docs, notices, release files and generated blocks.

## Task 4: Integration and independent review

- [x] Run focused tests, `make validate-bootstrap`, `make validate`, and
  `make validate-release`; preserve raw logs and actual outcomes.
- [x] Verify real upstream staging and file fidelity in a disposable test home.
- [x] Obtain an independent scoped review, fix material findings with regression
  coverage, and report live exposure limits without claiming activation.

## Execution Record

The owner approved execution with "Давай делать" after reviewing the design.
Implementation proceeds in the existing checkout on a feature branch. No
production installation, external issue changes, push, or publication is implied.

The delivered catalog pins eight Pocock trees and their MIT license at
`d81f3a183412e71a5b1e84ca21bc1a35eea03a60`. Public archive staging verified all
eight catalog tree hashes and the license hash. Local lifecycle and CLI fixtures
use isolated temporary homes and mocked author transports where appropriate.

The final disposable CLI smoke downloaded the real reviewed source and installed
all eight skills with matching hashes. Repeated ensure left state unchanged and
created no new backup. Tracking checks reported `UNCHANGED`; `grill-me` routing
retained explicit invocation and `pending-exposure`. Dry-run and actual rollback
removed the eight managed skills while preserving an unrelated personal fixture.
Raw smoke records remain untracked under
`.engineering-bible/implementation/upstream-lifecycle/`.

The focused upstream suite passed 67 tests after review fixes. Final focused
review found no actionable issue; scoped Ruff and ty passed. Backup corruption
now refuses restoration, and concurrent local edits are preserved during
activation and recovery. A conflicting interrupted transaction can retain its
journal pending deliberate resolution. The final bootstrap and full profiles
passed. Release results distinguish the working Git index from the isolated
candidate snapshot rather than treating a rejected release gate as success.

Final verification outcomes:

| Command | Actual outcome |
| --- | --- |
| `python3.11 -m unittest tests.test_upstream_catalog tests.test_upstream_sources tests.test_upstream_skills tests.test_upstream_cli -v` | PASS: 67 tests |
| `make validate-bootstrap` | PASS |
| `make validate` | PASS, including full test discovery and install validation |
| `make validate-release` in the working checkout | FAIL: ten required new lifecycle files are not tracked in its Git index |
| `make validate-release` in an isolated copy of 277 current public files | PASS, including tracked snapshot bootstrap and install |
| `ruff check scripts tests` | PASS |
| `ruff format --check scripts tests` | PASS through full/release profiles |
| `ty check scripts tests` | PASS through full/release profiles |
| `python3.11 scripts/registry.py --root . docs` | PASS: generated blocks current |

The candidate release used a separate Git repository; the original Git index
was checked byte-for-byte unchanged. No commit or publication was performed.
An earlier temporary-index experiment failed because Git fixture subprocesses
inherited that index and added a fixture-only path. Its FAIL log is retained;
the isolated repository run resolved that test-environment coupling. Release
logs, exit codes and summaries remain in the untracked artifact directory above.

The pilot does not claim native host invocation, credentials/setup, background
tracking, automatic promotion of author changes, or full library migration.
`implement-spec` and additional authors remain deferred.
