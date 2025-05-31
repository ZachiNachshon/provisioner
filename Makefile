default: help
PYTHON_VERSION=3.11
POETRY_DEV=external/shell_scripts_lib/python/poetry_dev.sh
POETRY_PIP_RELEASER=external/shell_scripts_lib/python/poetry_pip_releaser.sh
PLUGINS_ROOT_FOLDER=plugins

# Generate SSH key for GitHub action of a repository with required access to another repository:
#  1. Go to user 'Settings' -> 'Developer Settings' -> 'Personal Access Token':
#     - Select Token (Classic)
#     - Generate new token on the classic mode with full 'repo' scope
#     - Copy the GitHub PAT secret
#  2. Add the private key as a secret in the repository running the workflow:
#     - Go to the repository's settings page on GitHub.
#     - Click on "Secrets and variables" in the left sidebar and then "Actions".
#     - Click on "New repository secret".
#     - Enter a name for the secret, such as MY_REPO_ACCESS_TOKEN, and paste the contents of the private key file into the "Value" field.
#     - Click on "Add secret".
#  3. On the GitHub workflow use is as:
#     - token: ${{ secrets.MY_REPO_ACCESS_TOKEN }}

.PHONY: init
init: ## Initialize project using uv package manager
	@uv venv --python $(PYTHON_VERSION)
	@source .venv/bin/activate
	@source .venv/bin/python -m ensurepip --upgrade
	@source .venv/bin/pip3 install --upgrade pip setuptools wheel
	@poetry self add poetry-multiproject-plugin

.PHONY: prod-mode
prod-mode: ## Enable production mode for packaging and distribution
	@poetry self add poetry-multiproject-plugin
	@./scripts/switch_mode.py prod
	@poetry lock

.PHONY: dev-mode-sources
dev-mode-sources: ## Enable local development from sources using abs file path on pyproject.toml
	@pip3 install tomlkit --disable-pip-version-check --no-python-version-warning
	@./scripts/switch_mode.py dev --force
	@poetry lock

.PHONY: deps-install
deps-install: ## Update and install pyproject.toml dependencies on all virtual environments
	@poetry lock
	@poetry install --with dev --sync -v
	@poetry lock
	
# .PHONY: dev-mode-pip-sdists
# dev-mode-pip-sdists: ## Enable local development from built sdists into project .venv
# 	@rm -rf provisioner_shared/dist
# 	@cd provisioner_shared; poetry build-project -f sdist; cd ..
# 	@mv provisioner_shared/dist/provisioner_shared*.tar.gz dockerfiles/poetry/dists/
# 	@rm -rf provisioner/dist
# 	$(MAKE) pip-install-runtime
# 	@mv provisioner/dist/provisioner*.tar.gz dockerfiles/poetry/dists/
# 	@rm -rf plugins/provisioner_installers_plugin/dist
# 	@cd plugins/provisioner_installers_plugin; poetry build-project -f sdist; cd ../..
# 	@mv plugins/provisioner_installers_plugin/dist/provisioner_*_plugin*.tar.gz dockerfiles/poetry/dists/

# $(MAKE) prod-mode
# @./.venv/bin/pip3 install provisioner_shared/dist/provisioner_shared*.tar.gz
# @rm -r plugins/provisioner_examples_plugin/dist
# $(MAKE) "pip-install-plugin examples"
# @rm -r plugins/provisioner_single_board_plugin/dist
# $(MAKE) "pip-install-plugin single-board"

.PHONY: run
run: ## Run provisioner CLI from sources (Usage: make run 'config view')
	@poetry run provisioner $(filter-out $@,$(MAKECMDGOALS))

# Another alternative to run a installed provisioner CLI
# ./.venv/bin/provisioner -h
	
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

.PHONY: test-all-in-container
test-all-in-container: ## Run full tests suite in a Docker container, Unit/IT/E2E (output: none)
	@./run_tests.py --all --container --report
	
.PHONY: test-skip-e2e
test-skip-e2e: ## Run only Unit/IT tests
	@./run_tests.py --all --skip-e2e

.PHONY: test-e2e
test-e2e: ## Run only E2E tests in a Docker container
	@./run_tests.py --all --only-e2e

.PHONY: test-coverage-html
test-coverage-html: ## Run tests suite on runtime and all plugins (output: HTML report)
	@./run_tests.py --all --container --report html

# This is the command used by GitHub Actions to run the tests
# It must fail the GitHub action step if any of the tests fail
# This is the reason we're performing an exist code check since it
# is a makefile that runs other makefiles within a for loop
# TODO: Need to separate the tests Docker image creation into a separate step
# 		  and do not build from scratch each time
.PHONY: test-coverage-xml
test-coverage-xml: ## Run tests suite on runtime and all plugins NO E2E (output: XML report)
	./run_tests.py --all --skip-e2e --report xml

.PHONY: pip-install-runtime
pip-install-runtime: ## [LOCAL] Install provisioner runtime to global pip
	@./scripts/install_locally.sh install runtime wheel

.PHONY: pip-install-plugin
pip-install-plugin: ## [LOCAL] Install any plugin to global pip (make pip-install-plugin examples)
	@./scripts/install_locally.sh install plugin $(word 2, $(MAKECMDGOALS)) wheel

.PHONY: pip-uninstall-runtime
pip-uninstall-runtime: ## [LOCAL] Uninstall provisioner from global pip
	@./scripts/install_locally.sh uninstall runtime wheel

.PHONY: pip-uninstall-plugin
pip-uninstall-plugin: ## [LOCAL] Uninstall any plugins source distributions from global pip (make pip-uninstall-plugin example)
	@./scripts/install_locally.sh uninstall plugin $(word 2, $(MAKECMDGOALS)) wheel

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
	@grep -E '^[a-zA-Z0-9_-]+:.*## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

