# Engineering Philosophy

Use this philosophy when choosing between valid designs.

## Prefer

- boring code over clever code;
- explicit dependencies over hidden imports or globals;
- composition over inheritance by default;
- immutability where it simplifies reasoning;
- local reasoning over spooky action at a distance;
- deterministic behavior over timing-dependent behavior;
- small focused modules over god files;
- stable interfaces over leaking implementation details;
- deletion over abstraction when the abstraction is not earning its keep;
- tests that describe behavior over tests that mirror implementation;
- observability that helps production debugging over noisy logs;
- standard library and existing dependencies over new dependencies;
- simple data structures over framework ceremony when sufficient;
- clear failure over silent partial success.

## Avoid

- speculative generalization;
- premature layering;
- helper/util dumping grounds;
- manager classes with no domain meaning;
- global mutable state;
- boolean flags that radically change behavior;
- hidden I/O;
- hidden transactions;
- broad exception swallowing;
- architectural rewrites during small bug fixes;
- dependency additions for trivial code.

## Boring solution rule

If two designs are equally correct, choose the one that future maintainers can understand faster.

If a design needs a long explanation to justify itself, it is probably too complex for the problem.
