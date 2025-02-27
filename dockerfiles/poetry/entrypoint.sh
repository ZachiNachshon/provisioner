#!/bin/bash
set -e

# Copy backup files
cp -r /tmp/app_backup/. /app

# If no arguments provided, run default test
if [ $# -eq 0 ]; then
    exec poetry run coverage run -m pytest
else
    exec poetry run coverage run -m pytest "$@"
fi