default: help

POETRY_WRAPPER=./poetry_runner.sh
POETRY_WRAPPER_DEV=./poetry_runner_dev.sh
PROJECT_LOCATION=.

# @rm -rf ${HOME}/Library/Caches/pypoetry

.PHONY: clear-virtual-env
clear-virtual-env: ## Clear Poetry virtual environments
	@rm -rf .venv

.PHONY: create-dev-env
create-dev-env: ## Create/Update a Python virtual env for development
	@${POETRY_WRAPPER_DEV} update  # Update latest changes in pyproject.toml lock file
	@${POETRY_WRAPPER_DEV} install # Download and install dependencies
	@${POETRY_WRAPPER_DEV} build   # Build a tarball package with local Python wheel

.PHONY: fmt
fmt: ## Format Python code using Black style (https://black.readthedocs.io)
	@${POETRY_WRAPPER_DEV} run black ${PROJECT_LOCATION}

.PHONY: fmtcheck
fmtcheck: ## Validate Python code format with Black style standards (https://black.readthedocs.io)
	@${POETRY_WRAPPER_DEV} run black ${PROJECT_LOCATION} --check

.PHONY: typecheck
typecheck: ## Check for Python static types errors (https://mypy.readthedocs.io/en/stable/index.html)
	@${POETRY_WRAPPER_DEV} run mypy tools/**/*.py

.PHONY: test
test: fmtcheck ## Run Unit/E2E/IT tests
	@echo "Cleaning up previous runs..."
	-@rm -rf "$(PWD)/htmlcov"
	@echo "Done."
	@echo "\nRunning tests/coverage..."
	-@${POETRY_WRAPPER_DEV} run coverage run -m pytest 
	-@${POETRY_WRAPPER} run coverage report
	-@${POETRY_WRAPPER} run coverage html
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
