# Engineering Bible AI

[![Validate](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml/badge.svg)](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Переносимый пакет инженерных стандартов, routing skills и инструментов
документации для AI coding agents. В репозитории лежат только
воспроизводимые standards, skills, templates, tests и installers; локального
runtime state и секретов здесь нет.

## Состав

- `AGENTS.md` - переносимые корневые инструкции Codex.
- `engineering/` - нейтральная к языкам инженерная библиотека с
  `engineering/README.md` как индексом выбора.
- `skills/` - Codex-compatible skills.
- `skills/registry.yml` - единый источник истины для групп skills.
- `templates/` - шаблоны report, ADR, PR, commit и implementation prompt.
- `scripts/` - установка, валидация и `be` CLI.
- `tests/` - исполняемые кейсы роутера.
- `reference/` - legacy/deprecated компактные references для совместимости.
- `examples/` - пример repo-level `AGENTS.md`.
- `.github/` - issue templates, PR template, CODEOWNERS, Dependabot и workflow
  валидации.

## Реестр skills

Установка по умолчанию берёт non-optional группы из `skills/registry.yml`.
Optional wiki group по умолчанию не ставится.

Core:
`workflow-router`, `engineering-standards`, `core-engineering`, `code-quality`,
`architecture-principles`, `testing-tdd`, `debugging`, `code-review`,
`security`, `performance`, `refactoring`, `documentation`, `quality-gates`.

Ecosystems:
`python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`,
`esp32`.

Routers:
`review-router`, `security-router`, `ui-router`, `ui-research`, `ui-build`,
`ui-figma`, `ui-qa`.

Review:
`architecture-map`, `architecture-normalizer`, `migration-planner`,
`multi-agent-pr-review`, `subagent-result-merge`, `agent-retrospective`,
`agents-md-retrospective`.

Security:
`security-diff-review`, `fix-security-finding`, `threat-model`,
`dependency-advisory-audit`, `secrets-and-config-review`,
`authz-boundary-review`, `deserialization-parser-review`,
`supply-chain-review`.

UI:
`ui-concept-first`, `design-system-extractor`, `figma-to-code`,
`code-to-figma`, `playwright-visual-qa`, `responsive-breakpoint-check`,
`accessibility-ui-review`.

Optional wiki:
`code-wiki-ru`.

## Граница worker/runtime

Репозиторий намеренно не содержит локальную runtime-конфигурацию:

- нет `~/.codex/config.toml`;
- нет auth-файлов;
- нет `.env`;
- нет model provider credentials;
- нет MCP secrets;
- нет Codex session/cache/worktree state.

Пакет устанавливает только standards и skills. Существующий Codex worker, MCP,
notify, Computer Use и model provider остаются локальными.

Смотри `docs/worker-runtime-boundary.md`.

## Установка

Основной путь установки:

```bash
git clone https://github.com/Mesteriis/Engineering-Bible-AI.git
cd Engineering-Bible-AI
make validate
make dry-run
make install
```

Установить optional wiki tooling:

```bash
make install-wiki
```

Установить все группы из реестра:

```bash
make install-all
```

Advanced quick install из GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh \
  | bash -s -- --dry-run --diff
```

Когда planned changes выглядят корректно, замени `--dry-run --diff` на
`--install`. `ENGINEERING_BIBLE_REF` можно переопределить на нужный tag, branch
или commit (например, `ENGINEERING_BIBLE_REF=v0.1.0`) при необходимости.

Installer пишет skills в `CODEX_HOME`, общие reference-доки в `CODEX_HOME` и
`AGENTS_HOME`, а также wrapper `be`. Старые managed-зеркала skills из
`AGENTS_HOME` удаляются после backup, чтобы Codex UI не показывал дубли. Он
показывает `ADD`, `UPDATE`, `REMOVE`, `UNCHANGED`, `SKIP` и `CONFLICT`.
Изменённые managed targets не перезаписываются без `--force`. `--no-overwrite`
копирует только отсутствующие targets и оставляет obsolete mirrors на месте.

После установки пакет ставит маленькую команду `be` в `~/.local/bin/be` по
умолчанию. Если `~/.local/bin` не входит в shell `PATH`, запускай команду через
`~/.local/bin/be` или добавь этот каталог в `PATH`.

Первые команды `be`:

```bash
be version
be doctor
be doctor --json
be validate --checkout .
be install --dry-run --diff
be update
be self-update
be add skill https://github.com/<owner>/<repo>/<path>
be audit
```

Варианты через Make:

```bash
make be-update
make be-self-update
make be-audit
make be-add-skill SOURCE=https://github.com/<owner>/<repo>/<path> [NAME=<name>] [REF=<ref>] [SKILL_PATH=<subdir>]
```

```bash
make audit
make quality-audit-tests
make shell-lint
make markdown-lint
```

## Проверка

```bash
make validate
```

Основные entry points валидации:

- `scripts/validate-repo-tree.sh .`
- `scripts/validate-installed-tree.sh ~/.codex ~/.agents`
- `scripts/validate-skill-tree.sh` как compatibility wrapper.
- `scripts/validate-router-cases.py --static`
- `scripts/validate-markdown-style.py .`
- `skills/workflow-router/scripts/validate-routing.sh --codex-only`

GitHub Actions запускает repo-local валидацию на push и pull request.

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
