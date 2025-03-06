#!/bin/bash
set -e

# Copy backup files
cp -r /tmp/app_backup/. /app

# If no arguments provided, run default test
if [ $# -eq 0 ]; then
    poetry run coverage run -m pytest
else
    poetry run coverage run -m pytest "$@"
fi

# echo -e "\n\n========= COVERAGE FULL REPORT ======================\n\n"		
# poetry run coverage report
# poetry run coverage html
# echo -e "\n====\n\nFull coverage report available on the following link:\n\n  • $(pwd)/htmlcov/index.html\n"