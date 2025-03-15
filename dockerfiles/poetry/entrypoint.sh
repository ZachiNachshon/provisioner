#!/bin/bash
set -e

. "${HOME}/.local/bin/env"

echo "Installing packages from ${TEST_SDIST_OUTPUTS_CONTAINER_PATH}..."

# poetry env info

# Install shared packages first
if find "${TEST_SDIST_OUTPUTS_CONTAINER_PATH}" -name "provisioner_shared-*.tar.gz" | grep -q .; then
    find "${TEST_SDIST_OUTPUTS_CONTAINER_PATH}" -name "provisioner_shared-*.tar.gz" -exec sh -c './.venv/bin/pip3 install --quiet {} 2>&1' \;
    echo "provisioner_shared was used from local sdist"
else
    echo "provisioner_shared was used from pip latest version"
fi

# Install runtime packages
if find "${TEST_SDIST_OUTPUTS_CONTAINER_PATH}" -name "provisioner_runtime-*.tar.gz" | grep -q .; then
    find "${TEST_SDIST_OUTPUTS_CONTAINER_PATH}" -name "provisioner_runtime-*.tar.gz" -exec sh -c './.venv/bin/pip3 install --quiet {} 2>&1' \;
    echo "provisioner_runtime was used from local sdist"
else
    echo "provisioner_runtime was used from pip latest version"
fi

# Install plugin packages
if find "${TEST_SDIST_OUTPUTS_CONTAINER_PATH}" -name "provisioner_*_plugin-*.tar.gz" | grep -q .; then
    find "${TEST_SDIST_OUTPUTS_CONTAINER_PATH}" -name "provisioner_*_plugin-*.tar.gz" -exec sh -c './.venv/bin/pip3 install --quiet {} 2>&1' \;
    echo "provisioner plugins were used from local sdists"
else
    echo "provisioner plugins were used from pip latest version"
fi

echo "Installed packages:"
./.venv/bin/pip3 list | grep prov
# poetry show | grep provisioner

echo ""

# If no arguments provided, run default test
if [ $# -eq 0 ]; then
    poetry run coverage run -m pytest
else
    poetry run coverage run -m pytest "$@"
fi

if [[ $* == *--report* ]]; then
    echo -e "\n\n========= COVERAGE FULL REPORT ======================\n\n"		
    poetry run coverage report
    poetry run coverage html
    echo -e "\n====\n\nFull coverage report available on the following link:\n\n  • $(pwd)/htmlcov/index.html\n"
fi