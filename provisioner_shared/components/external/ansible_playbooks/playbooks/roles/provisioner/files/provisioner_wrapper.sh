#!/bin/bash

# Title         Provisioner Wrapper
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Run a Provisioner CLI command on local/remote host machine
#==========================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="$HOME/.ansible/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

PIP_LIST_FLAGS="--no-python-downloads"
PIP_INSTALL_SUPPRESS_FLAGS="${PIP_LIST_FLAGS}"
# UV_TEMP_VENV_PATH="/opt/venv"
UV_TEMP_VENV_PATH="/$HOME/.provisioner/uv/venv"
PROV_TESTING_ARCHIVES_PATH="$HOME/.ansible/tmp/provisioner_scripts/"

should_install_using_pip() {
  [[ "${ENV_INSTALL_METHOD}" == "pip" ]]
}

should_install_using_github_release() {
  [[ "${ENV_INSTALL_METHOD}" == "github-release" ]]
}

should_install_from_local_dev() {
  [[ "${ENV_INSTALL_METHOD}" == "testing" ]]
}

get_provisioner_e2e_tests_archives_host_path() {
  echo "${PROV_TESTING_ARCHIVES_PATH}"
}

get_binary_path() {
  command -v "${ENV_PROVISIONER_BINARY}"
}

get_local_pip_pkg_path() {
  local pkg_name=$1
  echo "${ENV_LOCAL_PIP_PKG_FOLDER_PATH}/${pkg_name}"
}

get_python_bin_path() {
  local ver
  ver=$(cmd_run "uv python find ${ENV_PROVISIONER_PYTHON_VERSION}" 2>/dev/null)
  echo "${ver}"
}

verify_mandatory_run_arguments() {
  if should_install_using_github_release; then
    if [[ -z "${ENV_GITHUB_OWNER}" ]]; then
        log_fatal "missing Ansible variable for GitHub release. name: github_owner"
    fi
    if [[ -z "${ENV_GITHUB_REPOSITORY}" ]]; then
        log_fatal "missing Ansible variable for GitHub release. name: github_repository"
    fi
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if [[ "${os_type}" != "linux" && "${os_type}" != "darwin" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

uninstall_via_pip() {
  local pkg_name=$1
  local pkg_version=$2
  log_debug "Uninstalling pip package. name: ${pkg_name}"
  cmd_run "uv pip uninstall ${pkg_name}"
}

install_via_github_release() {
  local pkg_name=$1
  local pkg_version=$2
  local asset_name="${pkg_name}.tar.gz"

  local pkg_folder_path=$(get_local_pip_pkg_path "${pkg_name}")
  if is_directory_exist "${pkg_folder_path}"; then
    log_debug "Removing local pip pkg. path: ${pkg_folder_path}"
    cmd_run "rm -rf ${pkg_folder_path}"
  fi

  log_debug "Downloading a GitHub release. dest: ${pkg_folder_path}"
  github_download_release_asset \
    "${ENV_GITHUB_OWNER}" \
    "${ENV_GITHUB_REPOSITORY}" \
    "${ENV_PROVISIONER_VERSION}" \
    "${asset_name}" \
    "${pkg_folder_path}" \
    "${ENV_GITHUB_TOKEN}"

  if is_dry_run || is_file_exist "${pkg_folder_path}/${asset_name}"; then
    uninstall_via_pip "${pkg_name}" "${pkg_version}"
    log_debug "Installing from GitHub release. name: ${asset_name}, version: ${pkg_version}"
    cmd_run "uv pip install ${pkg_folder_path}/${asset_name} ${PIP_INSTALL_SUPPRESS_FLAGS} --quiet"
  else
    log_fatal "Cannot find downloaded package asset to install. path: ${pkg_folder_path}/${asset_name}"
  fi
}

install_via_pip() {
  local pkg_name=$1
  local pkg_version=$2
  local pkg_coords=""

  uninstall_via_pip "${pkg_name}" "${pkg_version}"

  log_debug "Installing from pip registry. name: ${pkg_name}, version: ${pkg_version}"
  if [[ -n "${pkg_version}" ]]; then
    pkg_coords="${pkg_name}==${pkg_version}"
  else
    pkg_coords="${pkg_name}"
  fi
  cmd_run "uv pip install ${pkg_coords} ${PIP_INSTALL_SUPPRESS_FLAGS} --quiet"
}

pip_get_package_version() {
  local pkg_name=$1
  local version="DUMMY_VER"
  if ! is_dry_run; then
    version=$(uv pip show "${pkg_name}" --no-color | grep -i '^Version:' | awk '{print $2}')
  fi
  echo "${version}"
}

is_pip_installed_package() {
  local pkg_name=$1
  log_debug "Checking if installed from pip. name: ${pkg_name}"
  cmd_run "uv pip list --no-color ${PIP_LIST_FLAGS} --python ${ENV_PROVISIONER_PYTHON_VERSION} | grep -w ${pkg_name} | head -1 > /dev/null"
}

create_provisioner_entrypoint() {
  local python_ver=$(uv python find "${ENV_PROVISIONER_PYTHON_VERSION}")
  local entrypoint="${ENV_LOCAL_BIN_FOLDER_PATH}/${ENV_PROVISIONER_BINARY}"
  if ! is_directory_exist "${ENV_LOCAL_BIN_FOLDER_PATH}"; then
    cmd_run "mkdir -p ${ENV_LOCAL_BIN_FOLDER_PATH}"
  fi
  new_line
  log_debug "Creating a provisioner entrypoint. path: ${entrypoint}"
  echo "#!${python_ver}
# -*- coding: utf-8 -*-
import re
import sys
from provisioner_runtime.main import main
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())" > "${entrypoint}"

  cmd_run "chmod +x ${entrypoint}"
  # ls -lah ~/.local/bin
}

install_package() {
  local pkg_name=$1
  local pkg_version=$2

  if should_install_using_pip; then
    install_via_pip "${pkg_name}" "${pkg_version}"
  elif should_install_using_github_release; then
    install_via_github_release "${pkg_name}" "${pkg_version}"
  else
    log_fatal "Install method is not supported. name: ${ENV_INSTALL_METHOD}"
  fi
}

install_or_update() {
  local pkg_name=$1
  local pkg_version=$2

  if ! is_pip_installed_package "${pkg_name}"; then
    log_debug "pip package is not installed. name: ${pkg_name}"
    install_package "${pkg_name}" "${pkg_version}"
  else
    log_debug "Trying to read pip package version. name: ${pkg_name}"
    local current_version=$(pip_get_package_version "${pkg_name}")
    if [[ "${current_version}" == "${ENV_PROVISIONER_VERSION}" ]]; then
      log_debug "Found installed pip package with expected version. name: ${pkg_name}, version: ${pkg_version}"
    else
      log_debug "pip package does not have the expected version. name: ${pkg_name}, current_version: ${current_version}, expected: ${pkg_version}"
      install_package "${pkg_name}" "${pkg_version}"
    fi
  fi
}

install_provisioner_engine() {
  # Install Provisioner Engine
  install_or_update "${ENV_PROVISIONER_RUNTIME_PIP_PKG_NAME}" "${ENV_PROVISIONER_VERSION}"

  # Only provisioner tool should be available as a binary, it is the engine that runs other plugins
  if is_tool_exist "${ENV_PROVISIONER_BINARY}"; then
    log_debug "Found installed binary. name: ${ENV_PROVISIONER_BINARY}, path: $(which "${ENV_PROVISIONER_BINARY}")"
  else
    log_fatal "The ${ENV_PROVISIONER_BINARY} binary is not installed as a global command"
  fi
}

install_provisioner_plugins() {
  # Install Required Plugins using array of tuple items:
  #   ['provisioner_examples_plugin:0.1.0', 'provisioner_installers_plugin']

  # Remove the square brackets and split the string into an array
  required_plugins=("${ENV_REQUIRED_PLUGINS//[\[\]]/}")

  log_debug "Installing required plugins: ${ENV_REQUIRED_PLUGINS}"

  for plugin in "${required_plugins[@]}"; do
      # Remove the single quotes from each element
      plugin="${plugin//\'}"
      # Extract name
      plugin_name=$(cut -d : -f -1 <<<"${plugin}" | xargs)
      # Extract version
      plugin_version=$(cut -d : -f 2- <<<"${plugin}" | xargs)
      # If version is missing, use an empty string which eventually get treated as latest when using pip
      [[ "$plugin_version" == "$plugin" ]] && plugin_version=""
      install_or_update "${plugin_name}" "${plugin_version}"
  done
}

maybe_install_python_version() {
  local python_ver=$(uv python find "${ENV_PROVISIONER_PYTHON_VERSION}")
  if [[ -n "${python_ver}" ]]; then
    log_debug "Found installed python${ENV_PROVISIONER_PYTHON_VERSION}. path: ${python_ver}"
  else
    log_warning "python${ENV_PROVISIONER_PYTHON_VERSION} is not installed as a global command, installing..."
    cmd_run "uv python install --reinstall ${ENV_PROVISIONER_PYTHON_VERSION}"
  fi
  cmd_run "mkdir -p ${UV_TEMP_VENV_PATH}"
  cmd_run "uv venv --directory ${UV_TEMP_VENV_PATH}"
}

maybe_install_uv() {
  if is_tool_exist "uv"; then
    log_debug "Found installed 'uv' command. path: $(which uv)"
  else
    log_warning "uv is not installed as a global command, installing..."
    cmd_run "curl -LsSf https://astral.sh/uv/install.sh | sh"
  fi
}

main() {
  evaluate_run_mode
  append_to_path "${ENV_LOCAL_BIN_FOLDER_PATH}"
  verify_supported_os
  maybe_install_uv
  maybe_install_python_version
  verify_mandatory_run_arguments

  maybe_non_default_pkg_mgr=""
  if should_install_from_local_dev; then
    cd "${UV_TEMP_VENV_PATH}" || exit
    local prov_archives=$(get_provisioner_e2e_tests_archives_host_path)
    if is_verbose; then
      new_line
      log_debug "Listing provisioner archives:"
      cmd_run "ls -lah ${prov_archives}"
    fi
    log_debug "Installing provisioner shared/runtime/installers-plugin from archives to local pip."
    cmd_run "uv pip install ${prov_archives}/provisioner_shared*.tar.gz --quiet"
    cmd_run "uv pip install ${prov_archives}/provisioner_runtime*.tar.gz --quiet"
    cmd_run "uv pip install ${prov_archives}/provisioner_*_plugin*.tar.gz --quiet"
    maybe_non_default_pkg_mgr="--package-manager uv"
  else
    install_provisioner_engine
    install_provisioner_plugins
  fi
  create_provisioner_entrypoint

  # Enable to debug the installed packages  
  if is_verbose; then
    new_line
    log_debug "Listing installed provisioner packages:"
    cmd_run "uv pip list --no-color ${PIP_LIST_FLAGS} | grep prov"  
  fi

  local prov_binary_path=$(get_binary_path)
  if is_verbose; then
    new_line
    echo -e "========= Running ${prov_binary_path} Command =========\n" >&1
    new_line
    # Print provisioner menu
    cmd_run "${ENV_PROVISIONER_BINARY} ${maybe_non_default_pkg_mgr}"
  fi

  cmd_run "${prov_binary_path} ${ENV_PROVISIONER_COMMAND} ${maybe_non_default_pkg_mgr}"
}

main "$@"
