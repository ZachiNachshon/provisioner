#!/bin/bash

# Title         Join a remote node as a k3s agent
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Install k3s agent on a remote machine
#==============================================================================
is_agent_installed() {
  systemctl list-units --full -all | grep -Fq "k3s-agent.service"
}

main() {
  if is_agent_installed; then
    echo "K3s agent is already installed and running."
  else
    curl -sfL http://get.k3s.io | K3S_URL=https://"${MASTER_IP_ADDRESS}":6443 K3S_TOKEN="${MASTER_JOIN_TOKEN}" sh -
  fi
}

main "$@"