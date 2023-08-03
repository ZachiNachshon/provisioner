#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ROOT_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/io.sh"
source "${ROOT_FOLDER_ABS_PATH}/cmd.sh"
source "${ROOT_FOLDER_ABS_PATH}/strings.sh"
source "${ROOT_FOLDER_ABS_PATH}/checks.sh"
source "${ROOT_FOLDER_ABS_PATH}/github.sh"
source "${ROOT_FOLDER_ABS_PATH}/prompter.sh"

SCRIPT_MENU_TITLE="Poetry pip Releaser"

CLI_ARGUMENT_INSTALL=""
CLI_ARGUMENT_PUBLISH=""
CLI_ARGUMENT_DELETE=""

CLI_FLAG_BUILD_TYPE=""             # options: sdist/wheel
CLI_FLAG_IS_MULTI_PROJECT=""       # true/false if missing
CLI_FLAG_FORCE_INSTALL_DEPS=""     # true/false if missing

CLI_FLAG_RELEASE_TYPE=""           # options: pypi/github
CLI_FLAG_RELEASE_TAG=""            # true/false if missing

CLI_FLAG_DELETE_ORIGIN=""          
CLI_VALUE_DELETE_ORIGIN=""         # options: pypi-local/pypi-remote/github
CLI_FLAG_DELETE_TAG=""

CLI_FLAG_DEV_MODE=""               # true/false if missing

CLI_VALUE_BUILD_TYPE=""
CLI_VALUE_RELEASE_TYPE=""
CLI_VALUE_RELEASE_TAG=""
CLI_VALUE_DELETE_TAG=""

POETRY_PACKAGE_NAME=""
POETRY_PACKAGE_VERSION=""

DEV_BINARY_PATH="${HOME}/.local/bin"

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

is_install_deps() {
  [[ -n "${CLI_FLAG_FORCE_INSTALL_DEPS}" ]]
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

is_release_tag_exist() {
  [[ -n "${CLI_FLAG_RELEASE_TAG}" ]]
}

get_release_tag() {
  echo "${CLI_VALUE_RELEASE_TAG}"
}

is_delete() {
  [[ -n "${CLI_ARGUMENT_DELETE}" ]]
}

is_delete_tag_exist() {
  [[ -n "${CLI_FLAG_DELETE_TAG}" && -n "${CLI_VALUE_DELETE_TAG}" ]]
}

get_delete_tag() {
  echo "${CLI_VALUE_DELETE_TAG}"
}

is_pypi_local_delete_origin() {
  [[ "${CLI_VALUE_DELETE_ORIGIN}" == "pypi-local" ]]
}

is_pypi_remote_delete_origin() {
  [[ "${CLI_VALUE_DELETE_ORIGIN}" == "pypi-remote" ]]
}

is_github_delete_origin() {
  [[ "${CLI_VALUE_DELETE_ORIGIN}" == "github" ]]
}

is_dev_mode() {
  [[ -n "${CLI_FLAG_DEV_MODE}" ]]
}

is_force_install_deps() {
  [[ -n "${CLI_FLAG_FORCE_INSTALL_DEPS}" ]]
}

get_escaped_package_path() {
  echo "${POETRY_PACKAGE_NAME}" | xargs | tr '-' '_'
}

get_sdist_name() {
  local escaped_pkg_name=$(get_escaped_package_path)
  echo "${escaped_pkg_name}-${POETRY_PACKAGE_VERSION}.tar.gz"
}

get_dev_pip_pkg_path() {
  echo "${HOME}/.config/${POETRY_PACKAGE_NAME}/.pip-pkg"
}

dev_prepare_pip_pkg_folder() {
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)
  if is_dry_run || is_directory_exist "${dev_pip_pkg_path}"; then
    log_info "Clearing previous locally installed Python distribution"
    cmd_run "rm -rf ${dev_pip_pkg_path}"
  fi
  cmd_run "mkdir -p ${dev_pip_pkg_path}"
}

dev_copy_pip_pkg_tarball() {
  local sdist_name=$(get_sdist_name)
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)

  log_info "Copy local pip package sdist tarball"
  cmd_run "mv dist/${sdist_name} ${dev_pip_pkg_path}"
}

dev_unpack_pip_pkg_tarball() {
  local sdist_name=$(get_sdist_name)
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)
  local cwd=$(pwd)

  if ! is_dry_run; then
    cd "${dev_pip_pkg_path}" || exit
  fi

  log_info "Unpacking local sdist pip package archive..."
  cmd_run "tar -xf ${sdist_name}"

  # Rename the sdist root folder from <package-name>-<version> to <package-name>
  cmd_run "mv ${POETRY_PACKAGE_NAME}-${POETRY_PACKAGE_VERSION} ${POETRY_PACKAGE_NAME}"

  if ! is_dry_run; then
    cd "${cwd}" || exit
  fi
}

dev_generate_launcher_script() {
  local escaped_pkg_name=$(get_escaped_package_path)
  local escaped_pkg_name_upper=$(to_upper "${escaped_pkg_name}")
  cat << EOF
#!/usr/bin/env python3
import os
import sys

"""
This file is used as a command launcher for ${POETRY_PACKAGE_NAME} private installation.
"""
def get_pkg_target_path():
    """
    Content of .pip-pkg folder is the extraction of pip wheel/sdist:
    .
    ├── ${escaped_pkg_name}
    │   ├── LICENSE
    │   ├── PKG-INFO
    │   ├── ${escaped_pkg_name}
    │   │   ├── ...
    │   │   └── <poetry-included-files-and-folders>
    │   └── setup.py
    └── ${escaped_pkg_name}-${POETRY_PACKAGE_VERSION}.tar.gz
    """
    return os.environ.get(
        "${escaped_pkg_name_upper}_PKG_PATH",  # used only for testing - DO NOT OVERRIDE
        os.path.expanduser(os.path.join("~", ".config", "${POETRY_PACKAGE_NAME}", ".pip-pkg", "${POETRY_PACKAGE_NAME}"))
    )


def launch(pkg_path: str):
    # Add the custom installation directory to PYTHONPATH so the modules are found
    sys.path = [pkg_path] + sys.path
    cwd = os.getcwd()
    try:
        os.chdir(pkg_path)
        from ${escaped_pkg_name}.main import main
        main()
        os.chdir(cwd)
    except ModuleNotFoundError:
        print("The '${escaped_pkg_name}' package could not be found. "
              "Please refer to the docs for installation instructions and troubleshooting")
        os.chdir(cwd)
        exit(2)


if __name__ == '__main__':
    launch(pkg_path=get_pkg_target_path())
EOF
}

dev_install_launcher_binary() {
  local dev_launch_script=$1

  if ! is_directory_exist "${DEV_BINARY_PATH}"; then
    log_info "Creating local bin folder (${DEV_BINARY_PATH})"
    cmd_run "mkdir -p ${DEV_BINARY_PATH}"
  fi

  local binary_path="${DEV_BINARY_PATH}/${POETRY_PACKAGE_NAME}"
  if is_dry_run; then
    log_info "\n\n${dev_launch_script}\n"
  else
    log_info "Copy ${POETRY_PACKAGE_NAME} binary. path: ${binary_path}"
    echo "${dev_launch_script}" > "${binary_path}"
  fi

  log_info "Elevating execution permissions"
  cmd_run "chmod +x ${binary_path}"
}

install_dev_local_pip_package() {
  dev_prepare_pip_pkg_folder
  dev_copy_pip_pkg_tarball
  dev_unpack_pip_pkg_tarball

  local dev_launch_script=$(dev_generate_launcher_script "${POETRY_PACKAGE_NAME}")
  dev_install_launcher_binary "${dev_launch_script}"
}

delete_dev_local_pip_package() {
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)
  if is_dry_run || is_directory_exist "${dev_pip_pkg_path}"; then
    log_info "Clearing locally installed Python distribution"
    cmd_run "rm -rf ${dev_pip_pkg_path}"
  else
    log_info "No locally installed Python distribution could be found"
  fi

  local binary_path="${DEV_BINARY_PATH}/${POETRY_PACKAGE_NAME}"
  if is_dry_run || ([[ -n ${POETRY_PACKAGE_NAME} ]] && is_file_exist "${binary_path}"); then
    log_info "Clearing locally installed Python binary"
    cmd_run "rm -rf ${binary_path}"
  else
    log_info "No locally installed Python binary could be found"
  fi 
}

install_pip_package_from_sdist() {
  local cwd=$(pwd)
  local sdist_filename=$(get_sdist_name)
  local pip_tarball_folder_path=""

  if ! is_dry_run; then
    pip_tarball_folder_path=$(mktemp -d "${TMPDIR:-/tmp}/${POETRY_PACKAGE_NAME}.XXXXXX")
  else
    pip_tarball_folder_path="/dry/run/dummy/path"
  fi 

  log_info "Copy sdist tarball. path: ${pip_tarball_folder_path}"
  cmd_run "mv dist/${sdist_filename} ${pip_tarball_folder_path}"

  if ! is_dry_run; then
    cd "${pip_tarball_folder_path}" || exit
  fi
  
  log_info "Installing pip package from sdist tarball..."
  cmd_run "python3 -m pip install ${pip_tarball_folder_path}/${sdist_filename} --no-python-version-warning --disable-pip-version-check"
  
  if ! is_dry_run; then
    cd "${cwd}" || exit
    # Clear temporary folder
    if [[ -n "${POETRY_PACKAGE_NAME}" ]]; then
      cmd_run "rm -rf ${pip_tarball_folder_path}"
    fi
  fi
}

delete_pip_package_from_local_pypi() {
  log_info "Uninstalling pip package. name: ${POETRY_PACKAGE_NAME}"
  cmd_run "python3 -m pip uninstall ${POETRY_PACKAGE_NAME} -y"
}

delete_pip_package_from_remote_pypi() {
  log_fatal "Deleting a remote pip pacakge release tag from PyPi is not yet supported"
}

delete_release_from_github() {
  local tag="no-tag"
  if is_delete_tag_exist; then
    tag=$(get_delete_tag)
  else
    tag=$(prompt_user_input "Insert tag to delete")
  fi
  if [[ -n "${tag}" ]]; then
    if github_is_release_tag_exist "${tag}"; then
        log_info "GitHub release tag was found. tag: ${tag}"
        new_line
        if github_prompt_for_approval_before_delete "${tag}"; then
          github_delete_release_tag "${tag}"
        else
          log_info "No GitHub release tag was deleted."
        fi
      else
        log_warning "No GitHub release tag was found. tag: ${tag}"
      fi
  fi
}

install_pip_package_from_wheel() {
  log_fatal "Installing a pip wheel is not yet supported"
}

delete_pip_package_from_wheel() {
  log_fatal "Uninstalling a pip wheel is not yet supported"
}

build_sdist_tarball()  {
  local build_cmd=""

  if is_multi_project; then
    log_info "Build a local Python source distribution ${COLOR_YELLOW}BUNDLED MULTI PROJECT${COLOR_NONE} (sdist tarball)"
    build_cmd="poetry build-project -f sdist"
  else
    log_info "Build a local Python source distribution ${COLOR_YELLOW}NON-BUNDLED SINGLE PROJECT${COLOR_NONE} (sdist tarball)"
    build_cmd="poetry build -f sdist"
  fi

  if is_verbose; then
    build_cmd+=" -vv"
  fi
  
  cmd_run "${build_cmd} || exit"
}

maybe_force_install_deps() {
  if is_force_install_deps; then
    pip_install_all_dependencies
  fi
}

build_wheel_package() {
  log_fatal "Building pip wheel is not supported yet"
}

build_pip_package() {
  if is_sdist_build_type; then
    build_sdist_tarball
  elif is_wheel_build_type; then
    build_wheel_package
  elif is_dev_mode; then
    build_sdist_tarball
  else
    log_fatal "Flag --build-type has invalid value or missing a value. value: ${CLI_VALUE_BUILD_TYPE}"
  fi
}

install_pip_package() {
  if is_dev_mode; then
    install_dev_local_pip_package
  elif is_sdist_build_type; then
    install_pip_package_from_sdist
    maybe_force_install_deps
  elif is_wheel_build_type; then
    install_pip_package_from_wheel
    maybe_force_install_deps
  else
    log_fatal "Flag --build-type has invalid value or missing a value. value: ${CLI_VALUE_BUILD_TYPE}"
  fi
}

delete_pip_package() {
  if is_dev_mode; then
    delete_dev_local_pip_package
  elif is_pypi_local_delete_origin; then
    delete_pip_package_from_local_pypi
  elif is_pypi_remote_delete_origin; then
    delete_pip_package_from_remote_pypi
  elif is_github_delete_origin; then
    delete_release_from_github
  else
    log_fatal "Flag --origin has invalid value or missing a value. value: ${CLI_VALUE_DELETE_ORIGIN}"
  fi
}

publish_asset_to_github_release() {
  local tag=$1
  local filepath=$2

  if github_prompt_for_approval_before_release "${tag}"; then
    if github_is_release_tag_exist "${tag}"; then
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

publish_pip_package_to_github_from_sdist() {
  local sdist_filename=$(get_sdist_name)
  local sdist_filename_escaped=$(echo "${sdist_filename}" | tr '-' '_')
  local pip_tarball_folder_path="dist/${sdist_filename_escaped}"

  log_info "Escaping release asset name. name: ${sdist_filename_escaped}"
  cmd_run "mv dist/${sdist_filename} ${pip_tarball_folder_path}"

  log_info "Publishing pip package as a GitHub release from sdist tarball..."
  new_line
  local tag=$(get_release_tag)
  publish_asset_to_github_release "${tag}" "${pip_tarball_folder_path}"
}

publish_pip_package_to_github_from_wheel() {
  log_fatal "Publishing pip package from a wheel is not supported yet"
}

publish_package() {
  if is_github_release_type; then
    check_tool "gh"
    if is_sdist_build_type; then
      publish_pip_package_to_github_from_sdist
    elif is_wheel_build_type; then
      publish_pip_package_to_github_from_wheel
    fi
  elif is_pypi_release_type; then
    log_fatal "Releasing to PyPi is not supported yet"
  else
    log_fatal "Invalid publish release type. value: ${CLI_FLAG_RELEASE_TYPE}"
  fi
}

resolve_project_name_version() {
  # POETRY_PACKAGE_NAME="provisioner"
  # POETRY_PACKAGE_VERSION="0.0.0"

  # if ! is_dry_run; then
  local poetry_project_info=$(cmd_run "poetry version")
  local poetry_project_info=$(poetry version --no-ansi)
  local name_ver_array=(${poetry_project_info})
  POETRY_PACKAGE_NAME=$(printf ${name_ver_array[0]})
  POETRY_PACKAGE_VERSION=$(printf ${name_ver_array[1]})
  # fi
}

pip_install_all_dependencies() {
  log_info "Installing all non-dev project dependencies to pip"

  # Create a virtual environment and install the project's dependencies.
  cmd_run "poetry install"

  # Create a requirements.txt file in the project directory 
  # that lists all the dependencies needed by the project
  cmd_run """poetry export \
    -f requirements.txt \
    --without dev \
    --without-urls \
    --without-hashes \
    --output requirements.txt"""

  # Install Poetry into pip to avoid error - ModuleNotFoundError: No module named 'poetry'
  cmd_run "python3 -m pip install -U poetry"

  # Install all the packages listed in the requirements.txt file 
  # in the virtual environment or globally
  cmd_run "python3 -m pip install -r requirements.txt"
}

pip_get_package_version() {
  local version="DUMMY_VER"
  if ! is_dry_run; then
    version=$(python3 -m pip show "${POETRY_PACKAGE_NAME}" --no-color --no-python-version-warning --disable-pip-version-check | grep -i '^Version:' | awk '{print $2}')
  fi
  echo "${version}"
}

is_pip_installed() {
  log_debug "Checking if installed from pip. name: ${POETRY_PACKAGE_NAME}"
  cmd_run "python3 -m pip list --no-color --no-python-version-warning --disable-pip-version-check | grep -w ${POETRY_PACKAGE_NAME} | head -1 > /dev/null"
}

print_help_menu_and_exit() {
  local exec_filename=$1
  local file_name=$(basename "${exec_filename}")
  echo -e ""
  echo -e "${SCRIPT_MENU_TITLE} - Build, install and release a pip package from a Poetry project"
  echo -e " "
  echo -e "${COLOR_WHITE}USAGE${COLOR_NONE}"
  echo -e "  "${file_name}" [command] [option] [flag]"
  echo -e " "
  echo -e "${COLOR_WHITE}ARGUMENTS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}install${COLOR_NONE}                   Build and Install a local pip package"
  echo -e "  ${COLOR_LIGHT_CYAN}publish${COLOR_NONE}                   Build and publish/release a pip package (always installes from local pip)"
  echo -e "  ${COLOR_LIGHT_CYAN}delete${COLOR_NONE}                    Delete pip package from a local machine or from a remote release"
  echo -e " "
  echo -e "${COLOR_WHITE}BUILD FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--build-type${COLOR_NONE} <option>     Type of the built pip package [${COLOR_GREEN}options: sdist/wheel${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--multi-project${COLOR_NONE}           Build a multi-project with bundled dependencies (required Poetry plugin: ${COLOR_GREEN}build-project${COLOR_NONE})"
  echo -e "  ${COLOR_LIGHT_CYAN}--force-install-deps${COLOR_NONE}      Force install all dependencies to local pip"
  echo -e " "
  echo -e "${COLOR_WHITE}PUBLISH FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-type${COLOR_NONE} <option>   Publish pkg destination [${COLOR_GREEN}options: pypi/github${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-tag${COLOR_NONE} <value>     Tag of the release"
  echo -e " "
  echo -e "${COLOR_WHITE}DELETE FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--origin${COLOR_NONE} <option>         Origin of the pip package to delete from [${COLOR_GREEN}options: pypi-local/pypi-remote/github${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--delete-tag${COLOR_NONE} <value>      Remote pip package tag to delete (pypi-remote/github only)"
  echo -e " "  
  echo -e "${COLOR_WHITE}GENERAL FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--dev-mode${COLOR_NONE}                Install/delete actions refer to a locally bundled Python package without pip (for development)"
  echo -e "  ${COLOR_LIGHT_CYAN}-y${COLOR_NONE} (--auto-prompt)        Do not prompt for approval and accept everything"
  echo -e "  ${COLOR_LIGHT_CYAN}-d${COLOR_NONE} (--dry-run)            Run all commands in dry-run mode without file system changes"
  echo -e "  ${COLOR_LIGHT_CYAN}-v${COLOR_NONE} (--verbose)            Output debug logs for commands executions"
  echo -e "  ${COLOR_LIGHT_CYAN}-s${COLOR_NONE} (--silent)             Do not output logs for commands executions"
  echo -e "  ${COLOR_LIGHT_CYAN}-h${COLOR_NONE} (--help)               Show available actions and their description"
  echo -e " "
  echo -e "${COLOR_WHITE}GLOBALS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}PYPI_TOKEN${COLOR_NONE}                Valid PyPI token with write access for publishing releases"
  echo -e "  ${COLOR_LIGHT_CYAN}GITHUB_TOKEN${COLOR_NONE}              Valid GitHub token with write access for publishing releases"
  echo -e " "
  exit 0
}

parse_program_arguments() {
  if [ $# = 0 ]; then
    print_help_menu_and_exit "$0"
  fi

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      install)
        CLI_ARGUMENT_INSTALL="install"
        shift
        ;;
      publish)
        CLI_ARGUMENT_PUBLISH="publish"
        shift
        ;;
      delete)
        CLI_ARGUMENT_DELETE="delete"
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
      --force-install-deps)
        CLI_FLAG_FORCE_INSTALL_DEPS="true"
        shift
        ;;
      --release-type)
        CLI_FLAG_RELEASE_TYPE="release-type"
        shift
        CLI_VALUE_RELEASE_TYPE=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --release-tag)
        CLI_FLAG_RELEASE_TAG="release-tag"
        shift
        CLI_VALUE_RELEASE_TAG=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --origin)
        CLI_FLAG_DELETE_ORIGIN="origin"
        shift
        CLI_VALUE_DELETE_ORIGIN=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --delete-tag)
        CLI_FLAG_DELETE_TAG="delete-tag"
        shift
        CLI_VALUE_DELETE_TAG=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --dev-mode)
        CLI_FLAG_DEV_MODE="true"
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
  ! is_install && ! is_publish && ! is_delete
}

check_install_invalid_build_type() {
  is_install && ! is_wheel_build_type && ! is_sdist_build_type
}

check_publish_invalid_release_type() {
  is_publish && ! is_pypi_release_type && ! is_github_release_type
}

check_delete_invalid_origin() {
  is_delete && ! is_pypi_local_delete_origin && ! is_pypi_remote_delete_origin && ! is_github_delete_origin
}

check_publish_release_type_missing_tokens() {
  if is_publish; then
    if is_pypi_release_type && [[ -z "${PYPI_TOKEN}" ]]; then
      log_fatal "Publish command is missing an authentication token. name: PYPI_TOKEN"
    fi
    if is_github_release_type && [[ -z "${GITHUB_TOKEN}" ]]; then
      log_fatal "Publish command is missing an authentication token. name: GITHUB_TOKEN"
    fi
  fi
}

check_publish_release_type_missing_tag() {
  if is_publish && [[ -z "${CLI_VALUE_RELEASE_TAG}" ]]; then
    log_fatal "Publish command is missing a release tag. flag: --release-tag"
  fi
}

check_delete_missing_tag() {
  if is_delete; then
    if is_pypi_remote_delete_origin && [[ -z "${CLI_VALUE_DELETE_TAG}" ]]; then
      log_fatal "Delete command from PyPi requires a delete tag. flag: --delete-tag"
    elif is_github_delete_origin && [[ -z "${CLI_VALUE_DELETE_TAG}" ]]; then
      log_fatal "Delete command from GitHub requires a delete tag. flag: --delete-tag"
    fi
  fi
}

check_no_dev_mode_for_publish() {
  if is_publish && is_dev_mode; then
    log_fatal "Publish command cannot run in dev mode"
  fi
}

check_unsupported_actions() {
  if is_wheel_build_type; then
    log_fatal "Building pip wheel is not supported yet"
  fi
  if is_pypi_release_type; then
    log_fatal "Releasing to PyPi is not supported yet"
  fi 
}

verify_program_arguments() {
  if check_legal_arguments; then
    log_fatal "Missing mandatory command argument. Options: install/publish/delete"
  fi
  if check_install_invalid_build_type; then
    log_fatal "Command argument 'install' is missing a mandatory flag value or has an invalid value. flag: --build-type, options: sdist/wheel"
  fi
  if check_publish_invalid_release_type; then
    log_fatal "Command argument 'publish' is missing a mandatory flag value or has an invalid value. flag: --release-type, options: pypi/github"
  fi
  if check_delete_invalid_origin; then
    log_fatal "Command argument 'delete' is missing a mandatory flag value or has an invalid value. flag: --origin, options: pypi-local/pypi-remote/github"
  fi
  check_publish_release_type_missing_tokens
  check_publish_release_type_missing_tag
  # check_delete_missing_tag
  check_no_dev_mode_for_publish
  check_unsupported_actions
  evaluate_dry_run_mode
}

prerequisites() {
  check_tool "poetry"

  if ! is_delete; then
    # Update lock file changes
    log_info "Updating changes to the Poetry lock file"
    cmd_run "poetry lock"
  fi
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
  resolve_project_name_version

  if is_install; then
    build_pip_package
    install_pip_package
  fi

  if is_delete; then
    delete_pip_package
  fi

  if is_publish; then
    build_pip_package
    publish_package
  fi
}

main "$@"
