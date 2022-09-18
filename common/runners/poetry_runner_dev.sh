#!/bin/bash

main() {
  # Working directory, usually the repository root absolute path
  local working_dir=$(pwd)

  # Should we add dev dependencies to the Poetry virtual environment
  local dev_mode="--dev-mode"

  # Create virtual environment if one is missing
  local verify_venv="--verify-venv"

  # Output verbosity (verbose / silent)
  local verbose=""
  # local verbose="--verbose"

  # Run in dry run mode without file system changes
  local dry_run=""
  # local dry_run="--dry-run"

  # Trigger the Poetry runner
  ./external/shell_scripts_lib/runner/poetry/poetry.sh \
    "working_dir: ${working_dir}" \
    "poetry_args: $*" \
    "${dev_mode}" \
    "${verify_venv}" \
    "${verbose}" \
    "${dry_run}"
}

main "$@"