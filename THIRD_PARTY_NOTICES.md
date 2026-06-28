# Third Party Notices

This repository does not vendor third-party runtime packages.

## GitHub Actions

The validation workflow uses public GitHub Actions:

- `actions/checkout`
- `actions/setup-python`

Those actions are used at CI runtime and are not vendored into this repository.

## Skill Format

Skills use the Codex-compatible `SKILL.md` file convention and optional
`agents/openai.yaml` metadata files. The files in this repository are packaged
as portable project content unless a future notice states otherwise.

## Future Additions

If third-party templates, skills, scripts, or generated assets are added later,
record their source, license, and local modifications in this file before
publishing the change.
