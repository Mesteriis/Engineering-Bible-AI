# Definition of Beautiful Code

Beautiful code is not decorative. It is easy to reason about under pressure.

## Beautiful code

- has one clear purpose;
- has explicit inputs and outputs;
- reads in the order the behavior happens;
- has names that carry domain meaning;
- exposes dependencies clearly;
- fails explicitly;
- is easy to test without theatrical mocking;
- is easy to delete;
- is easy to replace;
- keeps decisions close to the data and rules they depend on;
- avoids surprising side effects;
- does not require comments to explain normal control flow;
- makes invalid states difficult or impossible to represent;
- keeps public contracts small and stable.

## Ugly code

- hides I/O;
- hides mutable state;
- depends on global context;
- mixes unrelated responsibilities;
- changes behavior through magic flags;
- catches broad exceptions and continues;
- requires reading ten files to understand one rule;
- has names like `manager`, `helper`, `utils`, `processor`, or `thing` without precise meaning;
- is hard to test except by mocking half the world;
- uses abstraction to avoid making a clear decision.

## Readability rule

A competent maintainer should understand the main path of a function quickly.

If understanding requires reconstructing state from callbacks, globals, hidden context, and side effects, the code is not beautiful, no matter how clever it looks.
