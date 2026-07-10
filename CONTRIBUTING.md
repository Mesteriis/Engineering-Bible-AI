# Contributing

## Scope

This repository packages portable engineering instructions and Codex-compatible
skills. Contributions should improve reusable standards, routing behavior,
validation, documentation, or installation safety.

Do not add machine-local runtime state, credentials, generated agent sessions,
or private infrastructure details.

## Development Workflow

1. Create a focused branch.
2. Keep changes scoped to one concern.
3. Update documentation when commands, behavior, installation, or validation
   changes.
4. Run the validation commands below before opening a pull request.

## Validation

```bash
make validate-quick
```

Before release-sensitive or installer changes, also run:

```bash
make validate
make validate-release
```

Use `make registry-docs` after changing `skills/registry.yml`. The generated
blocks in both READMEs and `MANIFEST.md` are checked byte-for-byte. The full
test suite uses `python3 -m unittest discover -s tests -p 'test_*.py' -v`.

## Pull Requests

Pull requests should include:

- the reason for the change;
- affected files or skill groups;
- exact validation commands and results;
- any compatibility risk for existing Codex workers;
- confirmation that no secrets or runtime config were added.

## Secret Handling

Never commit:

- `.env` files;
- auth files;
- private keys or certificates;
- local Codex `config.toml`;
- model provider credentials;
- MCP server credentials;
- session, cache, rollout, or worktree state.

If a contribution accidentally includes sensitive material, stop and rotate the
affected credential before continuing.
