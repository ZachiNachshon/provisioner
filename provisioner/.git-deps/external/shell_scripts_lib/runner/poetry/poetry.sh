#!/bin/bash

# Title         Poetry runner a.k.a Python managed virtual environment
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Runs a Poetry command using a local Poetry binary, install binary if missing
#==============================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
RUNNER_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")
ROOT_FOLDER_ABS_PATH=$(dirname "${RUNNER_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/io.sh"
source "${ROOT_FOLDER_ABS_PATH}/checks.sh"
source "${ROOT_FOLDER_ABS_PATH}/props.sh"
source "${ROOT_FOLDER_ABS_PATH}/cmd.sh"

PROPERTIES_FOLDER_PATH=${ROOT_FOLDER_ABS_PATH}/runner/poetry

PYTHON_3_CLI_NAME="python3"
POETRY_BINARY_IN_USE=""

PARAM_POETRY_WORKING_DIR=""
PARAM_POETRY_ARGS=""
PARAM_POETRY_VERIFY_VENV=""
PARAM_POETRY_DEV_MODE=""

PROP_POETRY_CLI_NAME=""
PROP_POETRY_VERSION=""
PROP_POETRY_VENV_PATH=""
PROP_POETRY_CACHE_PATH=""

PATTERN_POETRY_HOME_PATH=""
PATTERN_POETRY_BINARY_PATH=""

is_verify_venv() {
  [[ -n ${PARAM_POETRY_VERIFY_VENV} ]]
}

is_dev_mode() {
  [[ -n ${PARAM_POETRY_DEV_MODE} ]]
}

try_get_poetry_binary() {
  local result=""

  # User might install Poetry manually
  if is_tool_exist "${PROP_POETRY_CLI_NAME}"; then
    result="${PROP_POETRY_CLI_NAME}"
  elif is_file_exist "${PATTERN_POETRY_BINARY_PATH}"; then
    # Verify a custom installation on a specific location at ~/.local
    result="${PATTERN_POETRY_BINARY_PATH}"
  fi

  echo "${result}"
}

install_poetry_if_missing() {
  local maybe_poetry_binary=$(try_get_poetry_binary)

  if [[ -n "${maybe_poetry_binary}" ]]; then
    POETRY_BINARY_IN_USE="${maybe_poetry_binary}"
  else 
    log_warning "Missing '${PROP_POETRY_CLI_NAME}' to manage Python virtual environment, installing..."
    install_poetry "${PROP_POETRY_VERSION}"
    POETRY_BINARY_IN_USE="${PATTERN_POETRY_BINARY_PATH}"
  fi

  log_debug "Poetry binary in use: ${POETRY_BINARY_IN_USE}"
}

install_poetry() {
  if ! is_directory_exist "${PATTERN_POETRY_HOME_PATH}"; then
    mkdir -p "${PATTERN_POETRY_HOME_PATH}"
  fi

  local verbose_flag=""
  if [[ -n ${LOGGER_VERBOSE} ]]; then
    verbose_flag="-vv"
  fi

  log_info "Downloading Poetry. version: ${PROP_POETRY_VERSION}, path: ${PATTERN_POETRY_BINARY_PATH}"
  cmd_run "curl -sSL https://install.python-poetry.org | POETRY_HOME=${PATTERN_POETRY_HOME_PATH} POETRY_VERSION=${PROP_POETRY_VERSION} python3 ${verbose_flag} - --force"

  if ! is_file_exist "${PATTERN_POETRY_BINARY_PATH}"; then
    log_fatal "Failed to install Poetry from remote"
  fi

  cmd_run "chmod +x ${PATTERN_POETRY_BINARY_PATH}"
}

run_poetry() {
  local args="$@"

  if [[ "${POETRY_BINARY_IN_USE}" == "${PROP_POETRY_CLI_NAME}" || \
        "${POETRY_BINARY_IN_USE}" == "${PATTERN_POETRY_BINARY_PATH}" ]]; then
    cmd_run "${POETRY_BINARY_IN_USE} ${args}"
  else
    log_fatal "Cannot identify a valid Poetry binary. value: ${POETRY_BINARY_IN_USE}"
  fi
}

poetry_get_virtualenvs_path() {
  echo "${PARAM_POETRY_WORKING_DIR}/${PROP_POETRY_VENV_PATH}"
}

poetry_set_env_configuration() {
  run_poetry config "cache-dir" "${PROP_POETRY_CACHE_PATH}"
  run_poetry config "virtualenvs.path" "${PROP_POETRY_VENV_PATH}"
  # No need to use the 'in-project' config
  # We are overriding both cache and venv paths to create the environmetn under project root folder
  run_poetry config "virtualenvs.in-project" "false"
  # Use the current Python version managed by pyenv
  # run_poetry config "virtualenvs.prefer-active-python" "true"
}

poetry_create_virtual_environment() {
  local no_dev_deps_flag=''
  if is_dev_mode; then 
    no_dev_deps_flag="--without dev" 
  fi
  run_poetry env use "$(pyenv which python3)" # Don't want to force using pyenv
  run_poetry update "${no_dev_deps_flag}"
  run_poetry install "${no_dev_deps_flag}"
  run_poetry build
  # run_poetry build-project
}

poetry_is_active_venv() {
  log_debug "Checking if Poetry virtual env is active..."
  local output=$(run_poetry env list --full-path | grep Activated)
  [[ -n ${output} ]]
}

create_virtual_env_if_missing() {
  local virtualenvs_path=$(poetry_get_virtualenvs_path)

  if is_directory_exist "${virtualenvs_path}" || poetry_is_active_venv; then
    log_debug "${COLOR_GREEN}Poetry virtual environment is active and ready. venv: ${virtualenvs_path}${COLOR_NONE}"
  else
    log_error "${COLOR_RED}Poetry virtual environment is not active${COLOR_NONE}"
    poetry_set_env_configuration
    poetry_create_virtual_environment
  fi
}

check_python3() {
  if ! is_tool_exist "${PYTHON_3_CLI_NAME}"; then
    log_fatal "Missing ${PYTHON_3_CLI_NAME}, please install and run again (https://www.python.org/downloads/)."
  fi
}

change_dir_to_working_dir() {
  cd "${PARAM_POETRY_WORKING_DIR}" || exit
  log_debug "Working directory set. path: ${PARAM_POETRY_WORKING_DIR}"
}

parse_poetry_arguments() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      working_dir*)
        PARAM_POETRY_WORKING_DIR=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      poetry_args*)
        PARAM_POETRY_ARGS=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --verify-venv)
        PARAM_POETRY_VERIFY_VENV="true"
        shift
        ;;
      --dev-mode)
        PARAM_POETRY_DEV_MODE="true"
        shift
        ;;
      --dry-run)
        # Used by logger.sh
        export LOGGER_DRY_RUN="true"
        shift
        ;;
      -y)
        # Used by prompter.sh
        export PROMPTER_SKIP_PROMPT="y"
        shift
        ;;
      -v | --verbose)
        # Used by logger.sh
        export LOGGER_VERBOSE="true"
        shift
        ;;
      -s | --silent)
        # Used by logger.sh
        export LOGGER_SILENT="true"
        shift
        ;;
      *)
        break
        ;;
    esac
  done
}

verify_poetry_arguments() {
  if [[ -z "${PARAM_POETRY_WORKING_DIR}" ]]; then
    log_fatal "Missing mandatory param. name: working_dir"
  elif ! is_directory_exist "${PARAM_POETRY_WORKING_DIR}"; then
    log_fatal "Invalid working directory. path: ${PARAM_POETRY_WORKING_DIR}"
  fi
}

resolve_required_properties() {
  PROP_POETRY_CLI_NAME=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.cli.name")
  PROP_POETRY_VERSION=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.version")
  PROP_POETRY_CACHE_PATH=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.cache.path")
  PROP_POETRY_VENV_PATH=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.virtual.envs.path")
}

resolve_required_patterns() {
  PATTERN_POETRY_HOME_PATH=$(pattern "${PROPERTIES_FOLDER_PATH}" "runner.poetry.home.path")
  PATTERN_POETRY_BINARY_PATH=$(pattern "${PROPERTIES_FOLDER_PATH}" "runner.poetry.binary.path")
}

####################################################################
# Run Poetry from local binary or download and install if missing
# 
# Globals:
#   None
# 
# Arguments:
#   working_dir    - Host root working directory
#   poetry_args    - Poetry command arguments
#   --verify_venv  - Should verify if venv exists and create otherwise
#   --dev_mode     - Should install development packages
#   --dry-run      - Run all commands in dry-run mode without file system changes
#   --verbose      - Output debug logs for commands executions
# 
# Usage:
# ./runner/poetry/poetry.sh \
#   "working_dir: /path/to/working/dir" \
#   "poetry_args: --help" \
#   "--verify-venv" \
#   "--dev-mode" \
#   "--dry-run" \
#   "--verbose"
####################################################################
main() {
  parse_poetry_arguments "$@"
  verify_poetry_arguments

  check_python3
  change_dir_to_working_dir

  resolve_required_properties
  resolve_required_patterns

  install_poetry_if_missing

  if is_verify_venv; then
    create_virtual_env_if_missing
  fi
  
  run_poetry "${PARAM_POETRY_ARGS}"
}

main "$@"
