# Upstream Skill Additions

Recorded: 2026-10-03, following the owner's request.
Status: 30 original author trees are cataloged; default profiles require 20:
the complete Superpowers pack, original Karpathy-inspired guidelines and three
business UI specialists and original property-based testing. Nine Pocock skills
and context compression remain opt-in.
The [62-skill ledger](absorbed-skills-migration.md)
records local replacements, owner policies and native integrations. Host invocation
remains separate evidence; this document
does not install anything in the owner's production environment.

## Adoption Rule

Add author-maintained skills as traceable upstream dependencies, retaining their
instructions, referenced files, assets, license, and update source. Bible owns
selection, routing, personal policies, and small host adapters. Do not replace
the author's procedure with an extracted summary.

The lifecycle design is
[Bible as a policy and routing layer](superpowers/specs/2026-10-03-upstream-managed-skills-design.md).
The delivered commands and recovery limits are documented in
[Author skill lifecycle](upstream-skills.md).

## Addition Queue

Source: [mattpocock/skills](https://github.com/mattpocock/skills), MIT.
The pilot pin `d81f3a183412e71a5b1e84ca21bc1a35eea03a60` was reviewed on
2026-10-03. `config/upstream-skills.json` records the full commit, each complete
skill-tree digest and the MIT license digest. The four groups in
`skills/registry.yml` are opt-in; the ordinary Bible installer does not install
the author pack automatically. Inclusion means the lifecycle can manage these
trees, not that a native host has exposed or functionally exercised them.

| Status | Author skills | Purpose | Bible integration |
| --- | --- | --- | --- |
| Pilot catalog | `grill-me`, `grilling` | Stress-test plans using dependent rounds of decisions | Explicit interview route; reuse the author procedure |
| Pilot catalog | `grill-with-docs`, `domain-modeling` | Interview with glossary and ADR capture | Retain the author's documentation workflow and owner project conventions |
| Pilot catalog | `writing-for-agents` | Write and maintain agent-facing instructions | Route instruction/skill authoring to the real upstream reference |
| Pilot catalog | `pr` | Explain changes with before/after evidence and merge impact | Use upstream guidance with repository-specific PR requirements |
| Pilot catalog | `retro` | Improve the agent environment after a session | Keep `agent-retrospective` as a separately named owner workflow |
| Pilot catalog | `to-questionnaire` | Prepare questions for a domain expert | Explicit document-creation route; sending remains separate |
| Deferred | `implement-spec` | Implement a dependency graph on one integration branch | Verify parallel-work, ownership and review limits before adoption |

`grill-me` invokes `grilling`. `grill-with-docs` invokes both `grilling` and
`domain-modeling`. `retro` loads `writing-for-agents`. The pilot declares these
required skill edges and installs their transitive closure. Preserve referenced files
such as `domain-modeling/GLOSSARY-FORMAT.md` and
`writing-for-agents/SKILL-MECHANICS.md`; a lone `SKILL.md` is insufficient.

## Review Notes

- `grill-me` and `grill-with-docs` are user-invoked upstream entry points. Preserve
  their explicit-invocation policy when projecting host metadata.
- Current `grilling` asks rounds at the settled decision frontier. It explores
  facts through subagents and waits for shared-understanding confirmation. Check
  compatibility with the owner's invocation, delegation, and approval rules;
  report any adapter difference instead of silently rewriting the procedure.
- `grill-with-docs` also changes project documentation. Respect existing glossary
  and ADR locations. Do not run the author's setup workflow during import.
- `setup-matt-pocock-skills` edits project instructions and issue-tracker docs.
  If a selected workflow needs that setup, expose it as a separate reviewed
  configuration step. Do not install or run the whole setup by implication.
- `retro` can inspect local session logs. Keep that access bounded to the selected
  session; private transcripts and machine state do not belong in Bible.
- `implement-spec` is a later candidate. The author lists unresolved frontier,
  review-closeout, and parallel-safety work. Its worktree resets, merges, issue
  changes, and cleanup require a separately verified integration contract.
- Generic debugging, TDD, review, and architecture skills from the pack are not
  automatic additions. First inventory the existing Bible workflows and determine
  whether an upstream provider offers a distinct useful capability.

## Release Tracking

The [1.3 preparation PR](https://github.com/mattpocock/skills/pull/1120) merged on
2026-09-29, promoting `implement-spec`, `pr`, and `retro`, removing
`resolving-merge-conflicts`, and changing the domain-document convention to
`GLOSSARY.md` / `GLOSSARY-MAP.md`.
At review time the [latest published release](https://github.com/mattpocock/skills/releases)
was `v1.2.3` from 2026-08-06. Main-branch candidates must not be presented as an
already published 1.3 release. The pilot uses the reviewed full commit above,
not an asserted 1.3 release. Check release state again before a future pin update.

[Superpowers](https://github.com/obra/superpowers) is now a reviewed upstream
dependency, separate from the Pocock addition queue:

- [6.4.1](https://github.com/obra/superpowers/releases/tag/v6.4.1), 2026-09-19:
  session diagnosis and revised native plan execution.
- [6.4.2](https://github.com/obra/superpowers/releases/tag/v6.4.2), 2026-09-25:
  leaner decision-focused plans.

Reuse a compatible existing installation before considering another copy.
The complete 15-skill group is adopted with reviewed trees and dependency edges.
Preserve owner policy around planning, approvals, testing, and delegation when
invoking the original workflows.

## Remaining Adoption Work

Original PBT, handoff and context compression are now adopted as described in
[Testing And Context Author Skills](quality-context-authors.md). The optional
continuation group extends the original eight-skill Pocock pilot with handoff
at the same reviewed revision; it does not upgrade the other leaves.

- Verify native host exposure and actual invocation for each selected workflow;
  `be skills route` deliberately reports exposure as unverified.
- Review host-specific tool and setup needs during invocation. The 30 current
  catalog records declare no package-manager tool dependencies; this does not
  prove that external operations or native tools are available.
- Keep the migration ledger current when adding or replacing local workflows;
  unknown provenance must not be attributed to an unrelated author.
- Evaluate `implement-spec` and further authors as separately reviewed sources.
  Automatic promotion of an author's tracking tip remains disabled.

## Completion Criteria for Each Addition

- Record the source, full immutable revision, license, complete tree hashes,
  invocation policy, dependencies, and reviewed effects.
- Resolve an existing compatible provider or install only the required missing
  artifacts without duplicate host discovery.
- Verify the real host invocation and any tool prerequisites; distinguish
  installation, setup, session exposure, and functional validation.
- Verify that change detection and a staged update preserve author files and
  owner rules, detect local edits, and support recovery.
- Add deterministic routing and lifecycle regression coverage, update generated
  membership docs through `scripts/registry.py`, and report actual checks.
