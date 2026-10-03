# Context Cache And Targeted Mutation Checks

The owner authorized additions 3 and 4 on 2026-10-03: cache repeated context
and check whether existing tests detect selected defects. Preserve original
author workflows, private runtime configuration and unrelated worktree changes.

- [x] Build a bounded stable-context request preparer and provider-usage reader.
  Keep source freshness, authorization scope and requested route in its identity;
  preserve complete author text. A prepared prefix is not a provider cache hit.
- [x] Build an opt-in Python unittest mutation runner for explicit replacements
  in verified source copies. Require a passing baseline, distinguish assertion
  failures from execution errors, and enforce mutation/time/output limits.
- [x] Connect the tools to existing owner policies and public documentation;
  retain Stryker as the separately selected TypeScript project integration.
- [x] Obtain independent review, run focused regression tests and real local
  pilots, then validate portable installation and release snapshot membership.

Two budget implementation agents own disjoint new modules, CLI adapters,
regression tests and their guides. The parent owns integration; an independent
reviewer owns read-only failure-mode review. Neither code-author evidence nor
local API fixtures establish an independent cross-provider quorum.

The scope adds no model launcher, credentials, endpoint, framework dependency,
global hook, production installation or gateway mutation. Live cache support,
token minimums, actual hits and billed savings need a verified private adapter.
The existing gateway's model-substitution blocker remains in force.

Mutation execution is explicitly selected for a small Python pilot. Temporary
copies preserve the parent source, but are not a security sandbox. Test code
executes locally; tools must not inherit the parent's secret-bearing environment.
Raw reports, source snapshots and cache requests stay under ignored
`.engineering-bible/implementation/cache-mutation/`.

## Verification

Independent review found no remaining blocking findings after regression fixes.
The combined cache and mutation suite passed 32 tests. A local cache pilot
preserved all nine original author files and reused the stable prefix for two
different tasks. A mutation pilot passed its 23-test baseline and killed all
three selected worker-control defects through real assertion failures; parent
file bytes and modes stayed unchanged.

`make validate-bootstrap` and `make validate` passed. `make validate-release`
passed on an isolated indexed public candidate, including snapshot installation.
The working checkout still has required new files outside its Git index;
its release membership gate remains `FAIL`. The real index was not modified.
This verification closeout is the only documentation amendment after the
frozen candidate checks. Live provider cache hits and billed savings remain
unverified, and runtime activation remains blocked.
