# Drift Policy

Default source-of-truth order:

- Code is authoritative for factual runtime behavior.
- ADRs are authoritative for accepted architecture intent.
- Existing docs describe intended usage but can be stale.

## Drift Classes

- `code-docs`: stale documentation when docs disagree with verified code.
- `code-adr`: architectural drift when code no longer follows an accepted ADR.
- `docs-adr`: documentation inconsistency when docs disagree with ADR intent.

## Severity

- `critical`: documented behavior can cause data loss, security exposure, unsafe infrastructure action, or broken production operation.
- `major`: documented behavior will mislead implementation, operation, migration, or debugging.
- `minor`: localized inconsistency that does not change operational behavior.
- `suggestion`: improvement that increases clarity without correcting a false statement.

Every drift finding must include source file references and a recommended action.
