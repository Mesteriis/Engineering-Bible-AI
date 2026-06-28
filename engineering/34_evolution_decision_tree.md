# Evolution Decision Tree

Use this document when adding structure. It turns "maybe we need a new thing" into a sequence of checks, because apparently civilization requires flowcharts to avoid another `utils2_final_final.py`.

## Add a new file?

Ask in order:

1. Does the new code have a different responsibility from the current file?
   - No: keep it in the current file.
   - Yes: continue.
2. Does the current file exceed or approach the complexity budget?
   - Yes: split by responsibility.
   - No: continue.
3. Will the new code change for a different reason than the existing code?
   - Yes: create a new file.
   - No: keep together.
4. Does the split create a clearer public surface?
   - Yes: create a new file.
   - No: avoid fragmentation.
5. Can the new file be named by domain responsibility?
   - Yes: create it.
   - No: rethink the boundary.

Do not create files named `helpers`, `misc`, `common`, or `stuff` unless the repository already has that convention and the alternative would be worse.

## Add a new module/package?

Ask in order:

1. Is there a cohesive responsibility larger than one file?
   - No: do not create a module.
   - Yes: continue.
2. Does the responsibility have a stable public API?
   - No: keep internal structure simple.
   - Yes: continue.
3. Does it protect a dependency, domain, lifecycle, or side-effect boundary?
   - Yes: create the module.
   - No: continue.
4. Will multiple callers use it through the same concepts?
   - Yes: create the module.
   - No: avoid speculative modularity.
5. Can ownership be described in one sentence?
   - Yes: create the module.
   - No: boundary is not ready.

## Add a new abstraction?

Ask in order:

1. Is there real variation today?
   - No: do not abstract.
   - Yes: continue.
2. Does the abstraction hide volatile details or protect stable policy?
   - No: keep concrete code.
   - Yes: continue.
3. Will callers become simpler?
   - No: do not abstract.
   - Yes: continue.
4. Can the abstraction be named by behavior rather than technology?
   - No: redesign.
   - Yes: continue.
5. Is the test surface clearer after abstraction?
   - Yes: introduce it.
   - No: reconsider.

An abstraction that does not remove more complexity than it adds is not design. It is paperwork with methods.

## Add a new dependency?

Ask in order:

1. Is the problem real and current?
   - No: do not add.
   - Yes: continue.
2. Is local implementation riskier or more expensive?
   - No: write local code.
   - Yes: continue.
3. Is the dependency maintained and compatible with the project license and runtime?
   - No: reject.
   - Yes: continue.
4. Is the transitive footprint acceptable?
   - No: reject or isolate.
   - Yes: continue.
5. Does usage stay behind the right boundary?
   - Yes: add with validation.
   - No: wrap or redesign.

## Add configuration?

Ask in order:

1. Does behavior need to vary across environments, deploys, tenants, or rollouts?
   - No: do not add configuration.
   - Yes: continue.
2. Is the variation safe to expose as configuration?
   - No: keep it in code or product data.
   - Yes: continue.
3. Can the option be named clearly with type and units?
   - No: redesign.
   - Yes: continue.
4. Can it be validated at startup or update time?
   - No: avoid or constrain it.
   - Yes: continue.
5. Does it need documentation, observability, or lifecycle tracking?
   - Yes: add those with the config.
   - No: add minimal validated config.

## Add a feature flag?

Ask in order:

1. Is gradual rollout, experiment, or kill switch needed?
   - No: do not add a flag.
   - Yes: continue.
2. Is there an owner?
   - No: do not add.
   - Yes: continue.
3. Is the default safe?
   - No: redesign.
   - Yes: continue.
4. Is behavior observable by flag state?
   - No: add observability or avoid flag.
   - Yes: continue.
5. Is there a removal condition?
   - No: do not add yet.
   - Yes: add flag.

## Add a standard document?

Ask in order:

1. Does the rule apply across languages or projects?
   - No: put it in a specific skill or repo doc.
   - Yes: continue.
2. Does it resolve recurring ambiguity?
   - No: do not document yet.
   - Yes: continue.
3. Can it produce concrete decisions, checks, or thresholds?
   - No: rewrite until it can.
   - Yes: continue.
4. Does it overlap an existing standard?
   - Yes: extend the existing document.
   - No: continue.
5. Can the document be read independently?
   - Yes: add it.
   - No: redesign structure.

## Remove instead?

Before adding anything, ask:

- Can dead code be removed?
- Can duplicate logic be consolidated?
- Can a flag be retired?
- Can a dependency be removed?
- Can a workaround be deleted?
- Can documentation be corrected instead of expanding code?
- Can a smaller patch solve the actual problem?

Prefer deletion when it preserves behavior and reduces future cost. Deleting code is the closest software gets to cleaning its room.
