# Support

Use GitHub Issues for:

- installation problems;
- validation failures;
- broken skill routing;
- missing documentation;
- safe portability questions.

Before opening an issue, run:

```bash
bash scripts/validate-repo-tree.sh .
python3 scripts/validate-skill-frontmatter.py skills
python3 scripts/registry.py --root . validate
python3 scripts/validate-router-cases.py --static
bash scripts/secret-sanity.sh .
make validate-install
```

Include command output that does not contain secrets.

Do not post credentials, auth files, `.env` values, private infrastructure
details, or local runtime config.
