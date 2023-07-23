default: help

POETRY_DEV=./external/shell_scripts_lib/python/poetry_dev.sh
POETRY_PIP_RELEASER=./external/shell_scripts_lib/python/poetry_pip_releaser.sh

.PHONY: update-externals
update-externals: ## Update external source dependents
	@git-deps-syncer sync-all -y

.PHONY: clear-virtual-env
clear-virtual-env: ## Clear Poetry virtual environments
	@rm -rf .venv
	@echo Cleared.

.PHONY: deps
deps: ## Update and install pyproject.toml dependencies on the virtual environment
	@${POETRY_DEV} deps

.PHONY: typecheck
typecheck: ## Check for Python static type errors
	@${POETRY_DEV} types

.PHONY: fmtcheck
fmtcheck: ## Validate Python code format and sort imports
	@${POETRY_DEV} fmt --check-only

.PHONY: fmt
fmt: ## Format Python code using Black style and sort imports
	@${POETRY_DEV} fmt

.PHONY: test
test: ## Run tests suite
	@${POETRY_DEV} test

.PHONY: test-coverage-html
test-coverage-html: ## Run tests suite with HTML coverage report
	@${POETRY_DEV} test --coverage-type html

.PHONY: test-coverage-xml
test-coverage-xml: ## Run tests suite with XML coverage report (for app.codecov.io)
	@${POETRY_DEV} test --coverage-type xml

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
