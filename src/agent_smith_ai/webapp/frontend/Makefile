# With credit to Sierra Moxon: https://github.com/geneontology/go-fastapi/blob/main/Makefile
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help


dev-npm-server:
	npm start

build-static:
	npm run build

help:
	@echo ""
	@echo "dev-npm-server: runs the client server on port 3000 (mostly for debugging)"
	@echo "build-static: builds the static files for the client (for deployment)"
	@echo ""
