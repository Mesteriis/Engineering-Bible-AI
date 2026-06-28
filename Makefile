PYTHON ?= python3
CURL_INSTALL_URL ?= https://raw.githubusercontent.com/Mesteriis/Engineering-Bible-AI/main/scripts/install.sh
CODEX_HOME ?= $(HOME)/.codex
AGENTS_HOME ?= $(HOME)/.agents

.PHONY: help validate validate-tree validate-skills size secrets shell-syntax py-compile be-smoke dry-run install install-command

help:
	@printf '%s\n' \
		'Targets:' \
		'  make validate          Run all repository-local checks' \
		'  make be-smoke          Run be CLI smoke tests' \
		'  make dry-run           Show local Codex install actions without writing' \
		'  make install           Install into CODEX_HOME/AGENTS_HOME' \
		'  make install-command   Print the curl one-command installer' \
		'' \
		'Variables:' \
		'  PYTHON                 Python executable, default: python3' \
		'  CODEX_HOME             Passed through to scripts/install-codex.sh' \
		'  AGENTS_HOME            Passed through to scripts/install-codex.sh'

validate: validate-tree validate-skills size secrets shell-syntax py-compile be-smoke

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

be-smoke:
	$(PYTHON) -m unittest tests/test_be_cli.py -v

dry-run:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --dry-run

install:
	CODEX_HOME="$(CODEX_HOME)" AGENTS_HOME="$(AGENTS_HOME)" bash scripts/install-codex.sh --install

install-command:
	@printf 'curl -fsSL %s | bash -s\n' '$(CURL_INSTALL_URL)'
