#!/bin/bash

main() {
  # Should we add dev dependencies to the Poetry virtual environment
  local dev_mode="true"

  # Working directory, usually the repository root absolute path
  local working_dir=$(pwd)

  # Output verbosity (verbose / silent)
  local debug="debug"

  # Trigger the Poetry runner
  ./external/shell_scripts_lib/runner/poetry/poetry.sh \
    "working_dir: ${working_dir}" \
    "verify_venv: true" \
    "dev_mode: ${dev_mode}" \
    "poetry_args: $*" \
    "${debug}"
}

main "$@"