#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ROOT_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/provisioner/external/shell_scripts_lib/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/provisioner/external/shell_scripts_lib/io.sh"

main() {
  cwd=$(pwd)

  log_info "Build a local Python pip wheel"
  poetry build -f wheel -vvv || exit

  local pip_pkg_folder_path="${HOME}/.config/provisioner/.pip-pkg"

  if is_directory_exist "${pip_pkg_folder_path}"; then
    rm -rf "${pip_pkg_folder_path}"
  fi

  mkdir -p "${pip_pkg_folder_path}"

  mv dist/provisioner-0.1.0-py3-none-any.whl "${pip_pkg_folder_path}"

  cd "${pip_pkg_folder_path}" || exit

  echo "#!/usr/bin/env python3

from provisioner.rpi.main import main

main()
" >> dev.py

  chmod +x dev.py

  cd "${cwd}" || exit
}

main "$@"