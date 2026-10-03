# Author Skill Lifecycle

Bible owns rules, standards and routing. The catalog in
`config/upstream-skills.json` pins reviewed author skill trees; groups and profile
requirements in `skills/registry.yml` own membership. Author instructions and their relative
references remain intact. A tracking ref is used only to report newer author
commits, never to select installation content automatically.

The catalog contains 30 original skills: the complete 15-skill Superpowers 6.4.2
pack, the original Karpathy-inspired guidelines, nine Matt Pocock skills,
three [business UI specialists](business-ui-profile.md), property-based testing
and context compression. See [testing and context authors](quality-context-authors.md).
The normal `steady`, `full` and `minimal` installation includes the 20 originals
required by the `core`, `review` and `ui` groups. `fast` retains its compact owner-only
selection. See [the complete migration ledger](absorbed-skills-migration.md) for
the disposition of all 62 previous local skill trees.

The nine Matt Pocock skills remain an explicit selection at reviewed commit
`d81f3a183412e71a5b1e84ca21bc1a35eea03a60`:

| Opt-in group | Author skills |
| --- | --- |
| `pocock-interview` | `grill-me`, `grilling`, `grill-with-docs`, `domain-modeling` |
| `pocock-writing` | `writing-for-agents`, `pr` |
| `pocock-retro` | `retro` plus required `writing-for-agents` |
| `pocock-questionnaire` | `to-questionnaire` |
| `context-continuation` | `handoff` plus Context Engineering's `context-compression` |

The local debugging, TDD and review names are thin compatibility adapters; the
condensed Karpathy rendition is removed and replaced by the author's original
under its original name. Owner standards and integration policy stay local.
`implement-spec` and unproven additional author sources remain deferred.
Development validation uses disposable homes;
no production installation or native host activation is implied.

## Select and Install

Installing a normal Bible profile synchronizes its disclosed missing author
dependencies without enabling upstream hooks, running setup or starting helpers:

```bash
be install --dry-run
be install
be install --skill-root /path/to/existing/superpowers/skills
```

An existing compatible provider is reused with external ownership. Installation
never upgrades an existing original to a different catalog pin implicitly.
Superpowers relies on payloads in sibling skill directories. Its selected
originals must share one provider root; a partial native pack cannot be combined
with managed siblings in another root. Such a split is a conflict before any
author files are installed. Point `--skill-root` to the complete compatible pack.
Explicit `--skip-upstream` installs portable owner files only and records
incomplete author dependencies; installed validation reports their readiness
as `SKIP`. This is an offline preparation mode, not a complete usable profile.

Additional author selections use their independent lifecycle:

```bash
be skills list --json
be skills plan --group pocock-interview --json
be skills ensure --group pocock-interview --dry-run --json
be skills ensure --group pocock-interview --json
be skills status --group pocock-interview --json
```

Use repeated `--skill ID`, repeated `--group NAME`, or `--all` for an explicit
selection. `list` and `status` default to the complete reviewed catalog. `plan`,
`ensure`, `check` and `update` require a selection. Transitive skill requirements
are included automatically. Group names and canonical skill IDs are printed by
the registry and catalog; an unknown selection is an error.

Managed author trees install under the selected Codex home's `skills` directory.
Dependency locks, source/license provenance and backups live under the selected
Bible home's `dependencies` directory, separate from the Bible package manifest.
Source `skill_roots` declare narrowly reviewed original locations, including
`.agents/skills` and `.claude/skills`; their surrounding host configuration is
excluded. Original files are copied without path rewriting. Optional source
`notices` contain safe paths and reviewed SHA-256 digests; extraction checks them
before activation and retains their original paths beside licensing evidence.
For Bible-managed providers, `plan` reports `ATTRIBUTION_REQUIRED` if reviewed
licensing evidence is missing. `ensure` restores that evidence even when the
author tree is unchanged, without replacing the tree. Modified retained evidence
reports `MODIFIED` and stops synchronization. Native providers retain external
ownership and do not require a second managed attribution store.
Override these homes with the existing global `be --home` and `--codex-home`
options. No production installation is implied by repository development tests.

## Reuse Existing Providers

```bash
be skills plan --group pocock-interview --skill-root /path/to/native/plugin/skills --json
be skills ensure --group pocock-interview --skill-root /path/to/native/plugin/skills --json
```

`--skill-root` can repeat and points only to existing provider roots. These roots
are inspected and never modified. The default discovery surface is the selected
Codex skill root and its descendants, including legacy `external/` imports;
other plugin managers' private installation roots are not
discovered automatically and must be provided explicitly. Exact content matches
can satisfy dependencies without duplicate installation. Digests preserve file
bytes and paths with canonical Git file modes (`0644` for ordinary files and
`0755` for executables). Unknown, different, edited or symlinked providers
stop activation rather than being adopted or overwritten. Native plugin updates
remain the responsibility of the native manager.

## Track, Review and Update

```bash
be skills check --group pocock-interview --json
be skills update --group pocock-interview --dry-run --json
be skills update --group pocock-interview --json
be skills rollback --dry-run --json
be skills rollback --json
```

`check` reads author tracking refs and reports a newer commit without installing
it. A failed tracking read remains `ERROR` in the report and returns a nonzero
exit code. The report compares commit identities; it does not produce an
instruction or dependency diff. Review upstream instruction changes, executable
files, dependencies, license and owner-policy compatibility before changing the
catalog's commit and digests.
`update` applies only that reviewed catalog revision. It does not promote the
tracking result. `ensure` fills missing dependencies without upgrading existing
managed author trees. Repeated synchronization does not duplicate providers.

Skill transactions retain previous managed state for rollback. Conflicting local
edits are preserved; resolve them deliberately instead of using a force flag.
Rollback refuses missing, corrupt or changed backup content before restoration.
Local edits arriving during source staging or activation are preserved. Recovery
can stop with a transaction journal still present when current files no longer
match the recorded transaction; preserve the files, state, backups and journal
and resolve that conflict deliberately before retrying.
Rollback affects Bible-owned skill state. It does not undo native plugin updates,
tool package changes, authentication, hooks or other separate configuration.
Inspect a reported partial result before retrying any failed operation.

`be update` updates the Bible package and fills missing original dependencies of
its selected groups. Existing author pins require a separate `be skills update`.
A former Bible-owned same-name rendition can transfer to dependency ownership
only when the prior package manifest proves every file, byte and mode, with no
unmanaged additions. Modified or unowned renditions are refused even with
`--force`; `--no-overwrite` does not authorize replacing them.

Dependency and package transactions have separate ownership and backups. A
package failure compensates the dependency transaction only while its exact
backup is still current. An interrupted handoff can resume from verified
dependency state; concurrent edits or a newer transaction require deliberate
reconciliation. This is not a claim of one atomic cross-store transaction.

Legacy `be add skill`
remains a separate import operation and does not gain reviewed provenance or
dependency-update ownership automatically.

## Required Tools and Runtime Availability

`plan` discloses required tool versions, install commands and setup steps through
the existing tool catalog. Explicit `ensure` or `update` may install missing pinned
required tools after a successful skill transaction. Optional tool IDs are shown
but are not installed automatically. Unsupported required tools stop before
mutation. Unpinned missing tools or existing version mismatches require a separate
reviewed `be tools install` selection with its existing explicit flags.

The current 30 records declare no package-manager tool dependencies.
Author workflows may still need native host capabilities or external services;
read their actual instructions and verify those prerequisites when invoking them.
The generic tool integration is not evidence of functional execution of a pilot
workflow or authentication to any external service. Superpowers host references,
reviewer templates and sibling helper trees remain intact; the real host must
expose compatible invocation/delegation tools. Native Figma, Codex Security and
mobile testing adapters invoke original installed plugins and retain only owner
authorization and evidence policy; unavailable plugins remain unresolved.

Tool installer output and exit codes are retained in JSON results. A failed tool
step reports partial completion with already installed skill state intact. Tool
package changes may not be reversible; inspect `be tools list` before recovery.
Authentication, setup, hook activation and services are separate explicit actions.
No lifecycle command configures credentials or proves current-session exposure.

```bash
be skills route grill-me --json
```

Routing reports the selected provider, filesystem state and pending tool/setup
requirements. A file match remains pending exposure until the actual host exposes
the skill. User-named current-session skills take priority. Load the full author
instructions only when needed, using the host's real invocation capability. If
owner policy conflicts with an author step, state that conflict or choose an
explicitly named owner workflow; do not silently replace the author's procedure.
Normal task routing neither installs dependencies nor checks the network each turn.

## Catalog Maintenance and Fixtures

`--catalog PATH` and `--registry PATH` allow an explicit reviewed alternate catalog
and its group registry. They do not disable source, license, digest or dependency
validation. Private endpoints, credentials, host inventory, downloaded author
files and machine configuration do not belong in portable catalogs or Git.
