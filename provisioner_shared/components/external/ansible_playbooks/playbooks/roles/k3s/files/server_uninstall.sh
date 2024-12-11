#!/bin/bash

# Title         Uninstall a k3s master from remote machine
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Run the k3s master uninstall script
#==============================================================================
K3S_MASTER_UNINSTALL_SCRIPT="/usr/local/bin/k3s-uninstall.sh"

is_file_exist() {
  local path=$1
  [[ -f "${path}" || $(is_symlink "${path}") ]]
}

is_symlink() {
  local abs_path=$1
  [[ -L "${abs_path}" ]]
}

main() {
  if is_file_exist "${K3S_MASTER_UNINSTALL_SCRIPT}"; then
    ${K3S_MASTER_UNINSTALL_SCRIPT}
  else
    echo "Cannot find k3s uninstall script. path: ${K3S_MASTER_UNINSTALL_SCRIPT}."
    exit 1
  fi
}

main "$@"

# is_action_uninstall_agent() {
#   [[ "${ENV_K3S_ACTION}" == "uninstall_agent" ]]
# }

# uninstall_k3s_agent() {
#   log_fatal "Uninstall action is not yet implemented"
# }

# is_action_uninstall_server() {
#   [[ "${ENV_K3S_ACTION}" == "uninstall_server" ]]
# }

# uninstall_k3s_server() {
#   log_fatal "Uninstall action is not yet implemented"
# }

# main() {
#   evaluate_run_mode
#   verify_supported_os
#   verify_mandatory_variables

#   if is_action_install_server; then
#     install_k3s_server
#   elif is_action_uninstall_server; then
#     uninstall_k3s_server
#   elif is_action_install_agent; then
#     install_k3s_agent
#   elif is_action_uninstall_agent; then
#     uninstall_k3s_agent
#   else
#     log_fatal "Invalid K3s action. value: ${ENV_K3S_ACTION}"
#   fi
# }

# main "$@"