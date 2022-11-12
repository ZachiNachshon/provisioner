#!/bin/bash

# Title         Ansible playbook runner
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Run an Ansible playbook using local ansible or run via Docker container
#==============================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
RUNNER_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")
ROOT_FOLDER_ABS_PATH=$(dirname "${RUNNER_FOLDER_ABS_PATH}")

source "${CURRENT_FOLDER_ABS_PATH}/hosts_generator.sh"
source "${RUNNER_FOLDER_ABS_PATH}/base/runner_dockerized.sh"
source "${ROOT_FOLDER_ABS_PATH}/props.sh"
source "${ROOT_FOLDER_ABS_PATH}/paths.sh"

PROPERTIES_FOLDER_PATH=${ROOT_FOLDER_ABS_PATH}/runner/ansible
DEPENDENCY_FOLDER_NAME="shell_scripts_lib"

PARAM_ANSIBLE_WORKING_DIR=""
PARAM_ANSIBLE_SELECTED_HOSTS=""
PARAM_ANSIBLE_PASSWORD=""
PARAM_ANSIBLE_SSH_PRIVATE_KEY_FILE_PATH=""
PARAM_ANSIBLE_USERNAME=""
PARAM_ANSIBLE_PLAYBOOK_PATH=""
PARAM_ANSIBLE_ANSIBLE_VARS=""
PARAM_ANSIBLE_ANSIBLE_TAGS=""

PROP_ANSIBLE_CLI_NAME=""
PROP_ANSIBLE_VERSION=""
PROP_ANSIBLE_IMAGE_NAME=""
PROP_ANSIBLE_CONTAINER_WORKING_DIR=""
PROP_ANSIBLE_HOSTS_FILE_NAME=""

PATTERN_ANSIBLE_CLI_BINARY_FOLDER=""
PATTERN_ANSIBLE_LOCALHOST_CONFIG_FOLDER=""

copy_ansible_config_to_config_folder() {
  local localhost_ansible_config_path="${PATTERN_ANSIBLE_LOCALHOST_CONFIG_FOLDER}/config"
  if is_directory_exist "${localhost_ansible_config_path}" && [[ "${localhost_ansible_config_path}" == *ansible/config* ]]; then
    log_debug "Removing previous Ansible configuration..."
    cmd_run "rm -rf ${localhost_ansible_config_path}"
  fi

  local runner_ansible_config_folder=$(get_external_folder_dependency_path \
    "${PARAM_ANSIBLE_WORKING_DIR}" \
    "${DEPENDENCY_FOLDER_NAME}" \
    "runner/ansible/config")

  log_debug "Copying Ansible configuration. path: ${localhost_ansible_config_path}"
  cmd_run "cp -a ${runner_ansible_config_folder} ${localhost_ansible_config_path}"
}

generate_runner_args() {
  local hosts_file_path_localhost=$1
  local hosts_file_path_dockerized=$2

  # Local host
  local hosts_file_path="${hosts_file_path_localhost}"

  # Path to the hosts file depends on where Ansible is being executed, on hosts machine or dockerized
  if ! is_tool_exist "${PROP_ANSIBLE_CLI_NAME}"; then
    hosts_file_path="${hosts_file_path_dockerized}"
  fi

  local resolved_runner_args=$(generate_ansible_playbook_args "${hosts_file_path}")
  echo "${resolved_runner_args}"
}

generate_ansible_playbook_args() {
  local hosts_file_path=$1

  # usage: ansible-playbook [-h] [--version] [-v] [--private-key PRIVATE_KEY_FILE]
  #                      [-u REMOTE_USER] [-c CONNECTION] [-T TIMEOUT]
  #                      [--ssh-common-args SSH_COMMON_ARGS]
  #                      [--sftp-extra-args SFTP_EXTRA_ARGS]
  #                      [--scp-extra-args SCP_EXTRA_ARGS]
  #                      [--ssh-extra-args SSH_EXTRA_ARGS]
  #                      [-k | --connection-password-file CONNECTION_PASSWORD_FILE]
  #                      [--force-handlers] [--flush-cache] [-b]
  #                      [--become-method BECOME_METHOD]
  #                      [--become-user BECOME_USER]
  #                      [-K | --become-password-file BECOME_PASSWORD_FILE]
  #                      [-t TAGS] [--skip-tags SKIP_TAGS] [-C]
  #                      [--syntax-check] [-D] [-i INVENTORY] [--list-hosts]
  #                      [-l SUBSET] [-e EXTRA_VARS] [--vault-id VAULT_IDS]
  #                      [--ask-vault-password | --vault-password-file VAULT_PASSWORD_FILES]
  #                      [-f FORKS] [-M MODULE_PATH] [--list-tasks]
  #                      [--list-tags] [--step] [--start-at-task START_AT_TASK]
  #                      playbook [playbook ...]

  local verbose=""
  if is_verbose; then
    verbose="-vvv"
  fi

  local auth_cli_arg=""
  if [[ -n "${PARAM_ANSIBLE_PASSWORD}" ]]; then
    auth_cli_arg="-e ansible_ssh_pass=${PARAM_ANSIBLE_PASSWORD}"
  elif [[ -n "${PARAM_ANSIBLE_SSH_PRIVATE_KEY_FILE_PATH}" ]]; then
    auth_cli_arg="-e ansible_ssh_private_key_file=${PARAM_ANSIBLE_SSH_PRIVATE_KEY_FILE_PATH}"
  fi

  local runner_args="-i ${hosts_file_path} ${verbose} \
${PROP_ANSIBLE_CONTAINER_WORKING_DIR}/${PARAM_ANSIBLE_PLAYBOOK_PATH} \
-e ansible_user=${PARAM_ANSIBLE_USERNAME} \
${auth_cli_arg} \
-e local_bin_folder=${PATTERN_ANSIBLE_CLI_BINARY_FOLDER} \
${PARAM_ANSIBLE_ANSIBLE_VARS} \
${PARAM_ANSIBLE_ANSIBLE_TAGS}"

  echo "${runner_args}"
}

parse_ansible_arguments() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      working_dir*)
        PARAM_ANSIBLE_WORKING_DIR=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      selected_host*)
        selected_host=$(cut -d : -f 2- <<<"${1}" | xargs)
        # Force new line at the end
        PARAM_ANSIBLE_SELECTED_HOSTS+="${selected_host} 
"
        shift
        ;;
      password*)
        PARAM_ANSIBLE_PASSWORD=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      ssh_private_key_file_path*)
        PARAM_ANSIBLE_SSH_PRIVATE_KEY_FILE_PATH=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      username*)
        PARAM_ANSIBLE_USERNAME=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      playbook_path*)
        PARAM_ANSIBLE_PLAYBOOK_PATH=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      ansible_var*)
        # Do not user xargs in here to allow Ansible vars with spaces
        # Example: "var_name='This is a var with space'"
        ansible_var_kv_pair=$(cut -d : -f 2- <<<"${1}")
        PARAM_ANSIBLE_ANSIBLE_VARS+="-e ${ansible_var_kv_pair} "
        shift
        ;;
      ansible_tag*)
        if [[ -z "${PARAM_ANSIBLE_ANSIBLE_TAGS}" ]]; then
          PARAM_ANSIBLE_ANSIBLE_TAGS="--tags "
          TAGS_SEP=""
        fi
        ansible_tag_kv_pair=$(cut -d : -f 2- <<<"${1}" | xargs)
        PARAM_ANSIBLE_ANSIBLE_TAGS+="${TAGS_SEP}${ansible_tag_kv_pair}"
        TAGS_SEP=","
        shift
        ;;
      --force-dockerized)
        # Used by runner_dockerized.sh
        export PARAM_FORCE_DOCKERIZED="true"
        shift
        ;;
      --dry-run)
        # Used by logger.sh
        export LOGGER_DRY_RUN="true"
        shift
        ;;
      -y)
        # Used by prompter.sh
        export PROMPTER_SKIP_PROMPT="y"
        shift
        ;;
      -v | --verbose)
        # Used by logger.sh
        export LOGGER_VERBOSE="true"
        shift
        ;;
      -s | --silent)
        # Used by logger.sh
        export LOGGER_SILENT="true"
        shift
        ;;
      *)
        break
        ;;
    esac
  done
}

verify_ansible_arguments() {
  if [[ -z "${PARAM_ANSIBLE_WORKING_DIR}" ]]; then
    log_fatal "Missing mandatory param. name: working_dir"
  elif ! is_directory_exist "${PARAM_ANSIBLE_WORKING_DIR}"; then
    log_fatal "Invalid working directory. path: ${PARAM_ANSIBLE_WORKING_DIR}"
  fi

  if [[ -z "${PARAM_ANSIBLE_SELECTED_HOSTS}" ]]; then
    log_fatal "Missing mandatory param. name: selected_host"
  fi

  if [[ -z "${PARAM_ANSIBLE_PLAYBOOK_PATH}" ]]; then
    log_fatal "Missing mandatory param. name: playbook_path"
  fi
}

resolve_required_properties() {
  PROP_ANSIBLE_CLI_NAME=$(property "${PROPERTIES_FOLDER_PATH}" "runner.ansible.cli.name")
  PROP_ANSIBLE_VERSION=$(property "${PROPERTIES_FOLDER_PATH}" "runner.ansible.version")
  PROP_ANSIBLE_IMAGE_NAME=$(property "${PROPERTIES_FOLDER_PATH}" "runner.ansible.container.image.name")
  PROP_ANSIBLE_CONTAINER_WORKING_DIR=$(property "${PROPERTIES_FOLDER_PATH}" "runner.ansible.container.working_dir")
  PROP_ANSIBLE_HOSTS_FILE_NAME=$(property "${PROPERTIES_FOLDER_PATH}" "runner.ansible.hosts_file.name")
}

resolve_required_patterns() {
  PATTERN_ANSIBLE_CLI_BINARY_FOLDER=$(pattern "${PROPERTIES_FOLDER_PATH}" "runner.ansible.cli.binary_folder" "${PARAM_ANSIBLE_USERNAME}")
  PATTERN_ANSIBLE_LOCALHOST_CONFIG_FOLDER=$(pattern "${PROPERTIES_FOLDER_PATH}" "runner.ansible.localhost.config.folder")
}

####################################################################
# Run an Ansible playbook using local ansible or run via Docker container
# 
# Globals:
#   None
# 
# Arguments:
#   working_dir         - Host root working directory
#   username            - SSH remote username
#   password            - SSH remote password
#   selected_host       - (Repeating) Selected host with name identifier
#   playbook_path       - Host path of the playbook to execute
#   ansible_var         - (Repeating) Ansible variable to be used within the playbook
#   ansible_tag         - (Repeating) Ansible tag to play a specific task within the playbook
#   --force-dockerized  - Force to run the CLI runner in a dockerized container
#   --dry-run           - Run all commands in dry-run mode without file system changes
#   --verbose           - Output debug logs for commands executions
# 
# Usage:
# ./runner/ansible/ansible.sh \
#   "username: <ssh_remote_username>" \
#   "password: <ssh_remote_password>" \
#   "working_dir: /path/to/working/dir" \
#   "selected_host: kmaster ansible_host=192.168.1.200" \
#   "selected_host: knode1 ansible_host=192.168.1.201" \
#   "playbook_path: path/to/playbook.yaml" \
#   "ansible_var: key1=value1" \
#   "ansible_var: key2=value2" \
#   "ansible_tag: networking" \
#   "--force-dockerized" \
#   "--dry-run" \
#   "--verbose"
####################################################################
main() {
  parse_ansible_arguments "$@"
  verify_ansible_arguments

  resolve_required_properties
  resolve_required_patterns

  # hosts file is always generated on the localhost machine.
  # $HOME/.config/ansible/ansible_hosts
  generate_hosts_file "${PROP_ANSIBLE_HOSTS_FILE_NAME}" "${PATTERN_ANSIBLE_LOCALHOST_CONFIG_FOLDER}"
  local hosts_file_path_localhost="${PATTERN_ANSIBLE_LOCALHOST_CONFIG_FOLDER}/${PROP_ANSIBLE_HOSTS_FILE_NAME}"

  # /usr/runner/workspace/ansible_hosts
  local hosts_file_path_dockerized="${PROP_ANSIBLE_CONTAINER_WORKING_DIR}/${PROP_ANSIBLE_HOSTS_FILE_NAME}"

  # $HOME/.config/ansible/ansible_hosts:/usr/runner/workspace/ansible_hosts
  local hosts_file_volume_mount="${hosts_file_path_localhost}:${hosts_file_path_dockerized}"

  # $HOME/.config/ansible/config/:/usr/runner/workspace/config
  local config_folder_volume_mount="${PATTERN_ANSIBLE_LOCALHOST_CONFIG_FOLDER}/config:${PROP_ANSIBLE_CONTAINER_WORKING_DIR}/config"

  copy_ansible_config_to_config_folder

  local runner_args=$(generate_runner_args "${hosts_file_path_localhost}" "${hosts_file_path_dockerized}")

  run_maybe_docker \
    "working_dir: ${PARAM_ANSIBLE_WORKING_DIR}" \
    "runner_name: ${PROP_ANSIBLE_CLI_NAME}" \
    "runner_args: ${runner_args}" \
    "runner_version: ${PROP_ANSIBLE_VERSION}" \
    "docker_image: ${PROP_ANSIBLE_IMAGE_NAME}" \
    "docker_volume: ${hosts_file_volume_mount}" \
    "docker_volume: ${config_folder_volume_mount}" \
    "docker_build_context: ${ROOT_FOLDER_ABS_PATH}/runner/ansible"
}

main "$@"
