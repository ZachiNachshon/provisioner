#!/bin/bash

# Title         Define a static IP address
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux
# Description   Define a static IP address
#==============================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

get_static_ip() {
  echo "${STATIC_IP}"
}

get_gateway_address() {
  echo "${GATEWAY_ADDRESS}"
}

get_dns_address() {
  echo "${DNS_ADDRESS}"
}

get_connection_name_for_device() {
  local device_name="$1"
  # Get the connection name associated with the device
  local connection_name=$(nmcli -t -f NAME,DEVICE con show | grep ":${device_name}$" | cut -d: -f1)
  echo "${connection_name}"
}

print_network_info() {
  new_line
  echo "=== nmcli con show ==="
  nmcli con show
  new_line
  new_line
  echo "=== nmcli dev status ==="
  nmcli dev status
}

configure_static_ip_address() {
  local static_ip_address=$(get_static_ip)
  local gateway_address=$(get_gateway_address)
  local dns_address=$(get_dns_address)
  local device_name="eth0"
  local connection_name=$(get_connection_name_for_device "${device_name}")
  
  log_info "Using connection name '${connection_name}' for device ${device_name}"

  # Configure IP Address
  log_info "Configuring static IP address: ${static_ip_address}"
  nmcli con mod "${connection_name}" ipv4.addresses ${static_ip_address}/24

  # Configure default gateway
  log_info "Configuring gateway address: ${gateway_address}"
  nmcli con mod "${connection_name}" ipv4.gateway ${gateway_address}

  # Configure DNS address
  log_info "Configuring DNS address: ${dns_address}"
  nmcli con mod "${connection_name}" ipv4.dns ${dns_address}

  # Change the addressing from DHCP to static
  nmcli con mod "${connection_name}" ipv4.method manual

  # Save changes
  log_info "Bringing up network interface: ${device_name}"
  nmcli con up "${connection_name}"
}

verify_network_interface() {
  local static_ip_address=$(get_static_ip)
  local ip_addr_output=$(ip addr)
  if ! echo "${ip_addr_output}" | grep -q "${static_ip_address}"; then
    log_fatal "Static IP address ${static_ip_address} not found in network interfaces"
  fi
  log_indicator_good "Static IP address ${static_ip_address} found in network interfaces"
}

verify_nmcli_utility() {
  if ! is_tool_exist "nmcli"; then
    log_fatal "nmcli is not installed, cannot configure static IP address"
  fi
  log_info "Found nmcli utility (NetworkManager Command Line Tool). name: nmcli"
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if ! is_dry_run && [[ "${os_type}" != "linux" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

verify_mandatory_variables() {
  if [[ -z "${STATIC_IP}" ]]; then
    log_fatal "Missing mandatory parameter. name: STATIC_IP"
  fi

  if [[ -z "${GATEWAY_ADDRESS}" ]]; then
    log_fatal "Missing mandatory parameter. name: GATEWAY_ADDRESS"
  fi

  if [[ -z "${DNS_ADDRESS}" ]]; then
    log_fatal "Missing mandatory parameter. name: DNS_ADDRESS"
  fi
}

main() {
  evaluate_run_mode
  verify_supported_os
  verify_mandatory_variables
  verify_nmcli_utility

  print_network_info
  new_line
  configure_static_ip_address
  new_line
  verify_network_interface
  new_line
}

main "$@"
