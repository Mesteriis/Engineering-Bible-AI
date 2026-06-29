## Summary

-

## Validation

- [ ] `bash scripts/validate-repo-tree.sh .`
- [ ] `python3 scripts/registry.py --root . validate`
- [ ] `python3 scripts/validate-router-cases.py --static`
- [ ] `python3 scripts/validate-skill-frontmatter.py skills`
- [ ] `python3 scripts/check-file-size.py . --hard 10000`
- [ ] `bash scripts/secret-sanity.sh .`

## Runtime Boundary

- [ ] No `config.toml`, auth files, `.env`, credentials, session/cache/worktree
      state, or private infrastructure details were added.
