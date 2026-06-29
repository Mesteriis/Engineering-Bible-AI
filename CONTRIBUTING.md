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
make validate
```

Equivalent expanded commands:

```bash
bash scripts/validate-repo-tree.sh .
python3 scripts/validate-skill-frontmatter.py skills
python3 scripts/registry.py --root . validate
python3 scripts/validate-router-cases.py --static
python3 scripts/check-file-size.py . --hard 10000
bash scripts/secret-sanity.sh .
bash scripts/validate-markdown-style.py .
bash -n scripts/install.sh scripts/install-codex.sh scripts/secret-sanity.sh scripts/validate-installed-tree.sh scripts/validate-repo-tree.sh scripts/validate-skill-tree.sh skills/workflow-router/scripts/validate-routing.sh scripts/validate-markdown-style.py
make shell-lint
make markdown-lint
find scripts skills -name '*.py' -print0 | xargs -0 python3 -m py_compile
python3 -m unittest tests/test_be_cli.py -v
make audit
make quality-audit-tests
make validate-install
```

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
