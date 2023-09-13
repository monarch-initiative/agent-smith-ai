# With credit to Sierra Moxon: https://github.com/geneontology/go-fastapi/blob/main/Makefile
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help


help:
	@echo ""
	@echo "make help -- show this help"
	@echo "BASIC"
	@echo "  make install-dev -- install dependencies"
	@echo "  make test-basic -- run basic tests"
	@echo "  make example-cli-monarch -- run example CLI script"
	@echo "PUBLISHING"
	@echo "  make docs -- build documentation"
	@echo "  make pypi-publish-test -- publish to test PyPI"
	@echo "  make pypi-publish -- publish to PyPI"
	@echo "WEBAPP"
	@echo "  make webapp-dev -- run webapp in dev mode"
	@echo "  make webapp-dev-stop -- stop webapp dev mode"
	@echo "  make webapp-build -- build webapp static files"
	@echo "  make webapp-prod -- run webapp in prod mode"
	@echo "  make webapp-prod-stop -- stop webapp prod mode"
	@echo "BASH AGENT"
	@echo "  make bash-ai-alias -- print alias for bash agent"
	@echo ""

build: install-dev docs webapp-build

#### Basic ####

install-dev:
	poetry install

# TODO: tests for different utilities (main class, bash agent, web ui)
test-basic:
    # --capture=no to see stdout in logs for successful tests
	poetry run pytest --capture=no -v tests

example-cli-monarch: 
	poetry run python3 examples/monarch_cli.py



##### Publishing #####

.PHONY: docs
docs:
	poetry run $(MAKE) -C docs html

pypi-publish-test:
	rm -r dist/*
	poetry export -f requirements.txt --output requirements.txt
	poetry build
	twine upload -r testpypi dist/*

pypi-publish:
	rm -r dist/*
	poetry export -f requirements.txt --output requirements.txt
	poetry build
	twine upload dist/*


##### Webapp #####

example-streamlit:
	poetry run streamlit run examples/streamlit_server.py


##### Bash Agent #####

bash-ai-alias:
	@echo "# source <(make bash-ai-alias) && ai --help"
	@echo alias ai=\'poetry run python3 src/agent_smith_ai/bash_agent/main.py\'

