#!/bin/bash

# Title         Anchor command runner
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Run an Anchor action/workflow on local/remote host machine
#==========================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")

export LOGGER_DRY_RUN=${DRY_RUN}
export LOGGER_VERBOSE=${VERBOSE}
export LOGGER_SILENT=${SILENT}

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW="\033[0;33m"
COLOR_BLUE="\033[0;34m"
COLOR_PURPLE="\033[0;35m"
COLOR_LIGHT_CYAN='\033[0;36m'
COLOR_WHITE='\033[1;37m'
COLOR_NONE='\033[0m'

ICON_GOOD="${COLOR_GREEN}✔${COLOR_NONE}"
ICON_WARN="${COLOR_YELLOW}⚠${COLOR_NONE}"
ICON_BAD="${COLOR_RED}✗${COLOR_NONE}"

exit_on_error() {
  exit_code=$1
  message=$2
  if [ $exit_code -ne 0 ]; then
    #        >&1 echo "\"${message}\" command failed with exit code ${exit_code}."
    # >&1 echo "\"${message}\""
    exit $exit_code
  fi
}

is_verbose() {
  [[ -n "${LOGGER_VERBOSE}" ]]
}

is_silent() {
  [[ -n ${LOGGER_SILENT} ]]
}

is_dry_run() {
  [[ -n ${LOGGER_DRY_RUN} ]]
}

evaluate_run_mode() {
  if is_dry_run; then
    echo -e "${COLOR_YELLOW}Dry run: enabled${COLOR_NONE}" >&1
  fi

  if is_verbose; then
    echo -e "${COLOR_YELLOW}Verbose: enabled${COLOR_NONE}" >&1
  fi

  if is_silent; then
    echo -e "${COLOR_YELLOW}Silent: enabled${COLOR_NONE}" >&1
  fi

  new_line
}

_log_base() {
  prefix=$1
  shift
  echo -e "${prefix}$*" >&1
}

log_debug() {
  local debug_level_txt="DEBUG"
  if is_dry_run; then
    debug_level_txt+=" (Dry Run)"
  fi

  if ! is_silent && is_verbose; then
    _log_base "${COLOR_WHITE}${debug_level_txt}${COLOR_NONE}: " "$@"
  fi
}

log_info() {
  local info_level_txt="INFO"
  if is_dry_run; then
    info_level_txt+=" (Dry Run)"
  fi

  if ! is_silent; then
    _log_base "${COLOR_GREEN}${info_level_txt}${COLOR_NONE}: " "$@"
  fi
}

log_warning() {
  local warn_level_txt="WARNING"
  if is_dry_run; then
    warn_level_txt+=" (Dry Run)"
  fi

  if ! is_silent; then
    _log_base "${COLOR_YELLOW}${warn_level_txt}${COLOR_NONE}: " "$@"
  fi
}

log_error() {
  local error_level_txt="ERROR"
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  _log_base "${COLOR_RED}${error_level_txt}${COLOR_NONE}: " "$@"
}

log_fatal() {
  local fatal_level_txt="ERROR"
  if is_dry_run; then
    fatal_level_txt+=" (Dry Run)"
  fi
  _log_base "${COLOR_RED}${fatal_level_txt}${COLOR_NONE}: " "$@"
  message="$@"
  exit_on_error 1 "${message}"
}

new_line() {
  echo -e "" >&1
}

log_indicator_good() {
  local error_level_txt=""
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  if ! is_silent; then
    _log_base "${ICON_GOOD}${error_level_txt} " "$@"
  fi
}

log_indicator_warning() {
  local error_level_txt=""
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  if ! is_silent; then
    _log_base "${ICON_WARN}${error_level_txt} " "$@"
  fi
}

log_indicator_bad() {
  local error_level_txt=""
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  if ! is_silent; then
    _log_base "${ICON_BAD}${error_level_txt} " "$@"
  fi
}

is_run_command() {
  [[ "${ENV_ANCHOR_ANSIBLE_COMMAND}" == "Run" ]]
}

is_uninstall_command() {
  [[ "${ENV_ANCHOR_ANSIBLE_COMMAND}" == "Uninstall" ]]
}

should_install_or_update() {
  ! is_tool_exist "anchor" || [[ ($(anchor version) != "${ENV_ANCHOR_VERSION}") ]]
}

generate_anchor_github_url() {
  echo "https://${ENV_GIT_ACCESS_TOKEN}:@github.com/${ENV_ANCHOR_GITHUB_ORGANIZATION}/${ENV_ANCHOR_GITHUB_REPOSITORY}.git"
}

add_anchor_context() {
  # TODO: add to anchor an ability to check if context already exists

  # TODO: Implement this behavior within anchor itself, replace context if exists
  # echo "Clearing previous anchor config..."
  # rm -rf ${HOME}/.config/anchor/config.yaml

  local repo_url=$(generate_anchor_github_url)

  log_info "Setting anchor config context. \
context_name: ${ENV_ANCHOR_GITHUB_REPOSITORY}, \
url: ${repo_url}, \
branch: ${ENV_ANCHOR_GITHUB_REPO_BRANCH}"

  cmd_run "anchor config set-context-entry '${ENV_ANCHOR_GITHUB_REPOSITORY}' \
    --repository.remote.url='${repo_url}' \
    --repository.remote.branch='${ENV_ANCHOR_GITHUB_REPO_BRANCH}' \
    --repository.remote.autoUpdate='${ENV_ANCHOR_CONFIG_AUTO_UPDATE}' \
    --set-current-context"
}

# Binary options: 
#  - darwin_amd64 
#  - darwin_arm64 
#  - linux_arm64 
#  - linux_armv6 
#  - linux_amd64
install_or_update_anchor() {
  local os_type=$(read_os_type)
  local arch=$(read_arch "x86_64:amd64" "armv:armv6")
  local anchor_os_arch="${os_type}_${arch}"

  log_info "Installing anchor CLI. version: ${ENV_ANCHOR_VERSION}, os_arch: ${anchor_os_arch}"

  # Create a temporary folder
  local repo_temp_path=$(cmd_run "mktemp -d ${TMPDIR:-/tmp}/anchor-repo.XXXXXX")
  local cwd=$(pwd)
  cmd_run "cd '${repo_temp_path}' || exit"

  # Download & extract
  log_info "Downloading anchor to temp directory..."
  cmd_run "curl -sSL https://github.com/ZachiNachshon/anchor/releases/download/v${ENV_ANCHOR_VERSION}/anchor_${ENV_ANCHOR_VERSION}_${anchor_os_arch}.tar.gz | tar -xz"

  # Create a dest directory and move the binary
  log_info "Moving binary to ${ENV_LOCAL_BIN_FOLDER_PATH}"
  cmd_run "mv anchor ${ENV_LOCAL_BIN_FOLDER_PATH}"

  cmd_run "cd '${cwd}' || exit"

  # Cleanup
  if [[ -n ${repo_temp_path} && -d ${repo_temp_path} && ${repo_temp_path} == *"anchor-repo"* ]]; then
    log_info "Deleting temp directory..."
    cmd_run "rm -rf ${repo_temp_path}"
  fi

  log_info "Done (type 'anchor' for help)"
}

run_anchor() {
  if should_install_or_update; then
    install_or_update_anchor
  fi

  add_anchor_context
  cmd_run "${ENV_LOCAL_BIN_FOLDER_PATH}/anchor ${ENV_ANCHOR_RUN_ARGS}"
  # Try the next command if the previous fails printing to stdout on Ansible run
  # cmd_run "bash -ilc anchor ${ENV_ANCHOR_RUN_ARGS} 2>&1"
}

uninstall_anchor() {
  local binary_path="${ENV_LOCAL_BIN_FOLDER_PATH}/anchor"
  if is_file_exist "${binary_path}"; then
    cmd_run "rm -rf ${binary_path}"
    log_info "Deleted anchor binary. path: ${binary_path}"
  else
    log_info "Cannot locate anchor binary for removal. path: ${binary_path}"
  fi

  local config_folder_path="${HOME}/.config/anchor"
  if is_directory_exist "${config_folder_path}"; then
    cmd_run "rm -rf ${config_folder_path}"
    log_info "Deleted anchor config folder. path: ${config_folder_path}"
  else
    log_info "Cannot locate anchor config folder for removal. path: ${config_folder_path}"
  fi
}

is_file_exist() {
  local path=$1
  [[ -f "${path}" || $(is_symlink "${path}") ]]
}

is_symlink() {
  local abs_path=$1
  [[ -L "${abs_path}" ]]
}

is_directory_exist() {
  local path=$1
  [[ -d "${path}" ]]
}

#######################################
# Checks if local utility exists
# Globals:
#   None
# Arguments:
#   name - utility CLI name
# Usage:
#   is_tool_exist "kubectl"
#######################################
is_tool_exist() {
  local name=$1
  [[ $(command -v "${name}") ]]
}

#######################################
# Return OS type as plain string
# Globals:
#   OSTYPE
# Arguments:
#   None
# Usage:
#   read_os_type
#######################################
read_os_type() {
  if [[ "${OSTYPE}" == "linux"* ]]; then
    echo "linux"
  elif [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "darwin"
  else
    echo "OS type is not supported. os: ${OSTYPE}"
  fi
}

#######################################
# Return architecture as plain string
# Allow overriding arch with custom name
# Globals:
#   None
# Arguments:
#    string - (optional) custom mapping for arch e.g "x86_64:amd64"
# Usage:
#   read_arch
#   read_arch "x86_64:amd64" "armv:arm"
#######################################
read_arch() {
  local amd64="amd64"
  local arm="arm"
  local arm64="arm64"
  local i386="386"
  local override_arch=$(if [[ "$#" -gt 0 ]]; then echo "true"; else echo "false"; fi)

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      x86_64*)
        amd64=$(cut -d : -f 2- <<<"${1}")
        shift
        ;;
      i386*)
        i386=$(cut -d : -f 2- <<<"${1}")
        shift
        ;;
      armv*)
        arm=$(cut -d : -f 2- <<<"${1}")
        shift
        ;;
      arm64*)
        arm64=$(cut -d : -f 2- <<<"${1}")
        shift
        ;;
    esac
  done

  local arch=$(uname -m | tr '[:upper:]' '[:lower:]')
  local result="${arch}"

  # Replace arch with custom mapping, if supplied
  if [[ "${override_arch}" == "true" ]]; then
    case "${arch}" in
      x86_64*)
        result="${amd64}"
        ;;
      386*)
        result="${i386}"
        ;;
      armv*)
        result="${arm}"
        ;;
      arm64*)
        result="${arm64}"
        ;;
    esac
  fi

  echo "${result}"
}

#######################################
# Run a command from string
# Globals:
#   is_verbose - based on env var LOGGER_VERBOSE
#   is_dry_run - based on env var LOGGER_DRY_RUN
# Arguments:
#   cmd_string - shell command in string format
# Usage:
#   cmd_run "echo 'hello world'"
#######################################
cmd_run() {
  local cmd_string=$1
  if is_verbose; then
    echo """
    ${cmd_string}
  """ >&1
  fi
  if ! is_dry_run; then
    eval "${cmd_string}"
  fi
}

verify_mandatory_run_arguments() {
  if [[ -z "${ENV_ANCHOR_GITHUB_ORGANIZATION}" ]]; then
      log_fatal "missing mandatory argument. name: anchor_github_organization"
      exit 1
  fi

  if [[ -z "${ENV_ANCHOR_GITHUB_REPOSITORY}" ]]; then
      log_fatal "missing mandatory argument. name: anchor_github_repository"
      exit 1
  fi

  if [[ -z "${ENV_ANCHOR_GITHUB_REPO_BRANCH}" ]]; then
      log_fatal "missing mandatory argument. name: anchor_github_repo_branch"
      exit 1
  fi

  if [[ -z "${ENV_ANCHOR_RUN_ARGS}" ]]; then
      log_fatal "missing mandatory argument. name: anchor_args"
      exit 1
  fi

  if [[ -z "${ENV_GIT_ACCESS_TOKEN}" ]]; then
      log_fatal "missing mandatory argument. name: git_access_token"
      exit 1
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if ${os_type} != "linux" && ${os_type} != "darwin"; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

main() {
  verify_supported_os
  evaluate_run_mode

  if is_run_command; then
    verify_mandatory_run_arguments
    run_anchor
  elif is_uninstall_command; then
    uninstall_anchor
  else
    log_fatal "Invalid anchor playbook action. Supported: Run, Uninstall."
    exit 1
  fi
}

main "$@"
