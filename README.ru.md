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

- **core:** `workflow-router`, `mcp-tool-router`, `engineering-standards`, `core-engineering`, `code-quality`, `architecture-principles`, `testing-tdd`, `tdd-guard`, `debugging`, `code-review`, `security`, `performance`, `refactoring`, `documentation`, `quality-gates`, `context-pack`, `session-memory`.
- **ecosystems:** `python`, `typescript`, `rust`, `go`, `c-cpp`, `homeassistant`, `esphome`, `esp32`.
- **routers:** `review-router`, `security-router`, `ui-router`, `ui-research`, `ui-build`, `ui-figma`, `ui-qa`.
- **review:** `architecture-map`, `architecture-normalizer`, `migration-planner`, `multi-agent-pr-review`, `agent-squad`, `specialist-dispatch`, `subagent-result-merge`, `external-agent-pack-audit`, `agent-retrospective`, `agents-md-retrospective`.
- **security:** `security-diff-review`, `fix-security-finding`, `threat-model`, `dependency-advisory-audit`, `secrets-and-config-review`, `authz-boundary-review`, `deserialization-parser-review`, `supply-chain-review`.
- **ui:** `ui-business-apps`, `ui-concept-first`, `design-system-extractor`, `figma-to-code`, `code-to-figma`, `playwright-visual-qa`, `mobile-qa`, `responsive-breakpoint-check`, `accessibility-ui-review`.

### Опциональные группы

- **fast:** `fast`.
- **wiki:** `wiki-query`, `code-wiki-ru`.

### Навыки авторов по явному выбору

- **pocock-interview:** `pocock.grill-me`, `pocock.grilling`, `pocock.grill-with-docs`, `pocock.domain-modeling`.
- **pocock-writing:** `pocock.writing-for-agents`, `pocock.pr`.
- **pocock-retro:** `pocock.retro`.
- **pocock-questionnaire:** `pocock.to-questionnaire`.
- **superpowers:** `superpowers.brainstorming`, `superpowers.diagnosing-superpowers`, `superpowers.dispatching-parallel-agents`, `superpowers.executing-plans`, `superpowers.finishing-a-development-branch`, `superpowers.receiving-code-review`, `superpowers.requesting-code-review`, `superpowers.subagent-driven-development`, `superpowers.systematic-debugging`, `superpowers.test-driven-development`, `superpowers.using-git-worktrees`, `superpowers.using-superpowers`, `superpowers.verification-before-completion`, `superpowers.writing-plans`, `superpowers.writing-skills`.
- **karpathy:** `karpathy.karpathy-guidelines`.
- **business-ui:** `interface.interface-design`, `uipro.ui-ux-pro-max`, `impeccable.impeccable`.
- **property-testing:** `trailofbits.property-based-testing`.
- **context-continuation:** `pocock.handoff`, `context.context-compression`.

### Авторские зависимости профилей

- **core:** `superpowers.systematic-debugging`, `superpowers.test-driven-development`, `superpowers.requesting-code-review`, `superpowers.receiving-code-review`, `superpowers.verification-before-completion`, `karpathy.karpathy-guidelines`, `trailofbits.property-based-testing`.
- **review:** `superpowers.brainstorming`, `superpowers.diagnosing-superpowers`, `superpowers.dispatching-parallel-agents`, `superpowers.executing-plans`, `superpowers.finishing-a-development-branch`, `superpowers.receiving-code-review`, `superpowers.requesting-code-review`, `superpowers.subagent-driven-development`, `superpowers.systematic-debugging`, `superpowers.test-driven-development`, `superpowers.using-git-worktrees`, `superpowers.using-superpowers`, `superpowers.verification-before-completion`, `superpowers.writing-plans`, `superpowers.writing-skills`.
- **ui:** `interface.interface-design`, `uipro.ui-ux-pro-max`, `impeccable.impeccable`.
<!-- END GENERATED SKILL REGISTRY -->

## Обновляемые авторские навыки

Bible владеет личными правилами, стандартами и роутерами. Авторские навыки
сохраняют исходное содержимое, происхождение и отдельный цикл обновления.
Каталог включает 30 оригиналов: все 15 навыков Superpowers 6.4.2, оригинальный
навык Karpathy-inspired guidelines, девять навыков Matt Pocock, три специалиста
по рабочим интерфейсам, property-based testing и context compression.
Обычные профили устанавливают 20 обязательных авторских
зависимостей; группы Pocock выбираются
отдельно. Локальные debugging, TDD и review стали тонкими адаптерами; пересказ
Karpathy удалён. Решения по всем 62 прежним навыкам записаны в
[реестре миграции](docs/absorbed-skills-migration.md).

[Профиль рабочих интерфейсов](docs/business-ui-profile.md) ориентирован на
дашборды, CRM и приложения. Он выбирает оригинальные Interface Design,
UI UX Pro Max и Impeccable 4.5.0, дополняя их нативными навыками компонентов
и визуализации данных.
`implement-spec` и авторские источники без подтверждённого происхождения отложены.

[Новые навыки тестирования и контекста](docs/quality-context-authors.md)
сохраняются оригиналами. [Продолжение задач](docs/task-continuation.md) использует
короткий checkpoint и проверку свежести исходников.
[Ревью разными провайдерами](docs/cross-provider-review.md) и
[проверка кворума](docs/worker-quorum.md) связывают решение с фиксированным
снимком и доказательствами; сами модели и ключи в пакет не входят.

Оба режима по умолчанию выключены. `/multimodel <задача>` включает написание
кода бюджетной моделью и ревью сильной; `/quorum <задача>` отдельно включает
голосование ревьюеров. Для обоих режимов укажите обе команды. Обычная задача
использует текущую выбранную модель. Это команды в тексте задачи:
[правила включения](docs/cross-provider-review.md#explicit-activation).

[Подготовка кэшируемого контекста](docs/context-cache.md) сохраняет оригинальный
текст, проверяет свежесть и читает статистику кэша из ответа провайдера.
[Точечные мутации](docs/targeted-mutation-testing.md) проверяют силу выбранных
Python-тестов в изолированных копиях. Оба инструмента включаются явно; они не
активируют облачные аккаунты, не гарантируют экономию и не устанавливают фреймворк.

```bash
be skills list --json
be install --dry-run
be skills plan --group pocock-interview --json
be skills ensure --group pocock-interview
be skills route grill-me --json
be skills check --group pocock-interview --json
be skills update --group pocock-interview --dry-run --json
```

`ensure` устанавливает недостающие проверенные зависимости и использует уже
существующие идентичные навыки. `update` применяет проверенную версию из каталога;
`check` только сообщает изменения у автора. Обычный `be update` обновляет Bible
и добавляет недостающие зависимости профиля; обновления авторских версий
выбираются отдельно. `--skip-upstream` подготавливает только файлы Библии;
готовность авторских зависимостей при этом получает статус `SKIP`.
Корень навыков Codex проверяется рекурсивно, включая `external/`; дополнительные
корни существующих плагинов задаются повторяемым `--skill-root`.
Наличие файлов не доказывает доступность навыка в текущей сессии. См.
[установку и восстановление](docs/upstream-skills.md),
[схему библиотеки](docs/superpowers/specs/2026-10-03-upstream-managed-skills-design.md)
и [очередь добавлений](docs/upstream-skills-backlog.md).

## Граница worker/runtime

Репозиторий намеренно не содержит локальную runtime-конфигурацию:

- нет `~/.codex/config.toml`;
- нет auth-файлов;
- нет `.env`;
- нет model provider credentials;
- нет MCP secrets;
- нет Codex session/cache/worktree state.

Переносимый пакет включает инженерные инструкции, skills, standards,
документацию и CLI helpers. Существующий Codex worker, MCP, notify,
Computer Use и model provider остаются локальными.

Профили выбирают поиск по вопросу: точечный текстовый поиск для литералов,
LSP для символов, актуальный граф кода для архитектуры и ограниченный поиск
документов для docs и ADR. Все инструменты на каждую задачу не запускаются.
Runtime-сервисы остаются локальными; их доступность проверяется в текущем host.

Узкие workflows: `wiki-query` отвечает по существующей wiki без её изменения
(опциональная группа `wiki`); `mobile-qa` проверяет нативные Android/iOS-приложения
на выбранном устройстве с проверкой ожидаемого состояния; `architecture-map`
допускает необязательный рендеринг Archify после подтверждения фактов по коду.
Сами skills не устанавливают Mobile MCP, второй wiki-manager, renderer или
agent framework. Пилоты внешних runtime используют общий контракт worker и
подтверждают реальную область действий до активации.

Смотри `docs/worker-runtime-boundary.md`.

[Worker evidence helper](docs/worker-evidence.md) работает офлайн: фиксирует хеши
явно разрешённых файлов, проверяет общий контракт результатов worker и сравнивает
записанные прогоны одинаковых задач. Он сохраняет FAIL/SKIP и неизвестные метрики,
не устанавливает runtime и не подтверждает подлинность выполнения.
Он также определяет продолжение или остановку длительной задачи по измеренным
счётчикам, хешам прогресса и состоянию checkpoint. Опциональный
[memory retrieval helper](docs/memory-retrieval.md) готовит варианты запроса и
объединяет выдачу существующего поиска, сохраняя хеши источников и исходные
результаты. [Решение по Ruflo и результаты пилотов](docs/ruflo-adoption.md).

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

Переход между `steady`, `full` и `minimal` меняет routing policy, сохраняя
выбранный specialist-каталог. Переход с `fast` на `steady` также возвращает
default specialist skills.

## Установка

Основной путь установки:

```bash
git clone https://github.com/Mesteriis/Engineering-Bible-AI.git
cd Engineering-Bible-AI
make validate
make dry-run
make install
```

Установить опциональные wiki skills:

```bash
make install-wiki
```

Команда сохраняет текущий prompt profile. Если выбран `fast`, сначала перейдите
на `steady` командами выше: `fast` активирует только собственный skill даже при
запросе дополнительных групп. Это правило действует и для `make install-all`.

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
разрешением side effects. Bible не генерирует hooks, provider configuration,
credentials или local runtime services. Однако install scripts самих пакетов
могут менять настройки пользователя: изучите их и сохраните затрагиваемые
настройки до установки, затем сравните их после smoke-теста. Автоматическое
включение plugin пакетом не считается проверенной интеграцией.

В optional-каталоге есть pinned capabilities для task state, browser evidence,
исходников зависимостей и versioned документации. Browser runtime настраивается
явно и headless; task state работает в stealth-режиме; авторизация внешней
документации не входит в установку Bible.

Отдельно выбираются pinned CLI `opencode`, `qmd` и `semgrep`:

```bash
be tools plan --tool opencode --tool qmd --tool semgrep
be tools install --tool opencode --tool qmd --tool semgrep
be tools doctor --tool opencode --tool qmd --tool semgrep
```

Проверка `doctor` подтверждает запуск CLI, а не работу провайдера или MCP.
Перед установкой проверяйте также путь бинарника: отдельная локальная установка
может быть доступна host, хотя отсутствует в глобальном реестре менеджера пакетов.
Не устанавливайте второй экземпляр только из-за статуса `MISSING` в каталоге.
Каталог не настраивает работников, ключи, MCP, правила сканирования, коллекции
документов или веса моделей. Эти настройки и результаты функциональных тестов
остаются вне публичного репозитория. Контракт доказательств делегирования задан
в `skills/subagent-result-merge/SKILL.md`.

Claude Code использует собственный формат: `~/.claude/CLAUDE.md` может импортировать
установленный `instructions/global/steady.md`, а personal skills могут ссылаться
на установленные каталоги skills. Перед локальным подключением проверьте
поддержку ссылок в установленной версии и существующие файлы: сохраняйте
пользовательские отличия, не создавайте второй обнаруживаемый корень Bible и не
переносите Codex TOML. Основной installer по-прежнему управляет только своими
Codex-compatible файлами; он не изменяет Claude auth или runtime configuration.

Установить все группы из реестра:

```bash
make install-all
```

Stable install из GitHub release:

```bash
RELEASE=v0.4.1
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
Активные instructions и skills проецируются в `CODEX_HOME`/`AGENTS_HOME`.
Managed-копии `engineering/`, `docs/` и `templates/` также находятся в
`CODEX_HOME`, чтобы относительные ссылки активных owner skills разрешались.
Адаптеры Claude должны привязывать пути helpers и references к реальному
каталогу выбранного canonical skill. Ownership manifest хранит hash и mode
каждого managed file. Unmanaged files не
перезаписываются и не удаляются даже с `--force`. `--migrate-legacy` используется
только для осознанного переноса идентичной legacy installation. Операции
journaled, создают backup и откатываются при ошибке.
При обновлении удаляются только устаревшие пустые каталоги внутри portable
snapshot; rollback восстанавливает прежние права каталогов. Активные каталоги
пользовательских навыков в эту очистку не входят.

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
- В `steady` и `minimal` ясные задачи выбирают узкий leaf skill напрямую;
  `workflow-router` обрабатывает неоднозначные или multi-domain задачи. В `full`
  первый нетривиальный ход проходит через `workflow-router`, если явно не
  запрошен более узкий skill.
- `engineering-standards` читается только когда нужны standards, boundaries,
  smells, naming, refactoring, complexity или структура больших TODO/task plans.
