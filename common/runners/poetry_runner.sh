#!/bin/bash

main() {
  # Working directory, usually the repository root absolute path
  local working_dir=$(pwd)

  # Create virtual environment if one is missing
  local verify_venv="--verify-venv"

  # Trigger the Poetry runner
  ./external/shell_scripts_lib/runner/poetry/poetry.sh \
    "working_dir: ${working_dir}" \
    "poetry_args: $*" \
    "${verify_venv}"
}

main "$@"