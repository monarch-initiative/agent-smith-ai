# With credit to Sierra Moxon: https://github.com/geneontology/go-fastapi/blob/main/Makefile
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

all: install export-requirements start

dev: install start-dev

prod-server:
	poetry run gunicorn src.monarch_assistant.api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080

dev-server:
	poetry run uvicorn src.monarch_assistant.api:app --host 0.0.0.0 --port 3535 --reload

test:
    # --capture=no to see stdout in logs for successful tests
	poetry run pytest --capture=no -v tests

export-requirements:
	poetry export -f requirements.txt --output requirements.txt

install:
	poetry install

run-chat:
	poetry run python3 -m src.monarch_assistant.cli make_chat

chat: install export-requirements run-chat

help:
	@echo ""
	@echo "make all -- installs requirements, exports requirements.txt, runs production server"
	@echo "make dev -- installs requirements, runs hot-restart dev server"
	@echo "make test -- runs tests"
	@echo "make start -- runs production server"
	@echo "make start-dev -- runs hot-restart dev server"
	@echo "make run-chat -- starts the command-line chat interface only"
	@echo "make chat -- installs requirements, exports requirements.txt, starts the command-line chat interface"
	@echo "make export-requirements -- exports requirements.txt"
	@echo "make help -- show this help"
	@echo ""