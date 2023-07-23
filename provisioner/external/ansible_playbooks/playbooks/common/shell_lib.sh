#!/bin/bash

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

exit_on_error() {
  exit_code=$1
  message=$2
  if [ $exit_code -ne 0 ]; then
    #        >&1 echo "\"${message}\" command failed with exit code ${exit_code}."
    # >&1 echo "\"${message}\""
    exit $exit_code
  fi
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

is_file_exist() {
  local path=$1
  [[ -f "${path}" || $(is_symlink "${path}") ]]
}

is_file_contain() {
  local filepath=$1
  local text=$2
  grep -q -w "${text}" "${filepath}"
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

github_download_release_asset() {
  local owner=$1  
  local repo=$2
  local tag_name=$3
  local asset_name=$4
  local dl_path=$5
  local token=$6

  local header=""
  if [[ -n "${token}" ]]; then
    header="-H \"Authorization: Bearer ${token}\""
  fi

  cwd=$(pwd)
  if [[ -n "${dl_path}" ]] && ! is_directory_exist "${dl_path}"; then
    cmd_run "mkdir -p ${dl_path}"
  fi

  if [[ -n "${dl_path}" ]]; then
    cmd_run "cd ${dl_path} || exit"
  fi

  local curl_flags="-LJO"
  if is_verbose; then
    curl_flags="-LJOv"
  fi

  # Get the release information
  release_info=$(cmd_run "curl ${curl_flags} ${header} https://api.github.com/repos/${owner}/${repo}/releases/tags/${tag_name}")

  # Get the asset ID
  asset_id=$(echo "${release_info}" | jq ".assets[] | select(.name == \"${asset_name}\") | .id")

  if ! is_dry_run && [[ -z "${asset_id}" ]]; then
    log_fatal "Failed to retrieve asset id from GitHub release. tag: ${tag_name}, asset_name: ${asset_name}"
  fi

  # Download the asset
  cmd_run "curl ${curl_flags} ${header} -H \"Accept: application/octet-stream\" https://api.github.com/repos/${repo}/releases/assets/${asset_id}"

  if [[ -n "${dl_path}" ]]; then
    cmd_run "cd ${cwd} || exit"
  fi
}
