# Debugging Philosophy

Debugging is hypothesis-driven investigation, not random patching.

## Protocol

1. Reproduce or identify the failure.
2. Capture the exact error, input, state, or scenario.
3. Find the smallest relevant code path.
4. Form hypotheses.
5. Verify each hypothesis against code, logs, tests, runtime output, or documentation.
6. Fix the root cause.
7. Add validation that would fail without the fix.
8. Report evidence and remaining uncertainty.

## Rules

- Do not patch multiple unrelated things at once.
- Do not silence the error without understanding it.
- Do not convert a crash into silent wrong behavior.
- Do not remove validation because it is inconvenient.
- Do not rely on “works on my machine” without command output.

## Good debugging output

A good report includes:

- observed failure;
- root cause;
- fix;
- validation;
- residual risks.
