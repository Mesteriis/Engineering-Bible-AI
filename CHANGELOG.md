# Changelog

All notable changes to this project are documented here.

## [0.3.1] - 2026-07-10

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
- Reduced overlapping skill descriptions without removing any of the 60 skills
  or their explicit invocation paths.
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
