## Summary

-

## Validation

- [ ] `make validate-quick`
- [ ] `make validate`
- [ ] `make validate-release` for release/installer/registry changes
- [ ] Exact focused regression tests are listed in the PR description

## Runtime Boundary

- [ ] No `config.toml`, auth files, `.env`, credentials, session/cache/worktree
      state, or private infrastructure details were added.
