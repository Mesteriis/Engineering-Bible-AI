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

## Reviewed Upstream Skill Catalog

`config/upstream-skills.json` references selected skills from
[Matt Pocock's skills repository](https://github.com/mattpocock/skills), licensed
under MIT. The catalog records the reviewed commit, individual tree digests and
the upstream license digest. It does not vendor author skill files into this
repository. `be skills ensure` downloads complete selected trees and their
transitive dependencies into a local installation, preserving author content
and keeping the license and provenance in the separate dependency store.

Bible's policy and routing instructions are maintained independently. There are
no local changes to the author trees. Future source-pin changes must recheck the
license and required notices before release; native plugin providers retain
their original ownership and attribution.

The catalog also references all 15 original skills from
[Superpowers](https://github.com/obra/superpowers), maintained by Jesse Vincent
and Prime Radiant under MIT. The reviewed `v6.4.2` commit is
`8ca22dba9a94f28898bbce59f2537ff4d87c747d`; installations preserve complete
skill trees, including author prompts, references and executable helpers, and
store the original license separately. Installing the dependencies does not
execute their helpers, enable session hooks or start the optional visual
companion. Bible compatibility adapters and owner policy are separate from
the unchanged author files.

[Karpathy-inspired guidelines](https://github.com/multica-ai/andrej-karpathy-skills)
are maintained in the canonical Multica repository, formerly
`forrestchang/andrej-karpathy-skills`, and derive from Andrej Karpathy's public
observations. The reviewed commit is
`2c606141936f1eeef17fa3043a72095b4765b9c2`. That source declares MIT in its
README and skill frontmatter but has no standalone LICENSE file; the catalog
pins `README.md` as licensing evidence and the dependency store preserves it.
The original `skills/karpathy-guidelines` replaces the previous local adaptation
without modifying the author's contents. This is not represented as a repository
maintained by Karpathy himself.

See [the complete migration audit](docs/absorbed-skills-migration.md) for source
confidence, compatibility names, native provider boundaries and retained owner
rules. Generic engineering-policy similarity is not evidence of third-party
derivation; unknown origins are not assigned speculative attribution.

## Business UI Author Dependencies

The catalog references the complete original skill from
[Interface Design](https://github.com/Dammyjay93/interface-design), reviewed at
`2f9be3206855bcb2d1d0af262c8bae25cba6658d`, under MIT, and
[UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), reviewed at
`09170eec67eefd46a7ae85de61b40c194020f997`, under MIT. Their original licenses
are retained separately from the unchanged author leaves.

[Impeccable](https://github.com/pbakaus/impeccable), reviewed at release
`skill-v4.5.0` / `508d7e8955de3b3caf2d8676e85206723d41a887`, uses Apache-2.0.
Both original `LICENSE` and `NOTICE.md` are hash-checked and retained. The notice
attributes derived native-platform references to ehmo's MIT-licensed
`platform-design-skills`. No author files are vendored or rewritten here;
imports do not activate their engine, live helper, hooks or optional commands.

## Testing And Context Author Dependencies

[Trail of Bits property-based-testing](https://github.com/trailofbits/skills/tree/82fe8226252622fa807643bdca1710901198553a/plugins/property-based-testing)
is reviewed at `82fe8226252622fa807643bdca1710901198553a`, under CC-BY-SA-4.0.
The complete original skill leaf, including its README, references and attribution
asset, is retained unchanged. Its original license and exact source provenance
remain in the dependency store; the CC-BY-SA terms remain attached to that author
content. Bible's separate routing instructions do not replace or rewrite it.
Plugin-level evaluation harnesses and installation commands are outside the
reviewed skill root and are not imported or executed.

[Matt Pocock's handoff](https://github.com/mattpocock/skills/blob/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/productivity/handoff/SKILL.md)
uses the existing reviewed MIT source at
`d81f3a183412e71a5b1e84ca21bc1a35eea03a60`. Adding the original leaf does not
upgrade the other reviewed Pocock skills. Its explicit invocation metadata and
OS temporary-directory output remain unchanged.

[Context Engineering context-compression](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/58b55a8921758d13453b440704fb1b5b208c0b0e/skills/context-compression)
is reviewed at `58b55a8921758d13453b440704fb1b5b208c0b0e`, under MIT. The original
four-file leaf includes its evaluation reference, demonstration helper and tests;
the original license is retained separately. Importing it does not run the helper,
configure a judge model, export context or install a second memory system.

See [the audit and runtime boundaries](docs/quality-context-authors.md) for opt-in
continuation, dependency decisions and the demonstration evaluator's limits.
