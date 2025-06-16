#!/bin/bash

# # Exit immediately if a command exits with a non-zero status
set -e

PROMPTER_SKIP_PROMPT=""

SCRIPT_MENU_TITLE="Poetry Package Deployer"

CLI_ARGUMENT_BUILD=""
CLI_ARGUMENT_UPLOAD=""
CLI_ARGUMENT_PRERELEASE=""

CLI_FLAG_BUILD_TYPE=""         # options: sdist/wheel
CLI_FLAG_IS_MULTI_PROJECT=""   # true/false if missing
CLI_FLAG_VERSION=""            # custom version to build with

CLI_FLAG_RELEASE_NOTES_FILE=""
CLI_FLAG_ASSETS_DIR=""
CLI_FLAG_TARGET_BRANCH=""
CLI_FLAG_RELEASE_TAG=""
CLI_FLAG_RELEASE_TITLE=""
CLI_FLAG_SOURCE_TAG=""
CLI_FLAG_UPLOAD_ACTION=""  # options: promote-rc/upload-to-pypi
CLI_FLAG_COMPRESS=""           # compress output to tar.gz format
CLI_FLAG_PROJECT_PATH=""       # project directory path
CLI_FLAG_OUTPUT_PATH=""        # output directory for compressed assets

CLI_VALUE_BUILD_TYPE=""
CLI_VALUE_VERSION=""
CLI_VALUE_RELEASE_NOTES_FILE=""
CLI_VALUE_ASSETS_DIR=""
CLI_VALUE_TARGET_BRANCH=""
CLI_VALUE_RELEASE_TAG=""
CLI_VALUE_RELEASE_TITLE=""
CLI_VALUE_SOURCE_TAG=""
CLI_VALUE_UPLOAD_ACTION=""
CLI_VALUE_COMPRESS=""
CLI_VALUE_PROJECT_PATH=""
CLI_VALUE_OUTPUT_PATH=""

POETRY_PACKAGE_NAME=""
POETRY_PACKAGE_VERSION=""

BUILD_OUTPUT_FILE_PATH=""

is_build() {
  [[ -n "${CLI_ARGUMENT_BUILD}" ]]
}

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

is_upload() {
  [[ -n "${CLI_ARGUMENT_UPLOAD}" ]]
}

is_prerelease() {
  [[ -n "${CLI_ARGUMENT_PRERELEASE}" ]]
}

get_release_notes_file() {
  echo "${CLI_VALUE_RELEASE_NOTES_FILE}"
}

get_assets_dir() {
  echo "${CLI_VALUE_ASSETS_DIR}"
}

get_target_branch() {
  echo "${CLI_VALUE_TARGET_BRANCH}"
}

get_release_tag() {
  echo "${CLI_VALUE_RELEASE_TAG}"
}

get_release_title() {
  echo "${CLI_VALUE_RELEASE_TITLE}"
}

get_source_tag() {
  echo "${CLI_VALUE_SOURCE_TAG}"
}

get_upload_action() {
  echo "${CLI_VALUE_UPLOAD_ACTION}"
}

get_version() {
  echo "${CLI_VALUE_VERSION}"
}

get_compress() {
  echo "${CLI_VALUE_COMPRESS}"
}

get_project_path() {
  echo "${CLI_VALUE_PROJECT_PATH}"
}

get_output_path() {
  echo "${CLI_VALUE_OUTPUT_PATH}"
}

is_compress_enabled() {
  [[ "${CLI_VALUE_COMPRESS}" == "tar.gz" ]]
}

is_release_candidate_format() {
  [[ "${CLI_VALUE_COMPRESS}" == "tar.gz" ]]
}

is_promote_rc_action() {
  [[ "${CLI_VALUE_UPLOAD_ACTION}" == "promote-rc" ]]
}

is_upload_to_pypi_action() {
  [[ "${CLI_VALUE_UPLOAD_ACTION}" == "upload-to-pypi" ]]
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

compress_and_rename_asset() {
  local source_file=$1
  local target_dir=$2
  
  if [[ -f "${source_file}" ]]; then
    local new_name="${POETRY_PACKAGE_NAME}-v${POETRY_PACKAGE_VERSION}.tar.gz"
    
    # Use output path if specified, otherwise use target_dir
    local output_path=$(get_output_path)
    if [[ -n "${output_path}" ]]; then
      # Create output directory if it doesn't exist
      mkdir -p "${output_path}"
      local target_path="${output_path}/${new_name}"
    else
      local target_path="${target_dir}/${new_name}"
    fi
    
    # Create tar.gz archive
    tar -czf "${target_path}" -C "$(dirname "${source_file}")" "$(basename "${source_file}")"
    log_info "Compressed and renamed to: ${new_name}"
    echo "${target_path}"
  fi
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
  
  if is_build; then
    # For build command, keep files in dist folder
    BUILD_OUTPUT_FILE_PATH="dist/${bundle_filename}"
  else
    # For publish command, move to temp folder as before
    local pip_package_folder_path=$(mktemp -d "${TMPDIR:-/tmp}/${POETRY_PACKAGE_NAME}.XXXXXX")

    new_line
    log_info "Copy build output. path: ${pip_package_folder_path}"
    mv "dist/${bundle_filename}" "${pip_package_folder_path}"
    BUILD_OUTPUT_FILE_PATH="${pip_package_folder_path}/${bundle_filename}"
  fi
}

cleanup_build_path() {
  # Only cleanup temp folders for publish command, not build command
  if ! is_build && [[ "${BUILD_OUTPUT_FILE_PATH}" == *"${POETRY_PACKAGE_VERSION}-py3-none-any.whl"* ||
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
  
  # Handle compression if specified
  if is_compress_enabled; then
    local source_file="dist/${sdist_filename}"
    local compressed_asset=$(compress_and_rename_asset "${source_file}" "dist")
    if [[ -n "${compressed_asset}" ]]; then
      # Use the compressed file as the build output
      BUILD_OUTPUT_FILE_PATH="${compressed_asset}"
    else
      set_built_output_file_path "${sdist_filename}"
    fi
  else
    set_built_output_file_path "${sdist_filename}"
  fi
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
  
  # Handle compression if specified
  if is_compress_enabled; then
    local source_file="dist/${wheel_filename}"
    local compressed_asset=$(compress_and_rename_asset "${source_file}" "dist")
    if [[ -n "${compressed_asset}" ]]; then
      # Use the compressed file as the build output
      BUILD_OUTPUT_FILE_PATH="${compressed_asset}"
    else
      set_built_output_file_path "${wheel_filename}"
    fi
  else
    set_built_output_file_path "${wheel_filename}"
  fi
}

build_pip_package() {
  # Apply custom version if specified before building
  apply_version_if_specified
  
  if is_sdist_build_type; then
    build_sdist_tarball
  elif is_wheel_build_type; then
    build_wheel_package
  else
    log_fatal "Flag --build-type has invalid value or missing a value. value: ${CLI_VALUE_BUILD_TYPE}"
  fi
}

github_is_release_tag_prefix_exist() {
  local tag=$1
  log_info "Checking if release tag exist. tag: ${tag}"
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
  gh release upload "${tag}" "${filepath}"
}

github_upload_multiple_assets() {
  local tag=$1
  local assets_dir=$2
  
  if [[ ! -d "${assets_dir}" ]]; then
    log_warning "Assets directory not found: ${assets_dir}"
    return 0
  fi
  
  local assets_count=$(ls -1 "${assets_dir}" 2>/dev/null | wc -l)
  if [[ ${assets_count} -eq 0 ]]; then
    log_warning "No assets found in directory: ${assets_dir}"
    return 0
  fi
  
  log_info "Uploading ${assets_count} assets from directory: ${assets_dir}"
  gh release upload "${tag}" "${assets_dir}"/*
}

github_create_release_tag() {
  local tag=$1
  local title=$2
  local notes_file=$3
  local is_prerelease=$4
  local target_branch=$5
  
  if [[ -z "${title}" ]]; then
    title="${tag}"
  fi
  
  local create_cmd="gh release create \"${tag}\" --title \"${title}\""
  
  if [[ -n "${notes_file}" && -f "${notes_file}" ]]; then
    create_cmd="${create_cmd} --notes-file \"${notes_file}\""
  fi
  
  if [[ "${is_prerelease}" == "true" ]]; then
    create_cmd="${create_cmd} --prerelease"
  fi
  
  if [[ -n "${target_branch}" ]]; then
    create_cmd="${create_cmd} --target \"${target_branch}\""
  fi
  
  log_info "Creating a new GitHub release. tag: ${tag}, prerelease: ${is_prerelease:-false}"
  eval "${create_cmd}"
}



create_github_prerelease_with_assets() {
  local tag=$1
  local title=$2
  local notes_file=$3
  local assets_dir=$4
  local target_branch=${5:-"master"}
  
  log_info "Creating GitHub pre-release with assets. tag: ${tag}"
  
  # Check if release already exists
  if github_is_release_tag_prefix_exist "${tag}"; then
    log_fatal "Pre-release ${tag} already exists. Cannot create duplicate release."
  fi
  
  # Create the pre-release
  github_create_release_tag "${tag}" "${title}" "${notes_file}" "true" "${target_branch}"
  
  # Upload assets if directory exists and has files
  if [[ -n "${assets_dir}" ]]; then
    github_upload_multiple_assets "${tag}" "${assets_dir}"
  fi
  
  log_info "Successfully created pre-release ${tag}"
}

download_github_release_assets() {
  local source_tag=$1
  local download_dir=${2:-"downloaded-assets"}
  
  log_info "Downloading assets from GitHub release: ${source_tag}"
  
  # Create download directory
  mkdir -p "${download_dir}"
  
  # Check if release exists
  if ! github_is_release_tag_prefix_exist "${source_tag}"; then
    log_fatal "GitHub release not found: ${source_tag}"
  fi
  
  # Download all assets from the release
  gh release download "${source_tag}" --dir "${download_dir}"
  
  local asset_count=$(ls -1 "${download_dir}" 2>/dev/null | wc -l)
  log_info "Downloaded ${asset_count} assets to: ${download_dir}"
  
  echo "${download_dir}"
}

promote_rc_to_ga_release() {
  local source_tag=$1
  local target_tag=$2
  local target_title=$3
  local notes_file=$4
  
  log_info "Promoting RC to GA release. source: ${source_tag}, target: ${target_tag}"
  
  # Download assets from RC release
  local assets_dir=$(download_github_release_assets "${source_tag}")
  
  # Check if target release already exists
  if github_is_release_tag_prefix_exist "${target_tag}"; then
    log_fatal "Target release already exists: ${target_tag}"
  fi
  
  # Create GA release (not pre-release)
  github_create_release_tag "${target_tag}" "${target_title}" "${notes_file}" "false" "master"
  
  # Upload assets to new release
  if [[ -d "${assets_dir}" ]]; then
    github_upload_multiple_assets "${target_tag}" "${assets_dir}"
  fi
  
  log_info "Successfully promoted RC to GA release: ${target_tag}"
  
  # Cleanup downloaded assets
  rm -rf "${assets_dir}"
}

upload_ga_release_to_pypi() {
  local source_tag=$1
  
  log_info "Uploading GA release to PyPI. source: ${source_tag}, package: ${POETRY_PACKAGE_NAME}"
  
  # Download assets from GA release
  local assets_dir=$(download_github_release_assets "${source_tag}")
  
  # For PyPI uploads, we need to extract the wheel file from the compressed tar.gz asset
  # First, find the compressed asset for this package
  local compressed_asset=$(find "${assets_dir}" -name "${POETRY_PACKAGE_NAME}-v*.tar.gz" | head -1)
  
  if [[ -z "${compressed_asset}" || ! -f "${compressed_asset}" ]]; then
    log_fatal "Compressed asset not found for ${POETRY_PACKAGE_NAME} in release assets: ${source_tag}"
  fi
  
  log_info "Found compressed asset: $(basename "${compressed_asset}")"
  
  # Extract the tar.gz to get the original wheel file
  local extract_dir=$(mktemp -d)
  tar -xzf "${compressed_asset}" -C "${extract_dir}"
  
  # Find the wheel file in the extracted content
  local wheel_file=$(find "${extract_dir}" -name "*.whl" | head -1)
  
  if [[ -z "${wheel_file}" || ! -f "${wheel_file}" ]]; then
    log_fatal "Wheel file not found in compressed asset for ${POETRY_PACKAGE_NAME}"
  fi
  
  log_info "Extracted wheel file: $(basename "${wheel_file}")"
  
  # Upload to PyPI
  local username="__token__"
  local password="${PYPI_API_TOKEN}"
  
  log_info "Uploading wheel to PyPI: $(basename "${wheel_file}")"
  twine upload --username "${username}" --password "${password}" "${wheel_file}"
  
  log_info "Successfully uploaded ${POETRY_PACKAGE_NAME} to PyPI: ${source_tag}"
  
  # Cleanup
  rm -rf "${extract_dir}"
  rm -rf "${assets_dir}"
}

update_poetry_version() {
  local version=$1
  log_info "Updating poetry version to: ${version}"
  poetry version "${version}"
}

update_manifest_version() {
  local version=$1
  local manifest_path="resources/manifest.json"
  
  if [[ ! -f "${manifest_path}" ]]; then
    log_warning "manifest.json not found at ${manifest_path}"
    return
  fi
  
  log_info "Updating manifest.json version to: ${version}"
  
  # Use jq to update the version field
  local temp_file=$(mktemp)
  jq --arg version "${version}" '.version = $version' "${manifest_path}" > "${temp_file}"
  mv "${temp_file}" "${manifest_path}"
}

apply_version_if_specified() {
  local custom_version=$(get_version)
  
  if [[ -n "${custom_version}" ]]; then
    log_info "Applying custom version: ${custom_version}"
    
    # Update poetry version
    update_poetry_version "${custom_version}"
    
    # Update manifest version
    update_manifest_version "${custom_version}"
    
    log_info "Version updated successfully to: ${custom_version}"
  else
    log_info "No custom version specified, using existing poetry version"
  fi
}

change_to_project_directory() {
  local project_path=$(get_project_path)
  
  if [[ -n "${project_path}" ]]; then
    if [[ ! -d "${project_path}" ]]; then
      log_fatal "Project path does not exist: ${project_path}"
    fi
    
    log_info "Changing to project directory: ${project_path}"
    cd "${project_path}" || log_fatal "Failed to change to project directory: ${project_path}"
  else
    log_info "Using current directory as project path"
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

  log_info "Identified Poetry project name and version. name: ${POETRY_PACKAGE_NAME}, version: ${POETRY_PACKAGE_VERSION}"
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
  echo -e "  ${COLOR_LIGHT_CYAN}build${COLOR_NONE}                         Build pip package (sdist/wheel) to dist folder"
  echo -e "  ${COLOR_LIGHT_CYAN}prerelease${COLOR_NONE}                    Create GitHub pre-release with assets"
  echo -e "  ${COLOR_LIGHT_CYAN}upload${COLOR_NONE}                        Download GitHub release and promote RC to GA or upload GA to PyPI"
  echo -e " "
  echo -e "${COLOR_WHITE}BUILD FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--build-type${COLOR_NONE} <option>         Package build type [${COLOR_GREEN}options: sdist/wheel${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--version${COLOR_NONE} <value>             Custom version to build (${COLOR_GREEN}default: current poetry version${COLOR_NONE})"
  echo -e "  ${COLOR_LIGHT_CYAN}--compress${COLOR_NONE} <option>           Release asset format [${COLOR_GREEN}options: tar.gz${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--output-path${COLOR_NONE} <path>          Output directory for compressed assets (${COLOR_GREEN}default: dist${COLOR_NONE})"
  echo -e " "
  echo -e "${COLOR_WHITE}UPLOAD FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--upload-action${COLOR_NONE} <option>      Upload action [${COLOR_GREEN}options: promote-rc/upload-to-pypi${COLOR_NONE}]"
  echo -e "  ${COLOR_LIGHT_CYAN}--source-tag${COLOR_NONE} <value>          Source GitHub release tag to download (${COLOR_GREEN}example: v1.0.0-RC.1${COLOR_NONE})"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-tag${COLOR_NONE} <value>         Target release tag for promote-rc action (${COLOR_GREEN}example: v1.0.0${COLOR_NONE})"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-title${COLOR_NONE} <value>       Target release title for promote-rc action"
  echo -e " "
  echo -e "${COLOR_WHITE}PRE-RELEASE FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-tag${COLOR_NONE} <value>         GitHub release tag (${COLOR_GREEN}example: v1.0.0-RC.1${COLOR_NONE})"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-title${COLOR_NONE} <value>       GitHub release title"
  echo -e "  ${COLOR_LIGHT_CYAN}--release-notes-file${COLOR_NONE} <path>   Path to release notes file"
  echo -e "  ${COLOR_LIGHT_CYAN}--assets-dir${COLOR_NONE} <path>           Directory containing assets to upload"
  echo -e "  ${COLOR_LIGHT_CYAN}--target-branch${COLOR_NONE} <branch>      Target branch for release (${COLOR_GREEN}default: master${COLOR_NONE})"
  echo -e " "
  echo -e "${COLOR_WHITE}GENERAL FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--project-path${COLOR_NONE} <path>         Path to project directory (${COLOR_GREEN}default: current directory${COLOR_NONE})"
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
      build)
        CLI_ARGUMENT_BUILD="build"
        shift
        ;;
      upload)
        CLI_ARGUMENT_UPLOAD="upload"
        shift
        ;;
      prerelease)
        CLI_ARGUMENT_PRERELEASE="prerelease"
        shift
        ;;
      --build-type)
        CLI_FLAG_BUILD_TYPE="build-type"
        shift
        CLI_VALUE_BUILD_TYPE=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --version)
        CLI_FLAG_VERSION="version"
        shift
        CLI_VALUE_VERSION=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --multi-project)
        CLI_FLAG_IS_MULTI_PROJECT="true"
        shift
        ;;
      --release-notes-file)
        CLI_FLAG_RELEASE_NOTES_FILE="release-notes-file"
        shift
        CLI_VALUE_RELEASE_NOTES_FILE=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --assets-dir)
        CLI_FLAG_ASSETS_DIR="assets-dir"
        shift
        CLI_VALUE_ASSETS_DIR=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --target-branch)
        CLI_FLAG_TARGET_BRANCH="target-branch"
        shift
        CLI_VALUE_TARGET_BRANCH=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --release-tag)
        CLI_FLAG_RELEASE_TAG="release-tag"
        shift
        CLI_VALUE_RELEASE_TAG=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --release-title)
        CLI_FLAG_RELEASE_TITLE="release-title"
        shift
        CLI_VALUE_RELEASE_TITLE=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --source-tag)
        CLI_FLAG_SOURCE_TAG="source-tag"
        shift
        CLI_VALUE_SOURCE_TAG=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --upload-action)
        CLI_FLAG_UPLOAD_ACTION="upload-action"
        shift
        CLI_VALUE_UPLOAD_ACTION=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --compress)
        CLI_FLAG_COMPRESS="compress"
        shift
        CLI_VALUE_COMPRESS=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --project-path)
        CLI_FLAG_PROJECT_PATH="project-path"
        shift
        CLI_VALUE_PROJECT_PATH=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --output-path)
        CLI_FLAG_OUTPUT_PATH="output-path"
        shift
        CLI_VALUE_OUTPUT_PATH=$(cut -d ' ' -f 2- <<<"${1}" | xargs)
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
  ! is_build && ! is_upload && ! is_prerelease
}

check_upload_invalid_action() {
  is_upload && ! is_promote_rc_action && ! is_upload_to_pypi_action
}

check_upload_missing_tokens() {
  if is_upload; then
    if [[ -z "${GITHUB_TOKEN}" ]]; then
      log_fatal "Upload command requires GITHUB_TOKEN environment variable"
    fi
    if is_upload_to_pypi_action && [[ -z "${PYPI_API_TOKEN}" ]]; then
      log_fatal "Upload action 'upload-to-pypi' requires PYPI_API_TOKEN environment variable"
    fi
  fi
}

verify_program_arguments() {
  if check_legal_arguments; then
    log_fatal "Missing mandatory command argument. Options: build, upload, prerelease"
  fi
  
  # Build type is required for build command only
  if is_build && [[ -z "${CLI_VALUE_BUILD_TYPE}" ]]; then
    log_fatal "Command 'build' requires --build-type flag. options: sdist/wheel"
  fi
  
  # Upload command validation
  if is_upload; then
    if [[ -z "${CLI_VALUE_UPLOAD_ACTION}" ]]; then
      log_fatal "Command 'upload' requires --upload-action flag. options: promote-rc/upload-to-pypi"
    fi
    if [[ -z "${CLI_VALUE_SOURCE_TAG}" ]]; then
      log_fatal "Command 'upload' requires --source-tag flag"
    fi
    if is_promote_rc_action && [[ -z "${CLI_VALUE_RELEASE_TAG}" ]]; then
      log_fatal "Upload action 'promote-rc' requires --release-tag flag"
    fi
  fi
  
  if check_upload_invalid_action; then
    log_fatal "Command 'upload' has invalid --upload-action value. options: promote-rc/upload-to-pypi"
  fi
  check_upload_missing_tokens
  
  # Pre-release command validation
  if is_prerelease; then
    if [[ -z "${CLI_VALUE_RELEASE_TAG}" ]]; then
      log_fatal "Command 'prerelease' requires --release-tag flag"
    fi
    if [[ -z "${GITHUB_TOKEN}" ]]; then
      log_fatal "Command 'prerelease' requires GITHUB_TOKEN environment variable"
    fi
  fi
}

prerequisites() {
  check_tool "poetry"
  
  # Check for jq if version updates are needed
  if [[ -n "$(get_version)" ]]; then
    check_tool "jq"
  fi

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

  change_to_project_directory
  prerequisites
  poetry_resolve_project_name_version

  if is_build; then
    log_info "Building pip package..."
    build_pip_package
    log_info "Build completed. Output: ${BUILD_OUTPUT_FILE_PATH}"
  elif is_upload; then
    log_info "Processing upload command..."
    check_tool "gh"
    
    local source_tag=$(get_source_tag)
    local upload_action=$(get_upload_action)
    
    if is_promote_rc_action; then
      local target_tag=$(get_release_tag)
      local target_title=$(get_release_title)
      local notes_file=$(get_release_notes_file)
      
      # Use default title if not provided
      if [[ -z "${target_title}" ]]; then
        target_title="Release ${target_tag}"
      fi
      
      promote_rc_to_ga_release "${source_tag}" "${target_tag}" "${target_title}" "${notes_file}"
      log_info "RC promoted to GA successfully: ${source_tag} -> ${target_tag}"
      
    elif is_upload_to_pypi_action; then
      check_tool "twine"
      upload_ga_release_to_pypi "${source_tag}"
      log_info "GA release uploaded to PyPI successfully: ${source_tag}"
    fi
  elif is_prerelease; then
    log_info "Creating GitHub pre-release..."
    check_tool "gh"
    
    local release_tag=$(get_release_tag)
    local release_title=$(get_release_title)
    local notes_file=$(get_release_notes_file)
    local assets_dir=$(get_assets_dir)
    local target_branch=$(get_target_branch)
    
    # Use default title if not provided
    if [[ -z "${release_title}" ]]; then
      release_title="Release Candidate ${release_tag}"
    fi
    
    create_github_prerelease_with_assets "${release_tag}" "${release_title}" "${notes_file}" "${assets_dir}" "${target_branch}"
    log_info "Pre-release created successfully: ${release_tag}"
  fi

  cleanup_build_path
}

main "$@"
