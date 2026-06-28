---
name: threat-model
description: "Build a threat model for a repository, service, feature, endpoint, integration, or architecture change. Use for trust boundaries, assets, attackers, entrypoints, auth/authz, data flows, abuse cases, and security review preparation."
---

# Threat Model

Create a concise, evidence-based threat model.

## Workflow

1. Read the relevant repo instructions and architecture files.
2. Identify assets, actors, trust boundaries, entrypoints, data stores, and
   external integrations.
3. Map likely attacker-controlled inputs and privileged operations.
4. List abuse cases and required controls.
5. Recommend follow-up review skills.

## Output

- assets
- actors and attacker capabilities
- trust boundaries
- data flow and entrypoints
- required controls
- high-risk files or modules
- open questions

## Rule

If the Codex Security `threat-model` plugin skill is available, read it first
and use this skill as a concise local wrapper.
