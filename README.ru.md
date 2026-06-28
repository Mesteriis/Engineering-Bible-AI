# Engineering Bible AI

Переносимый пакет инженерных стандартов, роутинга skills и инструментов
документации для AI coding agents.

Это публично-переносимая версия локальной настройки Codex на `mb-avm`.
В репозитории лежат только воспроизводимые артефакты, без локального runtime
state и без секретов.

## Состав

- `AGENTS.md` - переносимые корневые инструкции Codex.
- `engineering/` - нейтральная к языкам инженерная библиотека.
- `skills/` - Codex-compatible skills для роутинга, инженерных стандартов,
  разработки, ревью, security, UI routing и генерации code wiki.
- `templates/` - шаблоны отчётов, ADR, PR, commit и prompt внедрения.
- `scripts/` - установка и валидация.
- `tests/` - кейсы роутера.
- `reference/` - компактные legacy-reference документы.
- `examples/` - пример repo-level `AGENTS.md`.

## Группы skills

- Роутинг: `workflow-router`, `review-router`, `security-router`, `ui-router`,
  `ui-research`, `ui-build`, `ui-figma`, `ui-qa`.
- Engineering Bible: `engineering-standards`, `core-engineering`,
  `code-quality`, `architecture-principles`, `testing-tdd`, `debugging`,
  `code-review`, `security`, `performance`, `refactoring`, `documentation`.
- Экосистемы: `python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`,
  `esphome`, `esp32`.
- Обёртки для review/security/UI: architecture, migration, diff/security,
  supply-chain, authz, parser, Figma, visual QA, responsive QA, accessibility.
- Wiki tooling: `code-wiki-ru` для русской Obsidian-compatible code wiki и
  проверки drift между кодом и документацией.

## Граница worker/runtime

Репозиторий намеренно не содержит локальную runtime-конфигурацию:

- нет `~/.codex/config.toml`;
- нет auth-файлов;
- нет `.env`;
- нет Moon Bridge или DeepSeek credentials;
- нет MCP secrets;
- нет Codex session/cache/worktree state.

Пакет устанавливает только standards и skills. Существующий Codex worker, MCP,
notify, Computer Use и model provider остаются локальными.

Смотри `docs/worker-runtime-boundary.md`.

## Установка

Dry-run:

```bash
bash scripts/install-codex.sh --dry-run
```

Установка в `~/.codex` и `~/.agents/skills`:

```bash
bash scripts/install-codex.sh --install
```

Installer делает backup заменяемых файлов в `~/.codex/backups/`.
`~/.codex/config.toml` он не перезаписывает.

## Проверка

```bash
bash scripts/validate-skill-tree.sh .
python3 scripts/check-file-size.py . --hard 10000
bash scripts/secret-sanity.sh .
```

## Принципы

- Root остаётся технологически нейтральным.
- Языковые правила живут в ecosystem skills.
- Общие инженерные принципы живут в `engineering/`.
- `workflow-router` остаётся входной точкой для нетривиальных инженерных задач.
- `engineering-standards` читается только когда нужны standards, boundaries,
  smells, naming, refactoring, complexity или структура больших TODO/task plans.
