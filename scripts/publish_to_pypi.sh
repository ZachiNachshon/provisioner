#!/bin/bash

PROMPTER_SKIP_PROMPT=""

SCRIPT_MENU_TITLE="Poetry pip Releaser"

CLI_ARGUMENT_PUBLISH=""

CLI_FLAG_BUILD_TYPE=""         # options: sdist/wheel
CLI_FLAG_IS_MULTI_PROJECT=""   # true/false if missing

CLI_FLAG_RELEASE_TYPE="" # options: pypi/github
CLI_FLAG_RELEASE_TAG_PREFIX=""  # true/false if missing

CLI_VALUE_BUILD_TYPE=""
CLI_VALUE_RELEASE_TYPE=""
CLI_VALUE_RELEASE_TAG_PREFIX=""

POETRY_PACKAGE_NAME=""
POETRY_PACKAGE_VERSION=""

BUILD_OUTPUT_FILE_PATH=""

is_install() {
  [[ -n "${CLI_ARGUMENT_INSTALL}" ]]
}

is_wheel_build_type() {
  [[ "${CLI_VALUE_BUILD_TYPE}" == "wheel" ]]
}

is_sdist_build_type() {
  [[ "${CLI_VALUE_BUILD_TYPE}" == "sdist" ]]
}

get_build_type() {
  echo "${CLI_VALUE_BUILD_TYPE}"
}

is_multi_project() {
  [[ -n "${CLI_FLAG_IS_MULTI_PROJECT}" ]]
}

is_publish() {
  [[ -n "${CLI_ARGUMENT_PUBLISH}" ]]
}

is_pypi_release_type() {
  [[ "${CLI_VALUE_RELEASE_TYPE}" == "pypi" ]]
}

is_github_release_type() {
  [[ "${CLI_VALUE_RELEASE_TYPE}" == "github" ]]
}

get_release_type() {
  echo "${CLI_VALUE_RELEASE_TYPE}"
}

is_release_tag_prefix_exist() {
  [[ -n "${CLI_FLAG_RELEASE_TAG_PREFIX}" ]]
}

get_release_tag_prefix() {
  echo "${CLI_VALUE_RELEASE_TAG_PREFIX}"
}

is_delete() {
  [[ -n "${CLI_ARGUMENT_DELETE}" ]]
}

get_escaped_package_path() {
  echo "${POETRY_PACKAGE_NAME}" | xargs | tr '-' '_'
}

get_sdist_name() {
  local escaped_pkg_name=$(get_escaped_package_path)
  echo "${escaped_pkg_name}-${POETRY_PACKAGE_VERSION}.tar.gz"
}

get_wheel_name() {
  local escaped_pkg_name=$(get_escaped_package_path)
  echo "${escaped_pkg_name}-${POETRY_PACKAGE_VERSION}-py3-none-any.whl"
}

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW="\033[0;33m"
COLOR_LIGHT_CYAN='\033[0;36m'
COLOR_WHITE='\033[1;37m'
COLOR_NONE='\033[0m'

_log_base() {
  prefix=$1
  shift
  echo -e "${prefix}$*" >&1
}

log_debug() {
  local debug_level_txt="DEBUG"
  _log_base "${COLOR_WHITE}${debug_level_txt}${COLOR_NONE}: " "$@"
}

log_info() {
  local info_level_txt="INFO"
  _log_base "${COLOR_GREEN}${info_level_txt}${COLOR_NONE}: " "$@"
}

log_warning() {
  local warn_level_txt="WARNING"
  _log_base "${COLOR_YELLOW}${warn_level_txt}${COLOR_NONE}: " "$@"
}

log_error() {
  local error_level_txt="ERROR"
  _log_base "${COLOR_RED}${error_level_txt}${COLOR_NONE}: " "$@"
}

log_fatal() {
  local fatal_level_txt="ERROR"
  _log_base "${COLOR_RED}${fatal_level_txt}${COLOR_NONE}: " "$@"
  message="$@"
  exit_on_error 1 "${message}"
}

exit_on_error() {
  exit_code=$1
  message=$2
  if [ $exit_code -ne 0 ]; then
    exit $exit_code
  fi
}

new_line() {
  echo -e "" >&1
}

#######################################
# Verify if local utility exists, fail otherwise
# Globals:
#   None
# Arguments:
#   name - utility CLI name
# Usage:
#   check_tool "kubectl"
#######################################
check_tool() {
  local name=$1
  local exists=$(command -v "${name}")
  if [[ "${exists}" != *${name}* && "${exists}" != 0 ]]; then
    log_fatal "missing utility. name: ${name}"
  fi
}

#######################################
# Prompt a yes/no question with severity levels
# Globals:
#   None
# Arguments:
#   message - prompt message
#   level   - (optional: critical/warning) highlight text colors
# Usage:
#   prompt_yes_no "Do you want to proceed" "warning"
#######################################
prompt_yes_no() {
  local message=$1
  local level=$2

  local prompt=""
  if [[ ${level} == "critical" ]]; then
    prompt="${COLOR_RED}${message}? (y/n):${COLOR_NONE} "
  elif [[ ${level} == "warning" ]]; then
    prompt="${COLOR_YELLOW}${message}? (y/n):${COLOR_NONE} "
  else
    prompt="${message}? (y/n): "
  fi

  if ! is_skip_prompt; then

    printf "${prompt}" >&0
    read input

    if [[ "${input}" != "y" ]]; then
      input=""
    fi
    echo "${input}"
  else
    printf "${prompt}y\n\n" >&0
    echo "y"
  fi
}

is_skip_prompt() {
  [[ -n ${PROMPTER_SKIP_PROMPT} ]]
}

prompt_for_approval_before_release() {
  local tag=$1
  log_warning "Make sure to update all version releated files/variables before you continue !"
  new_line
  [[ $(prompt_yes_no "Release tag ${tag}" "warning") == "y" ]]
}

set_built_output_file_path() {
  local bundle_filename=$1
  local pip_package_folder_path=$(mktemp -d "${TMPDIR:-/tmp}/${POETRY_PACKAGE_NAME}.XXXXXX")

  new_line
  log_info "Copy build output. path: ${pip_package_folder_path}"
  mv "dist/${bundle_filename}" "${pip_package_folder_path}"
  BUILD_OUTPUT_FILE_PATH="${pip_package_folder_path}/${bundle_filename}"
}

cleanup_build_path() {
  if [[ "${BUILD_OUTPUT_FILE_PATH}" == *"${POETRY_PACKAGE_VERSION}-py3-none-any.whl"* ||
    "${BUILD_OUTPUT_FILE_PATH}" == *"${POETRY_PACKAGE_VERSION}.tar.gz"* ]]; then
    new_line
    log_info "Clearing build output temporary folder..."
    rm -rf "${BUILD_OUTPUT_FILE_PATH}"
  fi
}

install_pip_package() {
  log_info "Installing pip package..."
  python3 -m pip install "${BUILD_OUTPUT_FILE_PATH}" --no-python-version-warning --disable-pip-version-check
}

build_sdist_tarball() {
  local build_cmd=""

  if is_multi_project; then
    log_info "Building a local Python source distribution ${COLOR_YELLOW}BUNDLED MULTI PROJECT${COLOR_NONE} (sdist tarball)"
    build_cmd="poetry build-project -f sdist -vv"
  else
    log_info "Building a local Python source distribution ${COLOR_YELLOW}NON-BUNDLED SINGLE PROJECT${COLOR_NONE} (sdist tarball)"
    build_cmd="poetry build -f sdist -vv"
  fi

  set -e
  eval "${build_cmd}" || exit
  set +e
  new_line

  local sdist_filename=$(get_sdist_name)
  set_built_output_file_path "${sdist_filename}"
}

build_wheel_package() {
  local build_cmd=""

  if is_multi_project; then
    log_info "Building a local Python wheel ${COLOR_YELLOW}BUNDLED MULTI PROJECT${COLOR_NONE}"
    build_cmd="poetry build-project -f wheel -vv"
  else
    log_info "Building a local Python wheel ${COLOR_YELLOW}NON-BUNDLED SINGLE PROJECT${COLOR_NONE}"
    build_cmd="poetry build -f wheel -vv"
  fi

  ${build_cmd} || exit

  local wheel_filename=$(get_wheel_name)
  set_built_output_file_path "${wheel_filename}"
}

build_pip_package() {
  if is_sdist_build_type; then
    build_sdist_tarball
  elif is_wheel_build_type; then
    build_wheel_package
  else
    log_fatal "Flag --build-type has invalid value or missing a value. value: ${CLI_VALUE_BUILD_TYPE}"
  fi
}

publish_asset_to_github_release() {
  local tag=$1
  local filepath=$2

  if prompt_for_approval_before_release "${tag}"; then
    new_line
    if github_is_release_tag_prefix_exist "${tag}"; then
      log_info "GitHub release tag was found. tag: ${tag}"
      github_upload_release_asset "${tag}" "${filepath}"
    else
      log_info "No GitHub release tag was found. tag: ${tag}"
      github_create_release_tag "${tag}"
      github_upload_release_asset "${tag}" "${filepath}"
    fi
  else
    log_warning "Nothing was uploaded."
  fi
}

github_is_release_tag_exist() {
  local tag=$1
  log_info "Checking if release tag exist. tag: ${tag}"
  if is_dry_run; then
    return 1 # Tag does not exist
  fi
  if gh release view "${tag}" >/dev/null 2>&1; then
    return 0 # Tag exists
  else
    return 1 # Tag does not exist
  fi
}

github_upload_release_asset() {
  local tag=$1
  local filepath=$2
  log_info "Uploading file. tag: ${tag}, path: ${filepath}"
  cmd_run "gh release upload ${tag} ${filepath}"
}

github_create_release_tag() {
  local tag=$1
  local title=$2
  if [[ -z "${title}" ]]; then
    title="${tag}"
  fi
  log_info "Creating a new GitHub release. tag: ${tag}"
  cmd_run "gh release create ${tag} --title ${title}"
}

publish_pip_package_to_github() {
  local tag="${POETRY_PACKAGE_VERSION}"
  local tag_ver="v${tag}"
  local release_filename="${POETRY_PACKAGE_NAME}-${tag_ver}.tar.gz"

  # Allow custom tagged releases e.g. hello-v1.0.0 or v1.0.0 for default without a prefix
  if is_release_tag_prefix_exist; then
    prefix=$(get_release_tag_prefix)
    tag_ver="${prefix}-${tag_ver}"
  fi

  log_info "Publishing pip package as a GitHub release (${tag_ver})..."
  new_line

  local output_filename=$(basename "${BUILD_OUTPUT_FILE_PATH}")
  local output_folder=$(dirname "${BUILD_OUTPUT_FILE_PATH}")
  local cwd=$(pwd)

  log_info "Creating a tarball archive from the pip package. path: ${output_folder}/${release_filename}"
  cd "${output_folder}" || exit
  tar --no-xattrs -zcf "${release_filename}" "${output_filename}"
  cd "${cwd}" || exit
  publish_asset_to_github_release "${tag_ver}" "${output_folder}/${release_filename}"
}

publish_to_pypi() {
  local tag="${POETRY_PACKAGE_VERSION}"
  local username="__token__"
  local password="${PYPI_API_TOKEN}"

  if prompt_for_approval_before_release "${tag}"; then
    log_info "Publishing pip package to PyPi (${tag})..."
    twine upload --username ${username} --password "${password}" "${BUILD_OUTPUT_FILE_PATH}"
  else
    log_info "Nothing was published."
  fi
}

publish_package() {
  if is_github_release_type; then
    check_tool "gh"
    publish_pip_package_to_github
  elif is_pypi_release_type; then
    check_tool "twine"
    publish_to_pypi
  else
    log_fatal "Invalid publish release type. value: ${CLI_FLAG_RELEASE_TYPE}"
  fi
}

poetry_resolve_project_name_version() {
  # POETRY_PACKAGE_NAME="provisioner"
  # POETRY_PACKAGE_VERSION="0.0.0"

  local poetry_project_info=$(poetry version)
  local poetry_project_info=$(poetry version --no-ansi)
  local name_ver_array=(${poetry_project_info})
  POETRY_PACKAGE_NAME=$(printf ${name_ver_array[0]})
  POETRY_PACKAGE_VERSION=$(printf ${name_ver_array[1]})

  if [[ -z "${POETRY_PACKAGE_NAME}" || -z "${POETRY_PACKAGE_VERSION}" ]]; then
    log_fatal "Poetry project name or version could not be resolved"
  fi
}

pip_get_package_version() {
  local version=$(python3 -m pip show "${POETRY_PACKAGE_NAME}" --no-color --no-python-version-warning --disable-pip-version-check | grep -i '^Version:' | awk '{print $2}')
  echo "${version}"
}

is_pip_installed() {
  log_debug "Checking if installed from pip. name: ${POETRY_PACKAGE_NAME}"
  python3 -m pip list --no-color --no-python-version-warning --disable-pip-version-check | grep -w "${POETRY_PACKAGE_NAME}" | head -1 > /dev/null
}

print_help_menu_and_exit() {
  local exec_filename=$1
  local file_name=$(basename "${exec_filename}")
  echo -e ""
  echo -e "${SCRIPT_MENU_TITLE} - Build and release a pip package from a Poetry project"
  echo -e " "
  echo -e "${COLOR_WHITE}USAGE${COLOR_NONE}"
  echo -e "  "${file_name}" [command] [option] [flag]"
  echo -e " "
  echo -e "${COLOR_WHITE}ARGUMENTS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}publish${COLOR_NONE}                       Build and publish/release a pip package"
  echo -e " "    
  echo -e "${COLOR_WHITE}PUBLISH FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-type${COLOR_NONE} <option>       Publish pkg destination [${COLOR_GREEN}options: pypi/github${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-tag-prefix${COLOR_NONE} <value>  (GitHub Only) Prefix used for the GitHub release tag (${COLOR_GREEN}example: hello-v1.0.0${COLOR_NONE})"
  echo -e " "
  echo -e "${COLOR_WHITE}GENERAL FLAGS${COLOR_NONE}"    
  echo -e "  ${COLOR_LIGHT_CYAN}-y${COLOR_NONE} (--auto-prompt)            Do not prompt for approval and accept everything"
  echo -e "  ${COLOR_LIGHT_CYAN}-h${COLOR_NONE} (--help)                   Show available actions and their description"
  echo -e " "
  echo -e "${COLOR_WHITE}GLOBALS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}GITHUB_TOKEN${COLOR_NONE}                  Valid GitHub token with write access for publishing releases"
  echo -e "  ${COLOR_LIGHT_CYAN}PYPI_API_TOKEN${COLOR_NONE}                Valid PyPI API token write access for publishing releases"
  # echo -e " "
  exit 0
}

parse_program_arguments() {
  if [ $# = 0 ]; then
    print_help_menu_and_exit "$0"
  fi

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      publish)
        CLI_ARGUMENT_PUBLISH="publish"
        shift
        ;;
      --build-type)
        CLI_FLAG_BUILD_TYPE="build-type"
        shift
        CLI_VALUE_BUILD_TYPE=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --multi-project)
        CLI_FLAG_IS_MULTI_PROJECT="true"
        shift
        ;;
      --release-type)
        CLI_FLAG_RELEASE_TYPE="release-type"
        shift
        CLI_VALUE_RELEASE_TYPE=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --release-tag-prefix)
        CLI_FLAG_RELEASE_TAG_PREFIX="release-tag-prefix"
        shift
        CLI_VALUE_RELEASE_TAG_PREFIX=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      -y | --auto-prompt)
        # Used by prompter.sh
        export PROMPTER_SKIP_PROMPT="y"
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
  ! is_publish
}

check_publish_invalid_release_type() {
  is_publish && ! is_pypi_release_type && ! is_github_release_type
}

check_publish_release_type_missing_tokens() {
  if is_publish; then
    if is_pypi_release_type; then
      if [[ -z "${PYPI_API_TOKEN}" ]]; then
        log_fatal "Publish command is missing a PyPi authentication token. name: PYPI_API_TOKEN"
      fi
    fi
    if is_github_release_type && [[ -z "${GITHUB_TOKEN}" ]]; then
      log_fatal "Publish command is missing a GitHub authentication token. name: GITHUB_TOKEN"
    fi
  fi
}

verify_program_arguments() {
  if check_legal_arguments; then
    log_fatal "Missing mandatory command argument. Options: publish"
  fi
  if check_publish_invalid_release_type; then
    log_fatal "Command argument 'publish' is missing a mandatory flag value or has an invalid value. flag: --release-type, options: pypi/github"
  fi
  check_publish_release_type_missing_tokens
}

prerequisites() {
  check_tool "poetry"

  # Update lock file changes
  log_info "Updating changes to the Poetry lock file"
  poetry lock
  new_line
}

get_script_name() {
  local file_name=$(basename "${exec_filename}")
  # Return filename without extension
  echo "${file_name%.*}"
}

main() {
  parse_program_arguments "$@"
  verify_program_arguments

  prerequisites
  poetry_resolve_project_name_version

  build_pip_package
  publish_package

  cleanup_build_path
}

main "$@"
