# Absorbed Skills Migration

Bible owns selection, personal engineering rules and integration policy. The
selected author's complete workflow belongs to the author and remains an
independently versioned dependency. Compatibility names must route to that
workflow; they must not contain another abbreviated implementation of it.

This audit covers all **62 local skill trees present before this migration**,
including the pending `mobile-qa` and `wiki-query` additions. Repository history
and current files identify one explicit named adaptation, several compatible
Superpowers workflow replacements, and native plugin integration wrappers.
Similarity of names or general engineering advice does not establish historical
derivation. An unknown origin is recorded as unknown rather than attributed to
an unrelated marketplace author.

## Reviewed Authors

| Source | Reviewed revision | Licensing evidence | Payload |
| --- | --- | --- | --- |
| [Superpowers, Jesse Vincent / Prime Radiant](https://github.com/obra/superpowers) | [`8ca22dba9a94f28898bbce59f2537ff4d87c747d`](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d), tag `v6.4.2` | MIT, original `LICENSE` | All 15 skill trees, references, prompts and helpers |
| [Karpathy-inspired guidelines, Multica / original forrestchang repository](https://github.com/multica-ai/andrej-karpathy-skills) | [`2c606141936f1eeef17fa3043a72095b4765b9c2`](https://github.com/multica-ai/andrej-karpathy-skills/tree/2c606141936f1eeef17fa3043a72095b4765b9c2) | MIT declared in pinned `README.md` and skill frontmatter; no standalone LICENSE file | Original `skills/karpathy-guidelines` |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | [`d81f3a183412e71a5b1e84ca21bc1a35eea03a60`](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60) | MIT, original `LICENSE`; `pr/CREDITS` retained | Existing eight reviewed skill trees |

The Karpathy repository describes guidelines derived from Andrej Karpathy's
observations. It is not represented here as a repository maintained by Karpathy
himself. The old `forrestchang` URL redirects to `multica-ai`; the canonical URL
is pinned in the catalog. Because this source has no standalone license file,
the dependency store preserves its complete pinned README as licensing evidence.

This migration introduced 24 author trees, their exact source paths,
mode-aware tree digests, license evidence digests and installation dependencies.
The registry owns group membership and which local groups require those author
dependencies. Author branch tips are discovery inputs; installations and updates
use the reviewed commits.
The current catalog adds three independently maintained
[business UI specialists](business-ui-profile.md), then
[testing/context authors](quality-context-authors.md), bringing the total to 30.

## Compatibility And Policy

| Legacy selection | Original provider | Local responsibility |
| --- | --- | --- |
| `debugging` | `superpowers.systematic-debugging` | Evidence scope, authorization and project validation constraints |
| `testing-tdd` | `superpowers.test-driven-development` | Project test conventions and explicitly authorized exceptions |
| `tdd-guard` | `superpowers.test-driven-development` | Explicit opt-in to strict test-first policy; no claim to install external hooks |
| `code-review` | `superpowers.requesting-code-review` | Review scope, severity rules and findings contract |
| `quality-gates` | `superpowers.verification-before-completion` | Bible evidence, regression and portable-tree gates |
| `agent-squad` | `superpowers.dispatching-parallel-agents` | Lane ownership, export permissions, limits and result merging |
| `karpathy-guidelines` | `karpathy.karpathy-guidelines` | Selection conditions; author retains the original skill name |

The Superpowers rows are deliberately identified as compatible workflow
replacements. Local history does not prove they were copied from Superpowers.
`karpathy-guidelines` explicitly identified itself as an adaptation, so its
original author tree replaces the local rendition rather than coexisting under
the same name. Bible policies belong outside that author tree.

`requesting-code-review` supplies the author's request workflow and reviewer
template. It is not evidence that a reviewer or subagent has run. The host must
expose a compatible review capability, or the integration must state the actual
limitation. The same separation applies to parallel dispatch and native plugins.

Superpowers' full group includes `brainstorming`, `writing-plans`,
`executing-plans`, `subagent-driven-development`, `using-git-worktrees`,
`finishing-a-development-branch`, `receiving-code-review`, `writing-skills`,
`diagnosing-superpowers` and `using-superpowers` in addition to the providers
above. The original files are not rewritten to impose Bible routing policy.
Higher-priority user and repository instructions still determine authorization,
model selection and scope.

## Complete Local Audit Ledger

`Owner` means a local policy or procedure tied to Bible's standards, tools or
evidence contract; no named author origin was established. `Integration` means
host selection of an existing original provider, whose availability must be
checked in the current session. `Adapter` means a legacy name delegates the
workflow to the reviewed original and keeps only owner integration policy.

| Legacy local skill | Decision | Evidence / retained responsibility |
| --- | --- | --- |
| `accessibility-ui-review` | Owner | Rendered accessibility evidence and reporting policy; no named source |
| `agent-retrospective` | Owner / integration | Local durable-failure policy; original `diagnosing-superpowers` for Superpowers-specific diagnosis or Pocock `retro` when explicitly selected |
| `agent-squad` | Adapter | Dispatch original; retain custom lane, export and worker evidence contracts |
| `agents-md-retrospective` | Owner | Scoped instruction-update policy, separate from authored skill writing |
| `architecture-map` | Owner | Verified source map and shared code-indexing contract |
| `architecture-normalizer` | Owner | Bible architecture normalization artifacts and standards |
| `architecture-principles` | Owner | References Bible architecture/domain standards; no named source |
| `authz-boundary-review` | Owner | Narrow authorization review policy; no named source |
| `c-cpp` | Owner | Bible language policy and existing project tooling |
| `code-quality` | Owner | Bible size, responsibility and complexity standards |
| `code-review` | Adapter | Original request/reviewer template; local findings and scope policy |
| `code-to-figma` | Integration | Explicit native Figma `figma-code-connect` / `figma-generate-design` providers |
| `code-wiki-ru` | Owner | Repository-owned indexing, planning, rendering and validation scripts |
| `context-pack` | Owner / tool integration | Repomix reference plus custom bounded-export contract; not a copied Repomix skill |
| `core-engineering` | Owner | Bible default policy and concrete code-discovery mapping |
| `debugging` | Adapter | Original complete `systematic-debugging` workflow |
| `dependency-advisory-audit` | Owner | Version/reachability review contract; no named source |
| `deserialization-parser-review` | Owner | Narrow input/parser review contract; no named source |
| `design-system-extractor` | Owner | Visual reference/evidence extraction contract; no named source |
| `documentation` | Owner | Bible public-behavior and documentation-drift policy |
| `engineering-standards` | Owner | Entry point to repository-owned standards library |
| `esp32` | Owner | Bible hardware safety policy and project-native validation |
| `esphome` | Owner | Bible hardware/configuration policy and project-native validation |
| `external-agent-pack-audit` | Owner | Provenance, instruction trust and runtime review contract |
| `fast` | Owner | User-selectable small reversible task policy |
| `figma-to-code` | Integration | Explicit native Figma prerequisite and implementation provider |
| `fix-security-finding` | Integration | Original Codex Security `fix-finding` provider; owner authorization/scope |
| `go` | Owner | Bible language policy and existing project tooling |
| `homeassistant` | Owner | Bible physical-device and automation policy |
| `karpathy-guidelines` | Original replaces adaptation | Explicit adaptation statement and matching named author source |
| `mcp-tool-router` | Owner router | Current-session capability choice and host adapter contract |
| `migration-planner` | Owner | Compatibility, slices, rollback and evidence contract |
| `mobile-qa` | Integration / owner policy | Reuse original Android/iOS testing skill when compatible; selected-device evidence policy |
| `multi-agent-pr-review` | Owner / integration | Bounded read-only review policy and findings merge contract; original dispatch when required |
| `performance` | Owner | Measured bottleneck and correctness policy; no named source |
| `playwright-visual-qa` | Owner / native tools | Accepted-reference screenshot evidence policy; no named skill origin |
| `python` | Owner | Bible language policy and existing project tooling |
| `quality-gates` | Adapter / owner policy | Original completion verification plus Bible-specific evidence/drift gates |
| `refactoring` | Owner | Bible behavior-preservation policy and refactoring references |
| `responsive-breakpoint-check` | Owner / native tools | Viewport evidence policy; no named skill origin |
| `review-router` | Owner router | Distinguish read-only review, planning and patch work |
| `rust` | Owner | Bible language policy and existing project tooling |
| `secrets-and-config-review` | Owner | Bounded metadata-first configuration review policy |
| `security` | Owner | Bible implementation trust and secret-handling policy |
| `security-diff-review` | Integration | Original Codex Security `security-diff-scan` provider |
| `security-router` | Owner router | Narrow security selection and authorized mutation scope |
| `session-memory` | Owner / tool integration | Custom durable-facts/privacy contract and existing memory/search tools; generic inspiration does not prove a Claude-Mem origin |
| `specialist-dispatch` | Owner / integration | Portable roles and enforced worker boundaries; original dispatch/execution providers for workflow |
| `subagent-result-merge` | Owner | Repository-defined result, evidence and unknown-state contract |
| `supply-chain-review` | Owner | Dependency/installer/release trust review policy |
| `tdd-guard` | Adapter | Original test-first workflow, explicit strict selection; no external hook installation |
| `testing-tdd` | Adapter | Original full test-driven-development workflow |
| `threat-model` | Integration | Explicit original Codex Security `threat-model` provider |
| `typescript` | Owner | Bible language policy and existing project tooling |
| `ui-build` | Owner router | Select actual original build provider exposed by host |
| `ui-concept-first` | Owner / integration | Reference-first policy; actual Figma, Product Design or build provider |
| `ui-figma` | Owner router | Select original native Figma provider and prerequisite |
| `ui-qa` | Owner router | Select actual original QA provider plus evidence policy |
| `ui-research` | Owner router | Named Lazyweb modes are references; missing native provider is unavailable, not a summarized substitute |
| `ui-router` | Owner router | Order genuinely mixed UI work, retain direct-leaf selection |
| `wiki-query` | Owner | Bounded read-only repository documentation lookup |
| `workflow-router` | Owner router | Narrow selection, stable continuation and dependency handoff |

## Dependency And Host Constraints

Install dependency edges represent mandatory background and cross-tree payload
references. Conditional handoffs between `writing-plans` and execution skills do
not become cyclic installation dependencies. Default Superpowers selection
includes the complete 15-skill group, so every author handoff remains available.

Important cross-tree payloads include:

- `executing-plans` uses helpers under
  `subagent-driven-development/scripts/`, host references under
  `using-superpowers/references/`, and the original reviewer template under
  `requesting-code-review/`.
- `subagent-driven-development` uses the original reviewer template and branch
  completion/worktree workflows.
- `writing-skills` requires original test-driven-development background and
  refers to original host-specific tools documentation.

Preserve these directory names and sibling relationships. Preserve executable
intent of author helpers; neither catalog inspection nor installation executes
them. Superpowers' optional visual companion has its own runtime and telemetry
behavior; dependency installation does not start it or enable a session hook.

Native plugin providers retain native ownership and update semantics. A plugin
installed by the host is reused when the reviewed original tree is compatible;
Bible does not take ownership of plugin caches. An unknown version, changed
tree, unavailable runtime tool or pending host reload remains visible. Do not
claim that files on disk prove current-session skill or tool exposure.

Local modifications and legacy installations require a checked handoff. Back up
only owned artifacts, validate provenance before replacing an adaptation, and
refuse unowned or modified conflicting trees. Updating author dependencies must
leave owner rules and routers intact. See [the lifecycle guide](upstream-skills.md)
for the implemented commands and recovery behavior.
