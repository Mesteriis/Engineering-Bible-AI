# Prompt Contracts

DeepSeek output must be Markdown with these sections:

## Summary

Russian summary of what the chunk proves.

## Proposed pages

One subsection per target page. Each subsection starts with:

```markdown
### docs/wiki/components/example.md
```

Then provide page content in Russian.

## Source coverage

List every source path used and the facts extracted from it.

## Drift candidates

List mismatches between code, docs, and ADRs. Use `Нет найденных расхождений.` when no mismatch is supported by the context.

The host agent stages proposed pages under `_meta/drafts/` and writes `patch-preview.diff`. The model does not apply changes.
