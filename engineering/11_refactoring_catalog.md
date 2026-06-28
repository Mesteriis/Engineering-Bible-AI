# Refactoring Catalog

Use refactoring tools deliberately. Preserve behavior unless explicitly changing it.

## Small refactorings

- Rename for domain meaning.
- Extract Function.
- Inline Function.
- Extract Constant.
- Replace Magic Value.
- Introduce Guard Clause.
- Reduce Nesting.
- Replace Boolean Parameter with separate functions.
- Replace Primitive with Value Object when invalid states are common.

## Structural refactorings

- Extract Class/Type.
- Extract Module/File.
- Move Responsibility.
- Split God File.
- Split Package by capability.
- Collapse unnecessary layer.
- Extract Interface/Protocol when a boundary needs protection.
- Replace Inheritance with Composition.
- Replace Service Locator with explicit dependencies.

## Architectural refactorings

- Move business rule from handler to application/domain layer.
- Move infrastructure details behind an adapter.
- Extract gateway/client for external integration.
- Introduce transaction boundary.
- Introduce domain service for cross-entity rule.
- Introduce value object for invariant.
- Split bounded contexts.
- Separate read model/projection when query shape differs from write model.

## Testing support

Before refactoring:

1. Identify expected behavior.
2. Find existing tests.
3. Add characterization tests if behavior is unclear and risk is high.
4. Refactor in small steps.
5. Run validation after meaningful steps.

## Refactoring report

Report:

- behavior preserved;
- responsibilities moved;
- tests run;
- remaining risks.
