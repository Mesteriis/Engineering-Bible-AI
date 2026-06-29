# Task Lifecycle Gates

Non-trivial engineering work must move through explicit gates. The amount of
ceremony scales with risk.

## Gate 1: Scope

Before acting, identify:

- requested outcome;
- affected behavior;
- constraints;
- unclear assumptions;
- expected artifact.

Ask only when ambiguity blocks correct work.

## Gate 2: Inspection

Before editing, inspect relevant files:

- project layout;
- dependency and validation files;
- existing implementation patterns;
- tests near the change;
- docs or installer behavior when public commands change.

Do not infer project shape when files can be read.

## Gate 3: Plan

For small changes, use a short inline plan.

For multi-step work, write or follow a task plan with:

- target files;
- behavior changes;
- validation;
- risks;
- commit slices.

## Gate 4: Implementation

Implement the smallest correct change.

Rules:
Rules:

- preserve existing boundaries;
- avoid unrelated refactors;
- avoid hidden side effects;
- do not add dependencies without a reason;
- do not use task notes as fake implementation.

## Gate 5: Validation

Run the best available validation:

- focused tests;
- full validation when behavior or shared tooling changes;
- static checks;
- manual verification only when automated checks are unavailable.

Report exact commands.

## Gate 6: Review And Risk

Before completion, identify:

- changed behavior;
- failure modes covered;
- tests added or updated;
- docs updated or not needed;
- remaining risks.

## Proportionality

Small read-only answer:

- evidence check;
- direct answer.

Small code change:

- inspect file;
- edit;
- focused validation;
- concise report.

Multi-file or behavior change:

- plan;
- implementation slices;
- validation;
- review gate;
- risk report.
