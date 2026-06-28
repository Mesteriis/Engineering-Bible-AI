# Wiki Taxonomy

Use Russian prose and Obsidian-compatible Markdown.

## Default Tree

- `index.md`: карта вики и ссылки на основные разделы.
- `systems/`: крупные подсистемы и bounded contexts.
- `components/`: модули, пакеты, классы, воркеры и runtime-компоненты.
- `flows/`: request flow, data flow, queues, jobs and lifecycle diagrams.
- `api/`: HTTP, RPC, CLI, event contracts and public interfaces.
- `data/`: persistence, schemas, migrations, models and state.
- `integrations/`: external services, SDKs, brokers, filesystems and network dependencies.
- `operations/`: config, startup, observability and troubleshooting.
- `decisions/`: ADR summaries and links from decisions to source files.
- `glossary/`: domain terms.
- `_meta/`: machine-maintained state.

## Page Rules

- Use lowercase kebab-case filenames.
- Use `[[wiki-links]]` for internal references.
- Use relative Markdown links for source docs and ADR files.
- Keep pages focused on one topic.
- Use Mermaid for architecture, lifecycle, and data-flow diagrams when the source context supports the diagram.
- Use short code excerpts only when they clarify behavior; prefer source references for large logic.
