default: help
POETRY_DEV=external/shell_scripts_lib/python/poetry_dev.sh
POETRY_PIP_RELEASER=external/shell_scripts_lib/python/poetry_pip_releaser.sh

PROJECTS=provisioner provisioner_features_lib
PLUGINS=examples installers single_board
PLUGINS_ROOT_FOLDER=plugins

# Generate SSH key for GitHub action:
#  1. On local machine: ssh-keygen -t ed25519 -C "GitHub Actions"
#  2. Add the public key as a deploy key to the repository you want to access:
#     - Go to the repository’s settings page on GitHub.
#     - Click on “Deploy keys” in the left sidebar.
#     - Click on “Add deploy key”.
#     - Enter a title for the key and paste the contents of the public key file into the “Key” field.
#     - Click on “Add key”.
#  3. Add the private key as a secret in the repository running the workflow:
#     - Go to the repository’s settings page on GitHub.
#     - Click on “Secrets” in the left sidebar and then "Actions".
#     - Click on “New repository secret”.
#     - Enter a name for the secret, such as SSH_PRIVATE_KEY, and paste the contents of the private key file into the “Value” field.
#     - Click on “Add secret”.
#  4. Copy the code snippet from .github/workflows/ci.yaml SSH loading step

.PHONY: update-externals-all
update-externals-all: ## Update external source dependents
	@echo "\n========= ROOT FOLDER ==============\n"
	@git-deps-syncer sync shell_scripts_lib -y
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; make update-externals; cd ..

.PHONY: deps-all
deps-all: ## Update and install pyproject.toml dependencies on all virtual environments
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make deps; cd ..; \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make deps; cd ../..; \
	done

.PHONY: typecheck-all
typecheck-all: ## Check for Python static type errors
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make typecheck; cd ..; \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make typecheck; cd ../..; \
	done

.PHONY: fmtcheck-all
fmtcheck-all: ## Validate Python code format and sort imports
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make fmtcheck; cd ..; \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make fmtcheck; cd ../..; \
	done

.PHONY: fmt-all
fmt-all: ## Format Python code using Black style and sort imports
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make fmt; cd ..; \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make fmt; cd ../..; \
	done

.PHONY: test-all
test-all: ## Run tests suite
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make test; cd ..; \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make test; cd ../..; \
	done
	@echo "\n\n========= COMBINING COVERAGE DATABASES ==============\n\n"
	@coverage combine \
		provisioner/.coverage \
		provisioner_features_lib/.coverage \
		${PLUGINS_ROOT_FOLDER}/provisioner_examples_plugin/.coverage \
		${PLUGINS_ROOT_FOLDER}/provisioner_installers_plugin/.coverage \
		${PLUGINS_ROOT_FOLDER}/provisioner_single_board_plugin/.coverage
	@echo "\n\n========= COVERAGE FULL REPORT ======================\n\n"		
	@coverage report
	@coverage html
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

.PHONY: test-coverage-xml-all
test-coverage-xml-all: ## Run Unit/E2E/IT tests
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make test-coverage-xml; cd ..; \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make test-coverage-xml; cd ../..; \
	done

.PHONY: enable-provisioner-dependency
enable-provisioner-dependency: ## Enable provisioner as a direct dependency to all Python modules
	@for project in $(PROJECTS); do \
		if [ "$$project" != "provisioner" ]; then \
			echo "\n========= PROJECT: $$project ==============\n"; \
			cd $${project}; sed -i '/# provisioner = { path = "..\/provisioner", develop = true }/s/^# //' pyproject.toml; cd ..; \
		fi \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; sed -i '/# provisioner = { path = "..\/..\/provisioner", develop = true }/s/^# //' pyproject.toml; cd ../..; \
	done

.PHONY: pip-install
pip-install: ## Install provisioner sdist to local pip
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; make pip-install; cd ..

.PHONY: pip-install-plugins
pip-install-plugins: ## Install all plugins source distributions to local pip
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make pip-install; cd ../..; \
	done

.PHONY: pip-uninstall
pip-uninstall: ## Uninstall provisioner from local pip
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; make pip-uninstall; cd ..

.PHONY: pip-uninstall-plugins
pip-uninstall-plugins: ## Uninstall all plugins source distributions from local pip
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make pip-uninstall; cd ../..; \
	done

.PHONY: pip-publish-github
pip-publish-github: ## Publish all pip packages tarballs as GitHub releases
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; make pip-publish-github; cd ..

.PHONY: pip-publish-plugins-github
pip-publish-plugins-github: ## Publish all plugins pip packages tarballs as GitHub releases
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make pip-publish-github; cd ../..; \
	done

.PHONY: clear-virtual-env-all
clear-virtual-env-all: ## Clear all Poetry virtual environments
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make clear-virtual-env; cd ..; \
	done
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd ${PLUGINS_ROOT_FOLDER}/provisioner_$${plugin}_plugin; make clear-virtual-env; cd ../..; \
	done

# http://localhost:9001/provisioner/
.PHONY: docs-site
docs-site: ## Run a local documentation site
	@${POETRY_DEV} docs

# http://192.168.x.xx:9001/
.PHONY: docs-site-lan
docs-site-lan: ## Run a local documentation site (LAN available)
	@${POETRY_DEV} docs --lan

.PHONY: pDev
pDev: ## Interact with ./external/.../poetry_dev.sh            (Usage: make pDev 'fmt --check-only')
	@${POETRY_DEV} $(filter-out $@,$(MAKECMDGOALS))

.PHONY: pReleaser
pReleaser: ## Interact with ./external/.../poetry_pip_releaser.sh   (Usage: make pReleaser 'install --build-type sdist --multi-project')
	@${POETRY_PIP_RELEASER} $(filter-out $@,$(MAKECMDGOALS))

# .PHONY: diagrams
# diagrams: ## Format Python code using Black style (https://black.readthedocs.io)
# 	@${POETRY_WRAPPER_DEV} run diagrams ${PROJECT_LOCATION}/rpi/os/diagrams/install_diag.py

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
