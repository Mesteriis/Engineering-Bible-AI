# Testing And Context Author Skills

Reviewed on 2026-10-03. The catalog adds three complete original leaves while
keeping Bible's routing and owner policy separate. The catalog now contains
30 author skills from eight sources; default owner groups require 20. Installing
a skill does not prove the host exposes it or that a model follows its routing.

| Original | Reviewed revision | License | Selection and purpose |
| --- | --- | --- | --- |
| [Trail of Bits property-based-testing](https://github.com/trailofbits/skills/tree/82fe8226252622fa807643bdca1710901198553a/plugins/property-based-testing) | `82fe8226252622fa807643bdca1710901198553a` | CC-BY-SA-4.0 | Required by the `core` owner group; use for real invariants, roundtrips, oracles and shrunk counterexamples |
| [Matt Pocock handoff](https://github.com/mattpocock/skills/blob/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/productivity/handoff/SKILL.md) | `d81f3a183412e71a5b1e84ca21bc1a35eea03a60` | MIT | Opt-in `context-continuation` group; explicit invocation for a fresh-agent handoff |
| [Context Engineering context-compression](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/58b55a8921758d13453b440704fb1b5b208c0b0e/skills/context-compression) | `58b55a8921758d13453b440704fb1b5b208c0b0e` | MIT | Opt-in `context-continuation` group; structured compression for long tasks |

`handoff` already exists in the previously reviewed Pocock revision. Its addition
does not upgrade any of the other eight Pocock leaves. The two new sources use
independent author leaves; no sibling skill is required by these three originals.
Other Context Engineering skills are related guidance for different tasks, not
mandatory imports for this leaf.

## Installation And Updates

Default installation requires property-based-testing with the existing core
authors. It makes that skill available for selection; it does not load its
instructions for every request or require property tests for trivial changes.
Continuation authors are absent from default requirements and global profiles.
Select them only for a long task, a compression design task, or an explicit
handoff:

```bash
be skills plan --group context-continuation
be skills ensure --group context-continuation
be skills route explicit-session-handoff
be skills route long-task-continuation
```

Use `be skills check` to discover author changes. Review new content, license,
runtime behavior and dependencies before changing a catalog pin, then apply
`be skills update`. Author content, tree digests, licensing and rollback state
remain separate from owner rules. Native providers retain their own ownership.

## Property-Based Testing Audit

The nine-file leaf has five task-specific references, original metadata and an
SVG attribution asset. All entry-point reference links resolve inside the leaf.
The source import is restricted to `plugins/property-based-testing/skills` and
the reviewed root license. Plugin configuration, commands, eval harnesses and
their intentionally broken fixtures are outside that scope.

The README describes plugin-root evaluation commands; those commands are not
available from this skill-only installation. No author helper, hook, package
manager or live model evaluation runs during import.

Use the project's existing PBT library. A new Hypothesis, fast-check, proptest
or other library is a dependency decision for the target project, with the
specific useful property, compatibility and existing authorization checked
first. Installing this instruction package does not authorize an unrelated
dependency addition or production refactor. The original asks for a separate
dependency decision and for the author to choose any production refactor;
respect existing user authorization instead of asking the same question again.

Assert the strongest useful property supported by the code. Tautologies,
vacuous assumptions and tests that repeat implementation logic do not establish
quality. No suitable invariant is a valid result; example tests can be the
better fit. Confirm current library compatibility before recommending one of
the author's language defaults.

The original frontmatter has `effort: low`. Hosts may interpret that metadata
differently; it is not permission for Bible to change a parent or external
reviewer's model or reasoning settings. License attribution and the original
CC-BY-SA terms remain attached to the unchanged author tree.

## Continuation Audit

`handoff` preserves both `disable-model-invocation: true` and original host
metadata `allow_implicit_invocation: false`. Bible records `user_invoked: true`.
An intent lookup identifies a route and does not authorize an implicit handoff.
The original saves a redacted document to the OS temporary directory, refers
to existing specs/plans/diffs instead of copying them, and names suggested
skills for the next agent. Temporary-file storage is not durable memory or
permission to send the document to another provider.

The four-file context-compression leaf preserves its reference, Python helper
and helper tests. Its Markdown reference resolves locally. The reviewed helper
imports only Python standard-library modules, and contains no actual network,
credential-loading or subprocess call. Importing the skill does not execute it.
Calling the helper's pipeline with a model callback can invoke whatever code
that caller supplies; a real judge integration needs its own bounded export,
provider, cost and authorization review.

The helper explicitly uses demonstration heuristics and a stub judge. Its
`gpt-5.2` default is a label without a real provider request or verified model
identity. Its unit tests exercise two heuristic scores. They do not establish
the quality of compression or a live model quorum. Likewise, source benchmark
ratios and score tables are not measured savings for this installation.

For real long tasks, preserve user constraints, decisions, exact paths and
identifiers, observed check outcomes, artifact links, remaining risks and the
next action. Validate a summary against current source material; do not let
compression discard tool schemas, erase a failure or invent a passing check.
Measure total tokens per completed task, repeated reads and continuity before
claiming improvement. The packaged demonstration summarizer is not installed
as an automatic compaction or memory engine.

## Reviewed Integrity

The project fingerprint includes every relative file path, Git executable mode
and file SHA-256. The catalog records the following exact complete-tree values:

| Original leaf | Files | Tree SHA-256 |
| --- | --- | --- |
| property-based-testing | 9 | `93aba13ae9fc6a49a912d97860a786fe3b6716b79a8c666edb5a3a721d787152` |
| handoff | 2 | `54899340fc95ea8e35fab661ef722b1f09cfb6a7cc45627417d8e9a1122cfb28` |
| context-compression | 4 | `e224beba84f9cbaa86be0bd273d4dbe20f82e3e3242124c5cbb475ea10c2370f` |

Original licenses are hash-checked before activation and retained in the
dependency store. Research copies and machine-specific evidence stay untracked.
No source-pin change, hook activation, author-helper execution or main-home
installation is implied by this audit.
