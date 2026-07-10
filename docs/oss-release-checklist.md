# OSS Release Checklist

Use this checklist before publishing a release or accepting a major packaging
change.

## Required Checks

- `LICENSE` is present and accurate.
- `CHANGELOG.md` includes the user-visible change.
- `SECURITY.md` still describes the supported branch and reporting path.
- `THIRD_PARTY_NOTICES.md` lists any newly added third-party material.
- `README.md` and `README.ru.md` describe current install and validation steps.
- GitHub issue and pull request templates still match the repository workflow.

## Runtime Boundary

Confirm the repository does not include:

- `~/.codex/config.toml`;
- auth files;
- `.env` files;
- provider or gateway credentials;
- MCP server secrets;
- Codex session, cache, rollout, or worktree state;
- private SSH material.

## Validation

```bash
make validate-release
```

The release profile includes dependency-light bootstrap checks, the complete
discovered unit-test suite, linters, type checks, temporary installation, and
the `git ls-files` snapshot gate. It fails when any check is skipped.

Useful focused commands while resolving a failure:

```bash
python3.11 scripts/validate.py --profile quick
python3.11 scripts/validate.py --profile bootstrap
python3.11 scripts/validate-router-cases.py --fixtures
python3.11 scripts/registry.py --root . validate
python3.11 -m unittest discover -s tests -p 'test_*.py' -v
```
