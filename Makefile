# With credit to Sierra Moxon: https://github.com/geneontology/go-fastapi/blob/main/Makefile
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

all: install export-requirements chat

test:
    # --capture=no to see stdout in logs for successful tests
	poetry run pytest --capture=no -v tests

export-requirements:
	poetry export -f requirements.txt --output requirements.txt

install:
	poetry install

cli-monarch: 
	poetry run python3 examples/monarch_cli.py

help:
	@echo ""
	@echo "make all -- installs requirements, exports requirements.txt, runs chat cli"
	@echo "make test -- runs tests"
	@echo "make cli-monarch -- runs the example monarch cli"
	@echo "make help -- show this help"
	@echo ""