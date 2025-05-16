#!/bin/bash

# Title         Add a DHCP static IP entry
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux
# Description   Define a static IP on the DHCP clietn deamon
#==============================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

RASPI_CONFIG_BINARY=/usr/bin/raspi-config
DHCPCD_NAME=dhcpcd
DHCPCD_SERVICE_NAME=dhcpcd.service
DHCPCD_CONFIG_FILEPATH=/etc/dhcpcd.conf

get_static_ip() {
  echo "${STATIC_IP}"
}

get_gateway_address() {
  echo "${GATEWAY_ADDRESS}"
}

get_dns_address() {
  echo "${DNS_ADDRESS}"
}

maybe_start_dhcpcd_service() {
  local status=$(cmd_run "systemctl show -p SubState ${DHCPCD_NAME}")
  if ! is_dry_run && [[ "${status}" != *"running"* ]]; then
    log_warning "DHCP client daemon is not running, starting service..."
    cmd_run "systemctl start ${DHCPCD_NAME}"
  else
    log_indicator_good "DHCP client daemon is running"
  fi

  local active_state=$(cmd_run "systemctl show -p ActiveState ${DHCPCD_NAME}")
  if ! is_dry_run && [[ "${active_state}" != *"active"* ]]; then
    log_warning "DHCP client daemon is not set as active, activating service..."
    cmd_run "systemctl enable ${DHCPCD_NAME}"
  else
    log_indicator_good "DHCP client daemon is enabled"
  fi
}

configure_static_ip_address() {
  local static_ip_address=$(get_static_ip)
  local gateway_address=$(get_gateway_address)
  local dns_address=$(get_dns_address)

  local eth0_static_ip_section="
interface eth0
static ip_address=${static_ip_address}/24
static routers=${gateway_address}
static domain_name_servers=${dns_address}
"
  
  if ! is_dry_run; then
    # Just check if the IP address is already defined and not commented out
    if grep -q "static ip_address=${static_ip_address}/24" "${DHCPCD_CONFIG_FILEPATH}" && ! grep -q "^#.*static ip_address=${static_ip_address}/24" "${DHCPCD_CONFIG_FILEPATH}"; then
      log_info "IP address ${static_ip_address} is already defined in ${DHCPCD_CONFIG_FILEPATH}, skipping..."
    else
      cmd_run "printf '${eth0_static_ip_section}' >> ${DHCPCD_CONFIG_FILEPATH}"
      log_indicator_good "Updated DHCP client daemon config file. path: ${DHCPCD_CONFIG_FILEPATH}"
    fi
  fi
}

verify_dhcpcd_system_service() {
  local dhcpcd_exists=$(cmd_run "systemctl list-units --full -all | grep -i '${DHCPCD_SERVICE_NAME}'")
  if ! is_dry_run && [[ -z "${dhcpcd_exists}" ]]; then
    log_fatal "Cannot find mandatory DHCP client daemon service. name: ${DHCPCD_SERVICE_NAME}"
  else
    log_info "Found DHCP client daemon service. name: ${DHCPCD_SERVICE_NAME}"
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if ! is_dry_run && [[ "${os_type}" != "linux" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

verify_mandatory_variables() {
  if ! is_dry_run && ! is_file_exist "${RASPI_CONFIG_BINARY}"; then
    log_fatal "Missing mandatory RPi utility. path: ${RASPI_CONFIG_BINARY}"
  fi

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
  verify_dhcpcd_system_service

  maybe_start_dhcpcd_service
  configure_static_ip_address
  new_line
}

main "$@"
