default: help
PROJECTS=provisioner python_core_lib provisioner_features_lib

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

.PHONY: typecheck-all
typecheck-all: ## Check for Python static type errors
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make typecheck; cd ..; \
	done

.PHONY: fmtcheck-all
fmtcheck-all: ## Validate Python code format and sort imports
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make fmtcheck; cd ..; \
	done

.PHONY: fmt-all
fmt-all: ## Format Python code using Black style and sort imports
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make fmt; cd ..; \
	done

.PHONY: test-all
test-all: ## Run tests suite
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make test; cd ..; \
	done
	@echo "\n\n========= COMBINING COVERAGE DATABASES ==============\n\n"
	@coverage combine \
		provisioner/.coverage \
		python_core_lib/.coverage \
		provisioner_features_lib/.coverage
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

.PHONY: pip-install
pip-install: ## Install provisioner sdist to local pip
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; make pip-install; cd ..

.PHONY: pip-uninstall
pip-uninstall: ## Uninstall provisioner from local pip
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; make pip-uninstall; cd ..

.PHONY: pip-publish-github
pip-publish-github: ## Publish all pip packages tarballs as GitHub releases
	@echo "\n========= PROJECT: provisioner ==============\n"
	@cd provisioner; make pip-publish-github; cd ..

.PHONY: clear-virtual-env-all
clear-virtual-env-all: ## Clear all Poetry virtual environments
	@for project in $(PROJECTS); do \
		echo "\n========= PROJECT: $$project ==============\n"; \
		cd $${project}; make clear-virtual-env; cd ..; \
	done

# .PHONY: diagrams
# diagrams: ## Format Python code using Black style (https://black.readthedocs.io)
# 	@${POETRY_WRAPPER_DEV} run diagrams ${PROJECT_LOCATION}/rpi/os/diagrams/install_diag.py

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
