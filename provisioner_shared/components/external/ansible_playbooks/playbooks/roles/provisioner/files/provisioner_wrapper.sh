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

PIP_COMMAND_NAME="pip"
PIP_LIST_FLAGS="--no-python-version-warning --disable-pip-version-check"
PIP_INSTALL_SUPPRESS_FLAGS="${PIP_LIST_FLAGS} --no-warn-script-location"

should_install_using_pip() {
  [[ "${ENV_INSTALL_METHOD}" == "${PIP_COMMAND_NAME}" ]]
}

should_install_using_github_release() {
  [[ "${ENV_INSTALL_METHOD}" == "github-release" ]]
}

get_binary_path() {
  # pip installs by default the binary in user folder: ~/.local/bin
  command -v "${ENV_PROVISIONER_BINARY}"
}

get_local_pip_pkg_path() {
  local pkg_name=$1
  echo "${ENV_LOCAL_PIP_PKG_FOLDER_PATH}/${pkg_name}"
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

verify_python_version() {
  if is_tool_exist "python3"; then
    log_debug "Found installed Python3. path: $(which python3)"
  else
    log_fatal "Python3 is not installed as a global command"
  fi

  local version=$(read_python_version)
  local major_minor_version=$(echo "${version}" | awk -F. '{print $1"."$2}')
  local expected_major_minor_version=$(echo "${ENV_PROVISIONER_PYTHON_VERSION}" | awk -F. '{print $1"."$2}')

  if [[ "${major_minor_version}" != "${expected_major_minor_version}" ]]; then
    log_fatal "Python3 version is not supported. version: ${version}, wanted: ${ENV_PROVISIONER_PYTHON_VERSION}"
  else
    log_info "Python3 version is supported. version: ${version}"
  fi

  if is_pip_installed; then
    log_debug "Found installed pip as a Python module"
  else
    log_fatal "Pip module is not installed as a Python module"
  fi
}

uninstall_via_pip() {
  local pkg_name=$1
  local pkg_version=$2
  log_debug "Uninstalling ${PIP_COMMAND_NAME} package. name: ${pkg_name}"
  cmd_run "python3 -m ${PIP_COMMAND_NAME} uninstall --yes ${pkg_name}"
}

install_via_github_release() {
  local pkg_name=$1
  local pkg_version=$2
  local asset_name="${pkg_name}.tar.gz"

  local pkg_folder_path=$(get_local_pip_pkg_path "${pkg_name}")
  if is_directory_exist "${pkg_folder_path}"; then
    log_debug "Removing local ${PIP_COMMAND_NAME} pkg. path: ${pkg_folder_path}"
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
    cmd_run "python3 -m ${PIP_COMMAND_NAME} install ${pkg_folder_path}/${asset_name} ${PIP_INSTALL_SUPPRESS_FLAGS}"
  else
    log_fatal "Cannot find downloaded package asset to install. path: ${pkg_folder_path}/${asset_name}"
  fi
}

install_via_pip() {
  local pkg_name=$1
  local pkg_version=$2
  local pkg_coords=""

  uninstall_via_pip "${pkg_name}" "${pkg_version}"

  log_debug "Installing from ${PIP_COMMAND_NAME} registry. name: ${pkg_name}, version: ${pkg_version}"
  if [[ -n "${pkg_version}" ]]; then
    pkg_coords="${pkg_name}==${pkg_version}"
  else
    pkg_coords="${pkg_name}"
  fi
  cmd_run "python3 -m ${PIP_COMMAND_NAME} install ${pkg_coords} ${PIP_INSTALL_SUPPRESS_FLAGS}"
}

pip_get_package_version() {
  local pkg_name=$1
  local version="DUMMY_VER"
  if ! is_dry_run; then
    version=$(python3 -m ${PIP_COMMAND_NAME} show "${pkg_name}" --no-color | grep -i '^Version:' | awk '{print $2}')
  fi
  echo "${version}"
}

is_pip_installed_package() {
  local pkg_name=$1
  log_debug "Checking if installed from ${PIP_COMMAND_NAME}. name: ${pkg_name}"
  cmd_run "python3 -m ${PIP_COMMAND_NAME} list --no-color ${PIP_LIST_FLAGS} | grep -w ${pkg_name} | head -1 > /dev/null"
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
    log_debug "Pip package is not installed. name: ${pkg_name}"
    install_package "${pkg_name}" "${pkg_version}"
  else
    log_debug "Trying to read ${PIP_COMMAND_NAME} package version. name: ${pkg_name}"
    local current_version=$(pip_get_package_version "${pkg_name}")
    if [[ "${current_version}" == "${ENV_PROVISIONER_VERSION}" ]]; then
      log_debug "Found installed ${PIP_COMMAND_NAME} package with expected version. name: ${pkg_name}, version: ${pkg_version}"
    else
      log_debug "Pip package does not have the expected version. name: ${pkg_name}, current_version: ${current_version}, expected: ${pkg_version}"
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

main() {
  evaluate_run_mode
  verify_supported_os
  verify_python_version
  verify_mandatory_run_arguments
  append_to_path "${ENV_LOCAL_BIN_FOLDER_PATH}"

  install_provisioner_engine
  install_provisioner_plugins

  cmd_run "python3 -m ${PIP_COMMAND_NAME} list --no-color ${PIP_LIST_FLAGS}"  

  local prov_binary_path=$(get_binary_path)
  if is_verbose; then
    new_line
    echo "========= Running ${prov_binary_path} Command =========" >&1
  fi
  cmd_run "${prov_binary_path} ${ENV_PROVISIONER_COMMAND}"

  # log_info "Printing menu:"
  # "${ENV_PROVISIONER_BINARY}"
}

main "$@"
