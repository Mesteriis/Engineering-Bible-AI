# Steady-State Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the complete Engineering Bible capability set while removing repeated router, skill-read, and runtime-discovery work from follow-up turns.

**Architecture:** Introduce a backward-compatible `steady` prompt profile as the new-install default, retain `full` as strict first-turn mode with same-task continuation reuse, sharpen skill metadata, and split detailed router material into on-demand references. Enforce the contracts with repository-level tests and validators.

**Tech Stack:** Python 3.11, shell installers, Markdown Agent Skills, YAML-like metadata, unittest.

## Global Constraints

- Cold-start latency is not the optimization target.
- No skill directory or explicit invocation is removed.
- Existing manifests preserve their prompt profile during update or reinstall.
- `full` remains exhaustive when a task begins or materially changes and reuses
  that route on same-task follow-ups.
- Validation claims require fresh command output.

---

### Task 1: Add regression tests for valid Agent Skills metadata

**Files:**
- Create: `tests/test_skill_frontmatter.py`
- Modify: `scripts/validate-skill-frontmatter.py`

**Interfaces:**
- Consumes: `validate_skill(skill_dir: Path) -> list[str]`
- Produces: strict name and description validation matching the Agent Skills contract.

- [ ] Add tests that reject `[be]`, uppercase, consecutive hyphens, directory mismatch, and descriptions over 1024 characters.
- [ ] Run the new tests and confirm they fail against the current canonicalizing validator.
- [ ] Replace prefix canonicalization with exact regex and directory checks.
- [ ] Run the new tests and confirm they pass.

### Task 2: Add and wire the steady prompt profile

**Files:**
- Create: `instructions/global/steady.md`
- Modify: `scripts/install_codex.py`
- Modify: `scripts/be.py`
- Modify: `scripts/validate-installed-tree.sh`
- Modify: `scripts/validate.py`
- Modify: `scripts/install.sh`
- Modify: `tests/test_be_cli.py`
- Modify: `tests/test_installer.py`

**Interfaces:**
- Produces: prompt profile value `steady`; default new-install profile `steady`.

- [ ] Add tests proving default install activates `steady`, installs normal default skills, and explicit `full` still works.
- [ ] Run targeted tests and confirm failure because `steady` is unsupported.
- [ ] Add profile choices, prompt budget, release-file requirements, and help text.
- [ ] Confirm update code still preserves a manifest-recorded profile.
- [ ] Run targeted tests and confirm pass.

### Task 3: Implement steady-state routing semantics

**Files:**
- Modify: `instructions/global/steady.md`
- Modify: `instructions/global/minimal.md`
- Modify: `AGENTS.md`
- Modify: `skills/workflow-router/SKILL.md`
- Create: `skills/workflow-router/references/routes.md`
- Modify: `skills/mcp-tool-router/SKILL.md`
- Create: `skills/mcp-tool-router/references/host-adapter.md`
- Create: `tests/test_steady_profile.py`

**Interfaces:**
- Produces: continuation fast path, direct leaf selection, lazy capability discovery.

- [ ] Add static contract tests for continuation reuse, no mandatory routing, bounded default skill set, and lazy discovery.
- [ ] Run tests and confirm failure against current prompts.
- [ ] Write the steady prompt and update minimal/project instructions.
- [ ] Slim router entry files and move exhaustive tables/contracts to references.
- [ ] Run static contract and router fixture tests.

### Task 4: Normalize and sharpen all skill metadata

**Files:**
- Modify: `skills/*/SKILL.md`
- Create: `tests/test_skill_catalog.py`

**Interfaces:**
- Produces: exact valid skill names and concise, non-overlapping descriptions.

- [ ] Add a catalog test that requires all 60 names to match directories and caps aggregate description characters.
- [ ] Run it and confirm failure on branded names and current catalog size.
- [ ] Normalize every name and rewrite descriptions with explicit trigger boundaries.
- [ ] Run catalog and frontmatter tests.

### Task 5: Update documentation and release metadata

**Files:**
- Modify: `README.md`
- Modify: `README.ru.md`
- Modify: `MANIFEST.md`
- Modify: `CHANGELOG.md`
- Modify: `VERSION`
- Modify: `pyproject.toml`
- Modify: `scripts/install.sh`

**Interfaces:**
- Produces: documented `steady`, `full`, `minimal`, and `fast` behavior.

- [ ] Document the new default and migration command.
- [ ] Record compatibility and steady-state behavior in the changelog.
- [ ] Bump patch version consistently.
- [ ] Run release-contract and generated-document checks.

### Task 6: Verify and package

**Files:**
- Create: `Engineering-Bible-AI-steady-state.patch`
- Create: `Engineering-Bible-AI-0.3.1-steady.zip`

**Interfaces:**
- Produces: reviewable patch and installable archive.

- [ ] Run focused tests.
- [ ] Run `make validate-quick`.
- [ ] Run `make validate-bootstrap` and release-contract checks.
- [ ] Review `git diff --check`, changed-file scope, and archive contents.
- [ ] Generate the patch and ZIP only after validation succeeds.
