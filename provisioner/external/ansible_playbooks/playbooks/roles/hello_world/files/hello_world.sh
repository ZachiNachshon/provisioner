#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")

main() {
  echo "Hello World, ${ENV_USERNAME}"
}

main "$@"