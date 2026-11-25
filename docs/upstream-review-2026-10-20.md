# Author Skill Review — 2026-10-20

Scope: all 30 catalogued originals across eight public sources. Tracking checks
found six changed source commits. Comparing the selected skill directories
found nine changed payloads; the other 21 trees are unchanged. Tracking and
payload equality are separate facts. The catalog pins immutable commits and
uses canonical file modes and SHA-256 tree digests.

## Reviewed Candidates

| Source | Reviewed commit | Selected payload change |
| --- | --- | --- |
| Matt Pocock | `5beb35b040e3de97e54fa9e386d7e42d15c295c2` | `grilling`: yes accepts the recommendation; `handoff`: explicit OS temporary directory fallback. Seven other trees unchanged. |
| Superpowers 7.0.0 | `bb92a77741419a4ab5f06e711a283343f1ada0c3` | Five trees changed: brainstorming, executing-plans, requesting-code-review, subagent-driven-development and systematic-debugging. |
| UI UX Pro Max | `56ea9cf174ed86786187daa9de0e6247cb0747e4` | One test-fixture runtime fingerprint changed; helper and instruction behavior unchanged. |
| Impeccable 4.7.0 | `dad8dbb3aac21ad1fa236c110315ef4abece23e8` | Instructions, references, launchers and browser helpers changed; requested engine advances from 0.1.11 to 0.1.16. |
| Trail of Bits | `5c99c03fb8a9ea568432ecbcba5d86e9f4ac2bf0` | Selected property-based-testing tree unchanged. |
| Context Engineering | `9ff0c99108b36d3b886defd825d8ac1f47dba374` | Selected context-compression tree unchanged. |

Karpathy Guidelines and Interface Design retain their existing commits and trees.
All reviewed license and NOTICE bytes are unchanged. Membership, dependency
edges, user-invocation flags and tool selections are unchanged.

## Compatibility And Execution Boundary

Superpowers brainstorming now handles clear requests immediately, permits an
explicit opt-out from questioning, and uses a builder check for written designs.
Small changes can proceed from an approved in-chat description. Large software
projects retain the design-to-plan handoff. Existing user authorization and
Bible owner policy retain precedence; importing a new version does not authorize
new delegation, data export or helpers. The other changes fix secret-printing
examples, empty test output, path normalization and preservation of existing
workspace ignore files. The visual server fixes replacement-string expansion.

Impeccable adds native and desktop review distinctions, clearer waiting for
answers, seed references instead of raw seed keys, and browser fixes for plain
HTTP, modal dialogs, IME and touch focus. Its shell launcher adds interrupted
download cleanup; Windows staging isolates concurrent downloads. The imported
leaf excludes repository setup and adjacent host hook configuration.

Engine 0.1.16 is a separate executable dependency: launcher syntax and imported
source checks do not verify its binary or runtime behavior. Keep
`IMPECCABLE_NO_UPDATE_CHECK=1` for Bible-managed invocations. Establish the actual
engine and perform a bounded task-specific check before using new engine
features. Hooks, live mode, CDP attachment and image-provider calls remain
separate runtime actions; skill installation enables none of them.

## Validation Scope

Public archives were staged through `scripts/upstream_sources.py`; archive path,
file-type, size, license and notice checks passed before activation. Candidate
tree digests were calculated with the installer's fingerprint function.
Repository and installed-tree checks establish file integrity and lifecycle
compatibility. They do not prove agent compliance, host exposure, design quality
or upstream engine behavior. Historical adoption reports retain their original
pins; this review and `config/upstream-skills.json` describe the new selection.
