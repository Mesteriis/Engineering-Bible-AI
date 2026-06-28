---
name: security-diff-review
description: "Review a PR, commit, branch diff, or local patch for security regressions in authorized code. Use for auth, authz, input validation, filesystem, network, secrets, parser, SSRF, path traversal, injection, CI/CD, and supply-chain changes."
---

# Security Diff Review

Run a diff-scoped security review.

## Workflow

1. If `security-diff-scan` from Codex Security is available, read and follow it.
2. Otherwise resolve the exact diff and review changed files plus directly
   supporting code.
3. Build a narrow threat model for touched assets and trust boundaries.
4. Discover plausible findings.
5. Validate each finding with code evidence or mark it unvalidated.
6. Report severity, exploit path, confidence, remediation, and proof gaps.

## Focus

- authentication and authorization
- tenant isolation and ownership checks
- input validation and parsers
- filesystem paths and archive handling
- network calls, SSRF, redirects, webhooks
- secrets, config defaults, logs
- dependency and CI/CD changes

## Rules

- Authorized code only.
- Review-only by default; do not edit files.
- Do not claim exploitability without evidence.
- Route concrete fixes to `fix-security-finding`.
