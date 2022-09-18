default: help

POETRY_WRAPPER=./common/runners/poetry_runner.sh
POETRY_WRAPPER_DEV=./common/runners/poetry_runner_dev.sh
PROJECT_LOCATION=.

# @rm -rf ${HOME}/Library/Caches/pypoetry

.PHONY: clear-virtual-env
clear-virtual-env: ## Clear Poetry virtual environments
	@rm -rf .venv

# Add -vv for debug logs
.PHONY: create-update-venv
create-update-venv: ## Create/Update a Python virtual env
	@${POETRY_WRAPPER_DEV} install # Download and install dependencies
	@${POETRY_WRAPPER_DEV} update  # Update latest changes in pyproject.toml lock file
	@${POETRY_WRAPPER_DEV} build   # Build a tarball package with local Python wheel

.PHONY: fmt
fmt: ## Format Python code using Black style (https://black.readthedocs.io)
	@${POETRY_WRAPPER_DEV} run black ${PROJECT_LOCATION}

.PHONY: fmtcheck
fmtcheck: ## Validate Python code format with Black style standards (https://black.readthedocs.io)
	@${POETRY_WRAPPER_DEV} run black ${PROJECT_LOCATION} --check

.PHONY: typecheck
typecheck: ## Check for Python static types errors (https://mypy.readthedocs.io/en/stable/index.html)
	@${POETRY_WRAPPER_DEV} run mypy */**/*.py

.PHONY: test
# test: fmtcheck ## Run Unit/E2E/IT tests
test: ## Run Unit/E2E/IT tests
	@echo "Cleaning up previous runs..."
	-@rm -rf "$(PWD)/htmlcov"
	@echo "Done."
	@echo "\nRunning tests/coverage..."
	@${POETRY_WRAPPER_DEV} run coverage run -m pytest
	@${POETRY_WRAPPER} run coverage report
	@${POETRY_WRAPPER} run coverage html
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

.PHONY: test-ci
# test-ci: fmtcheck ## Run Unit/E2E/IT tests with XML report for app.codecov.io
test-ci: ## Run Unit/E2E/IT tests with XML report for app.codecov.io
	@echo "Cleaning up previous runs..."
	-@rm -rf "$(PWD)/coverage.xml"
	@echo "Done."
	@echo "\nRunning tests/coverage..."
	@${POETRY_WRAPPER_DEV} run coverage run -m pytest
	@${POETRY_WRAPPER} run coverage report
	@${POETRY_WRAPPER} run coverage xml
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/coverage.xml\n"


.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
