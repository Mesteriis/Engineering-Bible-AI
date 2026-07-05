---
name: [be] secrets-and-config-review
description: "Ревьюит secrets handling, configuration defaults, environment variables, logs, credentials, token exposure, .env policy, CI secrets и небезопасную локальную или production config."
---

# Secrets And Config Review

Review configuration without exposing secret values.

## Workflow

1. Inspect config keys, file metadata, templates, and redacted examples first.
2. Avoid reading secret values unless the user explicitly scopes break-glass
   handling and it is safe.
3. Check logs, docs, tests, CI, Docker files, and sample env files for leakage.
4. Verify defaults, required variables, permissions, and error behavior.
5. Report risks and minimal mitigations.

## Output

- config surfaces reviewed
- secret exposure risks
- unsafe defaults
- logging/documentation risks
- remediation
- validation gaps

## Rules

- Never print secret values.
- Do not commit or document credentials.
- Prefer key names, metadata, and redacted evidence.
