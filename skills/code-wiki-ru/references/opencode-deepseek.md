# OpenCode DeepSeek

Use OpenCode only after deterministic scripts generate a bounded context pack.

## Codex Invocation

```bash
opencode run --model deepseek/deepseek-v4-pro --dir "$REPO_ROOT" --title "code-wiki-ru:$CHUNK_ID" "$(cat "$CONTEXT_PACK")"
```

Use `deepseek/deepseek-v4-flash` for smoke tests.

## Rules

- Do not pass secret-bearing file contents to OpenCode.
- Do not ask DeepSeek to apply patches.
- Treat DeepSeek output as a draft that must be staged under `_meta/drafts/`.
- Validate staged wiki pages before apply.
- Preserve Russian prose and exact source identifiers.
