# Serena Shared Indexing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install and configure Serena 1.7.0 as the shared code-indexing layer for Codex and Claude and encode the portable routing policy in Engineering Bible AI.

**Architecture:** The repository owns only the version pin, routing guidance, and validation. The installed `serena` executable and per-client MCP registrations remain machine-local. Serena handles symbol-level navigation; Graphify and Repomix retain their existing specialized roles.

**Tech Stack:** Python 3.13, uv tool management, Serena MCP, TOML/JSON client configuration, unittest, Make.

**Spec:** `docs/superpowers/specs/2026-09-09-shared-code-indexing.md`

## Global Constraints

- Pin `serena-agent` to exactly `1.7.0`.
- Do not install hooks or commit generated project/client state.
- Preserve unrelated dirty-worktree changes.
- Use Serena for broad/repeated symbol exploration, not every localized read.
- Keep Graphify as the architecture/dependency Tier 2 tool.

---

### Task 1: Portable catalog and routing policy

**Files:**
- Modify: `config/tools.json`
- Modify: `skills/core-engineering/SKILL.md`
- Modify: `tests/test_tool_catalog.py`

**Interfaces:**
- Consumes: catalog schema version 2 and the existing Project Context Bootstrap policy.
- Produces: pinned Serena installation metadata and an explicit Tier 1/Tier 2 routing contract.

- [x] **Step 1: Add a failing catalog assertion for Serena 1.7.0 and its healthcheck.**
- [x] **Step 2: Run `python3 -m unittest tests.test_tool_catalog -v` and confirm the new assertion fails before implementation.**
- [x] **Step 3: Add the Serena healthcheck metadata and tighten the routing text without changing Graphify's role.**
- [x] **Step 4: Re-run `python3 -m unittest tests.test_tool_catalog -v` and confirm it passes.**

### Task 2: Machine-local Serena installation and client registration

**Files:**
- Modify locally: the Codex MCP configuration under the active Codex home.
- Modify locally: the Claude MCP configuration under the active user profile.
- Remove locally: only the stale `trace-mcp` registration.

**Interfaces:**
- Consumes: `serena-agent==1.7.0` from the catalog and the installed `serena` executable.
- Produces: stdio MCP registrations that start Serena from the client's current project.

- [x] **Step 1: Install the selected catalog entry with `python3 scripts/tool_catalog.py --catalog config/tools.json install --tool serena --upgrade`.**
- [x] **Step 2: Verify `serena --version` and inspect `serena start-mcp-server --help` before writing client arguments.**
- [x] **Step 3: Back up each client configuration and add a minimal Serena stdio entry using the verified CLI.**
- [x] **Step 4: Remove only the stale `trace-mcp` entry and validate the resulting JSON/TOML syntax.**

### Task 3: Index and end-to-end verification

**Files:**
- Generate locally: Serena state outside tracked repository content where supported.
- Verify: repository status and validation output.

**Interfaces:**
- Consumes: installed Serena CLI and current repository root.
- Produces: a working code index and evidence that portable tracked files remain clean of runtime state.

- [x] **Step 1: Inspect `serena project index --help` and run the narrowest supported index command for this repository.**
- [x] **Step 2: Run Serena's health/version checks and confirm both client entries point to the installed executable.**
- [x] **Step 3: Run `make validate-quick`.**
- [x] **Step 4: Review `git diff --check`, `git status --short`, and the scoped diff for runtime-boundary drift.**
