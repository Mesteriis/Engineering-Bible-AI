# Shared Style Contract

## Purpose

Keep the same engineering style across languages and ecosystems.

The user prefers one consistent mental model even when switching between backend code, frontend code, firmware, automations, and tiny TODO apps.

## Style Invariants

Always prefer:

- explicit behavior;
- small cohesive units;
- strong boundaries;
- boring names;
- domain vocabulary;
- predictable errors;
- validation;
- tests for meaningful behavior;
- simple abstractions proportional to the problem.

Always avoid:

- god files;
- god classes/components;
- vague managers/helpers/utils;
- hidden mutable global state;
- implicit side effects;
- fake TODO implementations;
- broad catch-and-ignore error handling;
- unvalidated external input;
- leaking internal details through public boundaries;
- adding dependencies for trivial code.

## Small Projects Still Count

A small TODO app does not need full DDD, CQRS, adapters, repositories, and twelve folders named after conference talks.

It still needs:

- clear state;
- clear functions;
- readable names;
- small files;
- explicit validation;
- no hidden magic;
- simple tests if behavior matters.

## Same Style Across Languages

Different ecosystems have different idioms, but the design taste should remain stable:

- one responsibility per unit;
- boundaries before cleverness;
- tests before confidence;
- explicit errors before silent failure;
- stable public contracts;
- no uncontrolled growth.
