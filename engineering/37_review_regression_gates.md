# Review And Regression Gates

Review is a correctness tool. It is not a decorative approval ritual.

## Diff-Risk Review

For meaningful changes, review the diff for:

- public behavior changes;
- changed command or API contracts;
- persistence, config, installer, or runtime effects;
- security and secret handling;
- error handling and failure modes;
- compatibility with existing users;
- documentation impact.

## Regression Coverage

When fixing a defect, add coverage for the defect class when practical.

Good regression tests:

- fail before the fix;
- pass after the fix;
- verify behavior instead of implementation trivia;
- include the risky boundary where the defect happened.

## Review Output

A useful review says:

- what was checked;
- what evidence was used;
- whether there are Critical, Important, Minor, or Suggestion findings;
- what remains risky.

## Completion Gate

Before finishing, confirm:

- relevant tests passed;
- changed commands or docs were exercised;
- installer or runtime boundary changes were checked;
- no known blocking review findings remain;
- residual risks are reported.
