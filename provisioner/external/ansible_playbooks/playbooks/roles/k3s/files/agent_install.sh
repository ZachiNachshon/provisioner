#!/bin/bash

# Title         Install K3s agent and Join a remote server
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Install/uninstall a K3s agent on a local/remote machine
#==============================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="$HOME/.ansible/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

get_k3s_binary_name() {
  echo "${ENV_K3S_BINARY_NAME}"
}

has_local_bin_folder() {
  [[ -n "${ENV_LOCAL_BIN_FOLDER}" ]]
}

has_k3s_url() {
  [[ -n "${ENV_K3S_URL}" ]]
}

get_k3s_url() {
  echo "${ENV_K3S_URL}"
}

get_local_bin_folder() {
  echo "${ENV_LOCAL_BIN_FOLDER}"
}

has_k3s_version() {
  [[ -n "${ENV_K3S_VERSION}" ]]
}

get_k3s_version() {
  echo "${ENV_K3S_VERSION}"
}

has_k3s_token() {
  [[ -n "${ENV_K3S_TOKEN}" ]]
}

has_k3s_os() {
  [[ -n "${ENV_K3S_OS}" ]]
}

is_k3s_os_linux() {
  [[ "${ENV_K3S_OS}" == "linux" ]]
}

is_k3s_os_darwin() {
  [[ "${ENV_K3S_OS}" == "darwin" ]]
}

get_k3s_token() {
  echo "${ENV_K3S_TOKEN}"
}

has_additional_cli_args() {
  [[ -n "${ENV_K3S_ADDITIONAL_CLI_ARGS}" ]]
}

get_additional_cli_args() {
  echo "${ENV_K3S_ADDITIONAL_CLI_ARGS}"
}

is_install_as_binary() {
  [[ -n "${ENV_K3S_INSTALL_AS_BINARY}" && "${ENV_K3S_INSTALL_AS_BINARY}" == "True" ]]
}

is_k3s_agent_binary_installed() {
  log_info "Checking for previously installed K3s agent binary..."
  is_file_exist "$(get_local_bin_folder)/$(get_k3s_binary_name)"
}

is_k3s_agent_system_service_installed() {
  log_info "Checking for previously installed K3s server system service..."
  cmd_run "systemctl list-units --full -all | grep -Fq k3s-agent.service"
}

install_k3s_agent_binary() {
  if ! is_dry_run && is_k3s_agent_binary_installed; then
    log_warning "K3s agent binary is already installed."
  else
    log_info "Installing K3s agent binary..."
    new_line
    # agent is assumed because of K3S_URL
    cmd_run "curl -sfL https://get.k3s.io | K3S_URL=$(get_k3s_url) INSTALL_K3S_SKIP_ENABLE=true INSTALL_K3S_SKIP_START=true INSTALL_K3S_VERSION=\"$(get_k3s_version)\" INSTALL_K3S_BIN_DIR=\"$(get_local_bin_folder)\" sh -s - $(get_additional_cli_args) --token $(get_k3s_token)"
  fi
}

install_k3s_agent_system_service() {
  if ! is_dry_run && is_k3s_agent_system_service_installed; then
    log_warning "K3s agent system service is already installed and running."
  else
    log_info "Installing K3s agent system service. os: ${ENV_K3S_OS}, version: $(get_k3s_version)"
    new_line
  # agent is assumed because of K3S_URL
    cmd_run "curl -sfL https://get.k3s.io | K3S_URL=$(get_k3s_url) INSTALL_K3S_VERSION=\"$(get_k3s_version)\" INSTALL_K3S_BIN_DIR=\"$(get_local_bin_folder)\" sh -s - $(get_additional_cli_args) --token $(get_k3s_token)"
  fi
}

verify_mandatory_variables() {
  if ! has_local_bin_folder; then
    log_fatal "Missing mandatory env var. name: ENV_LOCAL_BIN_FOLDER"
  fi
  if ! has_k3s_token; then
    log_fatal "Missing mandatory env var. name: ENV_K3S_TOKEN"
  fi
  if ! has_k3s_url; then
    log_fatal "Missing mandatory env var. name: ENV_K3S_URL"
  fi
  if ! has_k3s_version; then
    log_fatal "Missing mandatory env var. name: ENV_K3S_VERSION"
  fi
  if ! has_k3s_os; then
    log_fatal "Missing mandatory env var. name: ENV_K3S_OS"
  fi
  if is_k3s_os_darwin && ! is_install_as_binary; then
    log_fatal "Installing a K3s as a system service on darwin is not supported."
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if ! is_dry_run && [[ "${os_type}" != "linux" && "${os_type}" != "darwin" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

main() {
  evaluate_run_mode
  verify_supported_os
  verify_mandatory_variables

  if is_install_as_binary; then
    install_k3s_agent_binary
  else
    install_k3s_agent_system_service
  fi
}

main "$@"
