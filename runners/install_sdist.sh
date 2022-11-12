#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ROOT_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/provisioner/external/shell_scripts_lib/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/provisioner/external/shell_scripts_lib/io.sh"

main() {
  cwd=$(pwd)

  log_info "Build a tarball package with local Python wheel"
  poetry build -f sdist -vvv || exit

  local pip_pkg_folder_path="${HOME}/.config/provisioner/.pip-pkg"

  if is_directory_exist "${pip_pkg_folder_path}"; then
    rm -rf "${pip_pkg_folder_path}"
  fi

  mkdir -p "${pip_pkg_folder_path}"

  mv dist/provisioner-0.1.0.tar.gz "${pip_pkg_folder_path}"

  cd "${pip_pkg_folder_path}" || exit

  tar -xvf provisioner-0.1.0.tar.gz
  mv provisioner-0.1.0 provisioner

  echo "#!/usr/bin/env python3

from provisioner.rpi.main import main

main()
" >> provisioner/dev.py

  chmod +x provisioner/dev.py

  cd "${cwd}" || exit
}

main "$@"