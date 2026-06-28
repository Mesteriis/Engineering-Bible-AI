---
name: subagent-result-merge
description: "Merge outputs from multiple subagents or independent review passes into one actionable report. Use after multi-agent PR review, parallel exploration, security phases, or split architecture/migration investigations."
---

# Subagent Result Merge

Normalize parallel findings into one decision-ready report.

## Workflow

1. Group findings by severity and affected behavior.
2. Deduplicate overlapping findings.
3. Preserve the strongest evidence and confidence level.
4. Separate confirmed issues from plausible/unverified risks.
5. Convert repeated themes into concrete follow-up actions.

## Output

- findings ordered by severity
- duplicates collapsed with source reviewers noted
- open questions
- recommended minimal fixes
- validation gaps
- next skill to use, if any

## Rule

Do not average confidence across reviewers. Prefer the most concrete evidence
and mark disagreement explicitly.
