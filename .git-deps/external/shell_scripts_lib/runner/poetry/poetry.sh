#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
RUNNER_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")
ROOT_FOLDER_ABS_PATH=$(dirname "${RUNNER_FOLDER_ABS_PATH}")

# shellcheck source=../../logger.sh
source "${ROOT_FOLDER_ABS_PATH}/logger.sh"

# shellcheck source=../../io.sh
source "${ROOT_FOLDER_ABS_PATH}/io.sh"

# shellcheck source=../../checks.sh
source "${ROOT_FOLDER_ABS_PATH}/checks.sh"

# shellcheck source=../../props.sh
source "${ROOT_FOLDER_ABS_PATH}/props.sh"

PROPERTIES_FOLDER_PATH=${ROOT_FOLDER_ABS_PATH}/runner/poetry

PYTHON_3_CLI_NAME="python3"

try_get_poetry_binary() {
  local result=""

  # User might install Poetry manually
  if is_tool_exist "${cli_name}"; then
    result="${cli_name}"
  elif is_file_exist "${poetry_binary}"; then
    # Verify a custom installation on a specific location at ~/.local
    result="${poetry_binary}"
  fi

  echo "${result}"
}

install_poetry_if_missing() {
  if [[ -z $(try_get_poetry_binary) ]]; then
    log_warning "Missing '${cli_name}' to manage Python virtual environment, installing..."
    install_poetry "${version}"
  fi
}

install_poetry() {
  if ! is_directory_exist "${poetry_home}"; then
    mkdir -p "${poetry_home}"
  fi

  log_info "Downloading Poetry. version: ${version}, path: ${poetry_binary}"
  curl -sSL https://install.python-poetry.org | POETRY_HOME="${poetry_home}" POETRY_VERSION="${version}" python3 - --force
  chmod +x "${poetry_binary}"
}

run_poetry() {
  local args="$@"
  local poetry_binary_in_use=$(try_get_poetry_binary)

  if is_debug; then
    new_line
    log_info "Poetry binary in use: ${poetry_binary_in_use}"
  fi

  cd "${working_dir}" || exit

  if is_debug; then
    log_info "Working directory set. path: ${working_dir}"
    new_line
    echo -e "--- Poetry Exec Command ---\n${poetry_binary_in_use} ${args}\n---"
  fi

  "${poetry_binary_in_use}" ${args}
}

poetry_get_virtualenvs_path() {
  echo "${working_dir}/${virtual_envs_path}"
}

poetry_set_env_configuration() {
  run_poetry config "cache-dir" "${cache_path}"
  run_poetry config "virtualenvs.path" "${virtual_envs_path}"
  # No need to use the 'in-project' config
  # We are overriding both cache and venv paths to create the environmetn under project root folder
  run_poetry config "virtualenvs.in-project" "false"
}

poetry_create_virtual_environment() {
  local no_dev_deps_flag=$(if is_dev_mode; then echo "--no-dev" else echo ''; fi)
  run_poetry update "${no_dev_deps_flag}"
  run_poetry install "${no_dev_deps_flag}"
  run_poetry build
}

poetry_is_active_venv() {
  local output=$(run_poetry env list --full-path | grep Activated)
  [[ -n ${output} ]]
}

create_virtual_env_if_missing() {
  local virtualenvs_path=$(poetry_get_virtualenvs_path)

  if is_debug; then
    echo -e "--- Poetry Virtual Env Status ---"
  fi

  if is_directory_exist "${virtualenvs_path}" && poetry_is_active_venv; then
    if is_debug; then
      echo -e "${COLOR_GREEN}Poetry virtual environment is active and ready${COLOR_NONE}"
      echo -e "${COLOR_GREEN}VENV path: ${virtualenvs_path}${COLOR_NONE}\n---"
    fi
  else
    echo -e "${COLOR_RED}Poetry virtual environment is not active${COLOR_NONE}\n---\n"
    poetry_set_env_configuration
    poetry_create_virtual_environment
  fi
}

check_python3() {
  if ! is_tool_exist "${PYTHON_3_CLI_NAME}"; then
    log_fatal "Missing ${PYTHON_3_CLI_NAME}, please install and run again (https://www.python.org/downloads/)."
  fi
}

is_verify_venv() {
  [[ -n ${verify_venv} ]]
}

is_debug() {
  [[ -n "${debug}" ]]
}

is_dev_mode() {
  [[ -n "${dev_mode}" ]]
}

parse_poetry_arguments() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      working_dir*)
        working_dir=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      poetry_args*)
        poetry_args=$(cut -d : -f 2- <<<"${1}")
        shift
        ;;
      verify_venv*)
        verify_venv=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      dev_mode*)
        dev_mode=$(cut -d : -f 2- <<<"${1}" | xargs)
        shift
        ;;
      debug*)
        debug="verbose"
        shift
        ;;
      *)
        break
        ;;
    esac
  done

  # Set defaults
  verify_venv=${verify_venv=''}
  dev_mode=${dev_mode=''}
  debug=${debug=''}
}

verify_poetry_arguments() {
  if [[ -z "${working_dir}" ]]; then
    log_fatal "Missing mandatory param. name: working_dir"
  elif ! is_directory_exist "${working_dir}"; then
    log_fatal "Invalid working directory. path: ${working_dir}"
  fi
}

# Runs a job CLI using a local Poetry CLI, install binary if missing
# Example:
# ./runner/poetry/poetry.sh \
#   "working_dir: /path/to/working/dir" \
#   "verify_venv: true" \
#   "dev_mode: true" \
#   "poetry_args: --help" \
#   "debug"
main() {
  parse_poetry_arguments "$@"
  verify_poetry_arguments

  check_python3

  cli_name=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.cli.name")
  version=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.version")
  cache_path=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.cache.path")
  virtual_envs_path=$(property "${PROPERTIES_FOLDER_PATH}" "runner.poetry.virtual.envs.path")

  poetry_home=$(pattern "${PROPERTIES_FOLDER_PATH}" "runner.poetry.home")
  poetry_binary=$(pattern "${PROPERTIES_FOLDER_PATH}" "runner.poetry.binary.path")

  install_poetry_if_missing

  if is_verify_venv; then
    create_virtual_env_if_missing
  fi

  run_poetry ${poetry_args}
}

main "$@"
