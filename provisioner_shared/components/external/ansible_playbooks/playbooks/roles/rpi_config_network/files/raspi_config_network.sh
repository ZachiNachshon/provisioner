#!/bin/bash

# Title         Configure RPi network settings
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux
# Description   Run RPi settings that affects network configurations
#==============================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="$HOME/.ansible/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

RASPI_CONFIG_BINARY=/usr/bin/raspi-config

has_host_name() {
  [[ -n "${HOST_NAME}" ]]
}

is_wifi_country() {
  [[ -n "${WIFI_COUNTRY}" ]]
}

is_wifi_ssid_passphrase() {
  [[ -n "${WIFI_SSID_PASSPHRASE}" ]]
}

configure_network_settings() {
  local curr_hostname=$(hostname)

  log_info "Configuring remote RPi node system. name: ${HOST_NAME}"

  if [[ "${curr_hostname}" == "${ENV_HOST_NAME}" ]]; then
    log_indicator_warning "Hostname is already configured. name: ${curr_hostname}"
  else
    cmd_run "${RASPI_CONFIG_BINARY} nonint do_hostname ${ENV_HOST_NAME}"
    log_indicator_good "Configured hostname on remote node. name: ${ENV_HOST_NAME}"
  fi

  if is_wifi_country; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${WIFI_COUNTRY}"
    log_indicator_good "Set wifi country as Israel"
  fi

  if is_wifi_ssid_passphrase; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${WIFI_SSID_PASSPHRASE}"
    log_indicator_good "Set wlan0 network to join <wifi_name> network using <password>"
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if ! is_dry_run && [[ "${os_type}" != "linux" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

verify_mandatory_variables() {
  if ! has_host_name; then
    log_fatal "Missing mandatory env var. name: HOST_NAME"
  fi

  if ! is_dry_run && ! is_file_exist "${RASPI_CONFIG_BINARY}"; then
    log_fatal "Missing mandatory RPi utility. path: ${RASPI_CONFIG_BINARY}"
  fi
}

main() {
  evaluate_run_mode
  verify_supported_os
  verify_mandatory_variables

  configure_network_settings
  new_line
}

main "$@"