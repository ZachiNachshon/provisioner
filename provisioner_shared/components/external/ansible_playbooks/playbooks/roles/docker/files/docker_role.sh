#!/bin/bash

set -e

install_docker() {

  # https://docs.docker.com/engine/install/debian/#install-using-the-repository
  if [[ ! $(which docker) || ($(docker --version) != "v${docker_version}") ]]; then

    echo "Setting up the repository..."
    apt-get update
    apt-get install \
      ca-certificates \
      curl \
      gnupg \
      lsb-release

    echo "Adding Dockers official GPG key"
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    echo "Starting Docker engine installation. version: ${docker_version}"
    apt-get install -y \
      docker-ce="${docker_version}" \
      docker-ce-cli="${docker_version}" \
      containerd.io

    # Add user to the Docker group
    echo "Adding user to a Docker group. name: ${docker_user}"
    usermod -aG docker "${docker_user}"

    echo "Verifying Docker engine installation"
    docker run hello-world

  else
    echo "Docker is already installed, skipping. version: ${docker_version}"
  fi
}

uninstall_docker() {
  apt-get purge docker-ce docker-ce-cli containerd.io
  rm -rf /var/lib/docker
  rm -rf /var/lib/containerd
}

is_install() {
  [[ "${task_action}" == "install" ]]
}

is_uninstall() {
  [[ "${task_action}" == "uninstall" ]]
}

verify_mandatory_variables() {
  if [[ -z "${docker_version}" ]]; then
      echo "missing mandatory argument. name: docker_version"
      exit 1
  fi

  if [[ -z "${docker_user}" ]]; then
      echo "missing mandatory argument. name: docker_user"
      exit 1
  fi
}

main() {
  local task_action=$1
  local docker_version=$2
  local docker_user=$3

  if is_install; then

    verify_mandatory_variables
    install_docker

  elif is_uninstall; then

    uninstall_docker
    
  else
    echo "Invalid playbook action flag, supported flags: install, uninstall."
    exit 1
  fi
}

main "$@"