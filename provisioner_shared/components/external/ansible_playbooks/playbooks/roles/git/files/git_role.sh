#!/bin/bash

set -e

should_install_or_update() {
  [[ ! $(which git) || ($(git version) != "${git_version}") ]]
}

install_git() {

  if should_install_or_update; then

    # This must be accepted explicitly before updates for this repository can be applied
    echo "Allowing apt release info changes..."
    apt-get -y update --allow-releaseinfo-change

    echo "Updating apt packages..."
    apt-get -y update

    echo "Installing git..."
    apt-get -y install git

  else
    echo "git is already installed, skipping. version: ${git_version}"
  fi
}

uninstall_git() {
  echo "Not implemented..."
  exit 1
}

is_install() {
  [[ "${task_action}" == "install" ]]
}

is_uninstall() {
  [[ "${task_action}" == "uninstall" ]]
}

verify_mandatory_variables() {
  if [[ -z "${git_version}" ]]; then
      echo "missing mandatory argument. name: git_version"
      exit 1
  fi
}

main() {
  local task_action=$1
  local git_version=$2

  if is_install; then

    install_git

  elif is_uninstall; then

    uninstall_git
    
  else
    echo "Invalid playbook action flag, supported flags: install, uninstall."
    exit 1
  fi
}

main "$@"