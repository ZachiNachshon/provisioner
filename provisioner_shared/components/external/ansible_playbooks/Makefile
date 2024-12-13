default: help

ROOT_RELATIVE_PATH=../../../..

.PHONY: copy-shell-script-lib
copy-shell-script-lib: ## Copy the common/shell_lib.sh to all playbooks roles
	@echo "\n========= PLAYBOOK: ANCHOR ===============================\n"
	@cd playbooks/roles/anchor/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: DHCP STATIC IP =======================\n"
	@cd playbooks/roles/dhcp_static_ip/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: DOCKER ===============================\n"
	@cd playbooks/roles/docker/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: GIT ==================================\n"
	@cd playbooks/roles/git/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: HELLO WORLD ==========================\n"
	@cd playbooks/roles/hello_world/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: K3S ==================================\n"
	@cd playbooks/roles/k3s/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: PROVISIONER ==========================\n"
	@cd playbooks/roles/provisioner/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: RPI_CONFIG_NETWORK ===================\n"
	@cd playbooks/roles/rpi_config_network/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}
	@echo "\n========= PLAYBOOK: RPI_CONFIG_NODE ======================\n"
	@cd playbooks/roles/rpi_config_node/files; cp ../../../common/shell_lib.sh shell_lib.sh; cd ${ROOT_RELATIVE_PATH}

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
