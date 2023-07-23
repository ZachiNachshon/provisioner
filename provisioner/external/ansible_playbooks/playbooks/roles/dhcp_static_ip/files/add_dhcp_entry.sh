#!/bin/bash

# Title         Add a DHCP static IP entry
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux
# Description   Define a static IP on the DHCP clietn deamon
#==============================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="$HOME/.ansible/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

RASPI_CONFIG_BINARY=/usr/bin/raspi-config
DHCPCD_NAME=dhcpcd
DHCPCD_SERVICE_NAME=dhcpcd.service
DHCPCD_CONFIG_FILEPATH=/etc/dhcpcd.conf

is_static_ip() {
  [[ -n "${STATIC_IP}" ]]
}

is_gateway_address() {
  [[ -n "${GATEWAY_ADDRESS}" ]]
}

is_dns_address() {
  [[ -n "${DNS_ADDRESS}" ]]
}

maybe_start_dhcpcd_service() {
  local status=$(cmd_run "systemctl show -p SubState ${DHCPCD_NAME}")
  if [[ "${status}" != *"running"* ]]; then
    log_warning "DHCP client daemon is not running, starting service..."
    cmd_run "systemctl start ${DHCPCD_NAME}"
  else
    log_indicator_good "DHCP client daemon is running"
  fi

  local active_state=$(cmd_run "systemctl show -p ActiveState ${DHCPCD_NAME}")
  if [[ "${active_state}" != *"active"* ]]; then
    log_warning "DHCP client daemon is not set as active, activating service..."
    cmd_run "systemctl enable ${DHCPCD_NAME}"
  else
    log_indicator_good "DHCP client daemon is enabled"
  fi
}

configure_static_ip_address() {
  local eth0_static_ip_section="
interface eth0
static ip_address=${ENV_STATIC_IP}/24
static routers=${ENV_GATEWAY_ADDRESS}
static domain_name_servers=${ENV_DNS_ADDRESS}
"

  if grep -q -w "ip_address=${ENV_STATIC_IP}" "${DHCPCD_CONFIG_FILEPATH}"; then
    log_info "Entry '${ENV_STATIC_IP}' already exists in ${DHCPCD_CONFIG_FILEPATH}"
  else
    cmd_run "printf '${eth0_static_ip_section}' >> ${DHCPCD_CONFIG_FILEPATH}"
    log_indicator_good "Updated DHCP client daemon config file. path: ${DHCPCD_CONFIG_FILEPATH}"
#    touch /tmp/test.conf
#    printf "${eth0_static_ip_section}" >> /tmp/test.conf
  fi
}

verify_dhcpcd_system_service() {
  local dhcpcd_exists=$(cmd_run "systemctl list-units --full -all | grep -i '${DHCPCD_SERVICE_NAME}'")
  if [[ -z "${dhcpcd_exists}" ]]; then
    log_fatal "Cannot find mandatory DHCP client daemon service. name: ${DHCPCD_SERVICE_NAME}"
  else
    log_info "Found DHCP client daemon service. name: ${DHCPCD_SERVICE_NAME}"
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if [[ "${os_type}" != "linux" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

verify_mandatory_variables() {
  if ! is_file_exist "${RASPI_CONFIG_BINARY}"; then
    log_fatal "Missing mandatory RPi utility. path: ${RASPI_CONFIG_BINARY}"
  fi

  if ! is_static_ip; then
    log_fatal "Missing mandatory parameter. name: STATIC_IP"
  fi

  if ! is_gateway_address; then
    log_fatal "Missing mandatory parameter. name: GATEWAY_ADDRESS"
  fi

  if ! is_dns_address; then
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
