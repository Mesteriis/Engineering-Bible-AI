PYTHON ?= python3
CURL_INSTALL_URL ?= https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh
CODEX_HOME ?= $(HOME)/.codex
AGENTS_HOME ?= $(HOME)/.agents

.PHONY: help validate validate-tree validate-skills size secrets shell-syntax py-compile quality-audit quality-audit-tests be-smoke dry-run install install-command be-update be-self-update be-add-skill

help:
	@printf '%s\n' \
		'Targets:' \
		'  make validate          Run all repository-local checks' \
		'  make be-smoke          Run be CLI smoke tests' \
		'  make quality-audit      Run Engineering-Bible quality gate checks' \
		'  make quality-audit-tests Run quality gate unit tests' \
		'  make dry-run           Show local Codex install actions without writing' \
		'  make install           Install into CODEX_HOME/AGENTS_HOME' \
		'  make install-command   Print the curl one-command installer' \
		'  make be-update         Run be update (same as `be update`)' \
		'  make be-self-update    Run be self-update (same as `be self-update`)' \
		'  make be-add-skill      Add external skill. Set SOURCE and optional NAME/REF/SKILL_PATH.' \
		'' \
		'Variables:' \
			'  PYTHON                 Python executable, default: python3' \
			'  CODEX_HOME             Passed through to scripts/install-codex.sh' \
			'  AGENTS_HOME            Passed through to scripts/install-codex.sh' \
			'  SOURCE                 be-add-skill source argument' \
			'  NAME                   Optional be-add-skill --name' \
			'  REF                    Optional be-add-skill --ref for git sources' \
			'  SKILL_PATH             Optional be-add-skill --path'

validate: validate-tree validate-skills size secrets shell-syntax py-compile quality-audit quality-audit-tests be-smoke

validate-tree:
	bash scripts/validate-skill-tree.sh .

validate-skills:
	$(PYTHON) scripts/validate-skill-frontmatter.py skills

size:
	$(PYTHON) scripts/check-file-size.py . --hard 10000

secrets:
	bash scripts/secret-sanity.sh .

shell-syntax:
	bash -n scripts/install.sh scripts/install-codex.sh scripts/secret-sanity.sh scripts/validate-skill-tree.sh

py-compile:
	find scripts skills -name '*.py' -print0 | xargs -0 $(PYTHON) -m py_compile

quality-audit:
	$(PYTHON) scripts/audit-quality-gates.py .

quality-audit-tests:
	$(PYTHON) -m unittest tests/test_quality_audit.py -v

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
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --dry-run

install:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install

install-command:
	@printf 'curl -fsSL %s | bash -s\n' '$(CURL_INSTALL_URL)'
