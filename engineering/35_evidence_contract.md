# Evidence Contract

Engineering claims must be traceable to evidence.

## What Counts As Evidence

Use the strongest available evidence:

- repository files with paths;
- command output from the current environment;
- test, lint, type-check, build, or audit results;
- official documentation when external behavior matters;
- direct user-provided context;
- explicitly stated uncertainty when evidence is unavailable.

## Claims That Need Evidence

Evidence is required for claims about:

- files, symbols, APIs, imports, and schemas;
- framework or dependency behavior;
- test status, build status, lint status, or CI status;
- git state, branches, commits, and diffs;
- runtime configuration and environment behavior;
- security posture, secrets, auth, permissions, and network exposure;
- installer, CLI, worker, or automation behavior.

## Reporting Uncertainty

If a fact cannot be confirmed from available context, say:

```text
I cannot confirm this from the available context.
```

Do not replace missing evidence with confidence.

## Validation Claims

Never say validation passed unless the command was actually run.

Report validation as:

```markdown
Validation:
- Ran: <exact command>
- Result: <passed, failed, or not run with reason>
```

## External Information

If a claim may have changed recently, verify it from a current source before
using it as a basis for engineering work.

## Evidence Review Checklist

Before finalizing meaningful work, check:

- Are important claims backed by file paths, command output, or test results?
- Are assumptions labeled?
- Are unverified facts explicitly marked?
- Are validation commands exact?
- Are limitations and residual risks visible?
