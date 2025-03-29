#!/bin/bash
set -e

. "${HOME}/.local/bin/env"

# Set terminal width to avoid line wrapping
export COLUMNS=200
export PYTHONIOENCODING=utf-8
# Set pytest options for cleaner output
export PYTEST_ADDOPTS="--tb=short --no-header --import-mode=importlib --ignore=.venv"

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

# Handle coverage reports based on COVERAGE_REPORT_TYPE environment variable
if [ -n "$COVERAGE_REPORT_TYPE" ]; then
    echo -e "\n\n========= COVERAGE FULL REPORT ======================\n\n"		
    poetry run coverage report

    case $COVERAGE_REPORT_TYPE in
        "html")
            poetry run coverage html
            echo -e "\n====\n\nFull coverage report available on the following link:\n\n  • $(pwd)/htmlcov/index.html\n"
            ;;
        "xml")
            poetry run coverage xml
            echo -e "\n====\n\nXML coverage report available at:\n\n  • $(pwd)/coverage.xml\n"
            ;;
        *)
            echo "Warning: Unknown report type '$COVERAGE_REPORT_TYPE'. Defaulting to HTML report."
            poetry run coverage html
            echo -e "\n====\n\nFull coverage report available on the following link:\n\n  • $(pwd)/htmlcov/index.html\n"
            ;;
    esac
fi