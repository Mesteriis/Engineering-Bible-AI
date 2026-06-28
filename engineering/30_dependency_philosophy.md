# Dependency Philosophy

A dependency is code you did not write but still get to debug at 03:00. Add one only when it pays rent.

## Admission rule

A new dependency must justify:

- the problem it solves;
- why local code is worse;
- maintenance status;
- security posture;
- license compatibility;
- transitive dependency cost;
- runtime footprint;
- API stability;
- operational behavior;
- replacement or removal path.

The smaller the problem, the more skeptical the admission review.

## Dependency categories

| Category | Default stance | Notes |
|---|---|---|
| Standard library | Prefer when sufficient | Still verify correctness and ergonomics |
| Small utility library | Skeptical | Avoid for trivial helpers |
| Framework | High scrutiny | Owns architecture gravity |
| SDK/client | Accept when external API is complex | Wrap volatile surfaces |
| Code generator | High scrutiny | Generated output must be reviewable or contained |
| Build/dev tool | Accept when it improves validation | Pin versions where practical |
| Runtime service | Very high scrutiny | Adds operational dependency |
| Vendored code | Avoid unless necessary | Requires update and security story |

## Wrapping

Wrap a dependency when:

- it talks to external infrastructure;
- its API is unstable or noisy;
- it leaks provider-specific types into domain code;
- it is hard to fake in tests;
- switching providers is plausible;
- error mapping matters.

Do not wrap every dependency mechanically. A pointless wrapper is just a dependency wearing a fake mustache.

## Framework boundaries

Frameworks should own edges, not business rules.

Keep domain and application policy independent from:

- HTTP request objects;
- ORM session objects;
- UI framework state;
- cloud provider SDK models;
- CLI parser internals;
- dependency injection container mechanics.

When a framework is intentionally the architecture, document that choice and keep the coupling consistent rather than pretending purity exists.

## Versioning and pinning

Dependency version policy should define:

- direct dependency versions;
- lockfile ownership;
- update cadence;
- vulnerability response;
- compatibility testing;
- rollback behavior.

Libraries used in production should not float casually unless the ecosystem explicitly expects that and validation catches regressions.

## Transitive dependencies

Before adding a dependency, inspect what it brings with it.

Risk signs:

- many transitive packages for a small feature;
- abandoned packages;
- native extensions without build support;
- broad permissions;
- post-install scripts;
- runtime network access;
- unclear license chain.

## Removal path

A dependency needs a removal story when:

- it is experimental;
- it is used for migration;
- it replaces local code temporarily;
- it is a provider SDK;
- it is a framework-level choice under evaluation.

At minimum, isolate usage behind a small surface.

## Do not add dependencies for

- one-line helpers;
- trivial formatting;
- avoidable abstractions;
- novelty;
- style preferences;
- hiding a design problem;
- copying a tutorial stack without repository evidence.

## Review checklist

Before merging a dependency change, verify:

- the problem is real;
- dependency choice is justified;
- license is acceptable;
- security risk is checked;
- transitive footprint is understood;
- usage is contained to the right layer;
- version policy is clear;
- tests or build validation cover the integration;
- removal path exists when risk is non-trivial.
