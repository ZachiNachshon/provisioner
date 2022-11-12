#!/bin/bash

# Title         Install a k3s master on remote machine
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Run the k3s master install script
#==============================================================================
is_master_installed() {
  # Check differently on Linux and macOS
  systemctl list-units --full -all | grep -Fq "k3s.service"
}

main() {
  if is_master_installed; then
    echo "K3s master is already installed and running."
  else
    curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC=" --no-deploy traefik --no-deploy kubernetes-dashboard" sh -
  fi
}

main "$@"