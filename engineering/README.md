# Engineering Standards Index

This directory is the language-neutral engineering standards library.

Use this index to choose the smallest relevant document set instead of loading the entire library by default. The goal is focused judgment, not ritualistic context hoarding.

## Core sequence

- `00_manifesto.md` - stable engineering intent.
- `01_constitution.md` - non-negotiable engineering law.
- `02_philosophy.md` - general engineering philosophy.
- `03_definition_of_done.md` - completion criteria.
- `04_definition_of_beautiful_code.md` - qualities of maintainable code.
- `05_design_principles.md` - SOLID, KISS, DRY, YAGNI, Clean Architecture, DDD, TDD as behavior.
- `06_responsibility_model.md` - responsibility at function, type, file, package, service, layer, and context levels.
- `07_complexity_budget.md` - size and complexity warning thresholds.
- `08_engineering_smells.md` - code-level smells.
- `09_architectural_smells.md` - boundary and architecture smells.
- `10_antipattern_catalog.md` - recurring bad design patterns.
- `11_refactoring_catalog.md` - safe refactoring tools.
- `12_naming_bible.md` - naming rules.
- `13_testing_philosophy.md` - testing principles.
- `14_debugging_philosophy.md` - debugging principles.
- `15_error_philosophy.md` - error handling principles.
- `16_security_philosophy.md` - security principles.
- `17_observability_contract.md` - logs, metrics, traces, and operational visibility.
- `18_performance_philosophy.md` - performance principles.
- `19_documentation_style.md` - documentation style.
- `20_review_checklist.md` - review checklist.
- `21_commit_pr_adr_style.md` - commit, PR, and ADR style.
- `22_evolution_rules.md` - rules for growing and removing code.
- `23_agent_behavior.md` - agent behavior contract.
- `24_task_todo_style.md` - structured task and TODO style.

## Expansion set

- `25_api_philosophy.md` - API contracts, compatibility, errors, idempotency, versioning, pagination, and protocol choice.
- `26_domain_modeling.md` - entities, value objects, aggregates, commands, events, policies, and invariants.
- `27_state_machine_philosophy.md` - explicit states, valid transitions, impossible states, retries, and side effects.
- `28_concurrency_philosophy.md` - async, locks, queues, actors, cancellation, timeouts, backpressure, and race risks.
- `29_configuration_philosophy.md` - config types, validation, secrets, feature flags, defaults, and lifecycle.
- `30_dependency_philosophy.md` - dependency admission, wrapping, risk, removal, and framework boundaries.
- `31_data_philosophy.md` - source of truth, ownership, schema changes, migrations, retention, caching, and consistency.
- `32_ui_architecture_philosophy.md` - UI state, component boundaries, server state, side effects, accessibility, and frontend architecture.
- `33_ai_engineering_philosophy.md` - evidence-bound AI engineering behavior beyond basic agent etiquette.
- `34_evolution_decision_tree.md` - decision trees for adding files, modules, abstractions, dependencies, config, and standards.

## Selection rules

Read only what the task needs:

- API, webhooks, SDKs, events, RPC, streaming: read `25_api_philosophy.md`.
- Business rules, invariants, workflows, domain boundaries: read `26_domain_modeling.md` and `27_state_machine_philosophy.md`.
- Async behavior, queues, locks, workers, retries, throughput, race bugs: read `28_concurrency_philosophy.md`.
- Environment variables, settings, secrets, flags, runtime behavior switches: read `29_configuration_philosophy.md`.
- New libraries, frameworks, SDKs, generated clients, vendored code: read `30_dependency_philosophy.md`.
- Persistence, cache, migrations, retention, projections, event sourcing, reporting: read `31_data_philosophy.md`.
- Frontend/UI, Figma-to-code, state management, accessibility, responsive behavior: read `32_ui_architecture_philosophy.md`.
- Agent prompts, autonomous coding behavior, AI review, AI-generated patches: read `33_ai_engineering_philosophy.md`.
- Any change that grows structure: read `34_evolution_decision_tree.md`.

## Operating rule

Do not apply these documents as slogans. Convert the relevant rule into a concrete design decision, patch shape, validation step, or review comment.
