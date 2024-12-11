#!/bin/bash

set -e

create_local_bin_folder() {
  if [[ ! -d "${local_bin_folder}" ]]; then
    echo "Missing local bin directory, creating directory. path: ${local_bin_folder}"
    mkdir -p "${local_bin_folder}"
  else
    echo "Local bin directory already exists. path: ${local_bin_folder}"
  fi

  if ! grep -q -w "${local_bin_folder}" "${rc_file_path}"; then
    echo "Adding PATH export statement to RC file. file: ${rc_file_path}, exported_path: ${local_bin_folder}"
    # Add this line to the *rc file (zshrc, bashrc etc..)
    echo "export PATH=${local_bin_folder}:${PATH}" >> "${rc_file_path}"
  else
    echo "RC file already exports the local bin directory to PATH. rc_file: ${rc_file_path}"
  fi

  echo "Local bin directory is properly set up. path: ${local_bin_folder}"
}

remove_local_bin_folder() {
  echo "Not implemented..."
  exit 1
}

# Some scripts that require sourcing of .bashrc file, 
# should run the following (force interactive):
#  - shell: bash -ilc "<COMMAND>"
# Ansible is running bash by default non-interactively, 
# .bashrc identify such case and skip itself from being sourced
source_local_bin() {
  if [[ "${PATH}" != *"${local_bin_folder}"* ]]; then
    export PATH="${local_bin_folder}:${PATH}"
    echo "Temporary exported bin folder to PATH. path: ${local_bin_folder}"
  else
    echo "PATH already exports local bin folder. path: ${local_bin_folder}"
  fi
}

is_install() {
  [[ "${task_action}" == "install" ]]
}

is_uninstall() {
  [[ "${task_action}" == "uninstall" ]]
}

verify_mandatory_variables() {
  if [[ -z "${local_bin_folder}" ]]; then
      echo "missing mandatory argument. name: local_bin_folder"
      exit 1
  fi

  if [[ -z "${rc_file_path}" ]]; then
      echo "missing mandatory argument. name: rc_file_path"
      exit 1
  fi
}

main() {
  local task_action=$1
  local local_bin_folder=$2
  local rc_file_path=$3

  if is_install; then

    verify_mandatory_variables
    create_local_bin_folder
    source_local_bin

  elif is_uninstall; then

    remove_local_bin_folder
    
  else
    echo "Invalid playbook action flag, supported flags: install, uninstall."
    exit 1
  fi
}

main "$@"