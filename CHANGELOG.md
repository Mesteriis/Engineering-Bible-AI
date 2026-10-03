# Changelog

All notable changes to this project are documented here.

## [0.4.1] - 2026-10-03

- Installed managed standards, documentation and templates beside active owner
  skills so their relative references resolve in Codex and linked Claude skills.
  Existing unowned files retain the installer's conflict protection; original
  author trees and their reviewed pins are unchanged.
- Added installation regressions for owner references, documentation template
  links and unowned reference-file conflicts.

## [0.4.0] - 2026-10-03

- Separated owner rules and routing from 30 complete, independently updated
  author skills with reviewed revisions, tree and license hashes; normal
  profiles require 20 originals. Added explicit plan, ensure, check, update
  and rollback commands without automatic adoption of author branch tips.
- Replaced absorbed debugging, TDD and review workflows with adapters to
  originals, including the complete Superpowers pack and Karpathy-inspired
  guidelines. Compatible native providers retain their own update ownership.
- Added the business UI profile for dashboards, CRM and working applications,
  routing to original Interface Design, UI UX Pro Max and Impeccable skills.
- Made `/multimodel` and `/quorum` separate task-scoped opt-ins. Ordinary tasks
  keep the selected model; offline quorum checks do not activate live reviewers.
- Added bounded worker evidence, continuation and offline review contracts,
  plus original property-based testing and optional handoff/context compression.
- Added deterministic context-cache preparation and provider-usage interpretation,
  and targeted Python unittest mutation checks. Neither prepares a live provider
  route or establishes billed savings.
- Hardened author dependency handoff, backup and rollback while preserving
  modified or unowned files. Upgrades prune retired empty directories only
  inside the portable package snapshot and restore their modes on rollback.
- Added opt-in pinned OpenCode, QMD and Semgrep tools and kept runtime
  configuration, credentials and model mappings outside the public package.
- Fixed compatibility with the pinned CI type checker without weakening
  runtime validation or changing the CI tool version.
- Preserved the `quality-audit` compatibility target, rejected `.env.*` runtime
  files and excluded local root worktrees while rejecting tracked private state.
- Merged pinned Checkout 7.0.1 and Setup Python 7.0.0 action updates.
- Added the `steady` prompt profile as the new-install default while preserving
  the complete default skill catalog.
- Preserved manifest-selected profiles during both update and reinstall unless
  `--prompt-profile` is supplied explicitly.
- Added same-task continuation reuse to `steady`, `minimal`, and strict `full`
  profiles so follow-up turns do not rerun routing, reread unchanged skills, or
  refresh unchanged runtime capability metadata.
- Kept exhaustive route coverage in on-demand router references and narrowed
  default routes to one primary skill plus at most one supporting skill.
- Fixed all skill frontmatter names to match the Agent Skills lowercase-hyphen
  contract and made the validator reject malformed names.
- Reduced overlapping skill descriptions while preserving explicit invocation
  paths.
- Compiled Python validation targets in-process instead of spawning one
  interpreter per file.

## [0.3.0] - 2026-07-10

- Pinned shell formatting validation to four-space indentation for reproducible CI results.

## [0.2.0] - 2026-07-10

- Fixed portable shell formatting and bootstrap usage diagnostics for release validation.
- Added the opt-in `fast` prompt profile that bypasses routing and optional runtime additions.

## [0.1.0] - 2026-07-10

- Added ownership-aware transactional installation and unified updates.
- Added runtime-derived MCP/tool capability discovery and repository-local recommendations.
- Added validation profiles, prompt profiles, provenance checks, and release gates.

## 2026-06-28

- Bootstrapped the public `Engineering-Bible-AI` repository.
- Added portable Codex engineering standards, routing skills, ecosystem skills,
  review/security/UI wrappers, and `code-wiki-ru`.
- Added installer and validation scripts.
- Documented the worker/runtime boundary to keep local config and credentials
  out of the portable package.
