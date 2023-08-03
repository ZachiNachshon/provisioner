default: help

SHFMT_RUNNER=./runner/shfmt/shfmt.sh
ANSIBLE_RUNNER=./runner/ansible/ansible.sh
POETRY_RUNNER=./runner/poetry/poetry.sh
PROJECT_LOCATION=.

.PHONY: fmt
fmt: ## Format shell scripts using shfmt bash style (https://github.com/mvdan/sh)
	@${SHFMT_RUNNER} \
  		"working_dir: $(PWD)" \
  		"shfmt_args: -w -ci -i=2 -ln=bash ${PROJECT_LOCATION}" \
  		"debug"

.PHONY: ansible
ansible: ## Run Ansible runner main CLI menu
	@${ANSIBLE_RUNNER} "working_dir:$(PWD)" "verbose" $(PWD) "--help"

.PHONY: poetry
poetry: ## Run Poetry runner main CLI menu
	@${POETRY_RUNNER} "working_dir:$(PWD)" "verbose" "prod" $(PWD) "--help"

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
