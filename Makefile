PYTHON ?= $(shell command -v python3.11 >/dev/null 2>&1 && printf python3.11 || printf python3)
PACKAGE_VERSION := $(strip $(shell cat VERSION 2>/dev/null || echo main))
CURL_INSTALL_REF ?= v$(PACKAGE_VERSION)
CURL_INSTALL_URL ?= https://github.com/Mesteriis/Engineering-Bible-AI/releases/download/$(CURL_INSTALL_REF)/install.sh
CODEX_HOME ?= $(HOME)/.codex
AGENTS_HOME ?= $(HOME)/.agents

.DEFAULT_GOAL := help

.PHONY: help validate validate-quick validate-bootstrap validate-release test audit quality-audit-tests validate-tree validate-skills validate-registry registry-docs validate-router-cases validate-install size secrets shell-syntax shell-lint markdown-lint py-compile be-smoke be-audit be-update be-self-update be-add-skill dry-run tools-dry-run install install-tools install-all install-wiki install-command

help:
	@printf '%s\n' \
		'Targets:' \
		'  make validate-quick        Run fast repository checks and discovered tests' \
		'  make validate-bootstrap    Run dependency-light artifact checks' \
		'  make audit                Run be audit (quality gate checks)' \
		'  make quality-audit-tests  Run quality gate audit tests' \
		'  make validate              Run the full validation profile' \
		'  make validate-release      Run full release gates; SKIP is a failure' \
		'  make test                  Discover and run every tests/test_*.py file' \
		'  make validate-install      Install into a temp HOME and validate installed tree' \
		'  make shell-lint             Run shellcheck/shfmt checks' \
		'  make markdown-lint          Run markdown style checks' \
		'  make be-smoke              Run be CLI smoke tests' \
		'  make be-audit              Run be audit from CLI' \
		'  make be-update             Run be update (same as `be update`)' \
		'  make be-self-update        Run be self-update (same as `be self-update`)' \
		'  make be-add-skill          Add external skill. Set SOURCE and optional NAME/REF/SKILL_PATH.' \
		'  make dry-run               Show local Codex install diff without writing' \
		'  make tools-dry-run         Show explicit --all companion CLI plan' \
		'  make install               Install default skill groups into CODEX_HOME/AGENTS_HOME' \
		'  make install-tools         Install companion CLIs (requires TOOL or TOOL_GROUP)' \
		'  make install-wiki          Install default groups plus optional wiki skill' \
		'  make install-all           Install every skill group' \
		'  make install-command       Print the advanced curl installer command' \
		'' \
		'Variables:' \
		'  PYTHON                     Python executable, default: $(PYTHON)' \
		'  CURL_INSTALL_REF           Release tag for remote installer, default: $(CURL_INSTALL_REF)' \
		'  SOURCE                     be-add-skill source argument' \
		'  NAME                       Optional be-add-skill --name' \
		'  REF                        Optional be-add-skill --ref for git sources' \
		'  SKILL_PATH                 Optional be-add-skill --path' \
		'  CODEX_HOME                 Passed through to scripts/install-codex.sh' \
		'  AGENTS_HOME                Passed through to scripts/install-codex.sh'

validate:
	$(PYTHON) scripts/validate.py --root . --profile full

validate-quick:
	$(PYTHON) scripts/validate.py --root . --profile quick

validate-bootstrap:
	$(PYTHON) scripts/validate.py --root . --profile bootstrap

validate-release:
	$(PYTHON) scripts/validate.py --root . --profile release

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

validate-tree:
	bash scripts/validate-repo-tree.sh .

validate-skills:
	$(PYTHON) scripts/validate-skill-frontmatter.py skills

validate-registry:
	$(PYTHON) scripts/registry.py --root . validate

registry-docs:
	$(PYTHON) scripts/registry.py --root . docs --write

validate-router-cases:
	$(PYTHON) scripts/validate-router-cases.py --fixtures

validate-install:
	set -e; \
	tmp_dir="$$(mktemp -d "$${TMPDIR:-/tmp}/engineering-bible-ai-install.XXXXXX")"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	HOME="$$tmp_dir/home" \
	CODEX_HOME="$$tmp_dir/home/.codex" \
	AGENTS_HOME="$$tmp_dir/home/.agents" \
	ENGINEERING_BIBLE_HOME="$$tmp_dir/home/.engineering-bible" \
	ENGINEERING_BIBLE_BIN_DIR="$$tmp_dir/home/.local/bin" \
	bash scripts/install-codex.sh --install; \
	HOME="$$tmp_dir/home" bash "$$tmp_dir/home/.engineering-bible/current/scripts/validate-installed-tree.sh" \
		"$$tmp_dir/home/.engineering-bible/current" "$$tmp_dir/home/.codex" "$$tmp_dir/home/.agents"; \
	HOME="$$tmp_dir/home" bash "$$tmp_dir/home/.codex/skills/workflow-router/scripts/validate-routing.sh" --codex-only

size:
	$(PYTHON) scripts/check-file-size.py . --hard 10000

secrets:
	bash scripts/secret-sanity.sh .

shell-lint:
	@if ! command -v shellcheck >/dev/null 2>&1; then \
		echo "shellcheck not found"; \
		exit 1; \
	fi
	shellcheck scripts/install.sh scripts/install-codex.sh scripts/install-tools.sh scripts/secret-sanity.sh scripts/validate-installed-tree.sh scripts/validate-repo-tree.sh scripts/validate-skill-tree.sh skills/workflow-router/scripts/validate-routing.sh

	@if ! command -v shfmt >/dev/null 2>&1; then \
		echo "shfmt not found"; \
		exit 1; \
	fi
	@unformatted=$$(shfmt -l scripts/*.sh skills/workflow-router/scripts/validate-routing.sh); \
	if [ -n "$$unformatted" ]; then \
		echo "shfmt would change:"; \
		echo "$$unformatted"; \
		exit 1; \
	fi

shell-syntax:
	@for file in scripts/*.sh skills/*/scripts/*.sh; do \
		[ -f "$$file" ] || continue; \
		bash -n "$$file" || exit 1; \
	done

markdown-lint:
	$(PYTHON) scripts/validate-markdown-style.py .

py-compile:
	find scripts skills -name '*.py' -print0 | xargs -0 $(PYTHON) -m py_compile

audit:
	$(PYTHON) scripts/audit-quality-gates.py .

quality-audit-tests:
	$(PYTHON) -m unittest discover -s tests -p 'test_quality_audit.py' -v

be-audit:
	$(PYTHON) scripts/be.py audit

be-smoke:
	$(PYTHON) -m unittest discover -s tests -p 'test_be_cli.py' -v

be-update:
	$(PYTHON) scripts/be.py update

be-self-update:
	$(PYTHON) scripts/be.py self-update

be-add-skill:
	@if [ -z "$(SOURCE)" ]; then \
		echo "error: SOURCE is required. Example: make be-add-skill SOURCE=https://github.com/user/repo SKILL_PATH=path/to/skill"; \
		exit 1; \
	fi
	$(PYTHON) scripts/be.py add skill "$(SOURCE)" $(if $(NAME),--name "$(NAME)",) $(if $(REF),--ref "$(REF)",) $(if $(SKILL_PATH),--path "$(SKILL_PATH)",)

dry-run:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --dry-run --diff

tools-dry-run:
	$(PYTHON) scripts/tool_catalog.py --catalog config/tools.json plan --all

install:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install

install-tools:
	@test -n "$(TOOL)$(TOOL_GROUP)" || (echo 'set TOOL=ID or TOOL_GROUP=NAME; no implicit bulk install' >&2; exit 2)
	$(PYTHON) scripts/tool_catalog.py --catalog config/tools.json install $(if $(TOOL),--tool $(TOOL),) $(if $(TOOL_GROUP),--group $(TOOL_GROUP),)

install-wiki:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install --group wiki

install-all:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install --all

install-command:
	@printf 'curl -fSLo engineering-bible-install.sh %s\n' '$(CURL_INSTALL_URL)'
	@printf 'bash engineering-bible-install.sh --dry-run --diff\n'
