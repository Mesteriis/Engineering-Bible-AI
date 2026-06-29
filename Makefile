PYTHON ?= python3
CURL_INSTALL_REF ?= v0.1.0
CURL_INSTALL_URL ?= https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/$(CURL_INSTALL_REF)/scripts/install.sh
CODEX_HOME ?= $(HOME)/.codex
AGENTS_HOME ?= $(HOME)/.agents

.PHONY: help validate audit quality-audit-tests validate-tree validate-skills validate-registry validate-router-cases validate-install size secrets shell-syntax py-compile be-smoke be-audit be-update be-self-update be-add-skill dry-run install install-all install-wiki install-command

	help:
	@printf '%s\n' \
		'Targets:' \
		'  make audit                Run be audit (quality gate checks)' \
		'  make quality-audit-tests  Run quality gate audit tests' \
		'  make validate              Run all repository-local and temp install checks' \
		'  make validate-install      Install into a temp HOME and validate installed tree' \
		'  make be-smoke              Run be CLI smoke tests' \
		'  make be-audit              Run be audit from CLI' \
		'  make be-update             Run be update (same as `be update`)' \
		'  make be-self-update        Run be self-update (same as `be self-update`)' \
		'  make be-add-skill          Add external skill. Set SOURCE and optional NAME/REF/SKILL_PATH.' \
		'  make dry-run               Show local Codex install diff without writing' \
		'  make install               Install default skill groups into CODEX_HOME/AGENTS_HOME' \
		'  make install-wiki          Install default groups plus optional wiki skill' \
		'  make install-all           Install every skill group' \
		'  make install-command       Print the advanced curl installer command' \
		'' \
		'Variables:' \
		'  PYTHON                     Python executable, default: python3' \
		'  CURL_INSTALL_REF           GitHub ref for curl installer, default: v0.1.0' \
		'  SOURCE                     be-add-skill source argument' \
		'  NAME                       Optional be-add-skill --name' \
		'  REF                        Optional be-add-skill --ref for git sources' \
		'  SKILL_PATH                 Optional be-add-skill --path' \
		'  CODEX_HOME                 Passed through to scripts/install-codex.sh' \
		'  AGENTS_HOME                Passed through to scripts/install-codex.sh'

validate: validate-tree validate-skills validate-registry validate-router-cases audit quality-audit-tests size secrets shell-syntax py-compile be-smoke validate-install

validate-tree:
	bash scripts/validate-repo-tree.sh .

validate-skills:
	$(PYTHON) scripts/validate-skill-frontmatter.py skills

validate-registry:
	$(PYTHON) scripts/registry.py --root . validate

validate-router-cases:
	$(PYTHON) scripts/validate-router-cases.py --static

validate-install:
	set -e; \
	tmp_dir="$$(mktemp -d "$${TMPDIR:-/tmp}/engineering-bible-ai-install.XXXXXX")"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	HOME="$$tmp_dir/home" \
	CODEX_HOME="$$tmp_dir/home/.codex" \
	AGENTS_HOME="$$tmp_dir/home/.agents" \
	ENGINEERING_BIBLE_BIN_DIR="$$tmp_dir/home/.local/bin" \
	bash scripts/install-codex.sh --install; \
	HOME="$$tmp_dir/home" bash "$$tmp_dir/home/.codex/scripts/validate-installed-tree.sh" "$$tmp_dir/home/.codex" "$$tmp_dir/home/.agents"; \
	HOME="$$tmp_dir/home" bash "$$tmp_dir/home/.codex/skills/workflow-router/scripts/validate-routing.sh" --codex-only

size:
	$(PYTHON) scripts/check-file-size.py . --hard 10000

secrets:
	bash scripts/secret-sanity.sh .

shell-syntax:
	bash -n scripts/install.sh scripts/install-codex.sh scripts/secret-sanity.sh scripts/validate-installed-tree.sh scripts/validate-repo-tree.sh scripts/validate-skill-tree.sh skills/workflow-router/scripts/validate-routing.sh

py-compile:
	find scripts skills -name '*.py' -print0 | xargs -0 $(PYTHON) -m py_compile

audit:
	$(PYTHON) scripts/audit-quality-gates.py .

quality-audit-tests:
	$(PYTHON) -m unittest tests/test_quality_audit.py -v

be-audit:
	$(PYTHON) scripts/be.py audit

be-smoke:
	$(PYTHON) -m unittest tests/test_be_cli.py -v

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

install:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install

install-wiki:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install --group wiki

install-all:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install --all

install-command:
	@printf 'ENGINEERING_BIBLE_REF=%s curl -fsSL %s | bash -s -- --dry-run --diff\n' '$(CURL_INSTALL_REF)' '$(CURL_INSTALL_URL)'
