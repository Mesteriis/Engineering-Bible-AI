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
- Moon Bridge or DeepSeek credentials;
- MCP server secrets;
- Codex session, cache, rollout, or worktree state;
- private SSH material.

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
bash -n scripts/install.sh scripts/install-codex.sh scripts/secret-sanity.sh scripts/validate-installed-tree.sh scripts/validate-repo-tree.sh scripts/validate-skill-tree.sh skills/workflow-router/scripts/validate-routing.sh
find scripts skills -name '*.py' -print0 | xargs -0 python3 -m py_compile
python3 -m unittest tests/test_be_cli.py -v
make audit
make quality-audit-tests
make validate-install
```
