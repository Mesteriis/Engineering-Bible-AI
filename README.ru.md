# Engineering Bible AI

[![Validate](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml/badge.svg)](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Переносимый пакет инженерных стандартов, роутинга skills и инструментов
документации для AI coding agents.

Это публично-переносимая версия локальной настройки Codex на `mb-avm`.
В репозитории лежат только воспроизводимые артефакты, без локального runtime
state и без секретов.

## Состав

- `AGENTS.md` - переносимые корневые инструкции Codex.
- `engineering/` - нейтральная к языкам инженерная библиотека с
  `engineering/README.md` как индексом выбора.
- `skills/` - Codex-compatible skills для роутинга, инженерных стандартов,
  разработки, ревью, security, UI routing и генерации code wiki.
- `templates/` - шаблоны отчётов, ADR, PR, commit и prompt внедрения.
- `scripts/` - установка и валидация.
- `tests/` - кейсы роутера.
- `reference/` - компактные legacy-reference документы.
- `examples/` - пример repo-level `AGENTS.md`.
- `.github/` - issue templates, PR template, CODEOWNERS, Dependabot и workflow
  валидации.

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

Установка одной командой из GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh | bash -s
```

Remote dry-run:

```bash
curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh | bash -s -- --dry-run
```

Dry-run:

```bash
make dry-run
```

Установка в `~/.codex` и `~/.agents/skills`:

```bash
make install
```

После установки пакет также ставит маленькую команду `be` в `~/.local/bin/be`
по умолчанию. Если `~/.local/bin` не входит в shell `PATH`, запускай команду
через `~/.local/bin/be` или добавь этот каталог в `PATH`.

Первые команды `be`:

```bash
be version
be doctor
be doctor --json
be validate --checkout .
be install --dry-run
```

Installer делает backup заменяемых файлов в `~/.codex/backups/`.
`~/.codex/config.toml` он не перезаписывает.

## Проверка

```bash
make validate
```

GitHub Actions запускает ту же repo-local валидацию на push и pull request.

## OSS

- Лицензия: MIT, смотри `LICENSE`.
- Как вносить изменения: `CONTRIBUTING.md`.
- Security reports: `SECURITY.md`.
- Support: GitHub Issues и `SUPPORT.md`.
- Release checklist: `docs/oss-release-checklist.md`.
- Third-party notices: `THIRD_PARTY_NOTICES.md`.

## Принципы

- Root остаётся технологически нейтральным.
- Языковые правила живут в ecosystem skills.
- Общие инженерные принципы живут в `engineering/`; используй
  `engineering/README.md`, чтобы выбирать только релевантные reference-доки.
- `workflow-router` остаётся входной точкой для нетривиальных инженерных задач.
- `engineering-standards` читается только когда нужны standards, boundaries,
  smells, naming, refactoring, complexity или структура больших TODO/task plans.
