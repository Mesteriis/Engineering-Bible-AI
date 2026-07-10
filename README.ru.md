# Engineering Bible AI

[![Validate](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml/badge.svg)](https://github.com/Mesteriis/Engineering-Bible-AI/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Переносимый пакет инженерных стандартов, routing skills и инструментов
документации для AI coding agents. В репозитории лежат только
воспроизводимые standards, skills, templates, tests и installers; локального
runtime state и секретов здесь нет.

## Состав

- `AGENTS.md` - инструкции для изменений в этом репозитории.
- `instructions/global/` - устанавливаемые steady, full, minimal и fast global
  profiles.
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

<!-- BEGIN GENERATED SKILL REGISTRY -->
### Группы по умолчанию

- **core:** `workflow-router`, `mcp-tool-router`, `engineering-standards`, `core-engineering`, `code-quality`, `architecture-principles`, `testing-tdd`, `tdd-guard`, `debugging`, `code-review`, `security`, `performance`, `refactoring`, `documentation`, `quality-gates`, `karpathy-guidelines`, `context-pack`, `session-memory`.
- **ecosystems:** `python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`, `esp32`.
- **routers:** `review-router`, `security-router`, `ui-router`, `ui-research`, `ui-build`, `ui-figma`, `ui-qa`.
- **review:** `architecture-map`, `architecture-normalizer`, `migration-planner`, `multi-agent-pr-review`, `agent-squad`, `specialist-dispatch`, `subagent-result-merge`, `external-agent-pack-audit`, `agent-retrospective`, `agents-md-retrospective`.
- **security:** `security-diff-review`, `fix-security-finding`, `threat-model`, `dependency-advisory-audit`, `secrets-and-config-review`, `authz-boundary-review`, `deserialization-parser-review`, `supply-chain-review`.
- **ui:** `ui-concept-first`, `design-system-extractor`, `figma-to-code`, `code-to-figma`, `playwright-visual-qa`, `responsive-breakpoint-check`, `accessibility-ui-review`.

### Опциональные группы

- **fast:** `fast`.
- **wiki:** `code-wiki-ru`.
<!-- END GENERATED SKILL REGISTRY -->

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

## Prompt profiles

- `steady` используется по умолчанию для новых установок. Он сохраняет полный
  default-каталог skills, выбирает узкий leaf workflow напрямую и повторно
  использует текущий route, загруженные инструкции и runtime metadata в
  продолжении той же задачи.
- `full` сохраняет исчерпывающий routing и capability discovery на первом ходе,
  но не повторяет их, пока задача, риск и требуемые tools не изменились.
- `minimal` сохраняет steady-state поведение с меньшим global prompt.
- `fast` является намеренно ограниченным режимом и устанавливает только skill
  `fast`.

Обновление или повторная установка через `be`, `make install` или локальный
installer сохраняет profile из ownership manifest. Переход выполняется явно
после просмотра плана:

```bash
be update --dry-run --prompt-profile steady
be update --prompt-profile steady
```

Меняется routing policy, а не доступный specialist-каталог. Явные вызовы skills
и все default specialist workflows остаются доступными.

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

Просмотреть и явно выбрать optional companion CLI tools:

```bash
be tools list
be tools plan --group foundation
be tools install --group foundation --allow-unpinned
be tools list --capability dependency-docs --json
be tools configure --tool agent-browser --step browser-runtime --allow-network
be tools doctor --tool agent-browser
```

Версионированный каталог показывает `OK`, `MISMATCH`, `UNPINNED`, `MISSING` и
`UNSUPPORTED`, если entry недоступен на текущей платформе.
Без `--group`, `--tool` или `--all` установка не начинается. Установка Bible
не устанавливает companion tools; настройка выполняется по одному шагу с явным
разрешением side effects. Hooks, provider configuration, credentials и local
runtime services автоматически не включаются.

В optional-каталоге есть pinned capabilities для task state, browser evidence,
исходников зависимостей и versioned документации. Browser runtime настраивается
явно и headless; task state работает в stealth-режиме; авторизация внешней
документации не входит в установку Bible.

Установить все группы из реестра:

```bash
make install-all
```

Stable install из GitHub release:

```bash
RELEASE=v0.1.0
curl -fSLo engineering-bible-install.sh \
  "https://github.com/Mesteriis/Engineering-Bible-AI/releases/download/${RELEASE}/install.sh"
bash engineering-bible-install.sh --dry-run --diff
```

Когда planned changes выглядят корректно, замени `--dry-run --diff` на
`--install`.

Mutable branch разрешается только явно:

```bash
bash engineering-bible-install.sh --ref main --allow-unstable --dry-run
```

Полный portable snapshot устанавливается в `$ENGINEERING_BIBLE_HOME/current`.
Активные instructions и skills проецируются в `CODEX_HOME`/`AGENTS_HOME`, а
ownership manifest хранит hash и mode каждого managed file. Unmanaged files не
перезаписываются и не удаляются даже с `--force`. `--migrate-legacy` используется
только для осознанного переноса идентичной legacy installation. Операции
journaled, создают backup и откатываются при ошибке.

После установки пакет ставит маленькую команду `be` в `~/.local/bin/be` по
умолчанию. Если `~/.local/bin` не входит в shell `PATH`, запускай команду через
`~/.local/bin/be` или добавь этот каталог в `PATH`.

Первые команды `be`:

```bash
be version
be doctor
be doctor --json
be validate --checkout .
be validate --checkout . --profile quick
be validate --checkout . --profile release
be validate --installed
be install --dry-run --diff
be install --dry-run --prompt-profile full
be install --dry-run --prompt-profile minimal
be install --dry-run --prompt-profile fast
be install --dry-run --migrate-legacy
be update
be update --ref main --allow-unstable --dry-run
RUNTIME_METADATA=/path/to/runtime-metadata.json
be mcp refresh --repo . --json < "$RUNTIME_METADATA"
be mcp status --repo . --json
printf '%s\n' 'проверь этот репозиторий' | be mcp candidates --repo . --task-stdin --json
TOOL_ID=opaque-tool-id
be mcp show "$TOOL_ID" --json
be tools list
TOOL_ID=tool-id
be tools plan --tool "$TOOL_ID"
SKILL_SOURCE=https://github.com/OWNER/REPOSITORY
SKILL_PATH=path/to/skill
be add skill "$SKILL_SOURCE" --path "$SKILL_PATH"
be acceptance validate .engineering-bible/evidence/acceptance.json --json
be audit
```

`be self-update` на один release остаётся deprecated alias для `be update`.
Runtime capability names обнаруживаются из текущей host session и записываются
только в локальное Git-excluded state под `.engineering-bible/mcp/`.
`refresh` не опрашивает и не вызывает capabilities: host adapter должен передать
через stdin текущий in-memory registry в нормализованной схеме, показанной в
`examples/runtime-capabilities.synthetic.json`. Нельзя строить этот input из
конфигурации репозитория или запомненного списка providers.
`--repo` должен указывать на Git working tree: если local exclude нельзя
безопасно настроить, refresh завершается до записи файлов каталога.

Варианты через Make:

```bash
make be-update
make be-self-update
make be-audit
make be-add-skill SOURCE="$SKILL_SOURCE" NAME=optional-name REF=optional-ref SKILL_PATH="$SKILL_PATH"
```

```bash
make audit
make quality-audit-tests
make shell-lint
make markdown-lint
```

## Проверка

```bash
make validate-quick
make validate-bootstrap
make validate
make validate-release
```

Единый runner помечает каждую проверку как `PASS`, `FAIL` или `SKIP`. Release
profile считает любой `SKIP` ошибкой и сверяет обязательный snapshot с
`git ls-files`.

Основные entry points:

- `scripts/validate.py --profile quick|bootstrap|full|release`
- `scripts/validate-repo-tree.sh .`
- `be validate --installed`
- `scripts/validate-installed-tree.sh "$ENGINEERING_BIBLE_HOME/current" ~/.codex ~/.agents`
- `scripts/validate-skill-tree.sh` как compatibility wrapper.
- `scripts/validate-router-cases.py --fixtures`
- `ENGINEERING_BIBLE_ROUTER_EVALUATOR=/absolute/path/to/evaluator scripts/validate-router-cases.py --runtime`
- `scripts/validate-markdown-style.py .`
- `skills/workflow-router/scripts/validate-routing.sh --codex-only`

Все тесты обнаруживаются автоматически:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

`skills/registry.yml` управляет generated-блоками в обоих README и manifest.
Обновляй их через `make registry-docs`; validation ловит любое расхождение.
Opt-in runtime evaluator получает JSON `{schema_version, cases}` через stdin и
должен вернуть `{schema_version, results: [{id, skills}]}` через stdout. Если
evaluator не настроен, runtime evaluation завершается с `SKIP`, а не сообщает
ложный успех.

GitHub Actions запускает repo-local валидацию на push и pull request.

## OSS

- Лицензия: MIT, смотри `LICENSE`.
- Как вносить изменения: `CONTRIBUTING.md`.
- Security reports: `SECURITY.md`.
- Support: GitHub Issues и `SUPPORT.md`.
- Release checklist: `docs/oss-release-checklist.md`.
- Third-party notices: `THIRD_PARTY_NOTICES.md`.

## Принципы

- Устанавливаемые global instructions остаются technology-neutral и
  capability-based.
- Default prompt profile — `steady`; `full` сохраняет строгий routing первого
  хода, `minimal` является компактным steady-state режимом, а `fast` активирует
  только fast skill.
- Языковые правила живут в ecosystem skills.
- Общие инженерные принципы живут в `engineering/`; используй
  `engineering/README.md`, чтобы выбирать только релевантные reference-доки.
- `workflow-router` используется для неоднозначных, multi-domain или заметно
  изменившихся задач. Ясные задачи выбирают узкий leaf skill напрямую.
- `engineering-standards` читается только когда нужны standards, boundaries,
  smells, naming, refactoring, complexity или структура больших TODO/task plans.
