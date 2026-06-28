---
name: dependency-advisory-audit
description: "Triage dependency CVEs, advisories, vulnerable packages, lockfile changes, or dependency upgrade risk. Use to determine real reachability, affected versions, exploitability in this repo, patch options, and validation commands."
---

# Dependency Advisory Audit

Triage advisories against actual repository usage.

## Workflow

1. Identify package manager and lockfiles.
2. Verify installed/requested versions from files, not memory.
3. Locate actual imports, execution paths, and exposed surfaces.
4. Determine whether the advisory is reachable in this repo.
5. Recommend upgrade, patch, config mitigation, or non-applicability.
6. Define validation commands.

## Output

- package and version evidence
- advisory summary
- reachability analysis
- impact and confidence
- remediation options
- validation plan

## Rules

- Do not invent CVE details.
- Browse or use official/advisory sources when advisory facts are not provided.
- Do not upgrade packages without explicit implementation scope.
