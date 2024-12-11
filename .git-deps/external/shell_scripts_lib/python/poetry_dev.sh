#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ROOT_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/io.sh"
source "${ROOT_FOLDER_ABS_PATH}/cmd.sh"
source "${ROOT_FOLDER_ABS_PATH}/strings.sh"
source "${ROOT_FOLDER_ABS_PATH}/checks.sh"
source "${ROOT_FOLDER_ABS_PATH}/github.sh"

SCRIPT_MENU_TITLE="Poetry Development Commands"

DEFAULT_PROJECT_LOCATION="."
DEFAULT_TYPE_CHECK_PATH="*/**/*.py"
DEFAULT_UNUSED_IMPORTS_PATH="."

DEFAULT_TESTS_PATH=$(pwd)

CLI_ARGUMENT_DEPS=""
CLI_ARGUMENT_TYPES=""
CLI_ARGUMENT_FMT=""
CLI_ARGUMENT_TEST=""
CLI_ARGUMENT_DOCS=""

CLI_FLAG_IS_MULTI_PROJECT="" # true/false if missing
CLI_FLAG_DEPS_IS_SHOW=""
CLI_FLAG_FMT_CHECK_ONLY=""   # true/false if missing
CLI_FLAG_TYPECHECK_PATH=""
CLI_FLAG_TESTS_PATH=""
CLI_FLAG_TEST_CONTAINERIZED="" # true/false if missing
CLI_FLAG_TEST_COVERAGE=""      # options: html/xml
CLI_FLAG_TEST_COVERAGE=""      # true/false if missing
CLI_FLAG_DOCS_LAN=""           # true/false if missing

CLI_VALUE_TESTS_PATH=""
CLI_VALUE_TYPECHECK_PATH=""
MYPY_CONFIG=""
RUFF_CONFIG=""
BLACK_CONFIG=""
CLI_VALUE_TEST_COVERAGE_TYPE=""

is_deps() {
  [[ -n "${CLI_ARGUMENT_DEPS}" ]]
}

is_show_deps() {
  [[ -n "${CLI_FLAG_DEPS_IS_SHOW}" ]]
}

is_fmt() {
  [[ -n "${CLI_ARGUMENT_FMT}" ]]
}

is_fmt_check_only() {
  [[ -n "${CLI_FLAG_FMT_CHECK_ONLY}" ]]
}

is_typecheck() {
  [[ -n "${CLI_ARGUMENT_TYPES}" ]]
}

get_typecheck_path() {
  echo "${CLI_VALUE_TYPECHECK_PATH:-${DEFAULT_TYPE_CHECK_PATH}}"
}

get_mypy_config() {
  echo "${MYPY_CONFIG}"
}

get_ruff_config() {
  echo "${RUFF_CONFIG}"
}

get_black_config() {
  echo "${BLACK_CONFIG}"
}

is_test() {
  [[ -n "${CLI_ARGUMENT_TEST}" ]]
}

is_test_generate_coverage() {
  [[ -n "${CLI_FLAG_TEST_COVERAGE}" ]]
}

is_html_coverage_type() {
  [[ "${CLI_VALUE_TEST_COVERAGE_TYPE}" == "html" ]]
}

is_xml_coverage_type() {
  [[ "${CLI_VALUE_TEST_COVERAGE_TYPE}" == "xml" ]]
}

is_multi_project() {
  [[ -n "${CLI_FLAG_IS_MULTI_PROJECT}" ]]
}

is_test_with_custom_test_path() {
  [[ -n "${CLI_FLAG_TESTS_PATH}" ]]
}

get_test_path() {
  echo "${CLI_VALUE_TESTS_PATH:-${DEFAULT_TESTS_PATH}}"
}

is_test_containerize() {
  [[ -n "${CLI_FLAG_TEST_CONTAINERIZED}" ]]
}

is_docs() {
  [[ -n "${CLI_ARGUMENT_DOCS}" ]]
}

is_docs_lan() {
  [[ -n "${CLI_FLAG_DOCS_LAN}" ]]
}

update_venv_dependencies() {
  # dev and test are Poetry custom groups that I've added as standards
  local install_flags=""
  log_info "Updating latest changes in pyproject.toml lock file"
  new_line

  cmd_run "poetry update"
  new_line

  if is_multi_project; then
    check_poetry_plugin "poetry-multiproject-plugin"
    install_flags="--all-extras"
    log_info "Downloading and installing all extra dependencies"
  else
    log_info "Downloading and installing dependencies"
  fi

  new_line
  cmd_run "poetry install ${install_flags}"

  new_line
  log_info "Virtual environment is up to date !"
}

check_for_static_type_errors() {
  # check_poetry_dev_dep "mypy"
  local typecheck_path=$(get_typecheck_path)
  local scan_path="$(get_project_name)/${typecheck_path}"
  log_info "Checking for Python static type errors. path: ${scan_path}"
  new_line
  local maybe_cfg_path=""
  if [[ -n "${MYPY_CONFIG}" ]]; then
    maybe_cfg_path=$(get_mypy_config)
    maybe_cfg_path="--config-file ${maybe_cfg_path}"
  fi
  cmd_run "poetry run mypy ${maybe_cfg_path} ${scan_path}"
}

report_on_format_errors() {
  local maybe_black_cfg_path=""
  if [[ -n "${BLACK_CONFIG}" ]]; then
    maybe_black_cfg_path=$(get_black_config)
    maybe_black_cfg_path="--config ${maybe_black_cfg_path}"
  fi
  log_info "Checking that Python code complies with black requirements..."
  new_line
  cmd_run "poetry run black ${DEFAULT_PROJECT_LOCATION} ${maybe_black_cfg_path} --check"
  new_line

  local maybe_ruff_cfg_path=""
  if [[ -n "${RUFF_CONFIG}" ]]; then
    maybe_ruff_cfg_path=$(get_ruff_config)
    maybe_ruff_cfg_path="--config ${maybe_ruff_cfg_path}"
  fi
  log_info "Checking for unused & unordered import statements..."
  new_line
  cmd_run "poetry run ruff check ${DEFAULT_UNUSED_IMPORTS_PATH} ${maybe_ruff_cfg_path} --show-fixes"
  new_line
}

format_python_sources() {
  local maybe_black_cfg_path=""
  if [[ -n "${BLACK_CONFIG}" ]]; then
    maybe_black_cfg_path=$(get_black_config)
    maybe_black_cfg_path="--config ${maybe_black_cfg_path}"
  fi
  log_info "Formatting Python source code using Black style..."
  new_line
  cmd_run "poetry run black ${DEFAULT_PROJECT_LOCATION} ${maybe_black_cfg_path}"
  new_line

  local maybe_ruff_cfg_path=""
  if [[ -n "${RUFF_CONFIG}" ]]; then
    maybe_ruff_cfg_path=$(get_ruff_config)
    maybe_ruff_cfg_path="--config ${maybe_ruff_cfg_path}"
  fi
  log_info "Removing unused and ordering import statements..."
  cmd_run "poetry run ruff check ${DEFAULT_UNUSED_IMPORTS_PATH} ${maybe_ruff_cfg_path} --show-fixes --fix"
  new_line
}

maybe_format_python_sources() {
  # check_poetry_dev_dep "black"
  # check_poetry_dev_dep "ruff"
  if is_fmt_check_only; then
    report_on_format_errors
  else
    format_python_sources
  fi
}

run_tests_on_host() {
  local tests_path=$(get_test_path)
  log_info "Runing tests suite on: ${COLOR_YELLOW}HOST MACHINE${COLOR_NONE}"
  # check_poetry_dev_dep "coverage"
  cmd_run "poetry run coverage run -m pytest"

  if is_test_generate_coverage; then
    local clean_path=""
    local report_type=""
    local report_path=""

    if is_html_coverage_type; then
      clean_path="${tests_path}/htmlcov"
      report_type="html"
      report_path="htmlcov/index.html"

    elif is_xml_coverage_type; then
      clean_path="${tests_path}/coverage.xml"
      report_type="xml"
      report_path="coverage.xml"

    else
      log_fatal "Invalid test coverage type. value: ${CLI_VALUE_TEST_COVERAGE_TYPE}"
    fi

    if [[ -n "${clean_path}" ]]; then
      log_info "Cleaning up previous test runs. path: ${clean_path}"
      cmd_run "rm -rf ${clean_path}"
    fi

    log_info "Generating test suite output"
    new_line
    cmd_run "poetry run coverage report"

    new_line
    log_info "Generating test suite coverage report"
    cmd_run "poetry run coverage ${report_type}"

    new_line
    log_info "Full coverage report is available here:\n\n  • ${tests_path}/${report_path}"
    new_line
  fi
}

run_tests_containerized() {
  log_fatal "Poetry containerized tests are not yet supported"
}

run_tests_suite() {
  if is_test_containerize; then
    run_tests_containerized
  else
    run_tests_on_host
  fi
}

start_local_docs_site() {
  check_tool "npm"
  check_tool "hugo"
  if ! is_dry_run; then
    cd docs-site || exit
  fi
  if is_docs_lan; then
    log_info "Running a local docs site opened for LAN access (http://192.168.x.xx:9001)"
    new_line
    cmd_run "npm run docs-serve-lan"
  else
    log_info "Running a local docs site (http://localhost:9001/<app-name>/)"
    new_line
    cmd_run "npm run docs-serve"
  fi
}

print_help_menu_and_exit() {
  local exec_filename=$1
  local file_name=$(basename "${exec_filename}")
  echo -e ""
  echo -e "${SCRIPT_MENU_TITLE} - Run common development commands on a Python Poetry project"
  echo -e " "
  echo -e "${COLOR_WHITE}USAGE${COLOR_NONE}"
  echo -e "  "${file_name}" [command] [option] [flag]"
  echo -e " "
  echo -e "${COLOR_WHITE}ARGUMENTS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}deps${COLOR_NONE}                      Update and install ${COLOR_GREEN}pyproject.toml${COLOR_NONE} dependencies on the virtual environment"
  echo -e "  ${COLOR_LIGHT_CYAN}types${COLOR_NONE}                     Run Python static type checks to identify static type errors"
  echo -e "  ${COLOR_LIGHT_CYAN}fmt${COLOR_NONE}                       Format Python code using Black style and clear unused imports"
  echo -e "  ${COLOR_LIGHT_CYAN}test${COLOR_NONE}                      Run tests suite"
  echo -e "  ${COLOR_LIGHT_CYAN}docs${COLOR_NONE}                      Run a local documentation site (http://localhost:9001/<project-name>/)"
  echo -e " "
  echo -e "${COLOR_WHITE}DEPS FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--multi-project${COLOR_NONE}           Install all extra dependencies for a multi-project with bundled dependencies"
  echo -e "  ${COLOR_LIGHT_CYAN}--show${COLOR_NONE}                    Print the installed prod/dev/other dependencies tree"
  echo -e " "
  echo -e "${COLOR_WHITE}TYPES FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--typecheck-path${COLOR_NONE}          Type checks folder path (default: ${COLOR_GREEN}${DEFAULT_TYPE_CHECK_PATH}${COLOR_NONE})"
  echo -e "  ${COLOR_LIGHT_CYAN}--mypy-config${COLOR_NONE}             MyPy config TOML file path"
  echo -e " "
  echo -e "${COLOR_WHITE}FORMAT FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--check-only${COLOR_NONE}              Only validate Python code format and imports"
  echo -e "  ${COLOR_LIGHT_CYAN}--ruff-config${COLOR_NONE}             Ruff config TOML file path"
  echo -e "  ${COLOR_LIGHT_CYAN}--black-config${COLOR_NONE}            Black config TOML file path"
  echo -e " "
  echo -e "${COLOR_WHITE}TEST FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--tests-path${COLOR_NONE} <path>       Tests folder path (default: ${COLOR_GREEN}${DEFAULT_PROJECT_LOCATION}${COLOR_NONE})"
  echo -e "  ${COLOR_LIGHT_CYAN}--coverage-type${COLOR_NONE} <option>  Generate tests coverage report output [${COLOR_GREEN}options: html/xml${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--containerized${COLOR_NONE}           Run tests suite within a Docker container"
  echo -e " "
  echo -e "${COLOR_WHITE}DOCS FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--lan${COLOR_NONE}                     Make the documentation site avaialble within LAN (http://192.168.x.xx:9001/)"
  echo -e " "
  echo -e "${COLOR_WHITE}GENERAL FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}-y${COLOR_NONE} (--auto-prompt)        Do not prompt for approval and accept everything"
  echo -e "  ${COLOR_LIGHT_CYAN}-d${COLOR_NONE} (--dry-run)            Run all commands in dry-run mode without file system changes"
  echo -e "  ${COLOR_LIGHT_CYAN}-v${COLOR_NONE} (--verbose)            Output debug logs for commands executions"
  echo -e "  ${COLOR_LIGHT_CYAN}-s${COLOR_NONE} (--silent)             Do not output logs for commands executions"
  echo -e "  ${COLOR_LIGHT_CYAN}-h${COLOR_NONE} (--help)               Show available actions and their description"
  echo -e " "
  exit 0
}

parse_program_arguments() {
  if [ $# = 0 ]; then
    print_help_menu_and_exit "$0"
  fi

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      deps)
        CLI_ARGUMENT_DEPS="deps"
        shift
        ;;
      types)
        CLI_ARGUMENT_TYPES="types"
        shift
        ;;
      fmt)
        CLI_ARGUMENT_FMT="fmt"
        shift
        ;;
      test)
        CLI_ARGUMENT_TEST="test"
        shift
        ;;
      docs)
        CLI_ARGUMENT_DOCS="docs"
        shift
        ;;
      --multi-project)
        CLI_FLAG_IS_MULTI_PROJECT="true"
        shift
        ;;
      --show)
        CLI_FLAG_DEPS_IS_SHOW="true"
        shift
        ;;
      --typecheck-path)
        CLI_FLAG_TYPECHECK_PATH="typecheck-path"
        shift
        CLI_VALUE_TYPECHECK_PATH=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --mypy-config)
        CLI_FLAG_MYPY_CONFIG_PATH="mypy-config"
        shift
        MYPY_CONFIG=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --ruff-config)
        CLI_FLAG_RUFF_CONFIG_PATH="ruff-config"
        shift
        RUFF_CONFIG=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --black-config)
        CLI_FLAG_BLACK_CONFIG_PATH="black-config"
        shift
        BLACK_CONFIG=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --check-only)
        CLI_FLAG_FMT_CHECK_ONLY="check-only"
        shift
        ;;
      --tests-path)
        CLI_FLAG_TESTS_PATH="test"
        shift
        CLI_VALUE_TESTS_PATH=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --containerized)
        CLI_FLAG_TEST_CONTAINERIZED="true"
        shift
        ;;
      --coverage-type)
        CLI_FLAG_TEST_COVERAGE="coverage-type"
        shift
        CLI_VALUE_TEST_COVERAGE_TYPE=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --lan)
        CLI_FLAG_DOCS_LAN="true"
        shift
        ;;
      -d | --dry-run)
        # Used by logger.sh
        export LOGGER_DRY_RUN="true"
        shift
        ;;
      -y | --auto-prompt)
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
      -h | --help)
        print_help_menu_and_exit "$0"
        ;;
      *)
        log_fatal "Unknown option $1 (did you mean =$1 ?)"
        ;;
    esac
  done
}

check_legal_arguments() {
  if ! is_deps && ! is_typecheck && ! is_fmt && ! is_test && ! is_docs; then
    log_fatal "No legal command could be found"
  fi
}

check_tests_path_has_value() {
  if is_test_with_custom_test_path && [[ -z "${CLI_VALUE_TESTS_PATH}" ]]; then
    log_fatal "Tests path flag is missing a folder path. flag: --tests-path"
  fi
}

verify_program_arguments() {
  check_legal_arguments
  check_tests_path_has_value
  evaluate_dry_run_mode
}

prerequisites() {
  check_tool "poetry"
}

check_poetry_dev_dep() {
  local name=$1
  local result=$(cmd_run "poetry show --no-ansi | grep '${name}'")
  if [[ -z "${result}" ]]; then
    log_fatal "Missing pip dev package on local venv. name: ${name}"
  fi
}

check_poetry_plugin() {
  local name=$1
  local result=$(cmd_run "poetry self show plugins --no-ansi | grep '${name}'")
  if [[ -z "${result}" ]]; then
    log_fatal "Missing Poetry plugin on local venv. name: ${name}"
  fi
}

get_project_name() {
  basename "$(pwd)"
}

print_poetry_version() {
  local poetry_version=$(cmd_run "poetry --version")
  log_info "Poetry version: ${poetry_version}"
}

print_poetry_venv_location() {
  local venv_location=$(cmd_run "poetry env info --path")
  log_info "Poetry venv location: ${venv_location}"
}

main() {
  parse_program_arguments "$@"
  verify_program_arguments

  prerequisites

  print_poetry_version
  print_poetry_venv_location

  if is_deps; then
    if is_show_deps; then
      cmd_run "poetry show --tree"
    else
      update_venv_dependencies
    fi
  fi

  if is_typecheck; then
    check_for_static_type_errors
  fi

  if is_fmt; then
    maybe_format_python_sources
  fi

  if is_test; then
    run_tests_suite
  fi

  if is_docs; then
    start_local_docs_site
  fi
}

main "$@"
