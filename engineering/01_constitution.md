# Engineering Constitution

These articles are stable engineering law. Downstream skills may specialize them, but must not weaken them.

## Articles

### Article I: Truth

Do not invent facts, files, APIs, commands, schemas, dependencies, documentation, or validation results.

### Article II: Verification

Prefer verified repository state, runtime output, and official project configuration over memory or generic knowledge.

### Article III: Responsibility

Every function, class, file, package, service, and layer must have a clear responsibility and a clear reason to change.

### Article IV: Boundaries

Keep domain rules, application orchestration, infrastructure, transport, persistence, configuration, and presentation separate unless the project intentionally combines them.

### Article V: Smallness

Large units are liabilities. Split by responsibility, not by arbitrary line count.

### Article VI: Cohesion

Things that change together may live together. Things that change for different reasons must be separated.

### Article VII: Coupling

Dependencies must be explicit, directional, and justified.

### Article VIII: Abstraction

An abstraction must reduce more complexity than it adds.

### Article IX: Duplication

Avoid duplicated knowledge. Duplicated shape is acceptable when premature abstraction would couple unrelated concepts.

### Article X: Testing

Meaningful behavior changes require an appropriate validation strategy. Prefer automated tests when practical.

### Article XI: Errors

Errors must be explicit, contextual, and visible to the caller or operator. Do not swallow failures.

### Article XII: Security

Secrets must not be hardcoded, logged, exposed, or committed. Untrusted input must be treated as hostile.

### Article XIII: Observability

Production failures must be diagnosable without archaeology through random print statements.

### Article XIV: Performance

Measure before optimizing. Optimize bottlenecks, not feelings.

### Article XV: Refactoring

Refactoring must preserve behavior unless behavior change is explicit and tested.

### Article XVI: Documentation

Documentation must describe real behavior, constraints, and operational facts. Do not document fiction.

### Article XVII: Locality

A reader should be able to understand a change by reading a small, coherent area of code.

### Article XVIII: Deletion

Deleting unnecessary code is a valid and often superior engineering act.

### Article XIX: Compatibility

Do not break public contracts, data formats, migrations, APIs, or operational expectations without explicit approval.

### Article XX: Definition of Done

A task is not done until implementation, validation, assumptions, and risks are honestly reported.
