# Steady-State Routing Design

## Goal

Reduce repeated per-turn instruction and skill-loading work in Codex while preserving the complete Engineering Bible skill catalog, strict workflows, validation guarantees, and explicit access to every specialist workflow.

## User Priority

Cold-start latency is acceptable. The optimization target is subsequent work in an already-open Codex thread, especially follow-up prompts in the same task.

## Current Problem

The default global prompt requires `workflow-router` for every non-trivial request, then requires every selected downstream `SKILL.md` to be read before substantive work. The runtime capability section similarly encourages discovery for every non-trivial task. Broad overlapping skill descriptions make ordinary coding prompts eligible for several generic skills. Together these rules repeatedly load routing and policy text even when the task and active domain have not changed.

The current skill frontmatter also uses names such as `[be] workflow-router`, which do not conform to the Agent Skills name contract and are accepted only because the repository validator strips the prefix.

## Design

### Profiles

Add a `steady` global prompt profile and make it the default for new installs. It installs the same default skill groups as the existing `full` profile.

- `steady`: optimized for ongoing work, direct leaf-skill selection, continuation reuse, lazy runtime discovery.
- `full`: retain exhaustive routing on the first task turn, then reuse the
  established route and capability metadata on same-task follow-ups.
- `minimal`: compact profile, updated to use the same steady-state routing semantics.
- `fast`: unchanged opt-in limited mode that installs only the `fast` skill.

Existing installation manifests keep their recorded profile during `be update`
and `be install`; no silent migration from `full` to `steady` occurs.

### Continuation Fast Path

When a user continues the same task in the same thread and the domain, risk, and tool requirements have not changed:

1. Reuse the current primary skill and any already-loaded supporting skill.
2. Do not invoke a router again.
3. Do not reread an unchanged `SKILL.md` already present in the conversation.
4. Do not refresh runtime capability metadata or generated catalogs.
5. Continue directly with inspection, implementation, or validation.

Reroute only when the request changes domain, changes mutation/risk class, introduces a new external system, explicitly names another skill, or the existing route cannot satisfy the request.

### Skill Selection

For a clear task, select the narrowest leaf skill directly. Use one primary skill and at most one supporting skill by default. Additional skills are allowed only when their procedures produce distinct required work.

`workflow-router` remains available and retains full routing coverage, but it is used only for ambiguous or genuinely mixed-domain requests. Its detailed route table moves into a reference file so the common router path remains small.

### Runtime Capability Discovery

Runtime discovery becomes demand-driven. Local repository work uses native repository tools without catalog refresh. `mcp-tool-router` is selected only when the user asks to inspect/select runtime capabilities or an external capability is materially required. Current-session metadata may be reused until there is evidence that it changed.

### Skill Metadata

All `SKILL.md` names must exactly match their parent directory and satisfy the Agent Skills lowercase-hyphen format. Descriptions remain trigger-capable but become concise and boundary-aware to reduce overlap and repeated prompt payload.

The validator must reject branded or malformed names rather than canonicalizing them. Branding belongs in optional `agents/openai.yaml` display metadata, not in `name`.

### Compatibility

- No skill directory is removed.
- No specialist workflow body is removed solely for performance.
- All existing explicit `$skill-name` invocations continue to work.
- The strict `full` profile remains available.
- Strict `full` routing still runs when a task begins or materially changes;
  only redundant same-task rerouting is removed.
- `be update`, `be install`, and direct local reinstall preserve the installed
  profile unless the user passes `--prompt-profile`.
- `fast` behavior remains unchanged.

## Validation

Automated coverage must prove:

- every repository skill name is valid and matches its directory;
- malformed `[be]` names are rejected;
- new installs default to `steady` and install the full default catalog;
- explicit `full`, `minimal`, and `fast` profiles remain accepted;
- updates preserve an existing profile;
- `steady` contains continuation reuse and lazy routing rules;
- description/catalog budgets do not regress without an explicit test update;
- repository, installer, CLI, and release checks pass.
