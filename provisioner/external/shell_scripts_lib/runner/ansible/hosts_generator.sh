#!/bin/bash

# Title         Ansible hosts file generator
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Generate an Ansible hosts file based on parameters
#==================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
RUNNER_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")
ROOT_FOLDER_ABS_PATH=$(dirname "${RUNNER_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/cmd.sh"

HOSTS_FORMAT=$(
  cat <<EOM
#
# THIS FILE IS BEING AUTO GENERATED BEFORE EVERY ANSIBLE RUN
#

[all:vars]
ansible_connection=ssh

# The RPi remote user (default: pi)
ansible_user=%s

# Authentication Options:
#   - Private SSH key local file path
#   - Remote machine user password
%s

# These are the user selected hosts from the prompted selection menu
[selected_hosts]
%s

EOM
)

generate_hosts_file() {
  local hosts_file_name=$1
  local destination_path=$2

  if ! is_directory_exist "${destination_path}"; then
    mkdir -p "${destination_path}"
  fi

  local auth_param=""
  if [[ -n "${PARAM_ANSIBLE_PASSWORD}" ]]; then
    auth_param="ansible_ssh_pass=${PARAM_ANSIBLE_PASSWORD}"
  elif [[ -n "${PARAM_ANSIBLE_SSH_PRIVATE_KEY_FILE_PATH}" ]]; then
    auth_param="ansible_ssh_private_key_file=${PARAM_ANSIBLE_SSH_PRIVATE_KEY_FILE_PATH}"
  fi

  local generated_hosts=$(printf "${HOSTS_FORMAT}" \
    "${PARAM_ANSIBLE_USERNAME}" \
    "${auth_param}" \
    "${PARAM_ANSIBLE_SELECTED_HOSTS}")

  local hosts_file_path="${destination_path}/${hosts_file_name}"
  cmd_run "echo \"${generated_hosts}\" >${hosts_file_path}"
  log_debug "Generated Ansible hosts file. path: ${hosts_file_path}"
}
