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