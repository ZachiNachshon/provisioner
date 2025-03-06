default: help
POETRY_DEV=external/shell_scripts_lib/python/poetry_dev.sh
POETRY_PIP_RELEASER=external/shell_scripts_lib/python/poetry_pip_releaser.sh
PLUGINS_ROOT_FOLDER=plugins

# Generate SSH key for GitHub action of a repository with required access to another repository:
#  1. Go to user 'Settings' -> 'Developer Settings' -> 'Personal Access Token':
#     - Select Token (Classic)
#     - Generate new token on the classic mode with full 'repo' scope
#     - Copy the GitHub PAT secret
#  2. Add the private key as a secret in the repository running the workflow:
#     - Go to the repository’s settings page on GitHub.
#     - Click on “Secrets and variables” in the left sidebar and then "Actions".
#     - Click on “New repository secret”.
#     - Enter a name for the secret, such as MY_REPO_ACCESS_TOKEN, and paste the contents of the private key file into the “Value” field.
#     - Click on “Add secret”.
#  3. On the GitHub workflow use is as:
#     - token: ${{ secrets.MY_REPO_ACCESS_TOKEN }}

.PHONY: prod-mode
prod-mode: ## Enable production mode for packaging and distribution
	@poetry self add poetry-multiproject-plugin
	@./scripts/switch_mode.py prod
	@poetry lock

.PHONY: dev-mode
dev-mode: ## Enable local development
	@pip3 install tomlkit --disable-pip-version-check --no-python-version-warning
	@./scripts/switch_mode.py dev --force
	@poetry lock

.PHONY: deps-install
deps-install: ## Update and install pyproject.toml dependencies on all virtual environments
	@poetry install --with dev --sync -v
	@poetry lock
	
.PHONY: run
run: ## Run provisioner CLI from sources (Usage: make run 'config view')
	@poetry run provisioner $(filter-out $@,$(MAKECMDGOALS))
	
.PHONY: typecheck
typecheck: ## Check for Python static type errors
	@poetry run mypy $(PWD)/*/**/*.py

.PHONY: fmtcheck
fmtcheck: ## Validate Python code format and sort imports
	@poetry run black . --check
	@poetry run ruff check . --show-fixes

.PHONY: fmt
fmt: ## Format Python code using Black style and sort imports
	@poetry run black . 
	@poetry run ruff check . --show-fixes --fix

# .PHONY: test-all
# test-all: ## Run full tests suite on host, Unit/IT/E2E (output: None)
# 	@poetry run coverage run -m pytest

.PHONY: test-all-in-container
test-all-in-container: ## Run full tests suite in a Docker container, Unit/IT/E2E (output: None)
	@./run_in_docker.py
	
.PHONY: test-skip-e2e
test-skip-e2e: ## Run only Unit/IT tests
	@poetry run coverage run -m pytest --skip-e2e

.PHONY: test-e2e
test-e2e: ## Run only E2E tests in a Docker container
	@./run_in_docker.py --only-e2e

.PHONY: test-coverage-html
test-coverage-html: ## Run tests suite on runtime and all plugins, use 'e2e' to run only E2E tests (output: HTML report)
	@if [ -n "$(word 2, $(MAKECMDGOALS))" ]; then \
		echo "Running tests IT/Unit/E2E (with coverage report)"; \
		poetry run coverage run -m pytest --only-e2e; \
	else \
		echo "Running tests IT/Unit (with coverage report)"; \
		poetry run coverage run -m pytest; \
	fi;
	if [ $$? -ne 0 ]; then \
		exit 1; \
	fi;
	@echo "\n\n========= COVERAGE FULL REPORT ======================\n\n"		
	@poetry run coverage report
	@poetry run coverage html
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

# This is the command used by GitHub Actions to run the tests
# It must fail the GitHub action step if any of the tests fail
# This is the reason we're performing an exist code check since it
# is a makefile that runs other makefiles within a for loop
.PHONY: test-coverage-xml
test-coverage-xml: ## Run tests suite on runtime and all plugins (output: XML report)
	@poetry run coverage run -m pytest; \
	if [ $$? -ne 0 ]; then \
		exit 1; \
	fi; 
	@echo "\n\n========= COVERAGE FULL REPORT ======================\n\n"		
	@poetry run coverage report
	@poetry run coverage xml
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/coverage.xml\n"

.PHONY: pip-install-runtime
pip-install-runtime: ## [LOCAL] Install provisioner runtime to local pip
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; poetry build-project -f sdist; cd ..
	@pip3 install provisioner/dist/provisioner_*.tar.gz	

# @cd provisioner; poetry build-project -f wheel; cd ..
# @pip3 install provisioner/dist/provisioner_*.whl

# @cd provisioner; poetry build-project -f sdist; cd ..
# @pip3 install provisioner/dist/provisioner_*.tar.gz	

.PHONY: pip-install-plugin
pip-install-plugin: ## [LOCAL] Install any plugin to local pip (make pip-install-plugin examples)
	@if [ -z "$(word 2, $(MAKECMDGOALS))" ]; then \
		echo "Error: plugin name is required. Usage: make pip-install-plugin <plugin_name>"; \
		exit 1; \
	fi
	@PLUGIN=$(word 2, $(MAKECMDGOALS)); \
	echo "\n========= PLUGIN: $$PLUGIN ==============\n"; \
	cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${PLUGIN}_plugin; poetry build-project -f sdist; cd ../..; \
	pip3 install ${PLUGINS_ROOT_FOLDER}/provisioner_$${PLUGIN}_plugin/dist/provisioner_*.tar.gz;

# cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${PLUGIN}_plugin; poetry build-project -f wheel; cd ../..; \
# pip3 install ${PLUGINS_ROOT_FOLDER}/provisioner_$${PLUGIN}_plugin/dist/provisioner_*.whl;

.PHONY: pip-uninstall-runtime
pip-uninstall-runtime: ## [LOCAL] Uninstall provisioner from local pip
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; pip3 uninstall -y provisioner_shared provisioner_runtime; cd ..

.PHONY: pip-uninstall-plugin
pip-uninstall-plugin: ## [LOCAL] Uninstall any plugins source distributions from local pip (make pip-uninstall-plugin example)
	@if [ -z "$(word 2, $(MAKECMDGOALS))" ]; then \
		echo "Error: plugin name is required. Usage: make pip-uninstall-plugin <plugin_name>"; \
		exit 1; \
	fi
	@PLUGIN=$(word 2, $(MAKECMDGOALS)); \
	echo "\n========= PLUGIN: $$PLUGIN ==============\n"; \
	pip3 uninstall -y provisioner_$${PLUGIN}_plugin;

.PHONY: clear-project
clear-project: ## Clear Poetry virtual environments and clear Python cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@poetry env remove --all

# http://localhost:9001/provisioner/
.PHONY: docs-site
docs-site: ## Run a local documentation site (required: npm, hugo)
	@cd docs-site; npm run docs-serve; cd-

# http://192.168.x.xx:9001/
.PHONY: docs-site-lan
docs-site-lan: ## Run a local documentation site with LAN available (required: npm, hugo)
	@cd docs-site; npm run docs-serve-lan; cd-

# 
# To add a submodule for the first time to an existing repository:
# 
#  git submodule add git@github.com:ZachiNachshon/provisioner-plugins.git plugins
# 
.PHONY: plugins-init
plugins-init: ## Initialize Provisioner Plugins git-submodule (only on fresh clone)
	@cd plugins; \
	git submodule init; \
	git submodule update; \

.PHONY: plugins-status
plugins-status: ## Show plugins submodule status (commit-hash)
	@git submodule status plugins

.PHONY: plugins-fetch
plugins-fetch: ## Prompt for Provisioner Plugins commit-hash to update the sub-module
	@read -p "Enter Provisioner Plugins git repo commit hash (dont forget to git push afterwards): " arg; \
	cd plugins; \
	git fetch; \
	git checkout $$arg; \
	cd ..; \
	git add plugins; \
	git commit -m "Update Provisioner Plugins to $$arg"; \

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

